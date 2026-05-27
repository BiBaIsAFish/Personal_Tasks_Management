from __future__ import annotations

from .agent_controller import AgentController
from .notion_tools import MockNotionTools


def main() -> None:
    tools = MockNotionTools()
    agent = AgentController(tools)
    print("Notion scheduler mock agent. Type 'exit' to quit.")
    while True:
        text = input("> ").strip()
        if text.lower() in {"exit", "quit"}:
            break
        response = agent.handle_message(text)
        print(response.message)
        print("tool_calls:", " -> ".join(call["name"] for call in response.tool_calls))


if __name__ == "__main__":
    main()
