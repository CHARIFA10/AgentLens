import re
from typing import Optional

from agentlens.analysis.similarity import semantic_similarity
from agentlens.schema.models import Trace, Finding
from agentlens.schema.profiles import get_agent_profile


SUCCESS_WORDS = re.compile(
    r"\b("
    r"successfully|"
    r"completed|"
    r"done|"
    r"cancelled|"
    r"updated|"
    r"sent|"
    r"processed|"
    r"fixed"
    r")\b",
    re.IGNORECASE,
)

FAILURE_DISCLOSURE_WORDS = re.compile(
    r"\b("
    r"could not|"
    r"couldn't|"
    r"unable to|"
    r"failed to|"
    r"cannot|"
    r"can't|"
    r"was not able to|"
    r"unfortunately"
    r")\b",
    re.IGNORECASE,
)


def detect_wrong_target(trace: Trace) -> Finding | None:
    """
    Detects cases where tools executed successfully, but operated on
    a different entity than the one explicitly requested by the user.
    """
    user_messages = [
        event.content
        for event in trace.events
        if event.type == "user_message" and event.content
    ]
    if not user_messages:
        return None

    user_text = " ".join(user_messages)

    target_match = re.search(
        r"\b(customer|order|user|account)\s+(?:id\s+|#)?(\d+)\b",
        user_text,
        re.IGNORECASE,
    )
    if not target_match:
        return None

    entity_type = target_match.group(1).lower()
    expected_id = target_match.group(2)

    # Check tool calls for mismatched entity IDs
    for event in trace.events:
        if event.type == "tool_call" and event.arguments:
            for key, val in event.arguments.items():
                val_str = str(val).strip()
                if val_str.isdigit() and val_str != expected_id:
                    # Check if agent subsequently claimed the expected entity was handled
                    agent_claims = [
                        e.content
                        for e in trace.events
                        if e.type == "agent_message" and e.content
                    ]
                    claim_matches = [
                        msg for msg in agent_claims
                        if expected_id in msg and any(
                            word in msg.lower()
                            for word in ["updated", "cancelled", "handled", "processed", "complete", "success"]
                        )
                    ]
                    if claim_matches:
                        return Finding(
                            trace_id=trace.trace_id,
                            failure_type="wrong_target",
                            confidence=0.96,
                            severity=0.95,
                            evidence=[
                                f"User requested action on {entity_type} '{expected_id}'.",
                                f"Tool '{event.tool}' was executed with '{key}={val_str}' instead.",
                                f"Agent confirmed action on {entity_type} '{expected_id}': '{claim_matches[-1]}'.",
                            ],
                        )

    return None


def detect_unsupported_success(trace: Trace) -> Finding | None:
    """
    Detects cases where a tool returned a failure that was never recovered,
    yet the agent claimed the operation succeeded.
    """
    # Track unrecovered failed tools
    unrecovered_failed_tools = []
    for i, event in enumerate(trace.events):
        if event.type == "tool_result" and event.status == "failed":
            # Check if there is a later successful result for this tool
            later_success = any(
                later.type == "tool_result"
                and later.tool == event.tool
                and later.status == "success"
                for later in trace.events[i + 1:]
            )
            if not later_success:
                unrecovered_failed_tools.append(event)

    if not unrecovered_failed_tools:
        return None

    # Check for agent success messages
    success_messages = []
    for event in trace.events:
        if event.type == "agent_message" and event.content:
            # If the agent explicitly disclosed failure, it is not an unsupported success
            if FAILURE_DISCLOSURE_WORDS.search(event.content):
                continue
            if SUCCESS_WORDS.search(event.content):
                success_messages.append(event)

    if not success_messages:
        return None

    failed_tool = unrecovered_failed_tools[-1]
    success_message = success_messages[-1]

    return Finding(
        trace_id=trace.trace_id,
        failure_type="unsupported_success",
        confidence=0.94,
        severity=0.90,
        evidence=[
            f"Tool '{failed_tool.tool}' returned failure: {failed_tool.content}",
            f"Agent subsequently made a success claim: {success_message.content}",
        ],
    )


