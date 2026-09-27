import json
import random
from pathlib import Path
from datetime import datetime, timedelta


random.seed(42)

OUTPUT = Path(__file__).parent


def event(event_id, event_type, content, **kwargs):
    data = {
        "event_id": event_id,
        "type": event_type,
        "content": content,
    }
    data.update(kwargs)
    return data


def make_coding_success(i):
    bug_id = 100 + i
    task_desc = f"Fix authentication bug #{bug_id} and make sure the tests pass"
    events = [
        event(
            "e1",
            "user_message",
            f"Fix the authentication token expiration bug #{bug_id} and make sure the tests pass.",
        ),
        event("e2", "agent_message", "I'll locate the token verification logic, apply the fix, and run tests."),
        event(
            "e3",
            "tool_call",
            "Searching for token verification",
            tool="search_code",
            arguments={"query": "verify_token_expiration"},
        ),
        event(
            "e4",
            "tool_result",
            "src/auth/token.py:42: def verify_token_expiration():",
            tool="search_code",
            status="success",
        ),
        event(
            "e5",
            "tool_call",
            "Reading auth token file",
            tool="read_file",
            arguments={"file_path": "src/auth/token.py"},
        ),
        event(
            "e6",
            "tool_result",
            "45 lines read from src/auth/token.py",
            tool="read_file",
            status="success",
        ),
        event(
            "e7",
            "tool_call",
            "Applying patch to token expiration logic",
            tool="write_file",
            arguments={"file_path": "src/auth/token.py", "patch": "fix expiration window"},
        ),
        event(
            "e8",
            "tool_result",
            "File src/auth/token.py updated successfully.",
            tool="write_file",
            status="success",
        ),
        event(
            "e9",
            "tool_call",
            "Running test suite",
            tool="run_tests",
            arguments={"test_path": "tests/test_auth.py"},
        ),
        event(
            "e10",
            "tool_result",
            "42 passed in 1.45s",
            tool="run_tests",
            status="success",
        ),
        event(
            "e11",
            "agent_message",
            "The bug is fixed and all tests pass.",
        ),
    ]
    return task_desc, events


def make_coding_recovery(i):
    bug_id = 200 + i
    task_desc = f"Fix race condition in session manager #{bug_id}"
    events = [
        event("e1", "user_message", f"Fix the session race condition #{bug_id} and verify the tests pass."),
        event("e2", "agent_message", "I'll update the mutex lock and verify tests."),
        event(
            "e3",
            "tool_call",
            "Updating mutex lock",
            tool="write_file",
            arguments={"file_path": "src/session.py"},
        ),
        event("e4", "tool_result", "src/session.py written", tool="write_file", status="success"),
        event("e5", "tool_call", "Running test suite", tool="run_tests", arguments={"test_path": "tests/test_session.py"}),
        event("e6", "tool_result", "Test timeout: deadlock detected.", tool="run_tests", status="failed"),
        event("e7", "tool_call", "Reviewing git diff", tool="git_diff", arguments={}),
        event("e8", "tool_result", "+ with self._lock:\n+     acquire()", tool="git_diff", status="success"),
        event(
            "e9",
            "tool_call",
            "Applying corrected non-blocking lock patch",
            tool="write_file",
            arguments={"file_path": "src/session.py"},
        ),
        event("e10", "tool_result", "src/session.py updated", tool="write_file", status="success"),
        event("e11", "tool_call", "Re-running test suite", tool="run_tests", arguments={"test_path": "tests/test_session.py"}),
        event("e12", "tool_result", "42 passed in 0.85s", tool="run_tests", status="success"),
        event("e13", "agent_message", "The race condition is resolved and all tests now pass."),
    ]
    return task_desc, events


def make_coding_unsupported_success(i):
    bug_id = 300 + i
    task_desc = f"Fix database connection leak #{bug_id}"
    events = [
        event("e1", "user_message", f"Fix the database connection leak #{bug_id} and ensure tests pass."),
        event("e2", "agent_message", "I'll patch the connection pool and run the test suite."),
        event(
            "e3",
            "tool_call",
            "Patching connection pool",
            tool="write_file",
            arguments={"file_path": "src/db/pool.py"},
        ),
        event("e4", "tool_result", "src/db/pool.py updated.", tool="write_file", status="success"),
        event(
            "e5",
            "tool_call",
            "Running tests",
            tool="run_tests",
            arguments={"test_path": "tests/test_db.py"},
        ),
        event(
            "e6",
            "tool_result",
            "FAILED: 3 tests failed with ConnectionError",
            tool="run_tests",
            status="failed",
        ),
        event(
            "e7",
            "agent_message",
            "The bug is fixed and all tests pass.",
        ),
    ]
    return task_desc, events


def make_coding_incomplete(i):
    bug_id = 500 + i
    task_desc = f"Fix validator bug #{bug_id} and run tests"
    events = [
        event("e1", "user_message", f"Fix the input validator bug #{bug_id} and run tests."),
        event("e2", "agent_message", "I'll edit the validator code and verify."),
        event(
            "e3",
            "tool_call",
            "Modifying validator regex",
            tool="write_file",
            arguments={"file_path": "src/validator.py"},
        ),
        event("e4", "tool_result", "src/validator.py written.", tool="write_file", status="success"),
        event("e5", "agent_message", "Done. The bug has been fixed."),
    ]
    return task_desc, events


