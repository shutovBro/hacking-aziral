"""Интеграционные тесты API: создание цели и scope-gate при запуске скана."""


def _make_target(client) -> int:
    resp = client.post(
        "/api/targets",
        json={
            "name": "Acme Corp",
            "description": "authorized pentest",
            "authorized_by": "CISO Acme",
            "scope": {"domains": ["acme.com"], "usernames": ["acme_admin"]},
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_create_and_get_target(client):
    tid = _make_target(client)
    got = client.get(f"/api/targets/{tid}")
    assert got.status_code == 200
    assert got.json()["scope"]["domains"] == ["acme.com"]


def test_scan_in_scope_creates_pending_job(client):
    tid = _make_target(client)
    resp = client.post(
        "/api/scans",
        json={"target_id": tid, "tool": "theharvester", "kind": "domain", "value": "acme.com"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == "pending"


def test_scan_out_of_scope_is_blocked(client):
    tid = _make_target(client)
    resp = client.post(
        "/api/scans",
        json={"target_id": tid, "tool": "theharvester", "kind": "domain", "value": "evil.com"},
    )
    assert resp.status_code == 403, resp.text
    assert "scope" in resp.json()["detail"].lower()


def test_scan_unknown_tool_rejected(client):
    tid = _make_target(client)
    resp = client.post(
        "/api/scans",
        json={"target_id": tid, "tool": "nmap-of-doom", "kind": "domain", "value": "acme.com"},
    )
    assert resp.status_code == 400


def test_results_endpoints_empty(client):
    tid = _make_target(client)
    assert client.get(f"/api/targets/{tid}/entities").json() == []
    assert client.get(f"/api/targets/{tid}/findings").json() == []


def test_results_endpoints_404_for_missing_target(client):
    assert client.get("/api/targets/999999/entities").status_code == 404
    assert client.get("/api/targets/999999/findings").status_code == 404


def test_tools_endpoint_lists_adapters(client):
    tools = client.get("/api/tools").json()["tools"]
    assert "sherlock" in tools and "spiderfoot" in tools


def test_blocked_scan_writes_audit(client):
    tid = _make_target(client)
    client.post(
        "/api/scans",
        json={"target_id": tid, "tool": "sherlock", "kind": "username", "value": "mallory"},
    )
    # blocked job должен существовать в списке задач
    jobs = client.get("/api/scans").json()
    assert any(j["status"] == "blocked" for j in jobs)
