# Gemini Notion Discord Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Gemini function-calling controller that lets the Discord bot operate Notion through guarded Python tools.

**Architecture:** Discord remains an adapter in `run_bot/discord_bot.py`. `LLM_agent/gemini_controller.py` owns Gemini API interaction and tool-call looping. `notion_function/adapter.py` wraps existing Notion functions, injects Notion dependencies, validates tool calls, and records results.

**Tech Stack:** Python, `discord.py`, `python-dotenv`, `notion-client`, `google-genai`, `unittest`.

---

## File Structure

- Create `notion_function/adapter.py`
  - Owns `NotionFunctionAdapter`.
  - Exposes a safe `call_tool(name, arguments)` facade for Gemini.
  - Injects `notion` and `data_source_id` into existing `notion_functions.tools`.
  - Records `tool_calls`.

- Create `tests/test_notion_function_adapter.py`
  - Tests allowlist, argument validation, error handling, and dependency injection.

- Create `LLM_agent/gemini_controller.py`
  - Owns Gemini system prompt, function declarations, and tool-call loop.
  - Keeps `google-genai` SDK details contained.

- Create `tests/test_gemini_controller.py`
  - Uses a fake Gemini client so tests do not call the network.
  - Verifies tool dispatch and final response behavior.

- Modify `run_bot/discord_bot.py`
  - Add `build_agent()` so controller selection is testable.
  - Use Gemini controller when `GEMINI_API_KEY` exists.
  - Keep mock `AgentController(MockNotionTools())` fallback.

- Create `tests/test_discord_bot_config.py`
  - Verifies controller selection without starting Discord.

- Modify `run_bot/requirements.txt`
  - Add `google-genai`.

- Modify `run_bot/README.md`
  - Document new `.env` values and production mode.

---

## Task 1: Notion Function Adapter

**Files:**
- Create: `notion_function/adapter.py`
- Test: `tests/test_notion_function_adapter.py`

- [ ] **Step 1: Write failing adapter tests**

Create `tests/test_notion_function_adapter.py`:

```python
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
```

- [ ] **Step 2: Run adapter tests to verify failure**

Run:

```powershell
python -m unittest tests.test_notion_function_adapter -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'notion_function.adapter'`.

- [ ] **Step 3: Implement adapter**

Create `notion_function/adapter.py`:

```python
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from . import tools


class NotionFunctionAdapter:
    def __init__(self, notion: Any, data_source_id: str) -> None:
        self.notion = notion
        self.data_source_id = data_source_id
        self.tool_calls: list[dict[str, Any]] = []
        self._tools: dict[str, tuple[Callable[..., dict[str, Any]], set[str]]] = {
            "get_current_time": (self._get_current_time, set()),
            "query_notion_schedule": (self._query_notion_schedule, {"start_time", "end_time"}),
            "get_notion_task": (self._get_notion_task, {"task_id"}),
            "query_notion_tasks_by_date": (self._query_notion_tasks_by_date, {"date"}),
            "query_notion_tasks": (self._query_notion_tasks, set()),
            "create_notion_task": (self._create_notion_task, {"title", "start_time", "end_time"}),
            "update_notion_task": (self._update_notion_task, {"task_id"}),
            "delete_notion_task": (self._delete_notion_task, {"task_id"}),
        }

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools)

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        args = dict(arguments or {})
        if name not in self._tools:
            result = {"status": "error", "error": "unknown_tool", "message": f"Unknown tool: {name}"}
            self._record(name, args, result)
            return result

        function, required = self._tools[name]
        for argument in sorted(required):
            if argument not in args or args[argument] in (None, ""):
                result = {
                    "status": "error",
                    "error": "missing_argument",
                    "argument": argument,
                    "message": f"Missing required argument: {argument}",
                }
                self._record(name, args, result)
                return result

        try:
            result = function(**args)
        except Exception as exc:
            result = {"status": "error", "error": "tool_error", "message": str(exc)}

        self._record(name, args, result)
        return result

    def _record(self, name: str, arguments: dict[str, Any], result: dict[str, Any]) -> None:
        self.tool_calls.append({"name": name, "arguments": arguments, "result": result})

    def _get_current_time(self, timezone_name: str = "Asia/Taipei") -> dict[str, Any]:
        return tools.get_current_time(timezone_name=timezone_name)

    def _query_notion_schedule(self, start_time: str, end_time: str) -> dict[str, Any]:
        return tools.query_notion_schedule(self.notion, self.data_source_id, start_time, end_time)

    def _get_notion_task(self, task_id: str) -> dict[str, Any]:
        return tools.get_notion_task(self.notion, task_id)

    def _query_notion_tasks_by_date(self, date: str, timezone_name: str = "Asia/Taipei") -> dict[str, Any]:
        return tools.query_notion_tasks_by_date(self.notion, self.data_source_id, date, timezone_name)

    def _query_notion_tasks(
        self,
        start_time: str | None = None,
        end_time: str | None = None,
        category: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        keyword: str | None = None,
    ) -> dict[str, Any]:
        return tools.query_notion_tasks(
            self.notion,
            self.data_source_id,
            start_time=start_time,
            end_time=end_time,
            category=category,
            priority=priority,
            status=status,
            keyword=keyword,
        )

    def _create_notion_task(
        self,
        title: str,
        start_time: str,
        end_time: str,
        tags: list[str] | None = None,
        priority: str | None = None,
        status: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        return tools.create_notion_task(
            self.notion,
            self.data_source_id,
            title,
            start_time,
            end_time,
            tags=tags,
            priority=priority,
            status=status,
            notes=notes,
        )

    def _update_notion_task(
        self,
        task_id: str,
        title: str | None = None,
        new_start_time: str | None = None,
        new_end_time: str | None = None,
        tags: list[str] | None = None,
        priority: str | None = None,
        status: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        return tools.update_notion_task(
            self.notion,
            task_id,
            title=title,
            new_start_time=new_start_time,
            new_end_time=new_end_time,
            tags=tags,
            priority=priority,
            status=status,
            notes=notes,
        )

    def _delete_notion_task(self, task_id: str) -> dict[str, Any]:
        return tools.delete_notion_task(self.notion, task_id)
```

