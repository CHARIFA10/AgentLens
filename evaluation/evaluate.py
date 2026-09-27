import json
import sys
from pathlib import Path

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)

# Ensure UTF-8 stdout encoding for Windows console
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agentlens.ingestion.loader import load_traces
from agentlens.analysis.pipeline import analyze


def evaluate_dataset(name: str, traces_file: Path, truth_file: Path):
    print("\n" + "=" * 70)
    print(f"AGENTLENS EVALUATION — {name.upper()}")
    print("=" * 70)

    traces = load_traces(traces_file)
    findings, _ = analyze(traces)

    with open(truth_file, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    predictions = {finding.trace_id: finding.failure_type for finding in findings}
    ground_truth_by_id = {row["trace_id"]: row for row in ground_truth}

    # 1. FAILURE DETECTION
    y_true_failure = []
    y_pred_failure = []

    for trace in traces:
        trace_id = trace.trace_id
        actual = ground_truth_by_id[trace_id]
        actual_failure = actual["outcome"] == "failure"
        predicted_failure = trace_id in predictions
        y_true_failure.append(actual_failure)
        y_pred_failure.append(predicted_failure)

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true_failure,
        y_pred_failure,
        average="binary",
        zero_division=0,
    )

    print(f"\n1. FAILURE DETECTION ({len(traces)} traces)")
    print(f"   Precision : {precision:.2f}")
    print(f"   Recall    : {recall:.2f}")
    print(f"   F1-score  : {f1:.2f}")

    # 2. FAILURE TYPE CLASSIFICATION
    failure_labels = [
        "wrong_target",
        "unsupported_success",
        "repeated_question",
        "no_progress",
        "incomplete_task",
    ]

    y_true_type = []
    y_pred_type = []

    for trace in traces:
        trace_id = trace.trace_id
        actual = ground_truth_by_id[trace_id]
        if actual["outcome"] != "failure":
            continue
        y_true_type.append(actual["failure_type"])
        y_pred_type.append(predictions.get(trace_id, "undetected"))

    labels = failure_labels + ["undetected"]

    print("\n2. FAILURE TYPE CLASSIFICATION")
    print(
        classification_report(
            y_true_type,
            y_pred_type,
            labels=labels,
            zero_division=0,
        )
    )

    print("3. CONFUSION MATRIX")
    print(confusion_matrix(y_true_type, y_pred_type, labels=labels))
    print(f"Labels: {labels}")

    # 4. RECOVERY SAFETY
    recovery_ids = {row["trace_id"] for row in ground_truth if row["outcome"] == "recovery"}
    false_positive_recoveries = [t for t in recovery_ids if t in predictions]

    print("\n4. RECOVERY SAFETY")
    print(f"   Legitimate recoveries : {len(recovery_ids)}")
    print(f"   Incorrectly flagged   : {len(false_positive_recoveries)}")
    if false_positive_recoveries:
        print(f"   [!] False positives: {false_positive_recoveries}")
    else:
        print("   ✓ No legitimate recoveries were flagged.")

    # 5. HARD NEGATIVE CASES & AMBIGUOUS CASES
    hard_negatives = {
        row["trace_id"]
        for row in ground_truth
        if row["outcome"] == "success" and ("repeated" in row["trace_id"] or "failed" in row["trace_id"])
    }
    ambiguous_ids = {row["trace_id"] for row in ground_truth if row["outcome"] == "ambiguous"}
    ambiguous_flagged = [t for t in ambiguous_ids if t in predictions]

    print("\n5. AMBIGUOUS & NEGATIVE CONTROL CASES")
    print(f"   Ambiguous traces      : {len(ambiguous_ids)} (flagged: {len(ambiguous_flagged)})")

    return precision, recall, f1


if __name__ == "__main__":
    # Evaluate Customer Support Domain
    evaluate_dataset(
        "Customer Support Domain",
        PROJECT_ROOT / "data" / "traces.json",
        PROJECT_ROOT / "data" / "ground_truth.json",
    )

    # Evaluate Coding Agent Domain
    evaluate_dataset(
        "Coding Agent Domain",
        PROJECT_ROOT / "data" / "coding_traces.json",
        PROJECT_ROOT / "data" / "coding_ground_truth.json",
    )
