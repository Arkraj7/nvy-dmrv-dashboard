import json
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import fetch_and_humanize as fh


def _job():
    return {
        "id": "jrf-forestry-1",
        "clean_title": "JRF <Forest Ecology> & Remote Sensing",
        "organization": "ICFRE & FRI",
        "city": "Dehradun",
        "state": "Uttarakhand",
        "qualification_summary": "M.Sc. Forestry with NET/GATE",
        "compensation_or_fellowship": "Rs. 37,000/month",
    }


def _make_job(job_id, category, title, date_added):
    return {
        "id": job_id,
        "clean_title": title,
        "organization": "Test Institute",
        "city": "Pune",
        "state": "Maharashtra",
        "category": category,
        "position_type": "Full-Time",
        "opportunity_kind": "Job / Career",
        "qualification_summary": "M.Sc.",
        "date_added": date_added,
        "valid_through": (fh.ist_today() + timedelta(days=20)).isoformat(),
    }


def test_telegram_html_escapes_record_content_and_links_to_static_page():
    html = fh.build_telegram_digest_html([_job()], "2026-10-20", "New jobs")
    assert "&lt;Forest Ecology&gt;" in html
    assert "ICFRE &amp; FRI" in html
    assert "https://www.urbanforestpark.com/jobs/jrf-forestry-1" in html
    assert "parse_mode" not in html


def test_plain_text_fallback_strips_tags_and_unescapes():
    plain = fh._telegram_plain_text("<b>Hello &amp; welcome</b><br><a href='x'>link</a>")
    assert "<" not in plain
    assert "Hello & welcome" in plain
    assert "link" in plain


def test_heartbeat_marker_preserves_existing_telemetry(tmp_path):
    stats = tmp_path / "stats.json"
    stats.write_text(json.dumps({"active_jobs": 42, "weekly": {"x": 1}}), encoding="utf-8")
    fh.update_last_telegram_broadcast(stats, "2026-10-20")
    payload = json.loads(stats.read_text(encoding="utf-8"))
    assert payload["active_jobs"] == 42
    assert payload["weekly"] == {"x": 1}
    assert payload["last_telegram_broadcast_date"] == "2026-10-20"
    assert payload["telegram_last_status"] == "delivered"


def _mixed_registry():
    today = fh.ist_today().isoformat()
    old = (fh.ist_today() - timedelta(days=5)).isoformat()
    academic = "Academic, JRF, SRF & PhD Positions"
    forestry = "Forestry, Wildlife & Afforestation"
    esg = "ESG, Carbon Markets & Corporate Sustainability"
    gis = "GIS, Remote Sensing & Earth Observation"

    jobs = []
    for index in range(5):
        jobs.append(
            _make_job(
                f"academic-{index}",
                academic,
                f"Junior Research Fellow {index}",
                today if index < 4 else old,
            )
        )
    for index in range(3):
        jobs.append(
            _make_job(
                f"forestry-{index}",
                forestry,
                f"Wildlife Conservation Officer {index}",
                today if index < 2 else old,
            )
        )
    for index in range(3):
        jobs.append(
            _make_job(
                f"esg-{index}",
                esg,
                f"Sustainability and Carbon Analyst {index}",
                old,
            )
        )
    for index in range(2):
        jobs.append(
            _make_job(
                f"gis-{index}",
                gis,
                f"GIS and Remote Sensing Associate {index}",
                old,
            )
        )
    globals_ = [
        _make_job(
            "global-0",
            "Fellowships & Leadership Programs",
            "Global Climate Leadership Fellowship",
            today,
        ),
        _make_job(
            "global-1",
            "Grants & Research Funding",
            "International Conservation Grant",
            old,
        ),
    ]
    for job in globals_:
        job["region"] = "UN / Multilateral"
        job["country"] = "Switzerland"
    return jobs, globals_


