import unittest

from notion_agent_bot.gemini_controller import GeminiAgentController


class FakeFunctionCall:
    def __init__(self, name, args):
        self.name = name
        self.args = args


class FakePart:
    def __init__(self, function_call=None, text=None):
        self.function_call = function_call
        self.text = text


class FakeContent:
    def __init__(self, parts):
        self.parts = parts


class FakeCandidate:
    def __init__(self, parts):
        self.content = FakeContent(parts)


class FakeResponse:
    def __init__(self, parts=None, text=""):
        self.candidates = [FakeCandidate(parts or [])]
        self.text = text


class FakeModels:
    def __init__(self):
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            return FakeResponse(
                parts=[
                    FakePart(
                        function_call=FakeFunctionCall(
                            "get_current_time",
                            {"timezone_name": "Asia/Taipei"},
                        )
                    )
                ]
            )
        return FakeResponse(text="Now: 2026-05-28")


class FakeClient:
    def __init__(self):
        self.models = FakeModels()


class FakeAdapter:
    def __init__(self):
        self.tool_calls = []

    def call_tool(self, name, arguments):
        result = {"timezone": "Asia/Taipei", "current_time": "2026-05-28T12:00:00+08:00"}
        self.tool_calls.append({"name": name, "arguments": arguments, "result": result})
        return result


class GeminiAgentControllerTest(unittest.TestCase):
    def test_dispatches_tool_call_and_returns_final_text(self):
        client = FakeClient()
        adapter = FakeAdapter()
        controller = GeminiAgentController(client=client, adapter=adapter, model="fake-model")

        response = controller.handle_message("what time is it?")

        self.assertEqual(response.status, "ok")
        self.assertEqual(response.message, "Now: 2026-05-28")
        self.assertEqual(adapter.tool_calls[0]["name"], "get_current_time")
        self.assertEqual(len(client.models.calls), 2)

    def test_returns_error_response_when_controller_fails(self):
        class BrokenModels:
            def generate_content(self, **kwargs):
                raise RuntimeError("api unavailable")

        class BrokenClient:
            def __init__(self):
                self.models = BrokenModels()

        controller = GeminiAgentController(client=BrokenClient(), adapter=FakeAdapter(), model="fake-model")

        response = controller.handle_message("please create a task")

        self.assertEqual(response.status, "error")
        self.assertIn("api unavailable", response.message)


if __name__ == "__main__":
    unittest.main()
