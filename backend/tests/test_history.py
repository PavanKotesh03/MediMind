from api.routers import history as history_router


def test_get_grouped_history(client, monkeypatch):
    monkeypatch.setattr(
        history_router,
        "get_grouped_history",
        lambda db, email: {"today": []},
    )

    response = client.get(
        "/api/history/grouped?user_email=test@example.com",
    )

    body = response.json()
    assert body["success"] is True
    assert "today" in body["data"]


def test_get_conversation_not_found(client, monkeypatch):
    monkeypatch.setattr(
        history_router,
        "get_conversation_by_id",
        lambda db, sid, email: None,
    )

    response = client.get(
        "/api/history/s1?user_email=test@example.com",
    )

    assert response.json()["success"] is False


def test_delete_conversation(client, monkeypatch):
    monkeypatch.setattr(
        history_router,
        "delete_conversation",
        lambda db, sid, email: True,
    )

    response = client.delete(
        "/api/history/s1?user_email=test@example.com",
    )

    assert response.json()["success"] is True
