#!/usr/bin/env python3
"""Register the Urban Forest Park Telegram intake webhook.

Usage:
    py scripts/setup_telegram_webhook.py
    py scripts/setup_telegram_webhook.py --url https://www.urbanforestpark.com/api/telegram
    py scripts/setup_telegram_webhook.py --delete

Environment:
    TELEGRAM_BOT_TOKEN or TELEGRAM_INBOX_BOT_TOKEN
    TELEGRAM_WEBHOOK_URL      optional; defaults to the production intake route
    TELEGRAM_WEBHOOK_SECRET   optional Telegram secret_token header value

The script never prints the bot token. It prints the bot username and the
registered webhook URL so the result can be verified from CI or a terminal.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict

import requests

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
DEFAULT_URL = "https://www.urbanforestpark.com/api/telegram"
API = "https://api.telegram.org/bot{token}/{method}"


def load_env(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def call(token: str, method: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    response = requests.post(
        API.format(token=token, method=method),
        json=payload or {},
        timeout=30,
    )
    try:
        body = response.json()
    except Exception:
        body = {}
    return {
        "http": response.status_code,
        "ok": bool(body.get("ok")),
        "result": body.get("result") or {},
        "description": str(body.get("description") or response.text or "")[:300],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Register the Telegram intake webhook")
    parser.add_argument("--url", default="")
    parser.add_argument("--secret", default="")
    parser.add_argument("--delete", action="store_true")
    args = parser.parse_args(argv)
    load_env()

    token = (
        os.environ.get("TELEGRAM_INBOX_BOT_TOKEN")
        or os.environ.get("TELEGRAM_BOT_TOKEN")
        or ""
    ).strip()
    if not token:
        print("FAIL: set TELEGRAM_INBOX_BOT_TOKEN (or TELEGRAM_BOT_TOKEN).")
        return 2

    me = call(token, "getMe")
    print(
        "getMe:",
        "OK" if me["ok"] else "FAIL",
        "HTTP", me["http"],
        "bot=@" + str((me.get("result") or {}).get("username") or "?"),
        me["description"],
    )
    if not me["ok"]:
        return 1

    if args.delete:
        removed = call(token, "deleteWebhook", {"drop_pending_updates": False})
        print("deleteWebhook:", "OK" if removed["ok"] else "FAIL", "HTTP", removed["http"], removed["description"])
        return 0 if removed["ok"] else 1

    url = (args.url or os.environ.get("TELEGRAM_WEBHOOK_URL") or DEFAULT_URL).strip()
    if not url.startswith("https://"):
        print("FAIL: webhook URL must start with https://")
        return 2
    secret = (args.secret or os.environ.get("TELEGRAM_WEBHOOK_SECRET") or "").strip()
    payload: Dict[str, Any] = {
        "url": url,
        "allowed_updates": ["message", "edited_message"],
        "drop_pending_updates": False,
    }
    if secret:
        payload["secret_token"] = secret
    registered = call(token, "setWebhook", payload)
    print("setWebhook:", "OK" if registered["ok"] else "FAIL", "HTTP", registered["http"], registered["description"])
    if not registered["ok"]:
        return 1

    info = call(token, "getWebhookInfo")
    result = info.get("result") or {}
    print("webhook_url:", result.get("url") or "(none)")
    print("pending_update_count:", result.get("pending_update_count"))
    print("last_error_message:", result.get("last_error_message") or "(none)")
    return 0 if info["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
