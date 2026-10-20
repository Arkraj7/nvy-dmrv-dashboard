"""Unit tests for verify_link policy primitives (offline).

Network access is disabled: any test that reaches the fetcher fails loudly.
"""
from __future__ import annotations

import pytest

from verify_link import LinkVerifier, load_employers_registry

REGISTRY = {
    "employers": [
        {
            "id": "acme-green-foundation",
            "name": "Acme Green Foundation",
            "domains": ["acmegreen.org"],
            "ats_hosts": ["greenhouse.io"],
            "region": "india",
            "approved": True,
        }
    ]
}


@pytest.fixture()
def verifier():
    return LinkVerifier(REGISTRY, use_playwright=False)


def test_blocklist_is_checked_before_any_network_call(verifier, monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("network must not be touched for blocklisted hosts")

    monkeypatch.setattr(verifier, "_fetch_with_redirects", boom)
    result = verifier.verify(
        "https://www.linkedin.com/jobs/view/123456",
        "acme-green-foundation",
        "Research Associate",
        "Acme Green Foundation",
    )
    assert result.ok is False
    assert result.reason_code == "BLOCKED_HOST"
    assert result.http_status == 0
    assert result.host_class == "blocklisted"


def test_unregistered_host_is_rejected_before_fetch(verifier, monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("network must not be touched")

    monkeypatch.setattr(verifier, "_fetch_with_redirects", boom)
    result = verifier.verify(
        "https://random-blog.example/careers/job-1",
        "acme-green-foundation",
    )
    assert result.reason_code == "HOST_NOT_IN_REGISTRY"


def test_dns_filtered_resolution_needs_manual_check(verifier, monkeypatch):
    monkeypatch.setattr(
        verifier, "_is_private_ip", lambda host: "dns_filtered"
    )
    result = verifier.verify(
        "https://acmegreen.org/careers/research-associate",
        "acme-green-foundation",
        "Research Associate",
    )
    assert result.ok is False
    assert result.reason_code == "NEEDS_MANUAL_CHECK"
    assert "dns" in result.error_detail


def test_tls_error_needs_manual_check(verifier, monkeypatch):
    monkeypatch.setattr(verifier, "_is_private_ip", lambda host: False)
    monkeypatch.setattr(
        verifier,
        "_fetch_with_redirects",
        lambda url: (None, [url], "tls|SSLError|certificate verify failed"),
    )
    result = verifier.verify(
        "https://acmegreen.org/careers/research-associate",
        "acme-green-foundation",
    )
    assert result.reason_code == "NEEDS_MANUAL_CHECK"


def test_tracking_parameters_are_stripped(verifier):
    cleaned = verifier._strip_tracking_params(
        "https://acmegreen.org/jobs/1?utm_source=x&ref=y&job=7"
    )
    assert "utm_source" not in cleaned
    assert "ref=y" not in cleaned
    assert "job=7" in cleaned


def test_slug_style_job_url_is_a_posting(verifier):
    entry_type = verifier._detect_entry_type(
        "Job description. Key responsibilities. Qualifications. Apply now.",
        "https://acmegreen.org/careers/research-associate-urban-forests",
        "acmegreen.org",
    )
    assert entry_type == "posting"


def test_generic_careers_page_is_a_portal(verifier):
    entry_type = verifier._detect_entry_type(
        "Join our team. View all jobs. Current openings.",
        "https://acmegreen.org/careers",
        "acmegreen.org",
    )
    assert entry_type == "careers_portal"


def test_award_page_is_an_award_portal(verifier):
    entry_type = verifier._detect_entry_type(
        "The fellowship application deadline is 1 December. "
        "Eligibility criteria and selection criteria are below. "
        "Submit your application.",
        "https://acmegreen.org/fellowship/apply",
        "acmegreen.org",
    )
    assert entry_type == "award_portal"


def test_registry_loads_the_signed_off_source_of_truth():
    registry = load_employers_registry("public/employers.json")
    employers = registry["employers"]
    ids = {employer["id"] for employer in employers}
    assert "the-nature-conservancy-tnc" in ids
    assert "world-resources-institute-wri" in ids
    assert "global-environment-facility-small-grants-programme-sgp-implemented-by-undp" in ids

    wri = next(e for e in employers if e["id"] == "world-resources-institute-wri")
    assert "wri.org" in wri["domains"]
    assert "wri-india.org" in wri["domains"]

    sg = next(
        e
        for e in employers
        if e["id"]
        == "global-environment-facility-small-grants-programme-sgp-implemented-by-undp"
    )
    assert sg["domains"] == ["sgp.undp.org"]

    undp = next(
        e
        for e in employers
        if e["id"] == "united-nations-development-programme-undp"
    )
    assert "jobs.undp.org" in undp["ats_hosts"]
