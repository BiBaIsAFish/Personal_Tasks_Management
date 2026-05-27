import unittest

from notion_agent_bot.agent_controller import AgentController
from notion_agent_bot.notion_tools import MockNotionTools


class AgentControllerTest(unittest.TestCase):
    def test_creates_task_when_time_is_clear_and_no_conflict(self):
        tools = MockNotionTools(reference_now="2026-05-27T11:30:00+08:00")
        agent = AgentController(tools)

        response = agent.handle_message("明天下午三點開會一小時")

        self.assertEqual(response.status, "created")
        self.assertEqual(response.task["title"], "開會")
        self.assertEqual(response.task["start_time"], "2026-05-28T15:00:00+08:00")
        self.assertEqual(response.task["end_time"], "2026-05-28T16:00:00+08:00")
        self.assertEqual(
            [call["name"] for call in response.tool_calls],
            [
                "get_current_time",
                "parse_time_range",
                "query_notion_schedule",
                "create_notion_task",
            ],
        )

    def test_asks_for_confirmation_when_schedule_conflicts(self):
        tools = MockNotionTools(
            reference_now="2026-05-27T11:30:00+08:00",
            initial_tasks=[
                {
                    "task_id": "abc123",
                    "title": "Project Meeting",
                    "start_time": "2026-05-28T15:30:00+08:00",
                    "end_time": "2026-05-28T16:30:00+08:00",
                    "tags": ["work"],
                }
            ],
        )
        agent = AgentController(tools)

        response = agent.handle_message("明天三點排一個新行程")

        self.assertEqual(response.status, "needs_confirmation")
        self.assertIn("Project Meeting", response.message)
        self.assertEqual(len(tools.tasks), 1)
        self.assertEqual(
            [call["name"] for call in response.tool_calls],
            ["get_current_time", "parse_time_range", "query_notion_schedule"],
        )

    def test_uses_pending_conflict_when_user_confirms(self):
        tools = MockNotionTools(
            reference_now="2026-05-27T11:30:00+08:00",
            initial_tasks=[
                {
                    "task_id": "abc123",
                    "title": "Project Meeting",
                    "start_time": "2026-05-28T15:30:00+08:00",
                    "end_time": "2026-05-28T16:30:00+08:00",
                    "tags": ["work"],
                }
            ],
        )
        agent = AgentController(tools)
        agent.handle_message("明天三點排一個新行程")

        response = agent.handle_message("還是幫我加上去")

        self.assertEqual(response.status, "created")
        self.assertEqual(len(tools.tasks), 2)
        self.assertEqual(response.tool_calls[-1]["name"], "create_notion_task")

    def test_asks_for_more_information_when_time_is_ambiguous(self):
        tools = MockNotionTools(reference_now="2026-05-27T11:30:00+08:00")
        agent = AgentController(tools)

        response = agent.handle_message("週末找時間讀書")

        self.assertEqual(response.status, "needs_information")
        self.assertEqual(
            [call["name"] for call in response.tool_calls],
            ["get_current_time", "parse_time_range"],
        )


if __name__ == "__main__":
    unittest.main()
