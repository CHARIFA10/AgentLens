from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


EventType = Literal[
    "user_message",
    "agent_message",
    "tool_call",
    "tool_result",
]


class Event(BaseModel):
    event_id: str
    type: EventType
    content: Optional[str] = None

    tool: Optional[str] = None
    status: Optional[str] = None
    arguments: Optional[dict[str, Any]] = None


class Task(BaseModel):
    description: str


class Trace(BaseModel):
    trace_id: str
    session_id: str
    timestamp: str
    agent: str
    task: Task
    events: list[Event]


class Finding(BaseModel):
    trace_id: str
    failure_type: str

    confidence: float = Field(ge=0, le=1)
    severity: float = Field(ge=0, le=1)

    evidence: list[str]
