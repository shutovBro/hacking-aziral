"""Тесты адаптеров OSINT-инструментов (парсинг вывода, без реальных бинарей)."""
import json

import httpx
import pytest

from app.orchestrators import holehe, maigret, sherlock, spiderfoot, theharvester
from app.orchestrators._proc import ToolError


class FakeProc:
    def __init__(self, out: str):
        self.stdout = out
        self.returncode = 0


def test_sherlock_parses_found(monkeypatch):
    out = "[+] GitHub: https://github.com/alice\n[*] noise\n[+] Twitter: https://twitter.com/alice\n"
    monkeypatch.setattr(sherlock, "run_cmd", lambda args, timeout=300: FakeProc(out))
    res = sherlock.run("username", "alice")
    assert len(res) == 2
    assert all(r.entity_kind == "social_account" for r in res)


def test_sherlock_rejects_wrong_kind():
    with pytest.raises(ToolError):
        sherlock.run("email", "x@y.com")


def test_holehe_parses_used(monkeypatch):
    out = "[+] twitter.com\n[-] not used\n[+] github.com\n"
    monkeypatch.setattr(holehe, "run_cmd", lambda args, timeout=300: FakeProc(out))
    res = holehe.run("email", "a@acme.com")
    assert len(res) == 2
    assert res[0].entity_kind == "social_account"


def test_holehe_rejects_wrong_kind():
    with pytest.raises(ToolError):
        holehe.run("username", "alice")


def test_theharvester_parses_json(monkeypatch, tmp_path):
    base = tmp_path / "out"
    base.with_suffix(".json").write_text(
        json.dumps({"emails": ["a@acme.com"], "hosts": ["h.acme.com"], "ips": ["1.2.3.4"]})
    )
    monkeypatch.setattr(theharvester, "temp_path", lambda suffix="": base)
    monkeypatch.setattr(theharvester, "run_cmd", lambda args, timeout=420: FakeProc(""))
    res = theharvester.run("domain", "acme.com")
    kinds = {r.entity_kind for r in res}
    assert {"email", "host", "ip"} <= kinds


def test_theharvester_rejects_wrong_kind():
    with pytest.raises(ToolError):
        theharvester.run("username", "alice")


def test_spiderfoot_fetch_maps_event_types():
    rows = [
        ["t", "bob@acme.com", "src", "mod1", "EMAILADDR"],
        ["t", "1.2.3.4", "src", "mod2", "IP_ADDRESS"],
        ["t", "ignored", "src", "mod3", "SOME_UNKNOWN_TYPE"],
    ]
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=rows)),
                          base_url="http://sf")
    res = spiderfoot._fetch_results(client, "scan-1")
    kinds = {r.entity_kind for r in res}
    assert "email" in kinds and "ip" in kinds
    assert len(res) == 2  # неизвестный тип пропущен


def test_spiderfoot_rejects_wrong_kind():
    with pytest.raises(ToolError):
        spiderfoot.run("breach", "x")


def test_maigret_parses_sites(monkeypatch):
    out = "telegram: found\ninstagram: found\nnoise line without colon\n"
    monkeypatch.setattr(maigret, "run_cmd", lambda args, timeout=600: FakeProc(out))
    res = maigret.run("username", "alice")
    assert len(res) == 2
    assert all(r.entity_kind == "social_account" for r in res)
    assert all(r.raw["source"] == "maigret" for r in res)


def test_maigret_rejects_wrong_kind():
    with pytest.raises(ToolError):
        maigret.run("domain", "acme.com")
