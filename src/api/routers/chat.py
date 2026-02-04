import json
from typing import Iterator
from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from agno.run.agent import RunEvent

from src.agents.diet_planner import get_diet_planner

router = APIRouter()


@router.post("")
def chat(payload: dict) -> StreamingResponse:
    message = payload.get("message")
    if not message:
        return StreamingResponse(
            _event_stream(iter(["event: error\ndata: Missing message\n\n"])),
            media_type="text/event-stream",
        )

    session_id = payload.get("session_id")
    user_id = payload.get("user_id")
    if not session_id:
        session_id = str(uuid4())
    if not user_id:
        return StreamingResponse(
            _event_stream(iter(["event: error\ndata: Missing user_id\n\n"])),
            media_type="text/event-stream",
        )

    try:
        agent = get_diet_planner()
    except RuntimeError as exc:
        return StreamingResponse(
            _event_stream(iter([f"event: error\ndata: {exc}\n\n"])),
            media_type="text/event-stream",
        )

    stream = agent.run(
        input=message,
        stream=True,
        user_id=user_id,
        session_id=session_id,
        add_history_to_context=True,
    )

    return StreamingResponse(
        _event_stream(stream, session_id), media_type="text/event-stream"
    )


def _event_stream(stream: Iterator, session_id: str) -> Iterator[str]:
    yield f"data: {json.dumps({'type': 'session_id', 'session_id': session_id})}\n\n"
    for event in stream:
        if getattr(event, "event", None) == RunEvent.run_content:
            chunk = event.content or ""
            data = json.dumps({"type": "content", "content": chunk})
            yield f"data: {data}\n\n"

    yield "data: {\"type\":\"done\"}\n\n"
