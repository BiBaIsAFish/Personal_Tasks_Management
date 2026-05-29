# Notion 智慧排程代理（Notion Smart Scheduler）作業計畫

## 可行性結論

此題目可行，且符合 HW4 對 AI Harness 的要求：LLM 可作為 system controller，透過 function calling 呼叫 Notion 工具，並以短期記憶與多步驟 workflow 完成排程任務。

需要調整的是範圍：本作業評分重點是「系統設計、工具編排、workflow、evaluation、infographic、log」，不是完成可上線產品。因此本計畫以可交付的設計文件與單人私有 Discord Bot 原型為主，避免把時間花在多人部署、權限管理與長期維運等低評分比重但高風險的工程細節。

本文件先作為和 Codex 討論方向的草稿：先確定 Notion 智慧排程代理的作業範圍、工具邊界與評估方式。後續若要往可執行原型推進，會再把這裡的概念整理成更明確的設計規格。

## 題目定位

**應用場景：** 個人或團隊的智慧排程助理。

**核心問題：** 使用者用自然語言提出排程需求時，系統需要理解時間、查詢既有行程、判斷衝突，並在合適時建立或更新 Notion 行程。

**AI Harness 重點：**

- LLM 負責理解需求、決策下一步與產生回覆。
- Tools 負責取得時間、查詢 Notion、建立或更新行程。
- Memory 負責保存短期對話狀態與待確認資訊。
- Orchestration loop 負責控制 tool calling、衝突判斷與使用者確認。

## 建議系統架構

```text
User
  ↓
Private Discord Server
  ↓
Discord Bot
  ↓
Agent Controller / Orchestrator
  ├── Short-term Memory
  ├── System Prompt
  ├── Function Calling Schema
  ↓
LLM
  ↓ tool_calls
Tool Layer
  ├── get_current_time()
  ├── parse_time_range(text, reference_time)
  ├── query_notion_schedule(start_time, end_time)
  ├── create_notion_task(title, start_time, end_time, tags)
  └── update_notion_task(task_id, new_start_time, new_end_time)
  ↓
Notion Database
```

## 工具設計

至少在報告中完整描述前三個工具；第四、第五個可作為進階設計。

### Tool 1: `get_current_time()`

**目的：** 取得台灣時區目前時間，作為「今天、明天、下週三」等相對時間的基準。

**Input：** 無。

**Output：**

```json
{
  "timezone": "Asia/Taipei",
  "current_time": "2026-05-27T11:30:00+08:00"
}
```

### Tool 2: `parse_time_range(text, reference_time)`

**目的：** 將自然語言時間轉成明確起訖時間，例如「明天下午三點到四點」。

**Input：**

```json
{
  "text": "明天下午三點到四點",
  "reference_time": "2026-05-27T11:30:00+08:00"
}
```

**Output：**

```json
{
  "start_time": "2026-05-28T15:00:00+08:00",
  "end_time": "2026-05-28T16:00:00+08:00",
  "confidence": 0.93
}
```

### Tool 3: `query_notion_schedule(start_time, end_time)`

**目的：** 查詢 Notion database 中指定時間區間的既有行程。

**Input：**

```json
{
  "start_time": "2026-05-28T15:00:00+08:00",
  "end_time": "2026-05-28T16:00:00+08:00"
}
```

**Output：**

```json
{
  "conflicts": [
    {
      "task_id": "abc123",
      "title": "Project Meeting",
      "start_time": "2026-05-28T15:30:00+08:00",
      "end_time": "2026-05-28T16:30:00+08:00"
    }
  ]
}
```

### Tool 4: `create_notion_task(title, start_time, end_time, tags)`

**目的：** 在確認無衝突或使用者同意後，建立新的 Notion 行程。

### Tool 5: `update_notion_task(task_id, new_start_time, new_end_time)`

**目的：** 修改既有行程，支援重新排程。

## Workflow / Orchestration 設計

新增行程的標準流程：

1. 使用者輸入自然語言需求，例如「幫我排明天下午三點和同學討論報告」。
2. Agent 將訊息加入 short-term memory。
3. LLM 判斷需要時間基準，呼叫 `get_current_time()`。
4. LLM 呼叫 `parse_time_range()`，取得明確起訖時間。
5. LLM 呼叫 `query_notion_schedule()`，檢查該時段是否有衝突。
6. 若無衝突，呼叫 `create_notion_task()`。
7. 若有衝突，Agent 先回覆使用者並要求確認，不直接覆蓋既有行程。
8. 使用者確認後，Agent 才呼叫 `create_notion_task()` 或 `update_notion_task()`。
9. Agent 回傳最終結果，並將任務狀態寫入 memory。

關鍵控制原則：

