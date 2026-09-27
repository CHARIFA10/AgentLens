from collections import Counter


def prioritize(findings):

    counts = Counter(
        finding.failure_type
        for finding in findings
    )

    if not counts:
        return []

    max_count = max(counts.values())

    results = []

    for failure_type, count in counts.items():

        examples = [
            f
            for f in findings
            if f.failure_type == failure_type
        ]

        avg_confidence = sum(
            f.confidence
            for f in examples
        ) / len(examples)

        avg_severity = sum(
            f.severity
            for f in examples
        ) / len(examples)

        frequency = count / max_count

        priority = round(
            100
            * frequency
            * avg_confidence
            * avg_severity
        )

        results.append({
            "failure_type": failure_type,
            "count": count,
            "priority": priority,
            "confidence": round(
                avg_confidence,
                2,
            ),
        })

    return sorted(
        results,
        key=lambda x: x["priority"],
        reverse=True,
    )
