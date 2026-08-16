import os
import httpx

GEO_PROVIDER_A_URL = os.environ.get("GEO_PROVIDER_A_URL", "http://ip-api.com/json")
GEO_PROVIDER_B_URL = os.environ.get("GEO_PROVIDER_B_URL", "https://ipapi.co")

# Toggles for testing the fallback chain deterministically, without relying
# on the real providers actually being up or down.
FORCE_PROVIDER_A_DOWN = os.environ.get("FORCE_PROVIDER_A_DOWN", "false").lower() == "true"
FORCE_PROVIDER_B_DOWN = os.environ.get("FORCE_PROVIDER_B_DOWN", "false").lower() == "true"


def _lookup_provider_a(ip: str) -> dict | None:
    if FORCE_PROVIDER_A_DOWN:
        return None
    try:
        resp = httpx.get(f"{GEO_PROVIDER_A_URL}/{ip}", timeout=3.0)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "fail":
            return None
        return {"country": data.get("country"), "city": data.get("city")}
    except Exception as e:
        print(f"[geo] provider_a failed: {e}")
        return None


def _lookup_provider_b(ip: str) -> dict | None:
    if FORCE_PROVIDER_B_DOWN:
        return None
    try:
        resp = httpx.get(f"{GEO_PROVIDER_B_URL}/{ip}/json/", timeout=3.0)
        resp.raise_for_status()
        data = resp.json()
        if data.get("error"):
            return None
        return {"country": data.get("country_name"), "city": data.get("city")}
    except Exception as e:
        print(f"[geo] provider_b failed: {e}")
        return None


def enrich_ip(ip: str | None) -> dict:
    """
    Tries provider A, then provider B, then gives up gracefully.
    Always returns a dict -- never raises. Never blocks a submission.
    """
    if not ip or ip in ("127.0.0.1", "localhost", "testclient"):
        return {"country": None, "city": None, "provider_used": None}

    result = _lookup_provider_a(ip)
    if result:
        return {**result, "provider_used": "provider_a"}

    result = _lookup_provider_b(ip)
    if result:
        return {**result, "provider_used": "provider_b"}

    return {"country": None, "city": None, "provider_used": None}