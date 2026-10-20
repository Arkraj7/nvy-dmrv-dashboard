"""Unit tests for the editable direct-link policy (offline).

Network access is disabled; fetch results are injected.
"""
from __future__ import annotations

import pytest

from link_policy import (
    is_generic_url,
    matches_platform_pattern,
    platform_for,
    strip_tracking,
)
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


class FakeResponse:
    def __init__(self, status_code=200, text="", content_type="text/html"):
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}
        self._content_for_analysis = text.encode("utf-8")

    def close(self):
        return None


@pytest.fixture()
def verifier():
    return LinkVerifier(REGISTRY, use_playwright=False)


def no_network(monkeypatch, verifier):
    def boom(*args, **kwargs):
        raise AssertionError("network must not be touched")
    monkeypatch.setattr(verifier, "_fetch_with_redirects", boom)


def test_linkedin_direct_is_kept_without_fetch(verifier, monkeypatch):
    no_network(monkeypatch, verifier)
    result = verifier.verify(
        "https://www.linkedin.com/jobs/view/123456",
        "acme-green-foundation",
    )
    assert result.ok is True
    assert result.reason_code == "UNKNOWN_KEEP"
    assert result.entry_type == "posting"
    assert result.platform == "LinkedIn"
    assert result.http_status == 0


def test_linkedin_search_is_not_direct(verifier, monkeypatch):
    no_network(monkeypatch, verifier)
    result = verifier.verify(
        "https://in.linkedin.com/jobs/search?keywords=forestry",
        "acme-green-foundation",
    )
    assert result.reason_code == "NOT_DIRECT_LINK"
    assert result.entry_type == "careers_portal"
    assert result.ok is True


def test_indeed_direct_url_pattern(verifier, monkeypatch):
    no_network(monkeypatch, verifier)
    result = verifier.verify(
        "https://in.indeed.com/viewjob?jk=abc123&utm_source=alert",
        "acme-green-foundation",
    )
    assert result.reason_code == "UNKNOWN_KEEP"
    assert result.platform == "Indeed"
    assert "utm_source" not in result.final_url
    assert "jk=abc123" in result.final_url


def test_naukri_direct_and_listing(verifier, monkeypatch):
    no_network(monkeypatch, verifier)
    direct = verifier.verify(
        "https://www.naukri.com/job-listings-forest-officer-12345678"
    )
    listing = verifier.verify("https://www.naukri.com/forestry-jobs")
    assert direct.reason_code == "UNKNOWN_KEEP"
    assert listing.reason_code == "NOT_DIRECT_LINK"


def test_home_and_search_pages_are_not_direct(verifier, monkeypatch):
    no_network(monkeypatch, verifier)
    for url in (
        "https://acmegreen.org/",
        "https://acmegreen.org/careers",
        "https://acmegreen.org/jobs?q=forestry",
    ):
        result = verifier.verify(url, "acme-green-foundation")
        assert result.reason_code == "NOT_DIRECT_LINK", url
        assert result.ok is True


def test_404_is_dead(verifier, monkeypatch):
    monkeypatch.setattr(verifier, "_is_private_ip", lambda host: False)
    monkeypatch.setattr(
        verifier,
        "_fetch_with_redirects",
        lambda url: (FakeResponse(404), [url], ""),
    )
    result = verifier.verify(
        "https://acmegreen.org/careers/research-associate",
        "acme-green-foundation",
    )
    assert result.ok is False
    assert result.reason_code == "DEAD_LINK"


def test_closed_text_is_dead(verifier, monkeypatch):
    monkeypatch.setattr(verifier, "_is_private_ip", lambda host: False)
    html = (
        "<html><body><h1>Research Associate</h1>"
        "<p>Applications are closed.</p></body></html>"
    )
    monkeypatch.setattr(
        verifier,
        "_fetch_with_redirects",
        lambda url: (FakeResponse(200, html), [url], ""),
    )
    result = verifier.verify(
        "https://acmegreen.org/careers/research-associate",
        "acme-green-foundation",
    )
    assert result.reason_code == "DEAD_LINK"


def test_timeout_and_tls_errors_are_unknown_keep(verifier, monkeypatch):
    for detail in (
        "connect|ConnectTimeout|timed out",
        "tls|SSLError|certificate verify failed",
        "request|RetryError|too many retries",
        "ssrf_guard|PrivateIPError|Blocked private IP",
    ):
        monkeypatch.setattr(
            verifier, "_fetch_with_redirects", lambda url, d=detail: (None, [url], d)
        )
        result = verifier.verify(
            "https://acmegreen.org/careers/research-associate",
            "acme-green-foundation",
        )
        assert result.ok is True, detail
        assert result.reason_code == "UNKNOWN_KEEP", detail


def test_200_specific_page_is_ok(verifier, monkeypatch):
    monkeypatch.setattr(verifier, "_is_private_ip", lambda host: False)
    html = (
        "<html><body><h1>Research Associate - Urban Forests</h1>"
        "<p>Job description. Key responsibilities. Qualifications. Apply now.</p>"
        "</body></html>"
    )
    monkeypatch.setattr(
        verifier,
        "_fetch_with_redirects",
        lambda url: (FakeResponse(200, html), [url], ""),
    )
    result = verifier.verify(
        "https://acmegreen.org/careers/research-associate-urban-forests",
        "acme-green-foundation",
    )
    assert result.ok is True
    assert result.reason_code == "OK"
    assert result.entry_type == "posting"


def test_unresolved_wrapper_is_dropped(verifier, monkeypatch):
    monkeypatch.setattr(verifier, "_resolve_destination", lambda url: None)
    result = verifier.verify("https://news.google.com/articles/abc123")
    assert result.ok is False
    assert result.reason_code == "UNRESOLVED_WRAPPER"


def test_tracking_parameters_are_stripped(verifier):
    cleaned = verifier._strip_tracking_params(
        "https://acmegreen.org/jobs/1?utm_source=x&ref=y&job=7&jk=9"
    )
    assert "utm_source" not in cleaned
    assert "ref=y" not in cleaned
    assert "job=7" in cleaned and "jk=9" in cleaned


def test_platform_registry_is_config_driven():
    policy = {"platforms": [{"name": "Example", "hosts": ["example-jobs.com"]}]}
    assert platform_for("in.example-jobs.com", policy)["name"] == "Example"
    assert platform_for("acmegreen.org", policy) is None


def test_generic_url_helper():
    assert is_generic_url("https://acmegreen.org/")
    assert is_generic_url("https://acmegreen.org/careers/")
    assert not is_generic_url("https://acmegreen.org/careers/research-associate")
    assert not is_generic_url("https://acmegreen.org/job/12345")


def test_matches_platform_pattern():
    assert matches_platform_pattern(
        "https://www.linkedin.com/jobs/view/99",
        {"direct_patterns": [r"/jobs/view/\d+"]},
    )
    assert not matches_platform_pattern(
        "https://www.linkedin.com/jobs/",
        {"direct_patterns": [r"/jobs/view/\d+"]},
    )


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
