# Notion 智慧排程代理：AI Harness 系統設計報告

## 1. Problem Definition and Use Scenario

本設計的應用場景是個人智慧排程助理。使用者可以用自然語言提出排程需求，例如「幫我排明天下午三點和同學討論報告」或「把下午的會議改到四點」。系統需要理解時間、查詢既有行程、判斷是否衝突，並在合適時建立或更新 Notion 行程。

此問題適合用 AI Harness 處理，因為單靠 LLM 不能直接信任其內部推測結果。排程任務需要外部工具提供目前時間、結構化時間解析、Notion database 查詢與寫入能力。因此 LLM 的角色不是資料來源，而是 workflow controller：負責判斷何時呼叫工具、如何解讀 tool result，以及是否需要向使用者確認。

本作業的範圍設定為單人私有 Discord Bot 原型。Discord Bot 作為使用者入口，Agent Controller 管理對話狀態與工具呼叫，Notion API 在原型中可先用 mock database 模擬。這樣能保留 AI Harness 的核心設計，同時避免多人權限、資料隔離與正式部署造成範圍過大。

## 2. AI Harness Architecture

系統由六個主要元件組成：

| 元件 | 職責 |
| --- | --- |
| User / Discord Bot | 接收自然語言排程需求，回傳最終結果 |
| Agent Controller | 管理 orchestration loop、memory、tool result 與使用者確認 |
| LLM | 判斷使用者意圖、決定下一個工具呼叫、產生自然語言回覆 |
| Short-term Memory | 保存最近對話、待確認行程、使用者意圖與工具結果 |
| Tool Layer | 封裝時間、Notion 查詢、Notion 寫入等可執行功能 |
| Notion Database | 儲存行程資料，包含標題、起訖時間、標籤與狀態 |

資料流如下：使用者訊息先進入 Discord Bot，再傳給 Agent Controller。Controller 將訊息與 memory 組合後交給 LLM。LLM 若需要外部資訊，會輸出 function call。Controller 執行對應工具，將 tool result 回傳給 LLM。LLM 根據結果決定是否繼續呼叫工具、要求使用者確認，或產生最終回覆。

此架構的重點是分離「推理」與「執行」。LLM 負責選擇流程，但不能直接修改 Notion；所有實際動作都必須透過明確定義的工具完成。

## 3. Tool / Function Calling Design

### Tool 1: `get_current_time()`

用途是取得台灣時區目前時間，作為「今天、明天、下週三」等相對時間的解析基準。

```json
{
  "name": "get_current_time",
  "input": {},
  "output": {
    "timezone": "Asia/Taipei",
    "current_time": "2026-05-27T11:30:00+08:00"
  }
}
```

錯誤處理：若系統時間不可用，Controller 應回覆使用者目前無法解析相對時間，並要求提供明確日期與時間。

### Tool 2: `parse_time_range(text, reference_time)`

用途是將自然語言時間轉成明確起訖時間。

```json
{
  "name": "parse_time_range",
  "input": {
    "text": "明天下午三點到四點",
    "reference_time": "2026-05-27T11:30:00+08:00"
  },
  "output": {
    "start_time": "2026-05-28T15:00:00+08:00",
    "end_time": "2026-05-28T16:00:00+08:00",
    "confidence": 0.93
  }
}
```

錯誤處理：若 confidence 低於門檻，例如 0.7，Agent 不應建立行程，而應詢問使用者補充日期、時間或持續時間。

### Tool 3: `query_notion_schedule(start_time, end_time)`

用途是查詢指定時間區間是否已有重疊行程。

```json
{
  "name": "query_notion_schedule",
  "input": {
    "start_time": "2026-05-28T15:00:00+08:00",
    "end_time": "2026-05-28T16:00:00+08:00"
  },
  "output": {
    "conflicts": [
      {
        "task_id": "abc123",
        "title": "Project Meeting",
        "start_time": "2026-05-28T15:30:00+08:00",
        "end_time": "2026-05-28T16:30:00+08:00"
      }
    ]
  }
}
```

