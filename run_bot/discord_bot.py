from __future__ import annotations

import os
import sys
from pathlib import Path

import discord
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from notion_agent_bot.agent_controller import AgentController  # noqa: E402
from notion_agent_bot.notion_tools import MockNotionTools  # noqa: E402


load_dotenv(ROOT_DIR / "run_bot" / ".env")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
agent = AgentController(MockNotionTools())


@client.event
async def on_ready() -> None:
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return

    mentioned = client.user in message.mentions if client.user else False
    if message.guild is not None and not mentioned:
        return

    text = message.content
    if client.user:
        text = text.replace(f"<@{client.user.id}>", "")
        text = text.replace(f"<@!{client.user.id}>", "")
    text = text.strip()

    if not text:
        await message.channel.send("請輸入要新增的行程內容。")
        return

    response = agent.handle_message(text)
    await message.channel.send(response.message)


def main() -> None:
    token = os.environ["DISCORD_TOKEN"]
    client.run(token)


if __name__ == "__main__":
    main()
