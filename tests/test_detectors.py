from agentlens.ingestion.loader import load_traces
from agentlens.analysis.pipeline import analyze


def test_baseline_analysis():
    traces = load_traces("data/traces.json")
    findings, priorities = analyze(traces)

    assert len(traces) == 6
    assert len(findings) == 4

    findings_by_trace = {f.trace_id: f.failure_type for f in findings}
    assert findings_by_trace == {
        "trace_002": "unsupported_success",
        "trace_004": "repeated_question",
        "trace_005": "no_progress",
        "trace_006": "incomplete_task",
    }

    assert "trace_001" not in findings_by_trace
    assert "trace_003" not in findings_by_trace

    assert len(priorities) == 4
    priority_types = [p["failure_type"] for p in priorities]
    assert priority_types == [
        "unsupported_success",
        "incomplete_task",
        "no_progress",
        "repeated_question",
    ]


if __name__ == "__main__":
    test_baseline_analysis()
    print("All baseline tests passed successfully!")
