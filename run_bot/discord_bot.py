from __future__ import annotations

import os
import sys
from pathlib import Path

import discord
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from LLM_agent.agent_controller import AgentController  # noqa: E402
from LLM_agent.gemini_controller import GeminiAgentController  # noqa: E402
from notion_function import create_notion_client_from_env  # noqa: E402
from notion_function.adapter import NotionFunctionAdapter  # noqa: E402
from LLM_agent.notion_tools import MockNotionTools  # noqa: E402


load_dotenv(ROOT_DIR / "run_bot" / ".env")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


def build_agent():
    if os.environ.get("GEMINI_API_KEY"):
        notion, data_source_id = create_notion_client_from_env(ROOT_DIR / "run_bot" / ".env")
        adapter = NotionFunctionAdapter(notion, data_source_id)
        return GeminiAgentController.from_env(adapter)
    return AgentController(MockNotionTools())


agent = build_agent()


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
        await message.channel.send("請輸入要我處理的內容。")
        return

    response = agent.handle_message(text)
    await message.channel.send(response.message)


def main() -> None:
    token = os.environ["DISCORD_TOKEN"]
    client.run(token)


if __name__ == "__main__":
    main()
