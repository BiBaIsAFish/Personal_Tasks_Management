import os
import sys
import types
import unittest
from unittest.mock import patch

fake_discord = types.ModuleType("discord")


class FakeIntents:
    message_content = False

    @classmethod
    def default(cls):
        return cls()


class FakeClient:
    def __init__(self, *args, **kwargs):
        pass

    def event(self, function):
        return function

    def run(self, token):
        self.token = token


fake_discord.Intents = FakeIntents
fake_discord.Client = FakeClient
fake_discord.Message = object

fake_dotenv = types.ModuleType("dotenv")
fake_dotenv.load_dotenv = lambda *args, **kwargs: None

sys.modules.setdefault("discord", fake_discord)
sys.modules.setdefault("dotenv", fake_dotenv)

import run_bot.discord_bot as discord_bot
from LLM_agent.agent_controller import AgentController


class DiscordBotConfigTest(unittest.TestCase):
    def test_build_agent_uses_mock_without_gemini_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            agent = discord_bot.build_agent()

        self.assertIsInstance(agent, AgentController)

    def test_build_agent_uses_gemini_when_api_key_exists(self):
        class FakeGeminiController:
            @classmethod
            def from_env(cls, adapter):
                instance = cls()
                instance.adapter = adapter
                return instance

        with patch.dict(
            os.environ,
            {
                "GEMINI_API_KEY": "key",
                "NOTION_TOKEN": "notion",
                "NOTION_DATA_SOURCE_ID": "ds_123",
            },
            clear=True,
        ), patch.object(discord_bot, "GeminiAgentController", FakeGeminiController), patch.object(
            discord_bot,
            "create_notion_client_from_env",
            return_value=(object(), "ds_123"),
        ):
            agent = discord_bot.build_agent()

        self.assertIsInstance(agent, FakeGeminiController)
        self.assertEqual(agent.adapter.data_source_id, "ds_123")


if __name__ == "__main__":
    unittest.main()
