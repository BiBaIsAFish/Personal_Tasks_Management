from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


TAIPEI_TZ = timezone(timedelta(hours=8))


class MockNotionTools:
    def __init__(
        self,
        reference_now: str = "2026-05-27T11:30:00+08:00",
        initial_tasks: list[dict[str, Any]] | None = None,
    ) -> None:
        self.reference_now = reference_now
        self.tasks = list(initial_tasks or [])
        self.tool_calls: list[dict[str, Any]] = []

    def get_current_time(self) -> dict[str, str]:
        result = {
            "timezone": "Asia/Taipei",
            "current_time": self.reference_now,
        }
        self._record("get_current_time", {}, result)
        return result

    def parse_time_range(self, text: str, reference_time: str) -> dict[str, Any]:
        reference = datetime.fromisoformat(reference_time)
        target_date = self._resolve_date(text, reference)
        if target_date is None:
            result = {"confidence": 0.2, "error": "ambiguous_time"}
            self._record("parse_time_range", {"text": text, "reference_time": reference_time}, result)
            return result

        hour = self._resolve_hour(text)
        if hour is None:
            result = {"confidence": 0.4, "error": "missing_hour"}
            self._record("parse_time_range", {"text": text, "reference_time": reference_time}, result)
            return result

        duration_hours = 1
        if "到八點" in text and hour == 19:
            duration_hours = 1

        start = datetime(target_date.year, target_date.month, target_date.day, hour, 0, tzinfo=TAIPEI_TZ)
        end = start + timedelta(hours=duration_hours)
        result = {
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "confidence": 0.9,
        }
        self._record("parse_time_range", {"text": text, "reference_time": reference_time}, result)
        return result

    def query_notion_schedule(self, start_time: str, end_time: str) -> dict[str, Any]:
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
        conflicts = []
        for task in self.tasks:
            task_start = datetime.fromisoformat(task["start_time"])
            task_end = datetime.fromisoformat(task["end_time"])
            if start < task_end and end > task_start:
                conflicts.append(task)

        result = {"conflicts": conflicts}
        self._record("query_notion_schedule", {"start_time": start_time, "end_time": end_time}, result)
        return result

    def create_notion_task(
        self,
        title: str,
        start_time: str,
        end_time: str,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        task = {
            "task_id": f"task{len(self.tasks) + 1:03d}",
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "tags": list(tags or []),
        }
        self.tasks.append(task)
        result = {"status": "created", "task": task}
        self._record(
            "create_notion_task",
            {"title": title, "start_time": start_time, "end_time": end_time, "tags": tags or []},
            result,
        )
        return result

    def update_notion_task(self, task_id: str, new_start_time: str, new_end_time: str) -> dict[str, Any]:
        for task in self.tasks:
            if task["task_id"] == task_id:
                task["start_time"] = new_start_time
                task["end_time"] = new_end_time
                result = {"status": "updated", "task": task}
                self._record("update_notion_task", {"task_id": task_id}, result)
                return result
        result = {"status": "not_found", "task_id": task_id}
        self._record("update_notion_task", {"task_id": task_id}, result)
        return result

    def _record(self, name: str, arguments: dict[str, Any], result: dict[str, Any]) -> None:
        self.tool_calls.append({"name": name, "arguments": arguments, "result": result})

    def _resolve_date(self, text: str, reference: datetime) -> datetime | None:
        if "今天" in text:
            return reference
        if "明天" in text:
            return reference + timedelta(days=1)
        if "下週三" in text or "下周三" in text:
            return self._next_weekday(reference, 2)
        if "下週五" in text or "下周五" in text:
            return self._next_weekday(reference, 4)
        if "週末" in text or "周末" in text:
            return None
        return None

    def _resolve_hour(self, text: str) -> int | None:
        if "晚上七點" in text or "19:00" in text:
            return 19
        if "下午三點" in text or "明天三點" in text or " 15:00" in text or "15:00" in text:
            return 15
        if "四點" in text:
            return 16
        if "早上" in text:
            return 9
        if "10:00" in text:
            return 10
        return None

    def _next_weekday(self, reference: datetime, weekday: int) -> datetime:
        days_until = (weekday - reference.weekday()) % 7
        days_until = days_until + 7 if days_until == 0 else days_until
        return reference + timedelta(days=days_until)