- [ ] **Step 4: Run adapter tests to verify pass**

Run:

```powershell
python -m unittest tests.test_notion_function_adapter -v
```

Expected: PASS.

- [ ] **Step 5: Commit adapter**

```powershell
git add notion_function/adapter.py tests/test_notion_function_adapter.py
git commit -m "feat: add notion function adapter"
```

---

## Task 2: Gemini Controller

**Files:**
- Create: `LLM_agent/gemini_controller.py`
- Test: `tests/test_gemini_controller.py`

- [ ] **Step 1: Write failing Gemini controller tests**

Create `tests/test_gemini_controller.py`:

```python
import unittest

from LLM_agent.gemini_controller import GeminiAgentController


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
        return FakeResponse(text="?曉??2026-05-28??)


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

        response = controller.handle_message("?曉??嚗?)

        self.assertEqual(response.status, "ok")
        self.assertEqual(response.message, "?曉??2026-05-28??)
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

        response = controller.handle_message("?啣??予銝???")

        self.assertEqual(response.status, "error")
        self.assertIn("api unavailable", response.message)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run Gemini controller tests to verify failure**

Run:

```powershell
python -m unittest tests.test_gemini_controller -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'LLM_agent.gemini_controller'`.

- [ ] **Step 3: Implement Gemini controller**

Create `LLM_agent/gemini_controller.py`:

```python
from __future__ import annotations

import os
from typing import Any

from .schemas import AgentResponse


SYSTEM_PROMPT = """
雿 Notion 隞餃??拍???雿輻蝜?銝剜??? Discord 雿輻??
閬?嚗?1. 鞈?銝雲?????璅遙????嚗?亥岷?蝙?刻?銝??澆撖怠撌亙??2. ?啣?隞餃??耨?嫣遙????嚗????亥岷銵???3. ?交?銵?嚗???雿輻??瘙Ⅱ隤?銝?撱箇???啜?4. ?湔??文?嚗???蝣箄??臭??Ⅱ??task_id??5. 銝??芾??潭? Notion select?tatus?riority ?潦?6. 撌亙憭望???隤芣?憭望???嚗?閬恐蝔望???""".strip()


