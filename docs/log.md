# HW4 設計紀錄

## 維護規則

後續 session 若修改了 `plan.md`、`report.md`、系統架構、工具設計、workflow、evaluation 或 infographic，請在本檔案最後追加一筆簡短紀錄。

建議格式：

```markdown
### YYYY-MM-DD HH:mm - 標題

- 做了什麼：
- 為什麼：
- 下一步：
```

## 專案摘要

- 作業：HW4 - AI Harness Systems Design and Analysis
- 主題：Notion 智慧排程代理
- 目標：設計一個以 LLM 作為控制器、透過 function calling 呼叫工具、檢查行程衝突並完成排程的 AI Harness 系統。

## 紀錄

### 2026-05-27 11:43 - 修改計畫方向

- 做了什麼：重寫 `plan.md`，將重點從完整 Discord + Notion 產品實作，調整為作業要求的 AI Harness 系統設計。
- 為什麼：作業評分重點是架構、工具編排、workflow、evaluation、infographic 與 log，而不是部署完整產品。
- 下一步：依照新計畫撰寫 `report.md`，再整理 infographic 與 evaluation cases。

### 2026-05-27 11:45 - 建立 log.md

- 做了什麼：建立本檔案，作為後續 AI 協作與設計決策紀錄。
- 為什麼：作業要求記錄 AI 輔助設計與迭代過程。
- 下一步：後續有重要修改時，在檔案最後追加簡短紀錄。

### 2026-05-27 11:50 - 精簡 log 格式

- 做了什麼：將 `log.md` 改成較短的中文版本。
- 為什麼：原本格式過於詳細，不利於快速維護。
- 下一步：後續紀錄維持簡短即可。

### 2026-05-27 11:55 - 確認 Discord Bot 範圍

- 做了什麼：將 `plan.md` 的原型範圍調整為單人私有 Discord server 使用。
- 為什麼：使用者只會自己使用 bot，可降低多人權限、memory 隔離與部署複雜度。
- 下一步：後續實作以單一使用者、固定 Notion database schema 的 MVP 為目標。

### 2026-05-27 12:20 - 完成主要交付物草稿

- 做了什麼：新增 `report.md`、`infographic.md`、`evaluation_cases.md`，並建立 `LLM_agent/` mock prototype 與 `tests/test_agent_controller.py`。
- 為什麼：依照 `plan.md` 的執行順序，先覆蓋報告、圖表、evaluation，再用 mock tools 展示 function calling 與 orchestration。
- 下一步：若環境安裝可用 Python runner，可執行 `python -m unittest discover -s tests` 驗證 prototype；目前本機 `python`/`py` 無法執行。

### 2026-05-27 12:30 - Codex 協作內容摘要

- 做了什麼：依照 `plan.md` 補齊 HW4 主要交付物，包含 `report.md`、`infographic.md`、`evaluation_cases.md`；另外建立 `LLM_agent/` mock prototype 與 `tests/test_agent_controller.py`，展示 time parsing、Notion schedule query、conflict confirmation 與 task creation 的 orchestration。
- 為什麼：作業重點是 AI Harness 系統設計、function calling、workflow、evaluation 與 log，而不是完整部署 Discord Bot 或正式 Notion API。
- 驗證狀態：已檢查交付檔案與報告章節存在；Python 測試因本機 `python`/`py` runner 不可用而尚未執行。
- 下一步：若安裝可用 Python，可執行 `python -m unittest discover -s tests` 驗證 mock prototype。

### 2026-05-27 14:28 - 整理專案文件

- 做了什麼：檢查專案根目錄所有檔案，建立 `docs/`，並用 `git mv` 將 `hw4_description.md`、`image.png`、`evaluation_cases.md`、`infographic.md`、`log.md`、`plan.md`、`report.md` 移入 `docs/`。
- 為什麼：讓根目錄保留程式碼、測試與設定檔，文件與圖片集中放在 `docs/`，方便維護。
- 驗證狀態：已確認根目錄剩下 `.gitattributes`、`docs/`、`LLM_agent/`、`tests/`，git 狀態顯示上述檔案為 rename。
- 下一步：後續文件新增時優先放入 `docs/`。

### 2026-05-27 14:32 - 新增 Discord Bot 執行資料夾

- 做了什麼：建立 `run_bot/`，新增 `discord_bot.py`、`requirements.txt`、`.env.example`、`.gitignore`、`notion-discord-bot.service.example`、`README.md`。
- 為什麼：將 Discord bot 執行、環境變數、Oracle VM 部署與 systemd 常駐設定集中管理，不混入核心 agent 模組。
- 設計決策：`discord_bot.py` 作為 adapter，收到 Discord 訊息後呼叫既有 `AgentController.handle_message()`；server 內需提到 bot 才回覆，DM 會直接回覆。
- 驗證狀態：已確認 `run_bot/` 檔案存在，README 包含 Discord Developer Portal、本機測試、Oracle VM 與 systemd 步驟；因本機 `python`/`py` 不可用，尚未執行語法檢查。
- 下一步：在可用 Python 環境安裝 `run_bot/requirements.txt`，設定 `run_bot/.env` 後測試 bot 登入。