錯誤處理：若 Notion 查詢失敗，Agent 不應假設無衝突，也不應建立行程。正確做法是回覆查詢失敗並要求稍後重試。

### Tool 4: `create_notion_task(title, start_time, end_time, tags)`

用途是在無衝突，或使用者明確同意後建立新行程。

```json
{
  "name": "create_notion_task",
  "input": {
    "title": "討論報告",
    "start_time": "2026-05-28T15:00:00+08:00",
    "end_time": "2026-05-28T16:00:00+08:00",
    "tags": ["school"]
  },
  "output": {
    "task_id": "new456",
    "status": "created"
  }
}
```

### Tool 5: `update_notion_task(task_id, new_start_time, new_end_time)`

用途是重新安排既有行程，例如「把下午的會議改到四點」。

```json
{
  "name": "update_notion_task",
  "input": {
    "task_id": "abc123",
    "new_start_time": "2026-05-28T16:00:00+08:00",
    "new_end_time": "2026-05-28T17:00:00+08:00"
  },
  "output": {
    "task_id": "abc123",
    "status": "updated"
  }
}
```

## 4. Agent Workflow and Orchestration

新增行程的標準流程如下：

1. 使用者輸入自然語言需求。
2. Agent Controller 將訊息寫入 short-term memory。
3. LLM 判斷需要時間基準，呼叫 `get_current_time()`。
4. LLM 呼叫 `parse_time_range()`，取得明確起訖時間。
5. LLM 呼叫 `query_notion_schedule()`，檢查是否有衝突。
6. 若無衝突，呼叫 `create_notion_task()`。
7. 若有衝突，Agent 回覆衝突資訊並要求使用者確認。
8. 使用者確認後，Agent 才建立新行程或更新既有行程。
9. Agent 回傳最終結果，並將狀態寫入 memory。

此 workflow 有四個控制原則。第一，不可在時間未解析清楚前建立行程。第二，不可在未查詢既有行程前建立行程。第三，發現衝突時必須詢問使用者，不能直接覆蓋或新增。第四，工具失敗時要停止流程並說明原因。

這些原則讓 LLM 的決策可被追蹤，也讓系統避免典型錯誤，例如幻覺時間、跳過衝突檢查、或在使用者未確認時修改資料。

## 5. Evaluation Design and Expected Results

本系統使用小型測試集評估，不需要大量實驗。評估重點對應作業要求中的 tool use、workflow 與 orchestration。

| 評估面向 | 測試方式 | 成功標準 |
| --- | --- | --- |
| 時間解析正確性 | 輸入 10 筆自然語言時間 | 起訖時間符合預期，正確率至少 80% |
| 衝突偵測能力 | 建立重疊與不重疊 mock 行程 | 所有重疊案例都被阻擋 |
| Tool calling 順序 | 檢查 execution log | 必須依序呼叫 time、parse、query、create/update |
| 使用者確認機制 | 測試衝突情境 | 有衝突時不得直接寫入 Notion |
| 回覆可理解性 | 人工檢查最終回覆 | 回覆需包含時間、動作結果與下一步 |

預期結果是：簡單排程能自動建立；模糊時間會要求補充；衝突排程會先列出衝突事件並等待確認；工具錯誤會停止流程並回報原因。

## 6. Limitations and Future Improvements

本設計的限制是原型以單一使用者與 mock Notion database 為主，尚未處理正式 Notion OAuth、多人權限、跨時區協作與長期記憶。自然語言時間解析也可能受語句模糊度影響，例如「下午晚一點」或「下次開會前」需要更多上下文。

未來可改進方向包括：接入正式 Notion API、支援多使用者 session 隔離、加入行程偏好記憶、使用 LangGraph 管理狀態機、加入 retry 與 observability，以及把 evaluation cases 自動化成 regression tests。