class GeminiAgentController:
    def __init__(self, client: Any, adapter: Any, model: str) -> None:
        self.client = client
        self.adapter = adapter
        self.model = model

    @classmethod
    def from_env(cls, adapter: Any) -> "GeminiAgentController":
        from google import genai

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing GEMINI_API_KEY")
        model = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")
        return cls(client=genai.Client(api_key=api_key), adapter=adapter, model=model)

    def handle_message(self, text: str) -> AgentResponse:
        try:
            contents: list[Any] = [text]
            for _ in range(8):
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=self._config(),
                )
                function_calls = self._function_calls(response)
                if not function_calls:
                    return AgentResponse(
                        status="ok",
                        message=self._response_text(response),
                        tool_calls=list(self.adapter.tool_calls),
                    )

                contents.append(response.candidates[0].content)
                for call in function_calls:
                    result = self.adapter.call_tool(call.name, dict(call.args or {}))
                    contents.append(self._function_response(call.name, result))

            return AgentResponse(
                status="error",
                message="撌亙?澆甈⊥??嚗???瘙牧敺?Ⅱ銝暺?,
                tool_calls=list(self.adapter.tool_calls),
            )
        except Exception as exc:
            return AgentResponse(status="error", message=f"Gemini ??憭望?嚗exc}", tool_calls=list(self.adapter.tool_calls))

    def _config(self) -> dict[str, Any]:
        return {
            "system_instruction": SYSTEM_PROMPT,
            "tools": [{"function_declarations": self._function_declarations()}],
        }

    def _function_declarations(self) -> list[dict[str, Any]]:
        return [
            self._declaration("get_current_time", "Get current local time.", {"timezone_name": "string"}),
            self._declaration("query_notion_schedule", "Query schedule conflicts.", {"start_time": "string", "end_time": "string"}, ["start_time", "end_time"]),
            self._declaration("get_notion_task", "Get one Notion task by task_id.", {"task_id": "string"}, ["task_id"]),
            self._declaration("query_notion_tasks_by_date", "Query tasks overlapping a local date.", {"date": "string", "timezone_name": "string"}, ["date"]),
            self._declaration(
                "query_notion_tasks",
                "Query tasks by filters.",
                {
                    "start_time": "string",
                    "end_time": "string",
                    "category": "string",
                    "priority": "string",
                    "status": "string",
                    "keyword": "string",
                },
            ),
            self._declaration(
                "create_notion_task",
                "Create a Notion task.",
                {
                    "title": "string",
                    "start_time": "string",
                    "end_time": "string",
                    "tags": "array",
                    "priority": "string",
                    "status": "string",
                    "notes": "string",
                },
                ["title", "start_time", "end_time"],
            ),
            self._declaration(
                "update_notion_task",
                "Update a Notion task.",
                {
                    "task_id": "string",
                    "title": "string",
                    "new_start_time": "string",
                    "new_end_time": "string",
                    "tags": "array",
                    "priority": "string",
                    "status": "string",
                    "notes": "string",
                },
                ["task_id"],
            ),
            self._declaration("delete_notion_task", "Archive a Notion task.", {"task_id": "string"}, ["task_id"]),
        ]

    def _declaration(
        self,
        name: str,
        description: str,
        properties: dict[str, str],
        required: list[str] | None = None,
    ) -> dict[str, Any]:
        schema_properties = {}
        for prop_name, prop_type in properties.items():
            if prop_type == "array":
                schema_properties[prop_name] = {"type": "ARRAY", "items": {"type": "STRING"}}
            else:
                schema_properties[prop_name] = {"type": "STRING"}
        return {
            "name": name,
            "description": description,
            "parameters": {
                "type": "OBJECT",
                "properties": schema_properties,
                "required": required or [],
            },
        }

    def _function_calls(self, response: Any) -> list[Any]:
        calls = []
        for candidate in getattr(response, "candidates", []) or []:
            for part in getattr(candidate.content, "parts", []) or []:
                call = getattr(part, "function_call", None)
                if call:
                    calls.append(call)
        return calls

    def _response_text(self, response: Any) -> str:
        text = getattr(response, "text", "") or ""
        return text.strip() or "?瘜??閬?隢?閰虫?甈～?

    def _function_response(self, name: str, result: dict[str, Any]) -> dict[str, Any]:
        return {"role": "tool", "parts": [{"function_response": {"name": name, "response": result}}]}
```

- [ ] **Step 4: Run Gemini controller tests to verify pass**

Run:

```powershell
python -m unittest tests.test_gemini_controller -v
```

Expected: PASS.

- [ ] **Step 5: Commit Gemini controller**

```powershell
git add LLM_agent/gemini_controller.py tests/test_gemini_controller.py
git commit -m "feat: add gemini agent controller"
```

---

## Task 3: Discord Controller Selection

**Files:**
- Modify: `run_bot/discord_bot.py`
- Test: `tests/test_discord_bot_config.py`

- [ ] **Step 1: Write failing controller selection tests**

Create `tests/test_discord_bot_config.py`:

```python
import os
import unittest
from unittest.mock import patch

import run_bot.discord_bot as discord_bot
from LLM_agent.agent_controller import AgentController


