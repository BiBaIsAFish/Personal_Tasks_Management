# LLM_agent

Notion scheduling agent 的核心模組。它把使用者訊息轉成 task 操作，支援本機 mock 流程，也支援 Gemini function calling 串接外部 Notion tool adapter。

## 功能

- 解析自然語言排程需求，建立或更新 Notion task。
- 建立 task 前先查詢既有排程，遇到衝突時要求確認。
- 提供 mock tools，方便本機測試 orchestration flow。
- 提供 Gemini controller，讓 LLM 透過 tool calls 呼叫 Notion adapter。

## 檔案

| File | Purpose |
| --- | --- |
| `main.py` | 本機互動式 mock CLI entry point。 |
| `agent_controller.py` | Rule-based mock controller，負責時間解析、衝突檢查與建立 task。 |
| `gemini_controller.py` | Gemini API controller，處理 function calling loop 與錯誤回覆。 |
| `notion_tools.py` | In-memory mock Notion tools，用於測試與 fallback。 |
| `notion_task_creator.py` | 使用 `notion-client` 建立 Notion page 的 helper。 |
| `schemas.py` | `AgentResponse` response dataclass。 |
| `prompts.py` | 簡短 system prompt 常數。 |
| `system_prompt.md` | Gemini 使用的較完整 Notion task prompt template。 |

## 使用方式

安裝依賴：

```powershell
pip install -r run_bot\requirements.txt
```

執行 mock CLI：

```powershell
python -m LLM_agent.main
```

在 Discord bot 中使用：

```powershell
python run_bot\discord_bot.py
```

`run_bot/discord_bot.py` 會依環境變數選擇 controller：

- 有 `GEMINI_API_KEY`：使用 `GeminiAgentController` + Notion adapter。
- 沒有 `GEMINI_API_KEY`：使用 `AgentController(MockNotionTools())`。

## Environment Variables

Gemini mode 常用設定：

```env
GEMINI_API_KEY=your_google_ai_studio_key
GEMINI_MODEL=gemini-3-flash-preview
GEMINI_SYSTEM_PROMPT_PATH=../LLM_agent/system_prompt.md
```

Notion/Discord 相關設定放在 `run_bot/.env`，詳見 `run_bot/README.md`。

## Tests

```powershell
python -m unittest tests.test_agent_controller tests.test_gemini_controller tests.test_notion_task_creator
```

Integration test 需要真實 Notion token/database，預設不建議直接跑。
