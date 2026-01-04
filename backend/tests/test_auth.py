from api.routers import auth as auth_router


def test_register_success(client, monkeypatch):
    monkeypatch.setattr(
        auth_router,
        "register_user",
        lambda *args, **kwargs: {
            "name": "Test User",
            "email": "test@example.com",
            "age": 25,
            "gender": "male",
        },
    )

    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "age": 25,
            "gender": "male",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    body = response.json()
    assert body["success"] is True
    assert body["data"]["access_token"]


def test_register_failure(client, monkeypatch):
    monkeypatch.setattr(
        auth_router,
        "register_user",
        lambda *a, **k: (_ for _ in ()).throw(ValueError("exists")),
    )

    response = client.post(
        "/api/auth/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "age": 25,
            "gender": "male",
            "email": "test@example.com",
            "password": "x",
        },
    )

    assert response.json()["success"] is False


def test_login_success(client, monkeypatch):
    monkeypatch.setattr(
        auth_router,
        "login_user",
        lambda *a, **k: {"email": "test@example.com"},
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )

    body = response.json()
    assert body["success"] is True
    assert body["data"]["access_token"]


def test_login_failure(client, monkeypatch):
    monkeypatch.setattr(
        auth_router,
        "login_user",
        lambda *a, **k: (_ for _ in ()).throw(ValueError("invalid")),
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "wrong@example.com",
            "password": "wrong",
        },
    )

    assert response.json()["success"] is False
