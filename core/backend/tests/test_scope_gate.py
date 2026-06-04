"""Unit-тесты scope-gate (чистая логика)."""
from app.scope import check_in_scope

SCOPE = {
    "domains": ["example.com"],
    "emails": ["ceo@other.com"],
    "usernames": ["alice"],
    "hosts": ["vpn.partner.net"],
    "ip_ranges": ["10.0.0.0/24"],
}


def test_email_in_scope_by_domain():
    assert check_in_scope(SCOPE, "email", "bob@example.com").allowed


def test_email_in_scope_by_explicit():
    assert check_in_scope(SCOPE, "email", "ceo@other.com").allowed


def test_email_out_of_scope():
    assert not check_in_scope(SCOPE, "email", "x@evil.com").allowed


def test_username_in_scope():
    assert check_in_scope(SCOPE, "username", "alice").allowed


def test_username_out_of_scope():
    assert not check_in_scope(SCOPE, "username", "mallory").allowed


def test_subdomain_in_scope():
    assert check_in_scope(SCOPE, "host", "api.example.com").allowed


def test_explicit_host_in_scope():
    assert check_in_scope(SCOPE, "host", "vpn.partner.net").allowed


def test_domain_out_of_scope():
    assert not check_in_scope(SCOPE, "domain", "notexample.com").allowed


def test_ip_in_range():
    assert check_in_scope(SCOPE, "ip", "10.0.0.55").allowed


def test_ip_out_of_range():
    assert not check_in_scope(SCOPE, "ip", "10.0.1.5").allowed


def test_empty_scope_is_fail_closed():
    assert not check_in_scope({}, "email", "bob@example.com").allowed


def test_unknown_kind_blocked():
    assert not check_in_scope(SCOPE, "carrier_pigeon", "whatever").allowed