def test_digest_selector_excludes_recent_and_balances_tracks():
    jobs, globals_ = _mixed_registry()
    stats = {"recent_telegram_job_ids": ["academic-0", "forestry-0"]}
    picks = fh.select_daily_digest_jobs(jobs, globals_, stats, count=10)
    ids = {job["id"] for job in picks}
    tracks = {track: sum(1 for job in picks if job["_digest_track"] == track)
              for track in ("academic", "forestry", "esg", "gis", "global")}

    assert len(picks) == 10
    assert "academic-0" not in ids
    assert "forestry-0" not in ids
    assert tracks == {"academic": 4, "forestry": 2, "esg": 2, "gis": 1, "global": 1}
    assert len({job["id"] for job in picks}) == 10


def test_digest_selector_caps_new_items_at_six():
    jobs, globals_ = _mixed_registry()
    # Eight academic/forestry roles are new; ESG, GIS and global slots are
    # older inventory so the selector can still fill a ten-item brief.
    for job in jobs:
        if job["id"].startswith(("academic-", "forestry-")):
            job["date_added"] = fh.ist_today().isoformat()
    for job in globals_:
        job["date_added"] = (fh.ist_today() - timedelta(days=9)).isoformat()

    picks = fh.select_daily_digest_jobs(jobs, globals_, {}, count=10)
    assert len(picks) == 10
    assert sum(1 for job in picks if job.get("_digest_new")) == 6


def test_digest_selector_recycles_oldest_when_everything_was_broadcast():
    jobs, globals_ = _mixed_registry()
    all_ids = [job["id"] for job in jobs + globals_]
    picks = fh.select_daily_digest_jobs(
        jobs, globals_, {"recent_telegram_job_ids": all_ids}, count=10
    )
    tracks = {track: sum(1 for job in picks if job["_digest_track"] == track)
              for track in ("academic", "forestry", "esg", "gis", "global")}
    assert len(picks) == 10
    assert len({job["id"] for job in picks}) == 10
    assert tracks == {"academic": 4, "forestry": 2, "esg": 2, "gis": 1, "global": 1}


def test_update_last_telegram_broadcast_records_rolling_40_ids(tmp_path):
    stats = tmp_path / "stats.json"
    stats.write_text(
        json.dumps({"recent_telegram_job_ids": [f"old-{i}" for i in range(35)]}),
        encoding="utf-8",
    )
    fh.update_last_telegram_broadcast(
        stats, "2026-10-22", job_ids=[f"new-{i}" for i in range(10)]
    )
    payload = json.loads(stats.read_text(encoding="utf-8"))
    recent = payload["recent_telegram_job_ids"]
    assert len(recent) == 40
    assert recent[-10:] == [f"new-{i}" for i in range(10)]
    assert payload["last_broadcast_job_ids"] == [f"new-{i}" for i in range(10)]
    assert "old-0" not in recent


def test_digest_heading_rotates_by_date():
    first = fh.digest_heading("2026-10-22")
    second = fh.digest_heading("2026-10-23")
    assert first != second
    assert "22 Oct 2026" in first
    assert "23 Oct 2026" in second


def test_write_digests_uses_rotation_and_badges(tmp_path):
    jobs, globals_ = _mixed_registry()
    digest = fh.write_digests(
        jobs,
        jobs[:2],
        fh.ist_today().isoformat(),
        tmp_path / "daily_digest.json",
        tmp_path / "whatsapp_digest.txt",
        stats={"recent_telegram_job_ids": ["academic-0"]},
        global_jobs=globals_,
    )
    assert digest["count"] == 10
    assert "academic-0" not in [job["id"] for job in digest["jobs"]]
    assert any(job["badge"] == "🆕" for job in digest["jobs"])
    assert all(job["url"].startswith(fh.SITE_BASE_URL + "/jobs/") for job in digest["jobs"])
    assert (tmp_path / "whatsapp_digest.txt").exists()
