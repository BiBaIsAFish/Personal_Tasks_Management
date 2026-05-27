# Discord Bot 執行與 Oracle VM 部署

這個資料夾放 Discord bot 執行所需檔案：

- `discord_bot.py`: Discord 訊息 adapter，會呼叫 `notion_agent_bot.AgentController`
- `requirements.txt`: Python 依賴
- `.env.example`: 環境變數範例
- `notion-discord-bot.service.example`: Oracle VM 上的 systemd 範本

## 1. 建立 Discord Bot

1. 到 Discord Developer Portal 建立 Application。
2. 到 `Bot` 頁面建立 bot，複製 token。
3. 在 `Bot` 頁面啟用 `Message Content Intent`。
4. 到 `OAuth2 > URL Generator`：
   - Scopes: `bot`
   - Bot Permissions: `View Channels`, `Send Messages`, `Read Message History`
5. 用產生的 URL 邀請 bot 進 Discord server。

## 2. 本機測試

在專案根目錄執行：

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r run_bot\requirements.txt
cp run_bot\.env.example run_bot\.env
```

編輯 `run_bot\.env`：

```env
DISCORD_TOKEN=你的_discord_bot_token
```

啟動 bot：

```powershell
python run_bot\discord_bot.py
```

在 Discord server 裡提到 bot，例如：

```text
@你的bot 明天下午三點開會一小時
```

或直接傳 DM 給 bot。

## 3. Oracle VM 部署

以下以 Ubuntu VM、專案放在 `/home/ubuntu/hw4` 為例：

```bash
sudo apt update
sudo apt install -y python3 python3-venv git
git clone <你的 repo url> /home/ubuntu/hw4
cd /home/ubuntu/hw4
python3 -m venv .venv
source .venv/bin/activate
pip install -r run_bot/requirements.txt
cp run_bot/.env.example run_bot/.env
nano run_bot/.env
```

`run_bot/.env` 內容：

```env
DISCORD_TOKEN=你的_discord_bot_token
```

先手動確認可以啟動：

```bash
python run_bot/discord_bot.py
```

## 4. 用 tmux 常駐

安裝 tmux：

```bash
sudo apt install -y tmux
```

建立 tmux session：

```bash
cd /home/ubuntu/hw4
tmux new -s discord-bot
```

進入 tmux 後啟動 bot：

```bash
source .venv/bin/activate
python run_bot/discord_bot.py
```

常用快捷鍵與指令：

```text
# 離開 tmux，但讓 bot 繼續執行
Ctrl+b，放開後按 d

# 回到 bot session
tmux attach -t discord-bot

# 查看目前 session
tmux ls

# 停止 bot：回到 session 後按 Ctrl+C

# 關閉 session
tmux kill-session -t discord-bot
```

## 5. 注意事項

- Discord bot 是主動連到 Discord Gateway，通常 Oracle VM 不需要開 inbound port。
- 不要把 `run_bot/.env` commit 到 git。
- 目前 `notion_agent_bot.notion_tools.MockNotionTools` 還是 mock 工具，尚未串接真正 Notion API。
- 若 bot 在 server 內沒有回應，確認訊息有提到 bot，且 Developer Portal 已啟用 `Message Content Intent`。
