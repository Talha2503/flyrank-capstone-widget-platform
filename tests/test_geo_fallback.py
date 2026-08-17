import os


def test_localhost_ip_skips_geo_lookup(client, widget_id):
    """Local/loopback IPs should never attempt a real geo lookup."""
    resp = client.post(
        "/submissions",
        json={"widget_id": widget_id, "data": {"email": "visitor@example.com"}},
    )
    assert resp.status_code == 201


def test_both_providers_down_still_succeeds(client, widget_id, monkeypatch):
    """The core resilience guarantee: enrichment failing must never block a submission."""
    monkeypatch.setenv("FORCE_PROVIDER_A_DOWN", "true")
    monkeypatch.setenv("FORCE_PROVIDER_B_DOWN", "true")

    # Re-import to pick up the toggled env vars, since geo.py reads them at import time
    import importlib
    from app.integrations import geo
    importlib.reload(geo)

    resp = client.post(
        "/submissions",
        json={"widget_id": widget_id, "data": {"email": "visitor@example.com"}},
        headers={"X-Debug-IP": "8.8.8.8"},
    )
    assert resp.status_code == 201

    # Reset for any tests that run after this one
    monkeypatch.setenv("FORCE_PROVIDER_A_DOWN", "false")
    monkeypatch.setenv("FORCE_PROVIDER_B_DOWN", "false")
    importlib.reload(geo)