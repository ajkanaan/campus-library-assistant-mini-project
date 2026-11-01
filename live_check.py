"""Real-model acceptance check. Uses temporary reservations, never demo data."""
import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from agents import RunConfig, Runner
from dotenv import load_dotenv

from client import EXPECTED_TOOLS, PROJECT_DIR, ToolLog, build_agent, connect_server


async def verify():
    load_dotenv(PROJECT_DIR / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        print("NOT RUN: add OPENAI_API_KEY to .env, then rerun uv run python live_check.py")
        return 2
    prior_path = os.environ.get("LIBRARY_RESERVATIONS_PATH")
    turns = []
    try:
        with TemporaryDirectory(prefix="library-live-") as directory:
            path = Path(directory) / "reservations.json"
            os.environ["LIBRARY_RESERVATIONS_PATH"] = str(path)
            async with connect_server() as server:
                assert {t.name for t in await server.list_tools()} == EXPECTED_TOOLS
                agent = build_agent(server)
                history = []
                scenarios = [
                    ("Show me all available Python books, listing IDs in ascending order.", "search_books"),
                    ("Reserve the first book you just listed for student S001.", "reserve_book"),
                    ("Find an available Pragmatic Programmer book and reserve it for student S002.", "find_and_reserve_book"),
                    ("Try reserving B002 for student S003; check with the reservation tool even if it was reserved earlier.", "reserve_book"),
                ]
                for prompt, expected in scenarios:
                    print(f"\nYou: {prompt}", flush=True)
                    result = await Runner.run(agent, input=history + [{"role": "user", "content": prompt}], hooks=ToolLog(), run_config=RunConfig(tracing_disabled=True))
                    calls = [item.raw_item.name for item in result.new_items if item.type == "tool_call_item"]
                    assert expected in calls, f"Expected {expected}, got {calls}"
                    turns.append({"prompt": prompt, "tool_calls": calls, "answer": result.final_output})
                    history = result.to_input_list()
                    print(f"Assistant: {result.final_output}", flush=True)
                    saved = json.loads(path.read_text()) if path.exists() else []
                    if expected == "search_books":
                        assert saved == []
                    elif len(turns) == 2:
                        assert saved == [{"book_id": "B002", "student_id": "S001"}]
                    else:
                        assert saved == [{"book_id": "B002", "student_id": "S001"}, {"book_id": "B006", "student_id": "S002"}]
                report = {
                    "status": "passed",
                    "evidence": "real OpenAI model through Agents SDK and STDIO MCP",
                    "verified_at_utc": datetime.now(timezone.utc).isoformat(),
                    "model_configuration": os.getenv("OPENAI_MODEL") or "installed SDK default",
                    "turns": turns,
                    "temporary_reservations": saved,
                }
    finally:
        if prior_path is None:
            os.environ.pop("LIBRARY_RESERVATIONS_PATH", None)
        else:
            os.environ["LIBRARY_RESERVATIONS_PATH"] = prior_path
    destination = PROJECT_DIR / "docs" / "live_verification.json"
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("PASS: all three tool categories, follow-up history, persistence, and duplicate rejection.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(verify()))
