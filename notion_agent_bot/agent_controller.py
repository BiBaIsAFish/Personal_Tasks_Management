from __future__ import annotations

from typing import Any

from .notion_tools import MockNotionTools
from .schemas import AgentResponse


class AgentController:
    def __init__(self, tools: MockNotionTools) -> None:
        self.tools = tools
        self.memory: dict[str, Any] = {}

    def handle_message(self, text: str) -> AgentResponse:
        self.tools.tool_calls.clear()

        if self._is_confirmation(text) and self.memory.get("pending_task"):
            pending = self.memory.pop("pending_task")
            created = self.tools.create_notion_task(
                pending["title"],
                pending["start_time"],
                pending["end_time"],
                pending["tags"],
            )
            return AgentResponse(
                status="created",
                message=f"已依照你的確認建立行程：{pending['title']}",
                tool_calls=list(self.tools.tool_calls),
                task=created["task"],
            )

        current = self.tools.get_current_time()
        parsed = self.tools.parse_time_range(text, current["current_time"])
        if parsed.get("confidence", 0) < 0.7:
            return AgentResponse(
                status="needs_information",
                message="時間資訊不夠明確，請補充日期、開始時間與持續時間。",
                tool_calls=list(self.tools.tool_calls),
            )

        title = self._extract_title(text)
        tags = self._extract_tags(text)
        schedule = self.tools.query_notion_schedule(parsed["start_time"], parsed["end_time"])
        conflicts = schedule["conflicts"]
        if conflicts:
            pending = {
                "title": title,
                "start_time": parsed["start_time"],
                "end_time": parsed["end_time"],
                "tags": tags,
            }
            self.memory["pending_task"] = pending
            names = "、".join(conflict["title"] for conflict in conflicts)
            return AgentResponse(
                status="needs_confirmation",
                message=f"這段時間已有行程：{names}。是否仍要新增？",
                tool_calls=list(self.tools.tool_calls),
                conflicts=conflicts,
            )

        created = self.tools.create_notion_task(title, parsed["start_time"], parsed["end_time"], tags)
        return AgentResponse(
            status="created",
            message=f"已建立行程：{title}，時間為 {parsed['start_time']} 到 {parsed['end_time']}。",
            tool_calls=list(self.tools.tool_calls),
            task=created["task"],
        )

    def _is_confirmation(self, text: str) -> bool:
        return any(token in text for token in ["確認", "還是", "照樣", "加上去", "建立"])

    def _extract_title(self, text: str) -> str:
        if "開會" in text:
            return "開會"
        if "討論報告" in text:
            return "討論報告"
        if "健身" in text:
            return "健身"
        if "讀書" in text:
            return "讀書"
        if "新行程" in text:
            return "新行程"
        if "demo" in text.lower():
            return "demo"
        return "未命名行程"

    def _extract_tags(self, text: str) -> list[str]:
        tags = []
        for word in text.split():
            if word.startswith("#") and len(word) > 1:
                tags.append(word[1:])
        return tags

