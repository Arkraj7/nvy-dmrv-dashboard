import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import send_newsletter as nl


def _write(path: Path, records):
    path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")


def test_normalize_frequency_accepts_legacy_and_new_cadence():
    assert nl.normalize_frequency("3-day") == "3-days"
    assert nl.normalize_frequency("3-days") == "3-days"
    assert nl.normalize_frequency("weekly") == "weekly"
    assert nl.normalize_frequency("nonsense", default="") == ""


def test_coerce_recipients_skips_inactive_and_unsubscribed_records():
    records = [
        {"email": "active@b.in"},
        {"email": "inactive@b.in", "active": False},
        {"email": "gone@b.in", "status": "unsubscribed"},
        "plain@b.in",
    ]
    assert nl._coerce_recipients(records) == [
        {"email": "active@b.in"},
        {"email": "plain@b.in"},
    ]


def test_load_recipients_merges_file_env_and_smtp_user(tmp_path, monkeypatch):
    store = tmp_path / "subscribers.json"
    _write(
        store,
        [
            {"email": "file@b.in", "active": True},
            {"email": "inactive@b.in", "active": False},
        ],
    )
    monkeypatch.setattr(nl, "SUBSCRIBERS_FILE", store)
    monkeypatch.setenv("NEWSLETTER_SUBSCRIBERS", "env@b.in")
    monkeypatch.setenv("SMTP_USER", "owner@b.in")
    monkeypatch.delenv("NEWSLETTER_SUBSCRIBERS_CSV", raising=False)
    monkeypatch.delenv("NEWSLETTER_OWNER_EMAIL", raising=False)

    recipients, source = nl.load_recipients()

    assert [item["email"] for item in recipients] == [
        "file@b.in",
        "env@b.in",
        "owner@b.in",
    ]
    assert "data/subscribers.json" not in source  # temp path is outside the repo
    assert "NEWSLETTER_SUBSCRIBERS" in source
    assert "SMTP_USER" in source


def test_load_recipients_deduplicates_owner_and_file(tmp_path, monkeypatch):
    store = tmp_path / "subscribers.json"
    _write(store, [{"email": "owner@b.in"}])
    monkeypatch.setattr(nl, "SUBSCRIBERS_FILE", store)
    monkeypatch.delenv("NEWSLETTER_SUBSCRIBERS", raising=False)
    monkeypatch.delenv("NEWSLETTER_SUBSCRIBERS_CSV", raising=False)
    monkeypatch.setenv("SMTP_USER", "owner@b.in")

    recipients, _ = nl.load_recipients()
    assert recipients == [{"email": "owner@b.in"}]


def test_upsert_subscriber_preserves_welcome_marker_and_updates_preferences(tmp_path, monkeypatch):
    store = tmp_path / "subscribers.json"
    _write(
        store,
        [
            {
                "email": "person@b.in",
                "frequency": "3-day",
                "sector": "all",
                "welcome_sent": True,
                "welcome_sent_at": "2026-01-01T00:00:00+00:00",
            }
        ],
    )
    monkeypatch.setattr(nl, "SUBSCRIBERS_FILE", store)

    record = nl.upsert_subscriber("Person@B.in", "weekly", "corporate-esg")

    assert record["email"] == "person@b.in"
    assert record["frequency"] == "weekly"
    assert record["sector"] == "corporate-esg"
    assert record["welcome_sent"] is True
    assert record["welcome_sent_at"] == "2026-01-01T00:00:00+00:00"
    assert record["active"] is True


def test_upsert_subscriber_adds_new_record_without_duplicate(tmp_path, monkeypatch):
    store = tmp_path / "subscribers.json"
    _write(store, [])
    monkeypatch.setattr(nl, "SUBSCRIBERS_FILE", store)

    first = nl.upsert_subscriber("new@b.in", "3-days", "academic")
    second = nl.upsert_subscriber("NEW@b.in", "weekly", "forestry-gis")

    records = json.loads(store.read_text(encoding="utf-8"))
    assert len(records) == 1
    assert first["email"] == "new@b.in"
    assert second["frequency"] == "weekly"
    assert records[0]["sector"] == "forestry-gis"
    assert records[0]["welcome_sent"] is False


def test_mark_welcome_sent_writes_marker(tmp_path, monkeypatch):
    store = tmp_path / "subscribers.json"
    _write(store, [{"email": "person@b.in", "welcome_sent": False}])
    monkeypatch.setattr(nl, "SUBSCRIBERS_FILE", store)

    nl.mark_welcome_sent("PERSON@b.in")

    records = json.loads(store.read_text(encoding="utf-8"))
    assert records[0]["welcome_sent"] is True
    assert records[0]["welcome_sent_at"]


def test_welcome_command_persists_even_without_email_credentials(tmp_path, monkeypatch):
    store = tmp_path / "subscribers.json"
    preview = tmp_path / "welcome.html"
    _write(store, [])
    monkeypatch.setattr(nl, "WELCOME_PREVIEW", preview)
    monkeypatch.setattr(nl, "SUBSCRIBERS_FILE", store)
    for name in (
        "RESEND_API_KEY",
        "BREVO_API_KEY",
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "NEWSLETTER_FROM_EMAIL",
        "NEWSLETTER_OWNER_EMAIL",
    ):
        monkeypatch.delenv(name, raising=False)

    rc = nl.main(
        [
            "--welcome",
            "welcome-test@b.in",
            "--frequency",
            "3-days",
            "--sector",
            "all",
            "--subscribers",
            str(store),
        ]
    )

    assert rc == 0
    assert preview.exists()
    records = json.loads(store.read_text(encoding="utf-8"))
    assert records[0]["email"] == "welcome-test@b.in"
    assert records[0]["frequency"] == "3-days"
    assert records[0]["welcome_sent"] is False
