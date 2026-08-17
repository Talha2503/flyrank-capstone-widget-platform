def test_create_widget_requires_auth(client):
    resp = client.post("/api/widgets", json={"type": "signup_form", "title": "X"})
    assert resp.status_code in (401, 403)


def test_create_and_get_widget(client, auth_headers):
    resp = client.post(
        "/api/widgets",
        headers=auth_headers,
        json={"type": "signup_form", "title": "Newsletter", "fields": [], "button_text": "Go"},
    )
    assert resp.status_code == 201
    widget = resp.json()
    assert widget["title"] == "Newsletter"
    assert widget["version"] == 1

    get_resp = client.get(f"/api/widgets/{widget['id']}", headers=auth_headers)
    assert get_resp.status_code == 200


def test_tenant_isolation_on_widgets(client, auth_headers, widget_id):
    # Sign up a second, separate tenant
    client.post("/api/auth/signup", json={"email": "other@example.com", "password": "otherpass123"})
    login = client.post("/api/auth/login", json={"email": "other@example.com", "password": "otherpass123"})
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # Tenant B must not be able to see tenant A's widget
    resp = client.get(f"/api/widgets/{widget_id}", headers=other_headers)
    assert resp.status_code == 404


def test_update_bumps_version(client, auth_headers, widget_id):
    resp = client.put(
        f"/api/widgets/{widget_id}", headers=auth_headers, json={"title": "Updated title"}
    )
    assert resp.status_code == 200
    assert resp.json()["version"] == 2


def test_delete_widget(client, auth_headers, widget_id):
    resp = client.delete(f"/api/widgets/{widget_id}", headers=auth_headers)
    assert resp.status_code == 204

    get_resp = client.get(f"/api/widgets/{widget_id}", headers=auth_headers)
    assert get_resp.status_code == 404