#!/usr/bin/env python3
"""Telegram broadcast preflight and one-shot delivery check.

Usage:
    py scripts/verify_telegram.py                 # credentials + getMe/getChat
    py scripts/verify_telegram.py --send-test     # also posts a test message
    py scripts/verify_telegram.py --allow-missing # exit 0 when secrets unset

The script never prints the bot token. It logs the bot username, destination
title/type, HTTP status and Telegram message_id, which is enough to diagnose a
failed daily broadcast from a single GitHub Actions log line.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
API = "https://api.telegram.org/bot{token}/{method}"
TEST_MESSAGE = (
    "✅ Urban Forest Park broadcast check\n"
    "The daily jobs bot can reach this channel. Test sent at {stamp}."
)


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


def normalize_chat_id(raw: str) -> str:
    value = str(raw or "").strip()
    if not value:
        return ""
    if value.startswith("@") or value.startswith("-100"):
        return value
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{3,}", value):
        return "@" + value
    return value


def chat_candidates(raw: str) -> List[str]:
    value = normalize_chat_id(raw)
    out = [value] if value else []
    if re.fullmatch(r"\d{6,}", value):
        out.append("-100" + value)
    return out


def call(token: str, method: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    response = requests.post(
        API.format(token=token, method=method),
        json=payload or {},
        timeout=20,
    )
    body: Dict[str, Any]
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


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify Telegram bot + channel")
    parser.add_argument("--send-test", action="store_true")
    parser.add_argument("--allow-missing", action="store_true")
    args = parser.parse_args(argv)
    load_env()

    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    raw_chat = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    print("TELEGRAM_BOT_TOKEN:", "set" if token else "MISSING")
    print("TELEGRAM_CHAT_ID:", normalize_chat_id(raw_chat) if raw_chat else "MISSING")
    if not token or not raw_chat:
        if args.allow_missing:
            print("SKIP: Telegram secrets are not configured; broadcast is a safe no-op.")
            return 0
        print("FAIL: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
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

    destination_ok = False
    for chat_id in chat_candidates(raw_chat):
        chat = call(token, "getChat", {"chat_id": chat_id})
        result = chat.get("result") or {}
        print(
            "getChat:",
            chat_id,
            "OK" if chat["ok"] else "FAIL",
            "HTTP", chat["http"],
            "title=" + repr(result.get("title") or ""),
            "type=" + repr(result.get("type") or ""),
            chat["description"],
        )
        if not chat["ok"]:
            continue
        destination_ok = True
        if args.send_test:
            sent = call(
                token,
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": TEST_MESSAGE.format(
                        stamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                    ),
                },
            )
            result = sent.get("result") or {}
            print(
                "sendMessage:",
                "OK" if sent["ok"] else "FAIL",
                "HTTP", sent["http"],
                "message_id=" + str(result.get("message_id") or "-"),
                sent["description"],
            )
            if not sent["ok"]:
                return 1
        break

    stats_path = ROOT / "public" / "stats.json"
    if stats_path.exists():
        try:
            stats = json.loads(stats_path.read_text(encoding="utf-8"))
            print(
                "last_telegram_broadcast_date:",
                stats.get("last_telegram_broadcast_date") or "(none)",
            )
        except Exception:
            print("last_telegram_broadcast_date: unreadable stats.json")
    return 0 if destination_ok else 1


if __name__ == "__main__":
    sys.exit(main())
