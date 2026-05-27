# Evaluation Cases

## Metrics

| Metric | Target |
| --- | --- |
| Time parsing accuracy | At least 8 / 10 natural language cases correct |
| Conflict detection | 5 / 5 overlap cases handled correctly |
| Tool calling order | 100% follows required order |
| Confirmation behavior | 100% asks before writing when conflict exists |
| Response clarity | Final response includes action, time, and result |

## Test Cases

| ID | User input | Mock database state | Expected tool flow | Expected result |
| --- | --- | --- | --- | --- |
| E01 | 明天下午三點開會一小時 | No event at target time | get_current_time -> parse_time_range -> query_notion_schedule -> create_notion_task | Create event for tomorrow 15:00-16:00 |
| E02 | 今天晚上七點到八點健身 | No event at target time | get_current_time -> parse_time_range -> query_notion_schedule -> create_notion_task | Create event for today 19:00-20:00 |
| E03 | 下週三早上和老師討論 | No event at target time | get_current_time -> parse_time_range -> query_notion_schedule -> create_notion_task | Create event with default one-hour duration |
| E04 | 明天三點排一個新行程 | Existing event 15:30-16:30 | get_current_time -> parse_time_range -> query_notion_schedule | Ask user to confirm because of conflict |
| E05 | 把下午的會議改到四點 | Existing meeting found | get_current_time -> parse_time_range -> query_notion_schedule -> update_notion_task | Update meeting after target time is conflict-free |
| E06 | 週末找時間讀書 | Ambiguous time | get_current_time -> parse_time_range | Ask user to provide specific date and time |
| E07 | 明天三點到兩點討論 | Invalid range | get_current_time -> parse_time_range | Reject invalid time range and ask for correction |
| E08 | 下週五 10:00 demo | Notion query failure | get_current_time -> parse_time_range -> query_notion_schedule | Stop and report schedule query failure |
| E09 | 明天 15:00 和同學討論報告 #school | No event at target time | get_current_time -> parse_time_range -> query_notion_schedule -> create_notion_task | Create event with school tag |
| E10 | 剛剛那個衝突還是幫我加上去 | Pending conflict stored in memory | create_notion_task | Create event only because user confirmed pending action |

## Expected Log Evidence

Each evaluation run should record:

- User input.
- Tool calls in order.
- Tool inputs and outputs.
- Decision point, especially conflict or ambiguity.
- Final user-facing response.
