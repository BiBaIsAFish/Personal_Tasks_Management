import unittest

from notion_agent_bot.notion_task_creator import create_notion_task_page


class FakePages:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return {"id": "page_123", **kwargs}


class FakeNotion:
    def __init__(self):
        self.pages = FakePages()


class NotionTaskCreatorTest(unittest.TestCase):
    def test_creates_page_payload_for_task_database_schema(self):
        notion = FakeNotion()

        result = create_notion_task_page(
            notion,
            database_id="database_123",
            title="Codex payload test",
            due_date="2026-05-28",
            category="測試",
            priority="低",
            status="未開始",
            notes="Created by unit test.",
        )

        self.assertEqual(result["id"], "page_123")
        self.assertEqual(
            notion.pages.calls[0],
            {
                "parent": {"database_id": "database_123"},
                "properties": {
                    "待辦事項": {"title": [{"text": {"content": "Codex payload test"}}]},
                    "截止日": {"date": {"start": "2026-05-28"}},
                    "類別": {"select": {"name": "測試"}},
                    "優先程度": {"select": {"name": "低"}},
                    "狀態": {"status": {"name": "未開始"}},
                    "備註": {"rich_text": [{"text": {"content": "Created by unit test."}}]},
                },
            },
        )


if __name__ == "__main__":
    unittest.main()
