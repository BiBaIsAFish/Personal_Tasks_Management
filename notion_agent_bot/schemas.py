from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentResponse:
    status: str
    message: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    task: dict[str, Any] | None = None
    conflicts: list[dict[str, Any]] = field(default_factory=list)