- 不可在未解析明確時間前建立行程。
- 不可在未查詢既有行程前建立行程。
- 發現衝突時必須詢問使用者。
- Tool 回傳錯誤時，LLM 應解釋原因並要求補充資訊。

## Evaluation 方法

本作業建議用小型測試集評估，不需要大量實驗。

| 評估面向 | 測試方式 | 指標 |
| --- | --- | --- |
| 時間解析正確性 | 輸入 10 筆自然語言時間 | 正確起訖時間比例 |
| 衝突偵測能力 | 建立 5 筆重疊與不重疊案例 | 是否正確阻擋衝突 |
| Tool calling 順序 | 檢查 log 中的 function calls | 是否符合 workflow |
| 使用者確認機制 | 測試衝突情境 | 是否先詢問再執行 |
| 回覆可理解性 | 人工檢查最終回覆 | 是否清楚說明結果 |

建議測試案例：

- 「明天下午三點開會一小時」
- 「下週三早上和老師討論」
- 「今天晚上七點到八點健身」
- 「幫我把下午的會議改到四點」
- 「明天三點排一個新行程」且 Notion 已有重疊事件

## 交付物工作分配

### 1. 書面報告（2-5 頁）

建議章節：

1. Problem Definition and Use Scenario
2. AI Harness Architecture
3. Tool / Function Calling Design
4. Agent Workflow and Orchestration
5. Evaluation Design and Expected Results
6. Limitations and Future Improvements

### 2. Infographic

建議畫一張圖即可，包含：

- User / Discord Bot or CLI
- Agent Controller
- LLM
- Memory
- Tool Layer
- Notion Database
- function calling sequence

可用 sequence diagram 或 pipeline diagram。重點是清楚呈現 LLM 如何決定呼叫工具，以及 tool result 如何回到 Agent。

### 3. `log.md`

需記錄：

- 最初題目選擇與原因。
- 和 LLM 討論出的架構版本。
- 為何將範圍從完整 Discord Bot 調整為設計優先、原型輔助。
- 工具設計的取捨。
- workflow 如何因衝突偵測需求而加入使用者確認步驟。
- evaluation 指標如何對應評分標準。

## 實作建議

本專案可實作單人使用的 Discord Bot 原型：使用者在自己的私人 Discord server 中邀請 bot，所有訊息都視為同一位使用者的個人排程需求。

原始草稿可先用 mock controller 驗證 workflow；若後續要接近實際可用版本，則可把本文件的架構延伸成三層：Discord adapter、LLM/Gemini controller、Notion function layer。這個方向已可對應到後續 design spec 與 implementation plan。

建議 prototype 檔案可從下列概念開始，實作時再對應到 repo 內實際資料夾：

```text
LLM_agent/
├── agent_controller.py        # mock / test-friendly orchestration
└── gemini_controller.py       # production function-calling controller
run_bot/
├── discord_bot.py             # Discord adapter
└── README.md
notion_function/
├── tools.py                   # Notion CRUD/search helpers
└── adapter.py                 # guarded tool facade for LLM calls
docs/
├── report.md
├── infographic.md
├── evaluation_cases.md
└── log.md
```

最低可行原型：

- Discord Bot 只需支援單一使用者、單一 server，不處理多人權限與資料隔離。
- Bot 接收文字訊息後呼叫 agent controller，並將最終結果回覆到同一個 channel。
- Notion API 可用 mock data 取代，但報告需說明實際 Notion API 對應方式。
- 必須保留 function calling schema、tool result、orchestration loop 的設計說明。

## 執行順序

1. 完成 report.md 大綱，先確保所有作業要求都有對應段落。
2. 定義工具 schema 與 workflow，將其放入報告與 infographic。
3. 建立 5-10 筆 evaluation cases。
4. 實作單人私有 Discord Bot MVP，必要時先用 mock Notion data 驗證 workflow。
5. 整理 `log.md`，補上設計迭代紀錄。
6. 最後檢查交付物是否覆蓋評分項目。

## 風險與修正

- **風險：Discord Bot 與 Notion API 設定耗時。** 修正：限定為單人私有 server MVP，只處理一位使用者與固定 Notion database schema。
- **風險：多人使用造成 memory 與權限複雜度。** 修正：本作業不支援多人情境，memory 可先用單一 user/session 狀態保存。
- **風險：工具太少或描述太抽象。** 修正：至少完整描述 3 個 tool 的 input/output、使用時機與錯誤處理。
- **風險：workflow 只有線性流程，缺少 decision-making。** 修正：加入衝突檢查、使用者確認、錯誤回復與 retry。
- **風險：evaluation 太空泛。** 修正：用具體測試案例與可量化指標呈現。
- **風險：log.md 事後補寫太薄。** 修正：每次架構調整都記錄原因、替代方案與最後決策。
