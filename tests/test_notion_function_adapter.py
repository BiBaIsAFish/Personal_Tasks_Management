import unittest

from notion_function.adapter import NotionFunctionAdapter


class FakeDataSources:
    def __init__(self):
        self.queries = []
        self.query_result = {"results": []}

    def query(self, **kwargs):
        self.queries.append(kwargs)
        return self.query_result


class FakePages:
    def __init__(self):
        self.created = []
        self.updated = []
        self.retrieved = []

    def create(self, **kwargs):
        self.created.append(kwargs)
        return {"id": "page_123", **kwargs}

    def update(self, **kwargs):
        self.updated.append(kwargs)
        return {"id": kwargs["page_id"], **kwargs}

    def retrieve(self, **kwargs):
        self.retrieved.append(kwargs)
        return {"id": kwargs["page_id"], "properties": {}}


class FakeNotion:
    def __init__(self):
        self.data_sources = FakeDataSources()
        self.pages = FakePages()


class NotionFunctionAdapterTest(unittest.TestCase):
    def test_rejects_unknown_tool_without_calling_notion(self):
        notion = FakeNotion()
        adapter = NotionFunctionAdapter(notion, "ds_123")

        result = adapter.call_tool("drop_database", {})

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "unknown_tool")
        self.assertEqual(notion.pages.created, [])
        self.assertEqual(adapter.tool_calls[0]["name"], "drop_database")

    def test_reports_missing_required_argument(self):
        adapter = NotionFunctionAdapter(FakeNotion(), "ds_123")

        result = adapter.call_tool(
            "create_notion_task",
            {
                "start_time": "2026-05-28T15:00:00+08:00",
                "end_time": "2026-05-28T16:00:00+08:00",
            },
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "missing_argument")
        self.assertEqual(result["argument"], "title")

    def test_injects_notion_and_data_source_for_create(self):
        notion = FakeNotion()
        adapter = NotionFunctionAdapter(notion, "ds_123")

        result = adapter.call_tool(
            "create_notion_task",
            {
                "title": "Project Meeting",
                "start_time": "2026-05-28T15:00:00+08:00",
                "end_time": "2026-05-28T16:00:00+08:00",
                "tags": ["work"],
            },
        )

        self.assertEqual(result["status"], "created")
        self.assertEqual(notion.pages.created[0]["parent"]["data_source_id"], "ds_123")
        self.assertEqual(adapter.tool_calls[-1]["result"]["status"], "created")

    def test_injects_notion_for_delete(self):
        notion = FakeNotion()
        adapter = NotionFunctionAdapter(notion, "ds_123")

        result = adapter.call_tool("delete_notion_task", {"task_id": "page_123"})

        self.assertEqual(result["status"], "deleted")
        self.assertEqual(notion.pages.updated[0], {"page_id": "page_123", "archived": True})

    def test_captures_tool_exception_as_error_result(self):
        adapter = NotionFunctionAdapter(FakeNotion(), "ds_123")

        result = adapter.call_tool(
            "create_notion_task",
            {
                "title": "   ",
                "start_time": "2026-05-28T15:00:00+08:00",
                "end_time": "2026-05-28T16:00:00+08:00",
            },
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "tool_error")
        self.assertIn("title", result["message"])


if __name__ == "__main__":
    unittest.main()