### 2026-05-27 14:36 - 說明環境檔複製方式

- 做了什麼：說明 `Copy-Item run_bot\.env.example run_bot\.env` 是 PowerShell 的檔案複製指令，用途是從 `.env.example` 產生實際 `.env`。
- 為什麼：使用者在 Git Bash 執行 PowerShell 指令會遇到 `command not found`。
- 設計決策：Windows PowerShell 使用 `Copy-Item`；Git Bash、Linux、Oracle VM 使用 `cp run_bot/.env.example run_bot/.env`。
- 下一步：README 若要同時支援 PowerShell 與 Git Bash，可把兩種指令都列出。

### 2026-05-27 18:07 - 改用 tmux 執行 Discord Bot

- 做了什麼：將 `run_bot/README.md` 第四步從 systemd 常駐改為 tmux 常駐，加入安裝 tmux、建立 `discord-bot` session、啟動 bot、離開與回到 session、查看與關閉 session 的基本指令。
- 為什麼：Oracle VM 上的 Discord bot 已可成功執行，使用者希望改用 tmux 直接在背景維持程序，不再使用 systemd。
- 下一步：在 Oracle VM 依照 README 第四步執行，確認 SSH 斷線後 bot 仍持續運作。

### 2026-05-27 18:15 - Discord bot 部署後續確認

- 做了什麼：確認 Oracle VM 上 bot 已可常駐後，整理後續應做事項，包含服務穩定性檢查、部署文件、更新流程、secret 安全、監控、端到端測試與備份復原。
- 做了什麼：檢查 `run_bot/discord_bot.py`、`run_bot/.env.example`、`run_bot/README.md`、`LLM_agent/notion_tools.py`、`LLM_agent/agent_controller.py`。
- 結論：目前 bot 使用 `AgentController(MockNotionTools())`，Discord 可以收訊息與回覆，但 Notion 操作只是在記憶體中模擬，尚未串接真正 Notion API。
- 結論：`.env.example` 目前只有 `DISCORD_TOKEN`，尚未設定 `NOTION_TOKEN`、`NOTION_DATABASE_ID` 等 Notion 串接參數。
- 驗證：嘗試用 `python -m py_compile` 檢查相關 Python 檔案，但本機 `python.exe` 無法被系統存取，因此沒有取得本機編譯結果。
- 下一步：建立 Notion integration、分享目標 database、加入 Notion 環境變數、實作真正的 Notion tools、將 `discord_bot.py` 從 `MockNotionTools` 改成真實工具，最後重新部署並重啟 VM 上的 bot。

### 2026-05-27 18:15 - Notion API 測試與 venv 排查

- 使用者問題：`run_bot/testNotion.py` 已設定 `run_bot/.env` 的 `NOTION_TOKEN` 與 `NOTION_DATABASE_ID`，但測試 Notion database 時失敗。
- 處理內容：確認原始程式沒有載入 `.env`，因此加入 `python-dotenv` 的 `load_dotenv(ROOT_DIR / "run_bot" / ".env")`，並補上 `NOTION_TOKEN` / `NOTION_DATABASE_ID` 缺漏檢查。
- 處理內容：排查 `.venv` 被刪除但 shell 仍處於已 activate 狀態的問題，建議關閉 terminal 或先 `deactivate` / `hash -r`，再重新建立 `.venv`。
- 處理內容：確認 Notion API 已成功取回 database title，但新版 Notion API 的欄位 schema 不在 `db["properties"]`，而是在 database 的 first `data_sources` 對應 object 中。
- 修改結果：更新 `run_bot/testNotion.py`，若 `databases.retrieve()` 沒有 `properties`，會改用 `notion.data_sources.retrieve(data_source_id=...)` 取得欄位 schema，再列出欄位名稱與型別。
- 後續事項：若要讓 Discord bot 實際操作 Notion，需要把 `discord_bot.py` 從 `MockNotionTools` 接到真正的 Notion tools，並確認 Notion integration 已 share 到目標 database。

### 2026-05-27 18:17 - Notion 任務新增測試與 Git 忽略規則

- 做了什麼：新增 `run_bot/notion_task_database_schema.json` 紀錄 Notion task database schema，新增 `LLM_agent/notion_task_creator.py` 建立 Notion page helper，並加入 unit test 與 opt-in integration test。
- 做了什麼：實際執行 Notion integration test，成功新增一筆 `Codex Notion API create test`；另新增根目錄 `.gitignore` 忽略 `.venv/`、`.env`、cache 與 `output.txt`。
- 為什麼：後續 LLM 需要依固定 schema 新增事件，且 `.venv`、secret 與輸出檔不應進入 Git。
- 下一步：將 `.venv` 從 Git index 移除後 commit `.gitignore` 與 Notion helper/test；後續再把 Discord bot 從 `MockNotionTools` 接到真實 Notion helper。

### 2026-05-27 18:18 - 建立 Notion function layer