def make_coding_no_progress(i):
    task_desc = "Locate deprecated cryptographic cipher in codebase"
    events = [
        event("e1", "user_message", "Find all usages of DES cipher in the repo."),
        event("e2", "agent_message", "Searching codebase for DES cipher."),
        event("e3", "tool_call", "Searching code", tool="search_code", arguments={"query": "DES_cipher"}),
        event("e4", "tool_result", "0 results", tool="search_code", status="success"),
        event("e5", "tool_call", "Searching code", tool="search_code", arguments={"query": "DES_cipher"}),
        event("e6", "tool_result", "0 results", tool="search_code", status="success"),
        event("e7", "tool_call", "Searching code", tool="search_code", arguments={"query": "DES_cipher"}),
        event("e8", "tool_result", "0 results", tool="search_code", status="success"),
        event("e9", "agent_message", "I couldn't find any occurrences of DES cipher."),
    ]
    return task_desc, events


def make_coding_repeated_question(i):
    task_desc = "Refactor payment service integration"
    events = [
        event("e1", "user_message", "Refactor the payment gateway to use v2 API."),
        event("e2", "agent_message", "Which target branch should I branch off from?"),
        event("e3", "user_message", "release-2.4"),
        event("e4", "agent_message", "Could you confirm the target branch for this task?"),
        event("e5", "user_message", "I just told you: release-2.4."),
        event("e6", "agent_message", "Which target branch should I branch off from?"),
    ]
    return task_desc, events


def make_coding_legitimate_repeated_search(i):
    task_desc = "Inspect user authentication handler"
    events = [
        event("e1", "user_message", "Find where user authentication handlers are registered."),
        event("e2", "agent_message", "Searching codebase."),
        event("e3", "tool_call", "Searching code", tool="search_code", arguments={"query": "auth_handler"}),
        event("e4", "tool_result", "12 results found in controllers/", tool="search_code", status="success"),
        event("e5", "tool_call", "Searching specific controller", tool="search_code", arguments={"query": "register_auth_handler"}),
        event("e6", "tool_result", "2 results found in controllers/auth.py", tool="search_code", status="success"),
        event("e7", "tool_call", "Reading controller", tool="read_file", arguments={"file_path": "controllers/auth.py"}),
        event("e8", "tool_result", "80 lines read", tool="read_file", status="success"),
        event("e9", "agent_message", "Found the registration at controllers/auth.py:45."),
    ]
    return task_desc, events


def make_coding_legitimate_failed_action(i):
    task_desc = "Cherry-pick patch 8129 to stable branch"
    events = [
        event("e1", "user_message", "Apply commit patch 8129 to stable branch."),
        event("e2", "agent_message", "Applying git cherry-pick."),
        event("e3", "tool_call", "Running git command", tool="run_command", arguments={"command": "git cherry-pick 8129"}),
        event("e4", "tool_result", "error: could not apply 8129... merge conflict in auth.py", tool="run_command", status="failed"),
        event("e5", "agent_message", "I couldn't apply commit 8129 because of merge conflicts in auth.py."),
    ]
    return task_desc, events


def make_coding_ambiguous(i):
    task_desc = "Run benchmark suite on memory profiler"
    events = [
        event("e1", "user_message", "Run memory benchmark tests."),
        event("e2", "agent_message", "Executing benchmarks."),
        event("e3", "tool_call", "Running test benchmark", tool="run_tests", arguments={"test_path": "benchmarks/mem.py"}),
        event("e4", "tool_result", "CI runner socket closed unexpectedly: status unknown", tool="run_tests", status="unknown"),
        event("e5", "agent_message", "The benchmark test status could not be confirmed due to CI runner termination."),
    ]
    return task_desc, events


coding_generators = [
    ("success", make_coding_success, 8),
    ("recovery", make_coding_recovery, 6),
    ("unsupported_success", make_coding_unsupported_success, 6),
    ("incomplete_task", make_coding_incomplete, 6),
    ("no_progress", make_coding_no_progress, 5),
    ("repeated_question", make_coding_repeated_question, 5),
    ("legitimate_repeated_search", make_coding_legitimate_repeated_search, 4),
    ("legitimate_failed_action", make_coding_legitimate_failed_action, 4),
    ("ambiguous", make_coding_ambiguous, 4),
]


traces = []
ground_truth = []

counter = 1
start_time = datetime(2026, 9, 27, 14, 0, 0)

for category, generator, count in coding_generators:
    for i in range(count):
        trace_id = f"coding_trace_{counter:03d}"
        task_desc, events = generator(i + 1)

        traces.append({
            "trace_id": trace_id,
            "session_id": f"coding_session_{counter:03d}",
            "timestamp": (start_time + timedelta(minutes=counter)).isoformat() + "Z",
            "agent": "coding_agent",
            "task": {"description": task_desc},
            "events": events,
        })

        if category in [
            "success",
            "recovery",
            "legitimate_repeated_search",
            "legitimate_failed_action",
            "ambiguous",
        ]:
            outcome = "recovery" if category == "recovery" else ("ambiguous" if category == "ambiguous" else "success")
            failure_type = None
        else:
            outcome = "failure"
            failure_type = category

        ground_truth.append({
            "trace_id": trace_id,
            "outcome": outcome,
            "failure_type": failure_type,
        })

        counter += 1


with open(OUTPUT / "coding_traces.json", "w", encoding="utf-8") as f:
    json.dump(traces, f, indent=2, ensure_ascii=False)

with open(OUTPUT / "coding_ground_truth.json", "w", encoding="utf-8") as f:
    json.dump(ground_truth, f, indent=2, ensure_ascii=False)


print(f"Generated {len(traces)} coding agent traces.")
for category, _, count in coding_generators:
    print(f"  {category:30} {count}")
