import os
import unittest
from pathlib import Path

from LLM_agent.notion_task_creator import create_notion_task_page


ROOT_DIR = Path(__file__).resolve().parents[1]


@unittest.skipUnless(
    os.getenv("RUN_NOTION_INTEGRATION") == "1",
    "set RUN_NOTION_INTEGRATION=1 to create a real Notion page",
)
class NotionIntegrationTest(unittest.TestCase):
    def test_creates_task_in_configured_notion_database(self):
        from dotenv import load_dotenv
        from notion_client import Client

        load_dotenv(ROOT_DIR / "run_bot" / ".env")
        token = os.getenv("NOTION_TOKEN")
        database_id = os.getenv("NOTION_DATABASE_ID")
        self.assertTrue(token, "Missing NOTION_TOKEN")
        self.assertTrue(database_id, "Missing NOTION_DATABASE_ID")

        notion = Client(auth=token)
        page = create_notion_task_page(
            notion,
            database_id=database_id,
            title="Codex Notion API create test",
            due_date="2026-05-28",
            notes="Created by tests/test_notion_integration.py.",
        )

        self.assertIn("id", page)


if __name__ == "__main__":
    unittest.main()
