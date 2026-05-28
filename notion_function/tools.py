from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo


TITLE_PROP = "待辦事項"
START_PROP = "開始日"
END_PROP = "截止日"
CATEGORY_PROP = "類別"
PRIORITY_PROP = "優先程度"
STATUS_PROP = "狀態"
NOTES_PROP = "備註"


def get_current_time(timezone_name: str = "Asia/Taipei") -> dict[str, str]:
    now = datetime.now(_timezone(timezone_name))
    return {
        "timezone": timezone_name,
        "current_time": now.isoformat(timespec="seconds"),
    }


def query_notion_schedule(
    notion: Any,
    data_source_id: str,
    start_time: str,
    end_time: str,
) -> dict[str, list[dict[str, Any]]]:
    response = notion.data_sources.query(
        data_source_id=data_source_id,
        filter={
            "and": [
                {"property": START_PROP, "date": {"before": end_time}},
                {"property": END_PROP, "date": {"after": start_time}},
            ]
        },
    )

    return {"conflicts": [_page_to_task(page) for page in response.get("results", [])]}


def get_notion_task(notion: Any, task_id: str) -> dict[str, Any]:
    page = notion.pages.retrieve(page_id=task_id)
    return {"task": _page_to_task(page)}


def query_notion_tasks_by_date(
    notion: Any,
    data_source_id: str,
    date: str,
    timezone_name: str = "Asia/Taipei",
) -> dict[str, list[dict[str, Any]]]:
    tz = _timezone(timezone_name)
    start = datetime.fromisoformat(date).replace(tzinfo=tz)
    end = start + timedelta(days=1)
    return query_notion_tasks(
        notion,
        data_source_id=data_source_id,
        start_time=start.isoformat(timespec="seconds"),
        end_time=end.isoformat(timespec="seconds"),
    )


def query_notion_tasks(
    notion: Any,
    data_source_id: str,
    start_time: str | None = None,
    end_time: str | None = None,
    category: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    filters: list[dict[str, Any]] = []
    if end_time is not None:
        filters.append({"property": START_PROP, "date": {"before": end_time}})
    if start_time is not None:
        filters.append({"property": END_PROP, "date": {"after": start_time}})
    if category is not None:
        filters.append({"property": CATEGORY_PROP, "select": {"equals": category}})
    if priority is not None:
        filters.append({"property": PRIORITY_PROP, "select": {"equals": priority}})
    if status is not None:
        filters.append({"property": STATUS_PROP, "status": {"equals": status}})
    if keyword is not None:
        filters.append({"property": TITLE_PROP, "title": {"contains": keyword}})

    query: dict[str, Any] = {"data_source_id": data_source_id}
    if len(filters) == 1:
        query["filter"] = filters[0]
    elif filters:
        query["filter"] = {"and": filters}

    response = notion.data_sources.query(**query)
    return {"tasks": [_page_to_task(page) for page in response.get("results", [])]}


def create_notion_task(
    notion: Any,
    data_source_id: str,
    title: str,
    start_time: str,
    end_time: str,
    tags: list[str] | None = None,
    priority: str | None = None,
    status: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    if not title.strip():
        raise ValueError("title is required")

    properties: dict[str, Any] = {
        TITLE_PROP: {"title": [{"text": {"content": title}}]},
        START_PROP: {"date": {"start": start_time}},
        END_PROP: {"date": {"start": end_time}},
    }

    if tags:
        properties[CATEGORY_PROP] = {"select": {"name": tags[0]}}
    if priority:
        properties[PRIORITY_PROP] = {"select": {"name": priority}}
    if status:
        properties[STATUS_PROP] = {"status": {"name": status}}
    if notes:
        properties[NOTES_PROP] = {"rich_text": [{"text": {"content": notes}}]}

    page = notion.pages.create(
        parent={"type": "data_source_id", "data_source_id": data_source_id},
        properties=properties,
    )

    return {
        "status": "created",
        "task_id": page["id"],
        "task": _page_to_task(page),
    }


def update_notion_task(
    notion: Any,
    task_id: str,
    title: str | None = None,
    new_start_time: str | None = None,
    new_end_time: str | None = None,
    tags: list[str] | None = None,
    priority: str | None = None,
    status: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    if title is not None:
        if not title.strip():
            raise ValueError("title cannot be empty")
        properties[TITLE_PROP] = {"title": [{"text": {"content": title}}]}
    if new_start_time is not None:
        properties[START_PROP] = {"date": {"start": new_start_time}}
    if new_end_time is not None:
        properties[END_PROP] = {"date": {"start": new_end_time}}
    if tags is not None:
        properties[CATEGORY_PROP] = {"select": {"name": tags[0]} if tags else None}
    if priority is not None:
        properties[PRIORITY_PROP] = {"select": {"name": priority} if priority else None}
    if status is not None:
        properties[STATUS_PROP] = {"status": {"name": status} if status else None}
    if notes is not None:
        properties[NOTES_PROP] = {"rich_text": [{"text": {"content": notes}}] if notes else []}

    if not properties:
        raise ValueError("at least one field is required")

    page = notion.pages.update(
        page_id=task_id,
        properties=properties,
    )

    return {
        "status": "updated",
        "task_id": page["id"],
        "task": _page_to_task(page),
    }


def delete_notion_task(notion: Any, task_id: str) -> dict[str, Any]:
    page = notion.pages.update(page_id=task_id, archived=True)
    return {
        "status": "deleted",
        "task_id": page["id"],
    }


def _page_to_task(page: dict[str, Any]) -> dict[str, Any]:
    properties = page.get("properties", {})
    title = _plain_title(properties.get(TITLE_PROP, {}))
    start_time = _date_start(properties.get(START_PROP, {}))
    end_time = _date_start(properties.get(END_PROP, {}))
    category = properties.get(CATEGORY_PROP, {}).get("select")
    priority = properties.get(PRIORITY_PROP, {}).get("select")
    status = properties.get(STATUS_PROP, {}).get("status")

    return {
        "task_id": page["id"],
        "title": title,
        "start_time": start_time,
        "end_time": end_time,
        "tags": [category["name"]] if category else [],
        "priority": priority["name"] if priority else None,
        "status": status["name"] if status else None,
        "notes": _plain_rich_text(properties.get(NOTES_PROP, {})),
    }


def _plain_title(property_value: dict[str, Any]) -> str:
    title_items = property_value.get("title", [])
    return "".join(item.get("plain_text") or item.get("text", {}).get("content", "") for item in title_items)


def _date_start(property_value: dict[str, Any]) -> str | None:
    date_value = property_value.get("date")
    return date_value.get("start") if date_value else None


def _plain_rich_text(property_value: dict[str, Any]) -> str:
    text_items = property_value.get("rich_text", [])
    return "".join(item.get("plain_text") or item.get("text", {}).get("content", "") for item in text_items)


def _timezone(timezone_name: str):
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        if timezone_name == "Asia/Taipei":
            return timezone(timedelta(hours=8))
        raise
