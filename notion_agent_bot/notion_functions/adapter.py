from __future__ import annotations

from collections.abc import Callable
from typing import Any

from . import tools


class NotionFunctionAdapter:
    def __init__(self, notion: Any, data_source_id: str) -> None:
        self.notion = notion
        self.data_source_id = data_source_id
        self.tool_calls: list[dict[str, Any]] = []
        self._tools: dict[str, tuple[Callable[..., dict[str, Any]], set[str]]] = {
            "get_current_time": (self._get_current_time, set()),
            "query_notion_schedule": (self._query_notion_schedule, {"start_time", "end_time"}),
            "get_notion_task": (self._get_notion_task, {"task_id"}),
            "query_notion_tasks_by_date": (self._query_notion_tasks_by_date, {"date"}),
            "query_notion_tasks": (self._query_notion_tasks, set()),
            "create_notion_task": (self._create_notion_task, {"title", "start_time", "end_time"}),
            "update_notion_task": (self._update_notion_task, {"task_id"}),
            "delete_notion_task": (self._delete_notion_task, {"task_id"}),
        }

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools)

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        args = dict(arguments or {})
        if name not in self._tools:
            result = {"status": "error", "error": "unknown_tool", "message": f"Unknown tool: {name}"}
            self._record(name, args, result)
            return result

        function, required = self._tools[name]
        for argument in sorted(required):
            if argument not in args or args[argument] in (None, ""):
                result = {
                    "status": "error",
                    "error": "missing_argument",
                    "argument": argument,
                    "message": f"Missing required argument: {argument}",
                }
                self._record(name, args, result)
                return result

        try:
            result = function(**args)
        except Exception as exc:
            result = {"status": "error", "error": "tool_error", "message": str(exc)}

        self._record(name, args, result)
        return result

    def _record(self, name: str, arguments: dict[str, Any], result: dict[str, Any]) -> None:
        self.tool_calls.append({"name": name, "arguments": arguments, "result": result})

    def _get_current_time(self, timezone_name: str = "Asia/Taipei") -> dict[str, Any]:
        return tools.get_current_time(timezone_name=timezone_name)

    def _query_notion_schedule(self, start_time: str, end_time: str) -> dict[str, Any]:
        return tools.query_notion_schedule(self.notion, self.data_source_id, start_time, end_time)

    def _get_notion_task(self, task_id: str) -> dict[str, Any]:
        return tools.get_notion_task(self.notion, task_id)

    def _query_notion_tasks_by_date(self, date: str, timezone_name: str = "Asia/Taipei") -> dict[str, Any]:
        return tools.query_notion_tasks_by_date(self.notion, self.data_source_id, date, timezone_name)

    def _query_notion_tasks(
        self,
        start_time: str | None = None,
        end_time: str | None = None,
        category: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        keyword: str | None = None,
    ) -> dict[str, Any]:
        return tools.query_notion_tasks(
            self.notion,
            self.data_source_id,
            start_time=start_time,
            end_time=end_time,
            category=category,
            priority=priority,
            status=status,
            keyword=keyword,
        )

    def _create_notion_task(
        self,
        title: str,
        start_time: str,
        end_time: str,
        tags: list[str] | None = None,
        priority: str | None = None,
        status: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        return tools.create_notion_task(
            self.notion,
            self.data_source_id,
            title,
            start_time,
            end_time,
            tags=tags,
            priority=priority,
            status=status,
            notes=notes,
        )

    def _update_notion_task(
        self,
        task_id: str,
        title: str | None = None,
        new_start_time: str | None = None,
        new_end_time: str | None = None,
        tags: list[str] | None = None,
        priority: str | None = None,
        status: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        return tools.update_notion_task(
            self.notion,
            task_id,
            title=title,
            new_start_time=new_start_time,
            new_end_time=new_end_time,
            tags=tags,
            priority=priority,
            status=status,
            notes=notes,
        )

    def _delete_notion_task(self, task_id: str) -> dict[str, Any]:
        return tools.delete_notion_task(self.notion, task_id)
