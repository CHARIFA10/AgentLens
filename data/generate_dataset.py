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


def make_success(i):
    order = 1000 + i
    task_desc = f"Where is order {order}?"
    events = [
        event("e1", "user_message", f"Where is order {order}?"),
        event("e2", "agent_message", "I'll check the order for you."),
        event(
            "e3",
            "tool_call",
            "Getting order information",
            tool="get_order",
            arguments={"order_id": str(order)},
        ),
        event(
            "e4",
            "tool_result",
            f"Order {order} is in transit.",
            tool="get_order",
            status="success",
        ),
        event("e5", "agent_message", f"Order {order} is currently in transit."),
    ]
    return task_desc, events


def make_recovery(i):
    order = 2000 + i
    task_desc = f"Check order {order} status and recover if error"
    events = [
        event("e1", "user_message", f"Check order {order}."),
        event("e2", "agent_message", "I'll check that for you."),
        event(
            "e3",
            "tool_call",
            "Getting order",
            tool="get_order",
            arguments={"order_id": str(order)},
        ),
        event(
            "e4",
            "tool_result",
            "Temporary timeout.",
            tool="get_order",
            status="failed",
        ),
        event(
            "e5",
            "tool_call",
            "Retrying get_order",
            tool="get_order",
            arguments={"order_id": str(order)},
        ),
        event(
            "e6",
            "tool_result",
            f"Order {order} is delivered.",
            tool="get_order",
            status="success",
        ),
        event("e7", "agent_message", f"Order {order} has been delivered successfully."),
    ]
    return task_desc, events


def make_unsupported_success(i):
    order = 3000 + i
    task_desc = f"Cancel order {order}"
    events = [
        event("e1", "user_message", f"Please cancel order {order}."),
        event("e2", "agent_message", "I'll cancel that order."),
        event(
            "e3",
            "tool_call",
            "Calling cancel_order",
            tool="cancel_order",
            arguments={"order_id": str(order)},
        ),
        event(
            "e4",
            "tool_result",
            "Order already shipped.",
            tool="cancel_order",
            status="failed",
        ),
        event("e5", "agent_message", "Your order has been successfully cancelled."),
    ]
    return task_desc, events


def make_repeated_question(i):
    order = 4000 + i
    task_desc = f"Inquire about order {order}"
    events = [
        event("e1", "user_message", f"Where is order {order}?"),
        event("e2", "agent_message", "What is your order number?"),
        event("e3", "user_message", str(order)),
        event("e4", "agent_message", "Could you provide your order number?"),
        event("e5", "user_message", f"I already gave you {order}."),
        event("e6", "agent_message", "What is your order number?"),
    ]
    return task_desc, events


def make_no_progress(i):
    task_desc = "Find replacement part for device"
    events = [
        event("e1", "user_message", "Find a replacement part for my device."),
        event("e2", "agent_message", "I'll search the inventory."),
        event(
            "e3",
            "tool_call",
            "Searching inventory",
            tool="search_inventory",
            arguments={"query": "replacement part"},
        ),
        event(
            "e4",
            "tool_result",
            "0 results",
            tool="search_inventory",
            status="success",
        ),
        event(
            "e5",
            "tool_call",
            "Searching inventory again",
            tool="search_inventory",
            arguments={"query": "replacement part"},
        ),
        event(
            "e6",
            "tool_result",
            "0 results",
            tool="search_inventory",
            status="success",
        ),
        event(
            "e7",
            "tool_call",
            "Searching inventory again",
            tool="search_inventory",
            arguments={"query": "replacement part"},
        ),
        event(
            "e8",
            "tool_result",
            "0 results",
            tool="search_inventory",
            status="success",
        ),
        event("e9", "agent_message", "I couldn't find a matching part."),
    ]
    return task_desc, events


def make_incomplete(i):
    order = 5000 + i
    task_desc = f"Book delivery and email confirmation for order {order}"
    events = [
        event(
            "e1",
            "user_message",
            f"Book delivery and email the confirmation for order {order}.",
        ),
        event(
            "e2",
            "agent_message",
            "I'll book the delivery and send the confirmation.",
        ),
        event(
            "e3",
            "tool_call",
            "Booking delivery",
            tool="book_delivery",
            arguments={"order_id": str(order)},
        ),
        event(
            "e4",
            "tool_result",
            "Delivery booked.",
            tool="book_delivery",
            status="success",
        ),
        event(
            "e5",
            "agent_message",
            "Your request is complete. The confirmation has been handled.",
        ),
    ]
    return task_desc, events


