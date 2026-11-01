# Campus Library Assistant

A small EECE 503P assignment demonstrating exactly three MCP tools. A fictional six-book catalog supports searching and one-copy reservations. The OpenAI Agents SDK selects tools from a local FastMCP server.

## Setup

Requires uv and Python 3.12 or later. The repository records Python 3.12 and dependency versions in `.python-version` and `uv.lock`.

```bash
git clone https://github.com/ajkanaan/campus-library-assistant-mini-project.git
cd campus-library-assistant-mini-project
uv sync --locked
cp .env.example .env
```

Edit `.env` locally and set `OPENAI_API_KEY`. Optional `OPENAI_MODEL` selects a model accessible to that key; leave it empty for the installed SDK default. Model requests use the OpenAI API. No key is needed for offline tests or direct MCP checks.

```bash
uv run python client.py
```

The client launches the server automatically. Type `exit` or `quit` to stop. EOF and Ctrl+C also exit. The server's STDIO channel carries protocol messages; diagnostics belong on stderr. Client logs show tool calls, arguments, and results as they happen. SDK tracing is disabled for this small demo; terminal logs provide the visible execution record.

## Three tools

| Category | Tool | Responsibility |
| --- | --- | --- |
| Data | `search_books(query: str) -> dict` | Case-insensitive title/author lookup with current availability. Does not change files. |
| Action | `reserve_book(book_id: str, student_id: str) -> dict` | Validate and save one reservation. |
| Orchestration | `find_and_reserve_book(query: str, student_id: str) -> dict` | Search, choose only a single available match, then call the reservation function. |

Each result contains `success` and `message`. Search also returns `books`; a successful reservation returns `reservation`; ambiguous orchestration returns `choices` without saving. Empty input, unknown IDs, unavailable books, duplicate reservations, and ambiguous/no-match orchestration produce clear results. These are application-level failures (`success: false`), rather than transport errors. Docstrings describe tool inputs, outputs, and write effects.

`library.py` holds ordinary functions. `server.py` exposes three thin wrappers with `@mcp.tool`; internal helpers are not exposed. The orchestration wrapper calls the ordinary orchestration function, which reuses search and reservation logic. Those internal calls do not need another MCP round trip. No separate resource is exposed: the required lookup is a Data tool.

## Data and persistence

The catalog is committed at `data/catalog.json`. Reservations are ignored by Git. On a fresh checkout, a missing reservations file means an empty list; the first successful reservation creates it. Search never creates it. A reservation makes that book unavailable without modifying the catalog. Student IDs are demo identifiers, not authenticated accounts.

The demo assumes sequential operations and one copy per book. The client disables parallel tool calls. Multiple clients/processes writing the same JSON file are outside this assignment's scope. A missing/corrupt catalog or malformed JSON is an operational error; preserve the file and fix it rather than treating it as an empty library.

For a fresh demo only, reset local reservations explicitly:

```bash
uv run python -c "from pathlib import Path; Path('data/reservations.json').write_text('[]\n', encoding='utf-8')"
```

Tests and `live_check.py` use temporary files via `LIBRARY_RESERVATIONS_PATH`, so your existing reservations are not changed.

## Verify

```bash
uv run pytest -q
uv run python check_server.py
uv run python live_check.py
```

- pytest covers library rules, actual SDK-to-STDIO calls, persistence after server restart, and the conversation loop using a scripted model. Scripted results are **not real-model evidence**.
- `check_server.py` discovers exactly three tools and calls search without a model.
- `live_check.py` requires the API key, uses the real configured model, and verifies search, a follow-up reservation using conversation history, orchestration, and duplicate rejection. It writes `docs/live_verification.json` only after passing. Missing credentials exit with code 2; failed assertions or API requests are not a pass.

A failed API turn can occur after a reservation was saved. The client stops rather than replaying the turn automatically; inspect the reservations file before retrying.

## Assignment materials

- [Part 1 summary](docs/summary.md): 300–400 words, with article and server references.
- [Reflection](docs/reflection.md): tool boundaries and possible next steps.
- [Recorded demonstration](docs/demo.mp4): compressed MP4 with audio.

The demonstration is included in the repository. The original high-resolution MOV is retained locally and excluded from Git.
