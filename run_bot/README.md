# run_bot

Discord Bot 的執行入口與部署設定，用來把 Discord 訊息接到 Gemini/Notion 任務助理。

## 檔案用途

| 檔案 | 用途 |
| --- | --- |
| `discord_bot.py` | Discord bot 主程式 |
| `requirements.txt` | Python 套件清單 |
| `.env.example` | 環境變數範本 |
| `.env` | 本機密鑰與設定，不要 commit |
| `.gitignore` | 忽略 `.env` |
| `notion-discord-bot.service.example` | Linux systemd service 範本 |
| `testNotion.py` | 手動檢查 Notion 連線與資料庫欄位 |
| `notion_task_database_schema.json` | Notion task database schema 參考 |
| `task_draft.json` | 建立 Notion task 時的暫存草稿 |
| `__pycache__/` | Python 執行後產生的快取 |

## 執行模式

`discord_bot.py` 會讀取 `run_bot/.env`：

- 有 `GEMINI_API_KEY`：使用 Gemini + Notion 真實工具。
- 沒有 `GEMINI_API_KEY`：使用本機 mock controller。

Notion 真實模式需要：

```env
NOTION_TOKEN=your_notion_integration_secret
NOTION_DATABASE_ID=your_notion_database_id
NOTION_DATA_SOURCE_ID=your_notion_data_source_id
```

`NOTION_DATA_SOURCE_ID` 可省略；若只提供 `NOTION_DATABASE_ID`，程式會從 database 取得第一個 data source。

## 本機設定

在專案根目錄執行：

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r run_bot\requirements.txt
Copy-Item run_bot\.env.example run_bot\.env
```

編輯 `run_bot\.env`：

```env
DISCORD_TOKEN=your_discord_bot_token
NOTION_TOKEN=your_notion_integration_secret
NOTION_DATABASE_ID=your_notion_database_id
NOTION_DATA_SOURCE_ID=your_notion_data_source_id
GEMINI_API_KEY=your_google_ai_studio_key
GEMINI_MODEL=gemini-3.1-flash-lite
GEMINI_SYSTEM_PROMPT_PATH=../LLM_agent/system_prompt.md
```

必要項目：

- `DISCORD_TOKEN`：啟動 Discord bot 必填。
- `GEMINI_API_KEY`：要使用 Gemini + Notion 真實模式才需要。
- `NOTION_TOKEN` / `NOTION_DATABASE_ID`：要連 Notion 才需要。

## 啟動 Bot

```powershell
.\.venv\Scripts\activate
python run_bot\discord_bot.py
```

在 server 內要 mention bot 才會回應；DM 可直接傳訊息。

## 檢查 Notion

```powershell
.\.venv\Scripts\activate
python run_bot\testNotion.py
```

這只會檢查 Notion token/database 是否可讀，不會啟動 Discord bot。

## Linux VM 部署

以下假設專案在 `/home/ubuntu/Personal_Tasks_Management`：

```bash
sudo apt update
sudo apt install -y python3 python3-venv git
git clone <repo-url> /home/ubuntu/Personal_Tasks_Management
cd /home/ubuntu/Personal_Tasks_Management
python3 -m venv .venv
source .venv/bin/activate
pip install -r run_bot/requirements.txt
cp run_bot/.env.example run_bot/.env
nano run_bot/.env
```

手動測試：

```bash
python run_bot/discord_bot.py
```

### 做法 1：systemd

適合正式部署，VM 開機後會自動啟動 bot。

安裝 systemd service：

```bash
sudo cp run_bot/notion-discord-bot.service.example /etc/systemd/system/notion-discord-bot.service
sudo systemctl daemon-reload
sudo systemctl enable notion-discord-bot
sudo systemctl start notion-discord-bot
```

如果 service 無法正常啟用，檢查 `/etc/systemd/system/notion-discord-bot.service`。

常用指令：

```bash
sudo systemctl status notion-discord-bot
journalctl -u notion-discord-bot -f
sudo systemctl restart notion-discord-bot
sudo systemctl stop notion-discord-bot
```

### 做法 2：tmux

適合臨時測試或手動維護；VM 重開機後不會自動恢復 bot。

安裝 tmux：

```bash
sudo apt install -y tmux
```

建立 session：

```bash
cd /home/ubuntu/Personal_Tasks_Management
tmux new -s discord-bot
```

在 tmux 內啟動 bot：

```bash
source .venv/bin/activate
python run_bot/discord_bot.py
```

常用指令：

```text
# 離開 tmux，但讓 bot 繼續執行
Ctrl+b，放開後按 d

# 回到 bot session
tmux attach -t discord-bot

# 查看 session
tmux ls

# 停止 bot：回到 session 後按 Ctrl+C

# 關閉 session
tmux kill-session -t discord-bot
```

## Discord Bot 設定

1. 到 Discord Developer Portal 建立 Application。
2. 建立 Bot，複製 token 到 `DISCORD_TOKEN`。
3. 啟用 `Message Content Intent`。
4. OAuth2 URL Generator 選：
   - Scopes: `bot`
   - Bot Permissions: `View Channels`, `Send Messages`, `Read Message History`
5. 用產生的 URL 邀請 bot 進 server。

## 注意事項

- Discord bot 主動連 Discord Gateway，VM 通常不需要開 inbound port。
- 不要 commit `run_bot/.env`。
- Notion database 欄位改變時，記得更新 `notion_task_database_schema.json`。
- 建立 task 失敗時，可查看 `task_draft.json` 的 `draft` 欄位。