- 做了什麼：新增 `notion_function/`，實作 Notion client helper、create、update、delete/archive、search by event id、search by start/end、search by date、search by filter 等 functions，並補 README 給後續 LLM/orchestrator 使用。
- 做了什麼：更新 `run_bot/notion_task_database_schema.json`，加入 `開始日`、`優先程度`、`狀態`、完整 `類別` options；實際在 Notion 建立 smoke test events，並驗證新增、修改、刪除/archive 與查詢流程。
- 為什麼：Discord bot 後續要串接 LLM function calling，需要先有穩定、可測試、與 Notion database schema 對齊的 tool layer。
- 下一步：後續實作 LLM orchestrator 時，直接依 `notion_function/README.md` 的 function 介面與 LLM rules 串接工具呼叫。

### 2026-05-28 13:59 - Gemini Notion Discord ???????

- ??????? Gemini Controller + Python Tool Guardrails ?? spec?????? implementation plan?
- ????? Discord bot ??? Gemini function calling ?? Notion CRUD??????????? raw Notion client?
- ????? implementation plan ?? adapter?Gemini controller?Discord controller selection?local tests ? README/env ???

### 2026-05-28 14:15 - Gemini Notion Discord ?????

- ?????? implementation plan ?? Notion function adapter?Gemini function-calling controller?Discord controller selection?`google-genai` dependency ? production `.env` ?????? focused/full unittest?
- ????? Discord bot ? `GEMINI_API_KEY` ????? Gemini + Notion guarded tools????? mock controller fallback?
- ????? VM ? `run_bot/.env` ?? `GEMINI_API_KEY`?`NOTION_TOKEN`?`NOTION_DATA_SOURCE_ID`???? Discord/Notion smoke test?

### 2026-05-28 15:27 - 修正 Notion 欄位錯碼

- 做了什麼：將 `notion_function/tools.py` 的 Notion property constants 改回 schema 對應的 `待辦事項`、`開始日`、`截止日`、`類別`、`優先程度`、`狀態`、`備註`，並新增 regression test 確認欄位名稱不再錯碼。
- 為什麼：Gemini 已能呼叫 tools，但 Python 端送到 Notion API 的欄位名稱是錯碼，導致查詢與新增都被 Notion ValidationError 拒絕。
- 下一步：將修正同步到 VM，旋轉已外洩的 Notion token，重啟 bot 後用 Discord 測試查詢與新增行程。

### 2026-05-28 16:30 - Gemini 錯誤處理與 Notion draft store

- 做了什麼：在 `LLM_agent/gemini_controller.py` 加入 Gemini 429 固定回覆與 `GEMINI_SYSTEM_PROMPT`；在 `notion_function/adapter.py` 接上 adapter 層的全域 JSON draft store，新增 `notion_function/task_draft_store.py` 與 `run_bot/task_draft.json` 模板，標明必填與可不填欄位。
- 為什麼：避免 Gemini quota/rate-limit 時把底層錯誤直接丟給 Discord 使用者，並在新增 Notion task 前後留下可檢查的結構化暫存資料；成功新增後清空 draft，失敗時保留 draft 方便追查。
- 下一步：視實際使用狀況調整 `GEMINI_MODEL`、`GEMINI_SYSTEM_PROMPT`，並評估是否讓 draft store 支援補欄位或更長期的對話摘要。

### 2026-05-29 11:15 - 補齊資料夾 README

- 做了什麼：先前 session 已在主要資料夾補上 `README.md`，說明各資料夾用途、執行方式或後續協作入口。
- 為什麼：讓 `LLM_agent/`、`notion_function/`、`run_bot/` 等模組的責任邊界更清楚，也方便後續從文件理解整個 HW4 專案結構。
- 下一步：若新增資料夾或改變模組責任，需同步更新對應 `README.md`。

### 2026-05-29 11:15 - 調整 plan.md 文件定位

- 做了什麼：小幅修改 `docs/plan.md`，補上本文件是和 Codex 討論用草稿，後續延伸到 Gemini/Discord/Notion design spec，再拆成 implementation plan 的脈絡。
- 為什麼：讓 project 看起來是從初始 HW4 設計草稿，逐步收斂到 `docs/superpowers/specs/2026-05-28-gemini-notion-discord-design.md` 與 `docs/superpowers/plans/2026-05-28-gemini-notion-discord.md`。
- 下一步：後續若 spec 或 implementation plan 再變動，回頭確認 `plan.md` 是否仍能作為合理的前導草稿。

### 2026-05-29 11:15 - 合併最終中文 report

- 做了什麼：將 `docs/infographic.md` 的 Mermaid 架構圖與 workflow 圖、`docs/evaluation_cases.md` 的 metrics 與測試案例，整合進 `docs/report.md`，並將 report 改成中文正式繳交版。
- 為什麼：HW4 要求書面報告、infographic 與 evaluation 方法；合併後的 `report.md` 可作為最終繳交主文件，同時保留個人用 MVP 是 design validation 而非 production product 的定位。
- 下一步：繳交前再次檢查 `docs/report.md` 是否符合 2-5 頁限制，並確認 `docs/log.md` 已涵蓋主要設計迭代。
