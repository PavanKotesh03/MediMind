def test_health_check(client):
    response = client.get("/")
    body = response.json()

    assert body["success"] is True
    assert body["data"]["version"] == "1.0.0"
