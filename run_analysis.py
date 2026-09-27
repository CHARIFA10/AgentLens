import sys
from pathlib import Path

# Ensure UTF-8 console output
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agentlens.ingestion.loader import load_traces
from agentlens.analysis.pipeline import analyze


def run_domain_analysis(title: str, filepath: str | Path):
    path = Path(filepath)
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    traces = load_traces(path)
    findings, priorities = analyze(traces)

    print("=" * 65)
    print(f"AGENTLENS — {title.upper()}")
    print("=" * 65)

    suspicious_ids = set(f.trace_id for f in findings)
    print(f"Traces analysed   : {len(traces)}")
    print(f"Suspicious traces : {len(suspicious_ids)}")
    print(f"Failure patterns  : {len(priorities)}")

    print("\nINVESTIGATION PRIORITY")
    print("-" * 65)
    for row in priorities:
        print(
            f"{row['failure_type']:25}"
            f" count={row['count']:2} "
            f"confidence={row['confidence']:.2f} "
            f"priority={row['priority']:3}"
        )
    print()


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    if target in ("all", "customer"):
        run_domain_analysis("Customer Support Domain", "data/traces.json")

    if target in ("all", "coding"):
        run_domain_analysis("Coding Agent Domain", "data/coding_traces.json")
