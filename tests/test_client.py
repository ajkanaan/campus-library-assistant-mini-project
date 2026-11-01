"""Offline scripted model: tests SDK control flow, not real LLM reasoning."""
import asyncio
import json

from agents import RunConfig, Runner
from agents.models.interface import Model, ModelResponse
from agents.usage import Usage
from openai.types.responses import ResponseFunctionToolCall, ResponseOutputMessage

from client import build_agent, connect_server, conversation


class ScriptedModel(Model):
    def __init__(self):
        self.inputs = []
        self.steps = iter([
            ResponseFunctionToolCall(type="function_call", name="search_books", arguments='{"query":"Python"}', call_id="search_1", id="fc_1"),
            ResponseOutputMessage(type="message", id="msg_1", role="assistant", status="completed", content=[{"type": "output_text", "text": "Choose B002 or B003.", "annotations": []}]),
            ResponseFunctionToolCall(type="function_call", name="reserve_book", arguments='{"book_id":"B002","student_id":"S001"}', call_id="reserve_1", id="fc_2"),
            ResponseOutputMessage(type="message", id="msg_2", role="assistant", status="completed", content=[{"type": "output_text", "text": "B002 reserved for S001.", "annotations": []}]),
        ])

    async def get_response(self, *args, **kwargs):
        self.inputs.append(kwargs.get("input", args[1] if len(args) > 1 else None))
        return ModelResponse(output=[next(self.steps)], usage=Usage(), response_id=None)

    async def stream_response(self, *args, **kwargs):
        raise NotImplementedError("This test uses non-streaming runs.")
        yield


def test_conversation_preserves_tool_history(tmp_path, monkeypatch, capsys):
    path = tmp_path / "reservations.json"
    monkeypatch.setenv("LIBRARY_RESERVATIONS_PATH", str(path))
    model = ScriptedModel()
    messages = iter(["", "Show Python books", "Reserve B002 for S001", "exit"])

    async def run():
        async with connect_server() as server:
            agent = build_agent(server)
            agent.model = model
            await conversation(agent, read_message=lambda prompt: next(messages))

    asyncio.run(run())
    assert json.loads(path.read_text()) == [{"book_id": "B002", "student_id": "S001"}]
    assert len(model.inputs) == 4
    # The next user turn contains the earlier tool call and its result.
    assert any(isinstance(item, dict) and item.get("type") == "function_call_output" for item in model.inputs[2])
    out = capsys.readouterr().out
    assert "[MCP call] search_books" in out
    assert "[MCP call] reserve_book" in out
    assert "B002 reserved for S001" in out
