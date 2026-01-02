from api.routers import chat as chat_router


def test_start_chat(client, monkeypatch):
    monkeypatch.setattr(
        chat_router,
        "start_session",
        lambda msg, email: ("s1", "Next question?", False),
    )

    response = client.post("/api/start", json={"message": "Fever"})
    body = response.json()

    assert body["success"] is True
    assert body["data"]["session_id"] == "s1"


def test_chat_continue(client, monkeypatch):
    monkeypatch.setattr(
        chat_router,
        "chat_session",
        lambda sid, msg: {"finished": False, "reply": "Another question"},
    )

    response = client.post(
        "/api/chat",
        json={"session_id": "s1", "message": "2 days"},
    )

    body = response.json()
    assert body["data"]["finished"] is False


def test_chat_finish(client, monkeypatch):
    monkeypatch.setattr(
        chat_router,
        "chat_session",
        lambda sid, msg: {
            "finished": True,
            "final": {
                "disease": "Flu",
                "severity": "Mild",
                "reason": "Symptoms match",
                "explanation": "Rest advised",
            },
        },
    )

    response = client.post(
        "/api/chat",
        json={"session_id": "s1", "message": "Yes"},
    )

    body = response.json()
    assert body["data"]["finished"] is True


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

    assert response.json()["success"] is True
