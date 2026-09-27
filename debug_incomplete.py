import json
import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

with open("data/traces.json", "r", encoding="utf-8") as f:
    traces = json.load(f)

with open("data/ground_truth.json", "r", encoding="utf-8") as f:
    truth = json.load(f)

incomplete_ids = {
    row["trace_id"]
    for row in truth
    if row["failure_type"] == "incomplete_task"
}

for trace in traces:

    if trace["trace_id"] not in incomplete_ids:
        continue

    print("\n" + "=" * 70)
    print(trace["trace_id"])
    print("TASK:", trace["task"]["description"])

    for event in trace["events"]:
        print(
            f"{event['type']:15} "
            f"{event.get('tool', ''):20} "
            f"{event.get('status', ''):10} "
            f"{event['content']}"
        )
