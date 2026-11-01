# Screencast guide

Record 5–7 minutes using the real agent after setting OPENAI_API_KEY. This is a preparation guide, not a recorded demonstration.

## Before recording

Run `uv run pytest -q` and `uv run python live_check.py`. Use only synthetic student IDs. Keep .env closed. Reset `data/reservations.json` to `[]` if you want a fresh demo; this deletes demo reservations. Open the terminal, server.py, library.py, and data/reservations.json.

## Recording outline

| Time | Show and explain |
| --- | --- |
| 0:00–0:45 | Introduce the fictional library, six-book catalog, and the three tool categories. |
| 0:45–1:30 | Show FastMCP wrappers and SDK connection. Explain host → client → STDIO server → function → result. Explain descriptions and typed inputs. |
| 1:30–2:20 | Run `uv run python client.py`. Ask “Show me available Python books, sorted by ID.” Show discovery and search call/result. |
| 2:20–3:10 | Ask “Reserve the first book you just listed for S001.” Explain preserved history; show the JSON reservation. |
| 3:10–4:00 | Ask “Find an available Pragmatic Programmer book and reserve it for S002.” Show the orchestration tool and explain its internal search/reserve sequence. |
| 4:00–4:45 | Ask “Try reserving B002 for S003; check with the reservation tool.” Show the failure and unchanged stored reservation. |
| 4:45–5:30 | Explain ambiguity: multiple available matches return choices. Show pytest results and distinguish offline tests from the live model. |
| 5:30–6:15 | Discuss single-purpose tools, one-copy/sequential limits, and potential database extension. Show repository URL. |

If the model asks a clarification, answer naturally. Do not claim a tool executed until the execution log confirms it. If the API fails, inspect persistence before retrying.

## Submission

Repository: https://github.com/ajkanaan/campus-library-assistant-mini-project

Include docs/summary.md and docs/reflection.md with the source repository. Record and upload the screencast, then add the real video URL to your submission. A recording link is still outstanding until that upload exists.
