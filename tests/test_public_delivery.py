def test_widget_config_is_public(client, widget_id):
    resp = client.get(f"/widgets/{widget_id}/config")
    assert resp.status_code == 200
    assert "cache-control" in resp.headers


def test_widget_config_unknown_id(client):
    resp = client.get("/widgets/00000000-0000-0000-0000-000000000000/config")
    assert resp.status_code == 404


def test_widget_js_served(client):
    resp = client.get("/widget.js")
    assert resp.status_code == 200
    assert "javascript" in resp.headers["content-type"]
    assert "fetch(" in resp.text  # sanity check it's the real script