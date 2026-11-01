"""Terminal host: model decisions, MCP tool calls, and conversation history."""
import asyncio
import os
import sys
from pathlib import Path

from agents import Agent, ModelSettings, RunConfig, RunHooks, Runner
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
from openai import APIError

PROJECT_DIR = Path(__file__).resolve().parent
EXPECTED_TOOLS = {"search_books", "reserve_book", "find_and_reserve_book"}


class ToolLog(RunHooks):
    """Show tool execution while it happens, for the assignment demonstration."""

    async def on_tool_start(self, context, agent, tool):
        arguments = getattr(context, "tool_arguments", "")
        print(f"\n[MCP call] {tool.name} {arguments}", flush=True)

    async def on_tool_end(self, context, agent, tool, result):
        print(f"[MCP result] {result}", flush=True)


def connect_server():
    """Use this project's interpreter and launch the server as a subprocess."""
    return MCPServerStdio(
        name="Campus Library Server",
        params={
            "command": sys.executable,
            "args": [str(PROJECT_DIR / "server.py")],
            "cwd": str(PROJECT_DIR),
            "env": dict(os.environ),
        },
        cache_tools_list=True,
        client_session_timeout_seconds=30,
    )


def build_agent(server):
    return Agent(
        name="Campus Library Assistant",
        model=os.getenv("OPENAI_MODEL") or None,
        model_settings=ModelSettings(parallel_tool_calls=False),
        instructions=(
            "You help students use a fictional campus library. "
            "Use search_books for searches and current availability. "
            "Use reserve_book for requests to reserve a specific book ID. "
            "Use find_and_reserve_book when asked to find and reserve a book. "
            "Ask for the student ID if it has not been supplied. "
            "When several matches are returned, show the choices and ask which one. "
            "Use conversation history to resolve the user's choice. "
            "Only reserve when requested. Never invent book details or availability, "
            "and only claim success when the tool reports success. "
            "Report failures clearly. Do not retry a failed write automatically. "
            "Keep answers concise."
        ),
        mcp_servers=[server],
    )


async def conversation(agent, read_message=input):
    history = []
    print("Library assistant ready. Type 'exit' to quit.")
    while True:
        try:
            message = read_message("\nYou: ").strip()
        except EOFError:
            break
        if message.casefold() in {"exit", "quit"}:
            break
        if not message:
            continue
        inputs = history + [{"role": "user", "content": message}]
        # A failed turn is not replayed: a tool may already have written data.
        result = await Runner.run(
            agent,
            input=inputs,
            hooks=ToolLog(),
            run_config=RunConfig(tracing_disabled=True),
        )
        print(f"\nAssistant: {result.final_output}", flush=True)
        history = result.to_input_list()


async def main():
    load_dotenv(PROJECT_DIR / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY in .env (see .env.example).", file=sys.stderr)
        return 1
    async with connect_server() as server:
        tools = await server.list_tools()
        names = {tool.name for tool in tools}
        if names != EXPECTED_TOOLS:
            raise RuntimeError(f"Expected exactly {sorted(EXPECTED_TOOLS)}, got {sorted(names)}")
        print("Connected tools:", ", ".join(sorted(names)))
        await conversation(build_agent(server))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nGoodbye.")
    except APIError as error:
        print(f"OpenAI request failed ({type(error).__name__}). Check credentials, model access, quota, and connectivity.", file=sys.stderr)
        print("A reservation may have been saved before the failure. Inspect data/reservations.json before retrying.", file=sys.stderr)
        raise SystemExit(1)