class DiscordBotConfigTest(unittest.TestCase):
    def test_build_agent_uses_mock_without_gemini_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            agent = discord_bot.build_agent()

        self.assertIsInstance(agent, AgentController)

    def test_build_agent_uses_gemini_when_api_key_exists(self):
        class FakeGeminiController:
            @classmethod
            def from_env(cls, adapter):
                instance = cls()
                instance.adapter = adapter
                return instance

        with patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": "key",
                "NOTION_TOKEN": "notion",
                "NOTION_DATA_SOURCE_ID": "ds_123",
            },
            clear=True,
        ), patch.object(discord_bot, "GeminiAgentController", FakeGeminiController), patch.object(
            discord_bot,
            "create_notion_client_from_env",
            return_value=(object(), "ds_123"),
        ):
            agent = discord_bot.build_agent()

        self.assertIsInstance(agent, FakeGeminiController)
        self.assertEqual(agent.adapter.data_source_id, "ds_123")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run Discord config tests to verify failure**

Run:

```powershell
python -m unittest tests.test_discord_bot_config -v
```

Expected: FAIL because `build_agent` is not defined.

- [ ] **Step 3: Refactor Discord bot wiring**

Modify `run_bot/discord_bot.py` imports and agent creation:

```python
from LLM_agent.agent_controller import AgentController  # noqa: E402
from LLM_agent.gemini_controller import GeminiAgentController  # noqa: E402
from notion_function import create_notion_client_from_env  # noqa: E402
from notion_function.adapter import NotionFunctionAdapter  # noqa: E402
from LLM_agent.notion_tools import MockNotionTools  # noqa: E402
```

Replace:

```python
agent = AgentController(MockNotionTools())
```

with:

```python
def build_agent():
    if os.environ.get("GEMINI_API_KEY"):
        notion, data_source_id = create_notion_client_from_env(ROOT_DIR / "run_bot" / ".env")
        adapter = NotionFunctionAdapter(notion, data_source_id)
        return GeminiAgentController.from_env(adapter)
    return AgentController(MockNotionTools())


agent = build_agent()
```

- [ ] **Step 4: Run Discord config tests to verify pass**

Run:

```powershell
python -m unittest tests.test_discord_bot_config -v
```

Expected: PASS.

- [ ] **Step 5: Commit Discord wiring**

```powershell
git add run_bot/discord_bot.py tests/test_discord_bot_config.py
git commit -m "feat: select gemini controller for discord bot"
```

---

## Task 4: Dependencies and Documentation

**Files:**
- Modify: `run_bot/requirements.txt`
- Modify: `run_bot/README.md`

- [ ] **Step 1: Add dependency**

Modify `run_bot/requirements.txt`:

```text
discord.py
python-dotenv
notion-client
google-genai
```

- [ ] **Step 2: Update README configuration**

Add a concise production `.env` section to `run_bot/README.md`:

## Gemini + Notion production mode

Set these values in `run_bot/.env`:

```env
DISCORD_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_google_ai_studio_key
GEMINI_MODEL=gemini-3-flash-preview
NOTION_TOKEN=your_notion_integration_secret
NOTION_DATA_SOURCE_ID=your_notion_data_source_id
```

`GEMINI_MODEL` is optional. If `GEMINI_API_KEY` is not set, the bot uses the local mock controller.

- [ ] **Step 3: Commit dependency and docs**

```powershell
git add run_bot/requirements.txt run_bot/README.md
git commit -m "docs: document gemini production config"
```

---

## Task 5: Full Verification

**Files:**
- No new files.

- [ ] **Step 1: Run focused tests**

Run:

```powershell
python -m unittest tests.test_notion_function_adapter tests.test_gemini_controller tests.test_discord_bot_config -v
```

Expected: PASS.

- [ ] **Step 2: Run existing test suite**

Run:

```powershell
python -m unittest discover tests -v
```

Expected: PASS. If existing tests fail because current repository files contain unrelated encoding or syntax issues, record the exact failing file and line before changing anything.

- [ ] **Step 3: Check git status**

Run:

```powershell
git status --short
```

Expected: no uncommitted implementation files after task commits, except user-owned unrelated changes if present.

---

## Self-Review

Spec coverage:

- Gemini production controller: Task 2.
- Python guardrail adapter: Task 1.
- Discord prompt flow and controller selection: Task 3.
- Environment configuration and dependency: Task 4.
- Runtime errors returned as Discord-readable messages: Task 1 and Task 2.
- Tests requested by spec: Tasks 1, 2, 3, and 5.

Completeness scan:

- All implementation steps include concrete file paths, commands, and expected results.

Type consistency:

- `NotionFunctionAdapter.call_tool(name, arguments)` is used consistently by controller tests and controller implementation.
- `GeminiAgentController.from_env(adapter)` is used consistently by Discord wiring.
- `AgentResponse.status/message/tool_calls` matches the existing schema.
