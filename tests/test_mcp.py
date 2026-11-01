"""Real SDK-to-STDIO-server integration, with no model/network required."""
import asyncio
import json

from client import EXPECTED_TOOLS, connect_server


def data(result):
    assert not result.is_error
    return json.loads(result.content[0].text)


def test_sdk_stdio_round_trip(tmp_path, monkeypatch):
    reservations = tmp_path / "reservations.json"
    monkeypatch.setenv("LIBRARY_RESERVATIONS_PATH", str(reservations))

    async def run():
        async with connect_server() as server:
            tools = await server.list_tools()
            assert {tool.name for tool in tools} == EXPECTED_TOOLS
            assert all(tool.description and tool.input_schema for tool in tools)
            search = data(await server.call_tool("search_books", {"query": "Python"}))
            assert len(search["books"]) == 2
            assert not reservations.exists()
            ambiguous = data(await server.call_tool("find_and_reserve_book", {"query": "Python", "student_id": "S001"}))
            assert len(ambiguous["choices"]) == 2
            assert not reservations.exists()
            action = data(await server.call_tool("reserve_book", {"book_id": "B002", "student_id": "S001"}))
            assert action["success"]
            failure = data(await server.call_tool("reserve_book", {"book_id": "B002", "student_id": "S001"}))
            assert not failure["success"]
            orchestration = data(await server.call_tool("find_and_reserve_book", {"query": "Pragmatic", "student_id": "S002"}))
            assert orchestration["success"]
            stored = json.loads(reservations.read_text())
            assert {r["book_id"] for r in stored} == {"B002", "B006"}
            # Persistence survives restarting the MCP server.
        async with connect_server() as server:
            search = data(await server.call_tool("search_books", {"query": "Pragmatic"}))
            assert not search["books"][0]["available"]

    asyncio.run(run())
