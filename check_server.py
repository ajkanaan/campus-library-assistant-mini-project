import asyncio
from pathlib import Path

from fastmcp import Client


async def main():
    server_path = Path(__file__).resolve().parent / "server.py"

    async with Client(server_path) as client:
        tools = await client.list_tools()

        assert {tool.name for tool in tools} == {"search_books", "reserve_book", "find_and_reserve_book"}

        print("Available tools:")
        for tool in tools:
            print(f"- {tool.name}")

        result = await client.call_tool(
            "search_books",
            {"query": "Python"},
        )

        print("\nSearch result:")
        print(result.data)


if __name__ == "__main__":
    asyncio.run(main())
