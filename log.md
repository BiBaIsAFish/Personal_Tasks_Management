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

- 做了什麼：新增 `report.md`、`infographic.md`、`evaluation_cases.md`，並建立 `notion_agent_bot/` mock prototype 與 `tests/test_agent_controller.py`。
- 為什麼：依照 `plan.md` 的執行順序，先覆蓋報告、圖表、evaluation，再用 mock tools 展示 function calling 與 orchestration。
- 下一步：若環境安裝可用 Python runner，可執行 `python -m unittest discover -s tests` 驗證 prototype；目前本機 `python`/`py` 無法執行。
