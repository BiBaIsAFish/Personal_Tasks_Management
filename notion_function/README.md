# notion_function

Notion task tools for the bot / LLM controller.  
此模組負責連接 Notion database/data source，並提供任務查詢、建立、更新與刪除功能。

## Files

| File | Purpose |
| --- | --- |
| `client.py` | 從 `run_bot/.env` 建立 Notion client |
| `tools.py` | Notion task CRUD / query functions |
| `adapter.py` | 將 functions 包成 LLM tool-call adapter |
| `task_draft_store.py` | 暫存 create task draft 到 `run_bot/task_draft.json` |
| `__init__.py` | 對外匯出常用 functions |

## Environment

在 `run_bot/.env` 設定：

```env
NOTION_TOKEN=secret_xxx
NOTION_DATA_SOURCE_ID=your_data_source_id
```

也可只提供 `NOTION_DATABASE_ID`；程式會讀取 database 的第一個 data source。

## Basic Usage

```python
from notion_function import create_notion_client_from_env, query_notion_tasks

notion, data_source_id = create_notion_client_from_env()

result = query_notion_tasks(
    notion,
    data_source_id,
    start_time="2026-05-28T00:00:00+08:00",
    end_time="2026-05-29T00:00:00+08:00",
)
```

## Main Functions

| Function | Description |
| --- | --- |
| `get_current_time()` | 回傳目前時間，預設 timezone 為 `Asia/Taipei` |
| `query_notion_schedule()` | 查詢指定時間區間是否有衝突任務 |
| `query_notion_tasks_by_date()` | 查詢某一天的任務 |
| `query_notion_tasks()` | 依時間、分類、優先度、狀態、關鍵字查詢 |
| `get_notion_task()` | 用 `task_id` 取得單一任務 |
| `create_notion_task()` | 建立 Notion task |
| `update_notion_task()` | 更新任務欄位 |
| `delete_notion_task()` | 封存 Notion page，作為 delete |

## Adapter Tools

`NotionFunctionAdapter` 提供以下 tool names：

```text
get_current_time
query_notion_schedule
get_notion_task
query_notion_tasks_by_date
query_notion_tasks
create_notion_task
update_notion_task
delete_notion_task
```

Example:

```python
from notion_function.adapter import NotionFunctionAdapter
from notion_function import create_notion_client_from_env

notion, data_source_id = create_notion_client_from_env()
adapter = NotionFunctionAdapter(notion, data_source_id)

result = adapter.call_tool("create_notion_task", {
    "title": "DRL homework",
    "start_time": "2026-05-28T15:00:00+08:00",
    "end_time": "2026-05-28T16:00:00+08:00",
    "tags": ["test"],
    "priority": "High",
    "status": "Todo",
    "notes": "Created by bot",
})
```

## Notes

- 時間格式使用 ISO 8601 with timezone，例如 `2026-05-28T15:00:00+08:00`。
- 建立或移動任務前，建議先用 `query_notion_schedule()` 檢查 conflict。
- `tags` 目前只會使用第一個值寫入 Notion select field。
- Notion property names 定義在 `tools.py` 的 constants，需與實際 database schema 一致。
- `delete_notion_task()` 不會 hard delete，只會 archive page。