def make_wrong_target(i):
    requested_id = 4820 + i
    modified_id = 4890 + i
    task_desc = f"Update customer {requested_id}'s email"
    events = [
        event(
            "e1",
            "user_message",
            f"Update customer {requested_id}'s email to new@example.com.",
        ),
        event(
            "e2",
            "agent_message",
            f"I'll locate customer {requested_id} and update their email.",
        ),
        event(
            "e3",
            "tool_call",
            f"Looking up customer {requested_id}",
            tool="get_customer",
            arguments={"customer_id": str(requested_id)},
        ),
        event(
            "e4",
            "tool_result",
            f"Customer record for {requested_id} found.",
            tool="get_customer",
            status="success",
        ),
        event(
            "e5",
            "tool_call",
            f"Updating email for customer {modified_id}",
            tool="update_customer",
            arguments={"customer_id": str(modified_id), "email": "new@example.com"},
        ),
        event(
            "e6",
            "tool_result",
            f"Customer {modified_id} updated successfully.",
            tool="update_customer",
            status="success",
        ),
        event(
            "e7",
            "agent_message",
            f"Customer {requested_id} has been updated.",
        ),
    ]
    return task_desc, events


def make_legitimate_repeated_search(i):
    task_desc = "Search catalog for battery replacement"
    events = [
        event("e1", "user_message", "Find a replacement battery for model X."),
        event("e2", "agent_message", "Searching the catalog."),
        event(
            "e3",
            "tool_call",
            "Searching inventory",
            tool="search_inventory",
            arguments={"query": "battery model X"},
        ),
        event(
            "e4",
            "tool_result",
            "14 results found.",
            tool="search_inventory",
            status="success",
        ),
        event(
            "e5",
            "tool_call",
            "Narrowing search",
            tool="search_inventory",
            arguments={"query": "battery model X li-ion"},
        ),
        event(
            "e6",
            "tool_result",
            "4 results found.",
            tool="search_inventory",
            status="success",
        ),
        event("e7", "agent_message", "Found 4 matching lithium-ion battery options."),
    ]
    return task_desc, events


def make_legitimate_failed_action(i):
    order = 7000 + i
    task_desc = f"Cancel order {order}"
    events = [
        event("e1", "user_message", f"Please cancel order {order}."),
        event("e2", "agent_message", "I will try to cancel the order."),
        event(
            "e3",
            "tool_call",
            "Cancelling order",
            tool="cancel_order",
            arguments={"order_id": str(order)},
        ),
        event(
            "e4",
            "tool_result",
            "Order already shipped.",
            tool="cancel_order",
            status="failed",
        ),
        event(
            "e5",
            "agent_message",
            f"I couldn't cancel order {order} because the order has already shipped.",
        ),
    ]
    return task_desc, events


def make_ambiguous(i):
    order = 6000 + i
    task_desc = f"Check refund status for order {order}"
    events = [
        event("e1", "user_message", f"Can you check the refund for order {order}?"),
        event("e2", "agent_message", "I'll check the refund status."),
        event(
            "e3",
            "tool_call",
            "Checking refund status",
            tool="refund_status",
            arguments={"order_id": str(order)},
        ),
        event(
            "e4",
            "tool_result",
            "Upstream response incomplete.",
            tool="refund_status",
            status="unknown",
        ),
        event("e5", "agent_message", "The refund status could not be confirmed."),
    ]
    return task_desc, events


generators = [
    ("success", make_success, 10),
    ("recovery", make_recovery, 8),
    ("unsupported_success", make_unsupported_success, 8),
    ("repeated_question", make_repeated_question, 7),
    ("no_progress", make_no_progress, 6),
    ("incomplete_task", make_incomplete, 7),
    ("wrong_target", make_wrong_target, 7),
    ("legitimate_repeated_search", make_legitimate_repeated_search, 4),
    ("legitimate_failed_action", make_legitimate_failed_action, 4),
    ("ambiguous", make_ambiguous, 4),
]


traces = []
ground_truth = []

counter = 1
start_time = datetime(2026, 9, 27, 10, 0, 0)

for category, generator, count in generators:
    for i in range(count):
        trace_id = f"trace_{counter:03d}"
        task_desc, events = generator(i + 1)

        traces.append({
            "trace_id": trace_id,
            "session_id": f"session_{counter:03d}",
            "timestamp": (start_time + timedelta(minutes=counter)).isoformat() + "Z",
            "agent": "customer_support",
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


with open(OUTPUT / "traces.json", "w", encoding="utf-8") as f:
    json.dump(traces, f, indent=2, ensure_ascii=False)

with open(OUTPUT / "ground_truth.json", "w", encoding="utf-8") as f:
    json.dump(ground_truth, f, indent=2, ensure_ascii=False)


print(f"Generated {len(traces)} customer support traces.")
for category, _, count in generators:
    print(f"  {category:30} {count}")
