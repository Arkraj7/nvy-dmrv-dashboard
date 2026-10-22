import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_seo_pages as seo


def _job(job_id, title, date_added="2026-10-20"):
    return {
        "id": job_id,
        "clean_title": title,
        "organization": "Test Institute & Co",
        "city": "Dehradun",
        "state": "Uttarakhand",
        "category": "Academic, JRF, SRF & PhD Positions",
        "position_type": "JRF",
        "date_added": date_added,
        "qualification_summary": "M.Sc. <Forestry> & NET/GATE",
        "compensation_or_fellowship": "Rs. 37,000/month",
    }


def test_rss_feed_is_well_formed_and_escaped():
    xml = seo.build_rss_feed(
        [_job("a&b", "JRF - Forest & Ecology")],
        "Test feed",
        "A & B description",
        "/feed.xml",
    )
    root = ET.fromstring(xml)
    assert root.tag == "rss"
    channel = root.find("channel")
    assert channel is not None
    item = channel.find("item")
    assert item is not None
    assert "Forest & Ecology" in item.findtext("title")
    assert item.findtext("link") == "https://www.urbanforestpark.com/jobs/a-b"
    assert "Forest &amp; Ecology" in xml


def test_excerpt_prefers_a_complete_sentence():
    text = "First sentence. " + ("Second sentence with many words. " * 20)
    assert seo.excerpt(text, 120) == "First sentence."
    fallback = seo.excerpt("word " * 100, 40)
    assert fallback.endswith("\u2026")
    assert not fallback.endswith(".\u2026")


def test_inject_feed_links_adds_alternate_and_footer(tmp_path):
    page = tmp_path / "index.html"
    page.write_text(
        "<html><head><title>x</title></head><body><footer>end</footer></body></html>",
        encoding="utf-8",
    )
    changed = seo.inject_feed_links(tmp_path)
    text = page.read_text(encoding="utf-8")
    assert changed == 1
    assert text.count("application/rss+xml") == 2
    assert "/feed.xml" in text and "/jrf-feed.xml" in text
    assert text.count("footer-rss") == 1
