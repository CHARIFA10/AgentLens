from agentlens.detectors.rules import detect_trace
from agentlens.analysis.prioritization import prioritize


def analyze(traces):

    findings = []

    for trace in traces:
        findings.extend(
            detect_trace(trace)
        )

    priorities = prioritize(findings)

    return findings, priorities
