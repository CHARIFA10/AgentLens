import json
from pathlib import Path

from agentlens.schema.models import Trace


def load_traces(path: str | Path) -> list[Trace]:
    path = Path(path)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return [
        Trace.model_validate(item)
        for item in data
    ]
