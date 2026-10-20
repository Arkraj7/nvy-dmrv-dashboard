import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import fetch_and_humanize as fh


def test_hard_negative_sales_titles_are_blocked():
    for title in (
        "Sales Manager - Sustainability",
        "Sales Analyst",
        "Area Sales Manager",
        "Business Development & Marketing Associate",
        "Customer Support Executive",
        "Telecaller",
        "Full Stack Developer",
    ):
        assert fh.is_excluded_role(title, "Acme", ""), title


def test_solar_bess_business_development_is_allowed():
    assert not fh.is_excluded_role(
        "Business Development Manager - Renewable Energy & BESS",
        "DEIF",
        "Solar hybrid and battery storage projects",
    )


def test_academic_quota_reserves_about_half_the_budget():
    candidates = [
        {"title": "Junior Research Fellow", "description": "JRF in forestry"},
        {"title": "Project Associate II", "description": "Ecology project"},
        {"title": "Sales Manager", "description": "excluded upstream"},
    ] + [
        {"title": "ESG Manager", "description": "BRSR reporting"}
        for _ in range(7)
    ]
    selected = fh.prioritize_academic_candidates(candidates, 6)
    academic = [c for c in selected if fh.is_academic_candidate(c)]
    assert len(selected) == 6
    assert len(academic) >= 2


def test_purge_removes_generic_roles_from_both_buckets():
    active = [{"id": "a", "clean_title": "Sales Manager", "organization": "X"}]
    archive = [{"id": "b", "clean_title": "General Accountant", "organization": "Y"}]
    kept_active, kept_archive, removed = fh.purge_excluded_records(active, archive)
    assert kept_active == [] and kept_archive == []
    assert {item["id"] for item in removed} == {"a", "b"}


def test_telegram_chat_normalisation():
    assert fh.normalize_telegram_chat_id("urbanforestpark_jobs") == "@urbanforestpark_jobs"
    assert fh.normalize_telegram_chat_id("@urbanforestpark") == "@urbanforestpark"
    assert fh.normalize_telegram_chat_id("-1001234567890") == "-1001234567890"
    assert fh.telegram_chat_candidates("123456789") == ["123456789", "-100123456789"]


def test_role_identity_ignores_year_url_and_punctuation():
    a = fh.role_identity({"clean_title": "Wildlife Enthusiasts Course 2026", "organization": "WII"})
    b = fh.role_identity({"title": "Wildlife Enthusiasts Course", "company": "WII"})
    assert a == b


def test_role_identity_differs_for_distinct_roles():
    assert fh.role_identity({"title": "JRF Forestry", "organization": "ICFRE"}) != fh.role_identity(
        {"title": "SRF Forestry", "organization": "ICFRE"}
    )


def test_core_domain_gate_accepts_environmental_roles():
    assert fh.has_core_domain_signal(
        "JRF - Forest Ecology", "Fieldwork in a wildlife corridor and GIS mapping"
    )
    assert fh.has_core_domain_signal(
        "Programme Associate", "Industrial heat decarbonisation policy research"
    )
    assert fh.has_core_domain_signal(
        "Quality Assurance Manager", "Decentralised drinking water quality audits"
    )


def test_core_domain_gate_rejects_non_environmental_roles():
    assert not fh.has_core_domain_signal(
        "Project Director, Preconception Nutrition & Care",
        "Integrating maternal nutrition into health systems",
    )
    assert not fh.has_core_domain_signal(
        "Head of Advocacy and Evidencing",
        "Rights and inclusion of older people in humanitarian frameworks",
    )
    assert not fh.has_core_domain_signal(
        "Assistant Director Programs",
        "Health, education and rural socio-economic progress",
    )


def test_generic_landing_titles_are_not_vacancies():
    assert fh.is_generic_landing_title("Job Openings")
    assert fh.is_generic_landing_title("WRI India Research Programme")
    assert not fh.is_generic_landing_title("Research Associate - Forest Carbon")


def test_academic_category_aliases_map_to_schema():
    assert fh.match_enum(
        "JRF, SRF & PhD Positions", fh.CATEGORIES, fh.CATEGORY_ALIASES
    ) == "Academic, JRF, SRF & PhD Positions"


def test_apply_url_identity_catches_title_variants():
    a = fh.apply_url_identity("https://Example.org/jobs/123/?utm_source=x")
    b = fh.apply_url_identity("https://example.org/jobs/123")
    assert a == b == "example.org/jobs/123"
    assert fh.apply_url_identity("https://example.org/jobs/456") != a


def test_apply_url_identity_keeps_posting_ids():
    one = fh.apply_url_identity("https://in.indeed.com/viewjob?jk=abc123&utm_source=x")
    two = fh.apply_url_identity("https://in.indeed.com/viewjob?jk=def456")
    assert one != two
    assert "jk=abc123" in one


def test_write_stats_preserves_telegram_broadcast_marker(tmp_path):
    path = tmp_path / "stats.json"
    path.write_text(
        json.dumps({"last_telegram_broadcast_date": "2026-10-21", "active_open_jobs": 1}),
        encoding="utf-8",
    )
    fh.write_stats({"active_open_jobs": 2}, path)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["last_telegram_broadcast_date"] == "2026-10-21"
    assert saved["active_open_jobs"] == 2
