import json
import sys
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
