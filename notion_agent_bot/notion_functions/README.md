# Notion Functions

This package exposes Notion task tools for the future LLM controller.

## Environment

Set these values in `run_bot/.env`:

```env
NOTION_TOKEN=secret_xxx
NOTION_DATA_SOURCE_ID=your_data_source_id
```

`NOTION_DATABASE_ID` is accepted as a fallback. When only the database ID is set,
the helper retrieves the database and uses its first data source ID.

## Database Schema

The functions expect this Notion data source schema:

| Field | Type | Purpose |
| --- | --- | --- |
| `待辦事項` | title | Task title |
| `開始日` | date | Task start time |
| `截止日` | date | Task end time |
| `類別` | select | First tag/category |
| `優先程度` | select | Optional priority |
| `狀態` | status | Optional status |
| `備註` | rich_text | Optional notes |

Current tested options:

| Field | Options |
| --- | --- |
| `類別` | `作業`, `報告`, `meeting`, `考試`, `專案`, `閱讀`, `個人`, `工作`, `生活`, `社交`, `test` |
| `優先程度` | `不重要不緊急 Low`, `不重要緊急 Medium`, `重要不緊急 High`, `重要緊急 Critical` |
| `狀態` | `尚未開始`, `進行中`, `已完成` |

## Tool Order

For scheduling requests, call tools in this order:

1. `get_current_time()`
2. Parse the user's natural language time into `start_time` and `end_time`.
3. `query_notion_schedule(start_time, end_time)`
4. If `conflicts` is empty, call `create_notion_task(...)`.
5. If `conflicts` is not empty, ask the user before creating or updating.

## Functions

### `create_notion_client_from_env()`

Returns a Notion client and data source ID.

```python
from notion_agent_bot.notion_functions import create_notion_client_from_env

notion, data_source_id = create_notion_client_from_env()
```

### `get_current_time(timezone_name="Asia/Taipei")`

Output:

```json
{
  "timezone": "Asia/Taipei",
  "current_time": "2026-05-27T11:30:00+08:00"
}
```

### `query_notion_schedule(notion, data_source_id, start_time, end_time)`

Searches by start/end time overlap. Use this before creating or moving a task.

Input:

```json
{
  "start_time": "2026-05-28T15:00:00+08:00",
  "end_time": "2026-05-28T16:00:00+08:00"
}
```

Output:

```json
{
  "conflicts": [
    {
      "task_id": "page_id",
      "title": "Project Meeting",
      "start_time": "2026-05-28T15:30:00+08:00",
      "end_time": "2026-05-28T16:30:00+08:00",
      "tags": ["work"]
    }
  ]
}
```

### `get_notion_task(notion, task_id)`

Searches by event ID.

Output:

```json
{
  "task": {
    "task_id": "page_id",
    "title": "Project Meeting",
    "start_time": "2026-05-28T15:00:00+08:00",
    "end_time": "2026-05-28T16:00:00+08:00",
    "tags": ["meeting"],
    "priority": "重要緊急 Critical",
    "status": "進行中",
    "notes": "Discuss milestones."
  }
}
```

### `query_notion_tasks_by_date(notion, data_source_id, date)`

Searches tasks overlapping one local date in `Asia/Taipei`.

Input:

```json
{
  "date": "2026-05-28"
}
```

### `query_notion_tasks(notion, data_source_id, start_time=None, end_time=None, category=None, priority=None, status=None, keyword=None)`

Searches by one or more filters. Multiple filters are combined with AND.

Supported filters:

| Argument | Notion field | Match |
| --- | --- | --- |
| `start_time` + `end_time` | `開始日`, `截止日` | overlapping time range |
| `category` | `類別` | select equals |
| `priority` | `優先程度` | select equals |
| `status` | `狀態` | status equals |
| `keyword` | `待辦事項` | title contains |

Example:

```json
{
  "start_time": "2026-05-28T00:00:00+08:00",
  "end_time": "2026-05-29T00:00:00+08:00",
  "category": "作業",
  "priority": "重要緊急 Critical",
  "status": "進行中",
  "keyword": "DRL"
}
```

### `create_notion_task(notion, data_source_id, title, start_time, end_time, tags=None, priority=None, status=None, notes=None)`

Creates a Notion page. `tags[0]` is written to `類別`. `priority` is written
to `優先程度`. `status` is written to `狀態`.

Output:

```json
{
  "status": "created",
  "task_id": "page_id",
  "task": {
    "task_id": "page_id",
    "title": "Project Meeting",
    "start_time": "2026-05-28T15:00:00+08:00",
    "end_time": "2026-05-28T16:00:00+08:00",
    "tags": ["work"]
  }
}
```

### `update_notion_task(notion, task_id, title=None, new_start_time=None, new_end_time=None, tags=None, priority=None, status=None, notes=None)`

Updates any provided fields on an existing Notion page. Omitted fields are not
changed. Pass an empty `tags` list, empty `priority`, empty `status`, or empty
`notes` to clear that field.

Output:

```json
{
  "status": "updated",
  "task_id": "page_id"
}
```

### `delete_notion_task(notion, task_id)`

Archives an existing Notion page. Notion pages are archived instead of hard
deleted.

Output:

```json
{
  "status": "deleted",
  "task_id": "page_id"
}
```

## LLM Rules

- Do not create a task until the user intent and time range are clear.
- Choose exactly one existing `類別`; do not invent new category names.
- Always query conflicts before creating a task.
- Before changing a task time, query the target range for conflicts.
- If conflicts exist, summarize the conflicting task names and ask for confirmation.
- To delete a task, call `delete_notion_task`; this archives the Notion page.
- Use ISO 8601 timestamps with timezone offsets.
- Use `task_id` from query results when updating an existing task.
