# Gemini Notion Discord Design

## Goal

Use Discord as the user interface, Gemini as the intent and function-calling controller, and Notion as the task database.

When a user mentions the Discord bot, the bot sends the remaining message to Gemini. Gemini decides which Notion operation is needed, calls only approved Python functions, and returns a final Traditional Chinese response for Discord. If the request lacks required information or is unsafe to execute, Gemini returns a clarification or error message and no Notion write happens.

## Architecture

The existing `run_bot/discord_bot.py` stays as the Discord adapter. It should strip the bot mention, pass text to an agent controller, and send the returned message.

Add `notion_agent_bot/gemini_controller.py` as the production controller. It will:

- Load Gemini configuration from environment variables.
- Build a Gemini client.
- Provide a system prompt with Notion operation rules.
- Expose a fixed list of Notion tools to Gemini.
- Run the tool-call loop until Gemini returns a final text response.
- Return `AgentResponse` with status, message, and recorded tool calls.

Add `notion_agent_bot/notion_functions/adapter.py` as the guardrail layer. It will wrap the existing Notion functions and bind the Notion client plus data source ID. Gemini will never receive direct access to the raw Notion client.

`AgentController(MockNotionTools())` remains available as the fallback and test-friendly mock path.

## Configuration

Use `run_bot/.env`:

```env
DISCORD_TOKEN=...
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3-flash-preview
NOTION_TOKEN=...
NOTION_DATA_SOURCE_ID=...
```

`GEMINI_MODEL` is optional. It should default to a current Flash model that supports function calling. Keeping it configurable avoids hard-coding a model name that may change.

## Tool Surface

Expose these Notion operations to Gemini:

- `get_current_time(timezone_name="Asia/Taipei")`
- `query_notion_schedule(start_time, end_time)`
- `get_notion_task(task_id)`
- `query_notion_tasks_by_date(date, timezone_name="Asia/Taipei")`
- `query_notion_tasks(start_time=None, end_time=None, category=None, priority=None, status=None, keyword=None)`
- `create_notion_task(title, start_time, end_time, tags=None, priority=None, status=None, notes=None)`
- `update_notion_task(task_id, title=None, new_start_time=None, new_end_time=None, tags=None, priority=None, status=None, notes=None)`
- `delete_notion_task(task_id)`

All timestamps must use ISO 8601 with timezone offsets.

## Guardrails

Python enforces these constraints before executing a tool:

- Only named allowlisted functions can run.
- Required arguments must be present.
- Empty titles are rejected.
- Update and delete require a concrete `task_id`.
- Tool exceptions are captured and returned to Gemini as structured errors.
- Tool calls are recorded for tests and debugging.

Gemini is instructed to follow these operation rules:

- Reply in Traditional Chinese.
- Ask for clarification if intent, time, target task, or required fields are unclear.
- Do not call write tools when required information is missing.
- Query schedule conflicts before creating a task or changing task time.
- If conflicts exist, ask the user for confirmation instead of writing.
- Before update or delete, identify one clear target task.
- Do not invent unsupported Notion select/status/priority values.
- Explain tool failures instead of claiming success.

## Data Flow

1. Discord receives a message.
2. Bot ignores messages from bots.
3. In a guild, bot processes only mentioned messages. In DM, it processes all user messages.
4. Bot strips its mention and sends the prompt to `GeminiAgentController.handle_message`.
5. Controller sends the prompt, system instruction, and tool declarations to Gemini.
6. If Gemini requests tool calls, controller dispatches each call through `NotionFunctionAdapter`.
7. Tool results are sent back to Gemini.
8. Gemini returns final text.
9. Bot sends final text to Discord.

## Error Handling

Missing environment variables should fail at startup with clear messages for production mode.

Runtime tool errors should not crash the Discord bot. The controller should return a readable Discord response, for example:

- Missing required information.
- Notion API failure.
- No matching task found.
- Multiple possible tasks found.
- Conflict detected.

## Testing

Add focused tests for:

- Gemini controller dispatches a tool call and returns the final model message.
- Adapter allowlist rejects unknown function names.
- Adapter reports validation errors without calling Notion.
- Discord bot selects Gemini controller when `GEMINI_API_KEY` is set and mock controller otherwise.

Existing Notion function tests remain the main coverage for Notion request payloads.

## Implementation Notes

Use the official `google-genai` Python SDK for Gemini API access and function calling. Keep the SDK boundary inside `gemini_controller.py` so the rest of the project remains easy to test.

The first implementation should prioritize correctness and debuggability over broad conversation memory. A later version can add per-user or per-channel pending confirmation state.
