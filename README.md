# HW4: Notion Smart Scheduler

本專案是一個 AI Harness / LLM agent prototype，用 Discord Bot 當使用者前端、Notion database 當資料後端，並由 LLM 負責理解自然語言、決定 tool calls、串接排程查詢與任務建立流程。

## 專案脈絡

- 最初的草稿計劃書放在 [docs/plan.md](docs/plan.md)。
- 後續透過 Superpowers 產生更明確的 spec 與 implementation plan：
  - [docs/superpowers/specs/2026-05-28-gemini-notion-discord-design.md](docs/superpowers/specs/2026-05-28-gemini-notion-discord-design.md)
  - [docs/superpowers/plans/2026-05-28-gemini-notion-discord.md](docs/superpowers/plans/2026-05-28-gemini-notion-discord.md)
- 實作過程與重要決策記錄在 [docs/log.md](docs/log.md)。

## 系統架構

```text
User
  -> Discord Bot frontend
  -> LLM controller / function-calling orchestrator
  -> guarded Notion tool layer
  -> Notion database backend
```

核心設計：

- Discord Bot 負責接收使用者訊息與回覆結果。
- LLM 負責解析排程意圖、判斷是否需要查詢或建立 Notion task。
- Notion tool layer 封裝 Notion API，避免 LLM 直接操作 raw client。
- Notion database 儲存排程任務、狀態、時間與備註。

## 部署與模型

我的實作部署在 Oracle VM 上，使用 `.env` 設定 Discord、Notion 與 Gemini API credentials。

LLM 選用 `gemini 3.1 flash lite`，主要考量是成本低、速度快，且 rate limit 對這個課堂 prototype 夠用。

Rate limit 參考：https://aistudio.google.com/rate-limit

## 資料夾結構

```text
.
├── LLM_agent/
├── notion_function/
├── run_bot/
├── docs/
├── tests/
├── README.md
├── .gitattributes
└── .gitignore
```

- `LLM_agent/`：LLM orchestration 核心，包含 mock agent、Gemini function-calling controller、prompt、schema 與系統提示。
- `notion_function/`：Notion 後端工具層，包含 client 建立、CRUD/search helper、guarded adapter 與 draft store。
- `run_bot/`：Discord Bot 執行入口，包含 bot adapter、環境變數範例、requirements、Oracle VM/systemd 範例與 Notion schema。
- `docs/`：作業文件與開發紀錄，包含 plan、report、infographic、evaluation cases、log，以及 Superpowers 產生的 specs/plans。
- `tests/`：單元測試與 opt-in integration test，驗證 agent workflow、Gemini controller、Discord config、Notion functions 與 adapter。

各主要資料夾內也有各自的 `README.md`，可查看更細的模組說明。
