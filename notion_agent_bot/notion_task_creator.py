from __future__ import annotations

from typing import Any


def create_notion_task_page(
    notion: Any,
    database_id: str,
    title: str,
    due_date: str | None = None,
    category: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    if not title.strip():
        raise ValueError("title is required")

    properties: dict[str, Any] = {
        "待辦事項": {"title": [{"text": {"content": title}}]},
    }
    if due_date:
        properties["截止日"] = {"date": {"start": due_date}}
    if category:
        properties["類別"] = {"select": {"name": category}}
    if priority:
        properties["優先程度"] = {"select": {"name": priority}}
    if status:
        properties["狀態"] = {"status": {"name": status}}
    if notes:
        properties["備註"] = {"rich_text": [{"text": {"content": notes}}]}

    return notion.pages.create(
        parent={"database_id": database_id},
        properties=properties,
    )
