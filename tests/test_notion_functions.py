import unittest

from notion_function.tools import (
    CATEGORY_PROP,
    END_PROP,
    NOTES_PROP,
    PRIORITY_PROP,
    START_PROP,
    STATUS_PROP,
    TITLE_PROP,
    create_notion_task,
    delete_notion_task,
    get_notion_task,
    query_notion_schedule,
    query_notion_tasks,
    query_notion_tasks_by_date,
    update_notion_task,
)


CRITICAL_PRIORITY = "??蝺?Critical"
IN_PROGRESS_STATUS = "?脰?銝?"


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
        self.retrieve_result = {"id": "page_123", "properties": {}}

    def create(self, **kwargs):
        self.created.append(kwargs)
        return {"id": "page_123", **kwargs}

    def update(self, **kwargs):
        self.updated.append(kwargs)
        return {"id": kwargs["page_id"], **kwargs}

    def retrieve(self, **kwargs):
        self.retrieved.append(kwargs)
        return self.retrieve_result


class FakeNotion:
    def __init__(self):
        self.data_sources = FakeDataSources()
        self.pages = FakePages()


class NotionFunctionsTest(unittest.TestCase):
    def test_property_names_match_task_database_schema(self):
        self.assertEqual(TITLE_PROP, "待辦事項")
        self.assertEqual(START_PROP, "開始日")
        self.assertEqual(END_PROP, "截止日")
        self.assertEqual(CATEGORY_PROP, "類別")
        self.assertEqual(PRIORITY_PROP, "優先程度")
        self.assertEqual(STATUS_PROP, "狀態")
        self.assertEqual(NOTES_PROP, "備註")

    def test_create_notion_task_writes_start_end_and_optional_fields(self):
        notion = FakeNotion()

        result = create_notion_task(
            notion,
            data_source_id="ds_123",
            title="Project Meeting",
            start_time="2026-05-28T15:00:00+08:00",
            end_time="2026-05-28T16:00:00+08:00",
            tags=["work"],
            priority="High",
            status="Not started",
            notes="Discuss milestones.",
        )

        self.assertEqual(result["task_id"], "page_123")
        self.assertEqual(
            notion.pages.created[0],
            {
                "parent": {"type": "data_source_id", "data_source_id": "ds_123"},
                "properties": {
                    TITLE_PROP: {"title": [{"text": {"content": "Project Meeting"}}]},
                    START_PROP: {"date": {"start": "2026-05-28T15:00:00+08:00"}},
                    END_PROP: {"date": {"start": "2026-05-28T16:00:00+08:00"}},
                    CATEGORY_PROP: {"select": {"name": "work"}},
                    PRIORITY_PROP: {"select": {"name": "High"}},
                    STATUS_PROP: {"status": {"name": "Not started"}},
                    NOTES_PROP: {"rich_text": [{"text": {"content": "Discuss milestones."}}]},
                },
            },
        )

    def test_query_notion_schedule_filters_overlapping_time_range(self):
        notion = FakeNotion()
        notion.data_sources.query_result = {
            "results": [
                {
                    "id": "page_123",
                    "properties": {
                        TITLE_PROP: {"title": [{"plain_text": "Project Meeting"}]},
                        START_PROP: {"date": {"start": "2026-05-28T15:30:00+08:00"}},
                        END_PROP: {"date": {"start": "2026-05-28T16:30:00+08:00"}},
                        CATEGORY_PROP: {"select": {"name": "work"}},
                    },
                }
            ]
        }

        result = query_notion_schedule(
            notion,
            data_source_id="ds_123",
            start_time="2026-05-28T15:00:00+08:00",
            end_time="2026-05-28T16:00:00+08:00",
        )

        self.assertEqual(
            notion.data_sources.queries[0],
            {
                "data_source_id": "ds_123",
                "filter": {
                    "and": [
                        {"property": START_PROP, "date": {"before": "2026-05-28T16:00:00+08:00"}},
                        {"property": END_PROP, "date": {"after": "2026-05-28T15:00:00+08:00"}},
                    ]
                },
            },
        )
        self.assertEqual(
            result,
            {
                "conflicts": [
                    {
                        "task_id": "page_123",
                        "title": "Project Meeting",
                        "start_time": "2026-05-28T15:30:00+08:00",
                        "end_time": "2026-05-28T16:30:00+08:00",
                        "tags": ["work"],
                        "priority": None,
                        "status": None,
                        "notes": "",
                    }
                ]
            },
        )

    def test_get_notion_task_retrieves_page_by_id(self):
        notion = FakeNotion()
        notion.pages.retrieve_result = {
            "id": "page_123",
            "properties": {
                TITLE_PROP: {"title": [{"plain_text": "Project Meeting"}]},
                START_PROP: {"date": {"start": "2026-05-28T15:30:00+08:00"}},
                END_PROP: {"date": {"start": "2026-05-28T16:30:00+08:00"}},
                CATEGORY_PROP: {"select": {"name": "meeting"}},
                PRIORITY_PROP: {"select": {"name": CRITICAL_PRIORITY}},
                STATUS_PROP: {"status": {"name": IN_PROGRESS_STATUS}},
                NOTES_PROP: {"rich_text": [{"plain_text": "Discuss milestones."}]},
            },
        }

        result = get_notion_task(notion, task_id="page_123")

        self.assertEqual(notion.pages.retrieved[0], {"page_id": "page_123"})
        self.assertEqual(result["task"]["priority"], CRITICAL_PRIORITY)
        self.assertEqual(result["task"]["status"], IN_PROGRESS_STATUS)
        self.assertEqual(result["task"]["notes"], "Discuss milestones.")

    def test_query_notion_tasks_by_date_queries_one_day_range(self):
        notion = FakeNotion()

        query_notion_tasks_by_date(notion, data_source_id="ds_123", date="2026-05-28")

        self.assertEqual(
            notion.data_sources.queries[0]["filter"],
            {
                "and": [
                    {"property": START_PROP, "date": {"before": "2026-05-29T00:00:00+08:00"}},
                    {"property": END_PROP, "date": {"after": "2026-05-28T00:00:00+08:00"}},
                ]
            },
        )

    def test_query_notion_tasks_combines_multiple_attribute_filters(self):
        notion = FakeNotion()

        query_notion_tasks(
            notion,
            data_source_id="ds_123",
            start_time="2026-05-28T00:00:00+08:00",
            end_time="2026-05-29T00:00:00+08:00",
            category="雿平",
            priority=CRITICAL_PRIORITY,
            status=IN_PROGRESS_STATUS,
            keyword="DRL",
        )

        self.assertEqual(
            notion.data_sources.queries[0]["filter"],
            {
                "and": [
                    {"property": START_PROP, "date": {"before": "2026-05-29T00:00:00+08:00"}},
                    {"property": END_PROP, "date": {"after": "2026-05-28T00:00:00+08:00"}},
                    {"property": CATEGORY_PROP, "select": {"equals": "雿平"}},
                    {"property": PRIORITY_PROP, "select": {"equals": CRITICAL_PRIORITY}},
                    {"property": STATUS_PROP, "status": {"equals": IN_PROGRESS_STATUS}},
                    {"property": TITLE_PROP, "title": {"contains": "DRL"}},
                ]
            },
        )

    def test_update_notion_task_updates_start_and_end_dates(self):
        notion = FakeNotion()

        result = update_notion_task(
            notion,
            task_id="page_123",
            title="Updated Meeting",
            new_start_time="2026-05-29T09:00:00+08:00",
            new_end_time="2026-05-29T10:00:00+08:00",
            tags=["work"],
            priority=CRITICAL_PRIORITY,
            status=IN_PROGRESS_STATUS,
            notes="Updated by test.",
        )

        self.assertEqual(result["status"], "updated")
        self.assertEqual(
            notion.pages.updated[0],
            {
                "page_id": "page_123",
                "properties": {
                    TITLE_PROP: {"title": [{"text": {"content": "Updated Meeting"}}]},
                    START_PROP: {"date": {"start": "2026-05-29T09:00:00+08:00"}},
                    END_PROP: {"date": {"start": "2026-05-29T10:00:00+08:00"}},
                    CATEGORY_PROP: {"select": {"name": "work"}},
                    PRIORITY_PROP: {"select": {"name": CRITICAL_PRIORITY}},
                    STATUS_PROP: {"status": {"name": IN_PROGRESS_STATUS}},
                    NOTES_PROP: {"rich_text": [{"text": {"content": "Updated by test."}}]},
                },
            },
        )

    def test_delete_notion_task_archives_page(self):
        notion = FakeNotion()

        result = delete_notion_task(notion, task_id="page_123")

        self.assertEqual(result["status"], "deleted")
        self.assertEqual(notion.pages.updated[0], {"page_id": "page_123", "archived": True})


if __name__ == "__main__":
    unittest.main()
