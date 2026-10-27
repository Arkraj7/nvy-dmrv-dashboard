"""Tests for the Google sitemap + Indexing API helper."""

import json

import google_indexing as gi


def test_collect_job_urls_skips_quarantined_and_unknown(tmp_path):
    public = tmp_path / "public"
    public.mkdir()
    (public / "jobs.json").write_text(
        json.dumps(
            [
                {
                    "id": "keep-me",
                    "status": "active",
                    "entry_type": "posting",
                    "clean_title": "Keep me",
                },
                {
                    "id": "quarantined",
                    "status": "quarantined",
                    "entry_type": "posting",
                },
                {
                    "id": "unknown",
                    "status": "active",
                    "entry_type": "unknown",
                },
                {
                    "id": "portal",
                    "status": "active",
                    "entry_type": "careers_portal",
                },
            ]
        ),
        encoding="utf-8",
    )
    (public / "global_jobs.json").write_text(
        json.dumps(
            [
                {
                    "id": "global-keep",
                    "status": "active",
                    "entry_type": "posting",
                    "clean_title": "Global keep",
                }
            ]
        ),
        encoding="utf-8",
    )

    urls = gi.collect_job_urls(public)

    assert "https://www.urbanforestpark.com/jobs/keep-me" in urls
    assert "https://www.urbanforestpark.com/jobs/global-keep" in urls
    assert "https://www.urbanforestpark.com/jobs/quarantined" not in urls
    assert "https://www.urbanforestpark.com/jobs/unknown" not in urls
    assert "https://www.urbanforestpark.com/jobs/portal" not in urls


def test_pending_urls_detects_changes():
    current = {"a": "1", "b": "2"}
    state = {"a": "1", "b": "old"}

    assert gi.pending_urls(current, state) == ["b"]
    assert gi.pending_urls(current, state, force=True) == ["a", "b"]


def test_fingerprint_changes_with_content():
    old = {"id": "x", "clean_title": "Old title", "status": "active"}
    new = {"id": "x", "clean_title": "New title", "status": "active"}

    assert gi.record_fingerprint(old) != gi.record_fingerprint(new)
