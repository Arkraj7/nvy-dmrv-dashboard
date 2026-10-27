"""Regression tests for sitemap hygiene and generated job redirects."""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import build_seo_pages as seo
import fetch_and_humanize as fh

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"


def _job(job_id="test-job", **overrides):
    job = {
        "id": job_id,
        "status": "active",
        "entry_type": "posting",
        "category": "Forestry, Wildlife & Afforestation",
        "title": "Test Forestry Job",
        "apply_url": "https://example.org/jobs/1",
        "date_added": "2026-10-27",
    }
    job.update(overrides)
    return job


def test_write_sitemap_excludes_query_views(tmp_path):
    path = tmp_path / "sitemap.xml"
    fh.write_sitemap([_job()], [], path)

    text = path.read_text(encoding="utf-8")
    assert "?job=" not in text
    assert "?category=" not in text
    assert "?state=" not in text
    assert "?view=" not in text
    ET.fromstring(text)


def test_write_sitemap_recovers_from_conflict_markers(tmp_path):
    path = tmp_path / "sitemap.xml"
    path.write_text("<<<<<<< Updated upstream\n", encoding="utf-8")

    fh.write_sitemap([_job()], [], path)

    text = path.read_text(encoding="utf-8")
    assert "<<<<<<<" not in text
    ET.fromstring(text)


def test_public_sitemap_is_well_formed_and_query_free():
    text = (PUBLIC / "sitemap.xml").read_text(encoding="utf-8")
    assert "<<<<<<<" not in text
    assert ">>>>>>>" not in text
    root = ET.fromstring(text)
    locs = [node.text for node in root.iter() if node.tag.endswith("loc")]
    assert locs
    assert all("?" not in loc for loc in locs)
    assert all(loc.startswith("https://www.urbanforestpark.com/") for loc in locs)


def test_sync_job_redirects_covers_missing_pages(tmp_path):
    public = tmp_path / "public"
    (public / "jobs").mkdir(parents=True)
    (public / "_redirects").write_text(
        "# hand written\n/jobs/keep-me /somewhere 301\n", encoding="utf-8"
    )
    (public / "jobs.json").write_text("[]", encoding="utf-8")
    (public / "archive.json").write_text(
        json.dumps(
            [
                {
                    "id": "gone-research",
                    "status": "archived",
                    "category": "Research Associate & Project Staff (Contractual)",
                },
                {
                    "id": "live-archive",
                    "status": "archived",
                    "category": "Forestry, Wildlife & Afforestation",
                },
            ]
        ),
        encoding="utf-8",
    )
    (public / "global_jobs.json").write_text("[]", encoding="utf-8")
    (public / "global_archive.json").write_text(
        json.dumps(
            [
                {
                    "id": "gone-global",
                    "status": "quarantined",
                    "category": "Fellowships & Leadership Programs",
                    "country": "Global",
                }
            ]
        ),
        encoding="utf-8",
    )
    (public / "jobs" / "live-archive.html").write_text("ok", encoding="utf-8")

    count = seo.sync_job_redirects(public)
    text = (public / "_redirects").read_text(encoding="utf-8")

    assert count >= 3
    assert "/jobs/gone-research /jrf-srf-project-associate-jobs 301" in text
    assert "/jobs/gone-global /global-climate-sustainability-opportunities 301" in text
    assert "/jobs/live-archive" not in text
    assert "/jobs/keep-me /somewhere 301" in text

    # Re-running must replace the managed block, not duplicate it.
    seo.sync_job_redirects(public)
    text = (public / "_redirects").read_text(encoding="utf-8")
    assert text.count(seo.REDIRECTS_START) == 1
    assert text.count("/jobs/gone-research") == 1
