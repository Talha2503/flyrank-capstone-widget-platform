def test_valid_submission_stored(client, widget_id):
    resp = client.post(
        "/submissions",
        json={"widget_id": widget_id, "data": {"email": "visitor@example.com"}},
    )
    assert resp.status_code == 201


def test_missing_required_field_rejected(client, widget_id):
    resp = client.post("/submissions", json={"widget_id": widget_id, "data": {}})
    assert resp.status_code == 400


def test_unknown_widget_rejected(client):
    resp = client.post(
        "/submissions",
        json={"widget_id": "00000000-0000-0000-0000-000000000000", "data": {"email": "x@x.com"}},
    )
    assert resp.status_code == 404


def test_oversized_field_rejected(client, widget_id):
    resp = client.post(
        "/submissions",
        json={"widget_id": widget_id, "data": {"email": "a" * 3000}},
    )
    assert resp.status_code == 413


def test_cors_preflight(client):
    resp = client.options(
        "/submissions",
        headers={"Origin": "http://localhost:5500", "Access-Control-Request-Method": "POST"},
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "*"


def test_honeypot_drops_spam_silently(client, widget_id):
    resp = client.post(
        "/submissions",
        json={
            "widget_id": widget_id,
            "data": {"email": "bot@spam.com"},
            "website": "http://spam.example.com",
        },
    )
    # Looks like success to the bot...
    assert resp.status_code == 201

    # ...but nothing was actually stored. We can't query the DB directly
    # here without importing a session, so we check indirectly: the
    # returned id is always the same placeholder, never a real new row.
    assert resp.json()["id"] == "00000000-0000-0000-0000-000000000000"


def test_rate_limit_returns_429_on_burst(client, widget_id):
    responses = []
    for _ in range(6):
        resp = client.post(
            "/submissions",
            json={"widget_id": widget_id, "data": {"email": "visitor@example.com"}},
        )
        responses.append(resp.status_code)

    assert responses.count(201) == 5  # first 5 succeed
    assert responses.count(429) == 1  # 6th is rate-limited