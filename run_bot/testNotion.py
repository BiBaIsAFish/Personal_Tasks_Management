import os
from pathlib import Path

from dotenv import load_dotenv
from notion_client import Client


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / "run_bot" / ".env")

token = os.getenv("NOTION_TOKEN")
db_id = os.getenv("NOTION_DATABASE_ID")

if not token:
    raise RuntimeError("Missing NOTION_TOKEN in run_bot/.env")
if not db_id:
    raise RuntimeError("Missing NOTION_DATABASE_ID in run_bot/.env")

notion = Client(auth=token)

db = notion.databases.retrieve(database_id=db_id)
title = db["title"][0]["plain_text"] if db.get("title") else "(untitled)"

properties = db.get("properties")
data_source_name = None

if properties is None:
    data_sources = db.get("data_sources", [])
    if not data_sources:
        raise RuntimeError("Database response has no properties or data_sources")

    data_source = data_sources[0]
    data_source_name = data_source.get("name")
    source = notion.data_sources.retrieve(data_source_id=data_source["id"])
    properties = source.get("properties")

    if properties is None:
        raise RuntimeError("Data source response has no properties")

print(f"\u8cc7\u6599\u5eab\u540d\u7a31: {title}")
if data_source_name:
    print(f"Data source: {data_source_name}")
print("\u6b04\u4f4d:")
for prop, info in properties.items():
    print(f"[{prop}] \u985e\u578b: {info['type']}")
