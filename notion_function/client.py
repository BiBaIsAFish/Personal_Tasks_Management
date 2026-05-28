from __future__ import annotations

import os
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]


def create_notion_client_from_env(env_path: str | Path | None = None) -> tuple[Any, str]:
    from dotenv import load_dotenv
    from notion_client import Client

    load_dotenv(env_path or ROOT_DIR / "run_bot" / ".env")

    token = os.getenv("NOTION_TOKEN")
    data_source_id = os.getenv("NOTION_DATA_SOURCE_ID")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not token:
        raise RuntimeError("Missing NOTION_TOKEN")
    if not data_source_id and not database_id:
        raise RuntimeError("Missing NOTION_DATA_SOURCE_ID or NOTION_DATABASE_ID")

    notion = Client(auth=token)
    if data_source_id:
        return notion, data_source_id

    database = notion.databases.retrieve(database_id=database_id)
    data_sources = database.get("data_sources", [])
    if not data_sources:
        raise RuntimeError("Database response has no data_sources")

    return notion, data_sources[0]["id"]
