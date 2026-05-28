from __future__ import annotations

import os
from typing import Any

from .schemas import AgentResponse


SYSTEM_PROMPT = """
You are a Notion scheduling assistant running behind a Discord bot.
Use tools when current time or Notion task data is needed.
Return concise, user-facing responses.
Do not invent Notion task IDs or select/status/priority values.
If a tool returns an error, explain what is missing or what failed.
""".strip()
RATE_LIMIT_MESSAGE = "Gemini API quota exceeded. Please try again later."


class GeminiAgentController:
    def __init__(self, client: Any, adapter: Any, model: str) -> None:
        self.client = client
        self.adapter = adapter
        self.model = model
        self.system_prompt = os.environ.get("GEMINI_SYSTEM_PROMPT", SYSTEM_PROMPT)

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
                message="Gemini exceeded the tool-call limit.",
                tool_calls=list(self.adapter.tool_calls),
            )
        except Exception as exc:
            if self._is_rate_limit_error(exc):
                return AgentResponse(
                    status="error",
                    message=RATE_LIMIT_MESSAGE,
                    tool_calls=list(self.adapter.tool_calls),
                )
            return AgentResponse(
                status="error",
                message=f"Gemini controller error: {exc}",
                tool_calls=list(self.adapter.tool_calls),
            )

    def _config(self) -> dict[str, Any]:
        return {
            "system_instruction": self.system_prompt,
            "tools": [{"function_declarations": self._function_declarations()}],
        }

    def _is_rate_limit_error(self, exc: Exception) -> bool:
        return getattr(exc, "status_code", None) == 429 or getattr(exc, "code", None) == 429

    def _function_declarations(self) -> list[dict[str, Any]]:
        return [
            self._declaration("get_current_time", "Get current local time.", {"timezone_name": "string"}),
            self._declaration(
                "query_notion_schedule",
                "Query schedule conflicts.",
                {"start_time": "string", "end_time": "string"},
                ["start_time", "end_time"],
            ),
            self._declaration(
                "get_notion_task",
                "Get one Notion task by task_id.",
                {"task_id": "string"},
                ["task_id"],
            ),
            self._declaration(
                "query_notion_tasks_by_date",
                "Query tasks overlapping a local date.",
                {"date": "string", "timezone_name": "string"},
                ["date"],
            ),
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
            content = getattr(candidate, "content", None)
            for part in getattr(content, "parts", []) or []:
                call = getattr(part, "function_call", None)
                if call:
                    calls.append(call)
        return calls

    def _response_text(self, response: Any) -> str:
        text = getattr(response, "text", "") or ""
        return text.strip() or "I could not produce a response."

    def _function_response(self, name: str, result: dict[str, Any]) -> dict[str, Any]:
        return {"role": "tool", "parts": [{"function_response": {"name": name, "response": result}}]}
