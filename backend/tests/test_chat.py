from api.routers import chat as chat_router
from unittest.mock import AsyncMock
import json


def test_start_chat(client, monkeypatch):
    async def mock_start_streaming(msg, email):
        yield {"type": "session_id", "data": "s1"}
        yield {"type": "token", "data": "Next question?"}
        yield {"type": "done", "data": {"finished": False}}

    monkeypatch.setattr(
        chat_router,
        "start_session_streaming",
        mock_start_streaming,
    )

    response = client.post("/api/start", json={"message": "Fever"})
    assert response.status_code == 200
    
    # Verify SSE format
    content = response.text
    assert "data: " in content
    assert '"session_id"' in content
    assert '"s1"' in content


def test_chat_continue(client, monkeypatch):
    async def mock_chat_streaming(sid, msg):
        yield {"type": "token", "data": "Another question"}
        yield {"type": "done", "data": {"finished": False}}

    monkeypatch.setattr(
        chat_router,
        "chat_session_streaming",
        mock_chat_streaming,
    )

    response = client.post(
        "/api/chat",
        json={"session_id": "s1", "message": "2 days"},
    )
    assert response.status_code == 200
    
    content = response.text
    assert "data: " in content
    assert '"Another question"' in content


def test_chat_finish(client, monkeypatch):
    async def mock_chat_streaming(sid, msg):
        yield {"type": "token", "data": "Finalizing..."}
        yield {
            "type": "final",
            "data": {
                "disease": "Flu",
                "severity": "Mild",
                "reason": "Symptoms match",
                "explanation": "Rest advised",
            }
        }
        yield {"type": "done", "data": {"finished": True}}

    monkeypatch.setattr(
        chat_router,
        "chat_session_streaming",
        mock_chat_streaming,
    )

    response = client.post(
        "/api/chat",
        json={"session_id": "s1", "message": "Yes"},
    )
    assert response.status_code == 200
    
    content = response.text
    assert '"final"' in content
    assert '"Flu"' in content
    assert '"finished": true' in content.lower()


def test_reset_chat(client, monkeypatch):
    monkeypatch.setattr(
        chat_router,
        "reset_session",
        lambda sid: None,
    )

    response = client.post(
        "/api/reset",
        json={"session_id": "s1"},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
