from .tools import (
    create_notion_task,
    delete_notion_task,
    get_notion_task,
    get_current_time,
    query_notion_tasks,
    query_notion_tasks_by_date,
    query_notion_schedule,
    update_notion_task,
)


def create_notion_client_from_env(*args, **kwargs):
    from .client import create_notion_client_from_env as create_client

    return create_client(*args, **kwargs)

__all__ = [
    "create_notion_client_from_env",
    "create_notion_task",
    "delete_notion_task",
    "get_notion_task",
    "get_current_time",
    "query_notion_tasks",
    "query_notion_tasks_by_date",
    "query_notion_schedule",
    "update_notion_task",
]