def detect_repeated_question(trace: Trace) -> Finding | None:
    messages = [
        event.content
        for event in trace.events
        if event.type == "agent_message" and event.content
    ]

    if len(messages) < 2:
        return None

    for i in range(len(messages)):
        for j in range(i + 1, len(messages)):
            similarity = semantic_similarity(messages[i], messages[j])
            if similarity >= 0.85:
                return Finding(
                    trace_id=trace.trace_id,
                    failure_type="repeated_question",
                    confidence=similarity,
                    severity=0.65,
                    evidence=[
                        "Two agent messages are semantically similar.",
                        f"Message A: {messages[i]}",
                        f"Message B: {messages[j]}",
                        f"Similarity: {similarity:.2f}",
                    ],
                )

    return None


def detect_no_progress(trace: Trace) -> Finding | None:
    results = [
        event
        for event in trace.events
        if event.type == "tool_result" and event.content
    ]

    if len(results) < 3:
        return None

    last_three = results[-3:]
    contents = [event.content.strip().lower() for event in last_three]

    if len(set(contents)) != 1:
        return None

    if not (
        "0 results" in contents[0]
        or "no results" in contents[0]
    ):
        return None

    return Finding(
        trace_id=trace.trace_id,
        failure_type="no_progress",
        confidence=0.92,
        severity=0.70,
        evidence=[
            "The same unsuccessful search result was observed three consecutive times.",
            f"Repeated result: {last_three[-1].content}",
        ],
    )


def detect_incomplete_task(trace: Trace) -> Finding | None:
    """
    Detects cases where the user requested multiple actions,
    but the agent completed only part of the request and
    still claimed completion. Uses AgentProfile capability mapping.
    """
    user_messages = [
        event.content.lower()
        for event in trace.events
        if event.type == "user_message" and event.content
    ]
    if not user_messages:
        return None

    user_request = " ".join(user_messages)
    profile = get_agent_profile(trace.agent)

    tool_calls = {
        event.tool
        for event in trace.events
        if event.type == "tool_call" and event.tool
    }

    agent_messages = [
        event.content.lower()
        for event in trace.events
        if event.type == "agent_message" and event.content
    ]

    completion_claim = any(
        phrase in message
        for message in agent_messages
        for phrase in [
            "request is complete",
            "completed",
            "successfully completed",
            "all done",
            "done",
            "finished",
            "bug is fixed and all tests pass",
            "fixed and all tests pass",
            "has been handled",
            "confirmation has been handled",
        ]
    )

    if not completion_claim:
        return None

    # Derive expected tools from profile capability keywords
    expected_tools = []
    for tool_name, capability in profile.tools.items():
        if any(keyword in user_request for keyword in capability.action_keywords):
            expected_tools.append(tool_name)

    missing_tools = [
        tool
        for tool in expected_tools
        if tool not in tool_calls
    ]

    if not missing_tools or not tool_calls:
        return None

    return Finding(
        trace_id=trace.trace_id,
        failure_type="incomplete_task",
        confidence=0.90,
        severity=0.80,
        evidence=[
            f"User request: {user_request}",
            f"Expected tools: {expected_tools}",
            f"Observed tools: {sorted(tool_calls)}",
            f"Missing expected tools: {missing_tools}",
            "Agent claimed the request was complete.",
        ],
    )


def detect_trace(trace: Trace) -> list[Finding]:
    detectors = [
        detect_wrong_target,
        detect_unsupported_success,
        detect_repeated_question,
        detect_no_progress,
        detect_incomplete_task,
    ]

    findings = []
    for detector in detectors:
        finding = detector(trace)
        if finding:
            findings.append(finding)

    return findings
