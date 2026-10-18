#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backfill bilingual (Hindi) metadata for the Urban Forest Park registry.

Every listing in public/jobs.json and public/archive.json carries two
bilingual fields (introduced with the हिंदी interface):

  * title_hi   - formal Hindi job title (Devanagari script; organisation
                 names and acronyms such as JRF / GIS / ESG / PhD stay in
                 Latin script)
  * summary_hi - two formal Hindi sentences covering the role and its
                 eligibility

The daily pipeline produces these fields for NEW listings (see the Gemini
prompt in scripts/fetch_and_humanize.py). This script backfills or repairs
EXISTING records.

Modes
-----
* Default: batches of listings are translated with Gemini (GEMINI_API_KEY,
  read from the environment or a local .env file). Any batch that fails
  quota / SDK / parsing is filled with the deterministic template instead,
  so the script never leaves a record without Hindi metadata.
* ``--deterministic``: skips the API entirely and uses the deterministic
  glossary + template (instant, zero quota).

The script is idempotent: records that already carry both fields are
skipped unless ``--force`` is given.

Usage
-----
    python scripts/backfill_hindi.py                    # AI + fallback
    python scripts/backfill_hindi.py --deterministic    # no API calls
    python scripts/backfill_hindi.py --limit 20
    python scripts/backfill_hindi.py --files public/jobs.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FILES = ["public/jobs.json", "public/archive.json"]

# Reuse the pipeline's .env loader and model order when importable (all of
# its heavy dependencies are imported defensively, so this is safe even in
# a bare environment).
_PIPELINE = None
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import fetch_and_humanize as _PIPELINE  # type: ignore
except Exception:  # pragma: no cover - bare environments
    _PIPELINE = None

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
BATCH_SIZE = 10
MAX_SUMMARY = 400


def log(message: str) -> None:
    print(f"[backfill-hindi] {message}", flush=True)


def squash(value: Any) -> str:
    return " ".join(str(value or "").split())


# ---------------------------------------------------------------------------
# Deterministic mode: glossary title translation + structured summary
# ---------------------------------------------------------------------------
# Longest phrases first so "research associate" wins over "research".
_ROLE_GLOSSARY: List[Tuple[str, str]] = [
    ("co-founder with investment", "सह-संस्थापक (निवेश के साथ)"),
    ("co-founder", "सह-संस्थापक"),
    ("investment", "निवेश"),
    ("junior research fellow", "जूनियर रिसर्च फेलो"),
    ("senior research fellow", "सीनियर रिसर्च फेलो"),
    ("research associate", "रिसर्च एसोसिएट"),
    ("research fellow", "रिसर्च फेलो"),
    ("research assistant", "रिसर्च असिस्टेंट"),
    ("project associate", "प्रोजेक्ट एसोसिएट"),
    ("project assistant", "प्रोजेक्ट असिस्टेंट"),
    ("project scientist", "प्रोजेक्ट वैज्ञानिक"),
    ("project coordinator", "प्रोजेक्ट समन्वयक"),
    ("project manager", "प्रोजेक्ट प्रबंधक"),
    ("programme manager", "कार्यक्रम प्रबंधक"),
    ("program manager", "कार्यक्रम प्रबंधक"),
    ("programme associate", "कार्यक्रम एसोसिएट"),
    ("program associate", "कार्यक्रम एसोसिएट"),
    ("programme officer", "कार्यक्रम अधिकारी"),
    ("program officer", "कार्यक्रम अधिकारी"),
    ("programme coordinator", "कार्यक्रम समन्वयक"),
    ("program coordinator", "कार्यक्रम समन्वयक"),
    ("young professional", "यंग प्रोफेशनल"),
    ("team member", "टीम सदस्य"),
    ("team lead", "टीम लीड"),
    ("technical expert", "तकनीकी विशेषज्ञ"),
    ("sector expert", "क्षेत्र विशेषज्ञ"),
    ("senior consultant", "वरिष्ठ सलाहकार"),
    ("senior analyst", "वरिष्ठ विश्लेषक"),
    ("senior associate", "वरिष्ठ एसोसिएट"),
    ("senior manager", "वरिष्ठ प्रबंधक"),
    ("senior engineer", "वरिष्ठ अभियंता"),
    ("senior scientist", "वरिष्ठ वैज्ञानिक"),
    ("senior specialist", "वरिष्ठ विशेषज्ञ"),
    ("doctoral fellowship", "डॉक्टोरल फेलोशिप"),
    ("doctoral student", "डॉक्टोरल शोध छात्र"),
    ("postdoctoral fellow", "पोस्टडॉक्टोरल फेलो"),
    ("postdoctoral fellowship", "पोस्टडॉक्टोरल फेलोशिप"),
    ("management trainee", "प्रबंधन प्रशिक्षु"),
    ("business development", "व्यवसाय विकास"),
    ("quality assurance", "गुणवत्ता आश्वासन"),
    ("climate change", "जलवायु परिवर्तन"),
    ("climate", "जलवायु"),
    ("environmental", "पर्यावरणीय"),
    ("environment", "पर्यावरण"),
    ("sustainability", "स्थिरता"),
    ("sustainable", "संधारणीय"),
    ("forestry", "वानिकी"),
    ("forest", "वन"),
    ("wildlife", "वन्यजीव"),
    ("afforestation", "वृक्षारोपण"),
    ("biodiversity", "जैवविविधता"),
    ("conservation", "संरक्षण"),
    ("ecology", "पारिस्थितिकी"),
    ("ecological", "पारिस्थितिकी"),
    ("geospatial", "भू-स्थानिक"),
    ("remote sensing", "रिमोट सेंसिंग"),
    ("mapping", "मानचित्रण"),
    ("carbon", "कार्बन"),
    ("renewable energy", "नवीकरणीय ऊर्जा"),
    ("energy", "ऊर्जा"),
    ("emissions", "उत्सर्जन"),
    ("water", "जल"),
    ("agriculture", "कृषि"),
    ("policy", "नीति"),
    ("governance", "शासन"),
    ("planning", "योजना"),
    ("development", "विकास"),
    ("research", "अनुसंधान"),
    ("analyst", "विश्लेषक"),
    ("analysis", "विश्लेषण"),
    ("scientist", "वैज्ञानिक"),
    ("engineer", "अभियंता"),
    ("engineering", "अभियांत्रिकी"),
    ("technician", "तकनीशियन"),
    ("consultant", "सलाहकार"),
    ("advisor", "सलाहकार"),
    ("adviser", "सलाहकार"),
    ("coordinator", "समन्वयक"),
    ("specialist", "विशेषज्ञ"),
    ("officer", "अधिकारी"),
    ("manager", "प्रबंधक"),
    ("management", "प्रबंधन"),
    ("associate", "एसोसिएट"),
    ("assistant", "सहायक"),
    ("trainee", "प्रशिक्षु"),
    ("internship", "इंटर्नशिप"),
    ("intern", "इंटर्न"),
    ("fellow", "फेलो"),
    ("fellowship", "फेलोशिप"),
    ("faculty", "संकाय"),
    ("professor", "प्रोफेसर"),
    ("dean", "डीन"),
    ("director", "निदेशक"),
    ("deputy", "उप"),
    ("head", "प्रमुख"),
    ("lead", "लीड"),
    ("executive", "कार्यकारी"),
    ("operations", "संचालन"),
    ("compliance", "अनुपालन"),
    ("auditor", "लेखा-परीक्षक"),
    ("risk", "जोखिम"),
    ("social", "सामाजिक"),
    ("urban", "शहरी"),
    ("rural", "ग्रामीण"),
    ("green", "हरित"),
    ("survey", "सर्वेक्षण"),
    ("data", "डेटा"),
]

_ROLE_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE), hindi)
    for word, hindi in _ROLE_GLOSSARY
]

_POSITION_TYPE_HI: Dict[str, str] = {
    "JRF / SRF": "जूनियर/सीनियर रिसर्च फेलोशिप (JRF / SRF)",
    "PhD / Doctoral Fellowship": "PhD / डॉक्टोरल फेलोशिप",
    "Project Associate / Research Associate": "प्रोजेक्ट एसोसिएट / रिसर्च एसोसिएट",
    "Young Professional / Consultant (Contractual)": "यंग प्रोफेशनल / परामर्शदाता (संविदा)",
    "Faculty / Academic": "शैक्षणिक / फैकल्टी पद",
    "Full-Time Corporate / NGO": "कॉर्पोरेट / गैर-सरकारी संगठन में पूर्णकालिक पद",
    "Fellowship / Internship": "फेलोशिप / इंटर्नशिप",
}


def deterministic_title(job: Dict[str, Any]) -> str:
    base = squash(job.get("clean_title"))
    org = squash(job.get("organization"))
    translated = base
    for pattern, hindi in _ROLE_PATTERNS:
        translated = pattern.sub(hindi, translated)
    if org and org.lower() not in base.lower():
        return f"{translated} — {org}"
    return translated


def deterministic_summary(job: Dict[str, Any]) -> str:
    org = squash(job.get("organization")) or "संबंधित संस्थान"
    state = squash(job.get("state")) or "भारत"
    position_type = squash(job.get("position_type")) or "नियुक्ति"
    type_hi = _POSITION_TYPE_HI.get(position_type, position_type)
    qualification = squash(job.get("qualification_summary"))
    first = f"यह {type_hi} {org} ({state}) हेतु उपलब्ध है।"
    if qualification:
        second = (
            f"आवश्यक योग्यता: {qualification}। आवेदन एवं पात्रता की पूर्ण "
            "जानकारी हेतु आधिकारिक पोर्टल अवश्य देखें।"
        )
    else:
        second = (
            "पात्रता एवं आवेदन प्रक्रिया की पूर्ण जानकारी हेतु आधिकारिक "
            "पोर्टल अवश्य देखें।"
        )
    return f"{first} {second}"


# ---------------------------------------------------------------------------
# AI mode
# ---------------------------------------------------------------------------
def _ai_prompt(batch: List[Dict[str, Any]]) -> str:
    compact = [
        {
            "id": job.get("id", ""),
            "title": squash(job.get("clean_title")),
            "organization": squash(job.get("organization")),
            "state": squash(job.get("state")),
            "position_type": squash(job.get("position_type")),
            "qualification": squash(job.get("qualification_summary")),
            "summary": squash(job.get("role_summary"))[:320],
        }
        for job in batch
    ]
    return (
        "You are a professional Hindi (Devanagari) localisation editor for "
        "India's environmental, forestry, JRF and ESG jobs registry.\n"
        "For EVERY listing below produce:\n"
        "  - title_hi: the job title in formal Hindi (Devanagari script) as "
        "printed in Indian government recruitment notices. Keep the "
        "organisation name in its original Latin form and keep acronyms "
        "(JRF, SRF, GIS, ESG, PhD, BRSR, IIT, IISc, IIFM, WII, QGIS, EIA) "
        "in Latin script. Never romanise English words into Devanagari "
        "spellings of English words where a natural Hindi term exists.\n"
        "  - summary_hi: exactly 2 formal Hindi sentences covering the role, "
        "the organisation, the state/location and the key eligibility. "
        "Keep technical terms/acronyms in Latin script.\n"
        "Return ONLY a JSON array with one object per listing, same order:\n"
        '[{"id": "<id>", "title_hi": "...", "summary_hi": "..."}, ...]\n\n'
        "Listings:\n" + json.dumps(compact, ensure_ascii=False, indent=1)
    )


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text


def _valid_result(item: Dict[str, Any]) -> bool:
    title = squash(item.get("title_hi"))
    summary = squash(item.get("summary_hi"))
    if not title or not summary:
        return False
    if not DEVANAGARI_RE.search(title) or not DEVANAGARI_RE.search(summary):
        return False
    return len(summary) <= MAX_SUMMARY or True


def _try_ai_batch(
    client: Any, models: List[str], batch: List[Dict[str, Any]]
) -> Optional[Dict[str, Dict[str, str]]]:
    prompt = _ai_prompt(batch)
    for model in models:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config={"response_mime_type": "application/json", "temperature": 0.3},
            )
            payload = _strip_fences(response.text or "")
            data = json.loads(payload)
            if isinstance(data, dict):
                data = data.get("jobs") or data.get("results") or data.get("listings") or []
            if not isinstance(data, list):
                raise ValueError("model returned a non-list payload")
            out: Dict[str, Dict[str, str]] = {}
            for item in data:
                if isinstance(item, dict) and _valid_result(item):
                    out[squash(item.get("id"))] = {
                        "title_hi": squash(item.get("title_hi")),
                        "summary_hi": squash(item.get("summary_hi")),
                    }
            if out:
                return out
        except Exception as exc:  # noqa: BLE001 - any SDK/quota error falls through
            log(f"model {model} failed: {exc}")
            continue
    return None


def _make_client() -> Tuple[Any, List[str]]:
    try:
        from google import genai  # type: ignore
    except Exception:
        return None, []
    api_key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if not api_key:
        return None, []
    models: List[str] = []
    override = (os.environ.get("GEMINI_MODEL") or "").strip()
    if override:
        models.append(override)
    if _PIPELINE is not None and getattr(_PIPELINE, "MODEL_CANDIDATES", None):
        models.extend(list(_PIPELINE.MODEL_CANDIDATES))
    if not models:
        models = ["gemini-2.5-flash", "gemini-2.0-flash"]
    seen = set()
    models = [m for m in models if m and not (m in seen or seen.add(m))]
    return genai.Client(api_key=api_key), models


# ---------------------------------------------------------------------------
# Record maintenance
# ---------------------------------------------------------------------------
def needs_backfill(job: Dict[str, Any], force: bool) -> bool:
    if force:
        return True
    return not squash(job.get("title_hi")) or not squash(job.get("summary_hi"))


def _insert_after(job: Dict[str, Any], anchor: str, key: str, value: str) -> Dict[str, Any]:
    if key in job:
        job[key] = value
        return job
    rebuilt: Dict[str, Any] = {}
    inserted = False
    for name, val in job.items():
        rebuilt[name] = val
        if name == anchor:
            rebuilt[key] = value
            inserted = True
    if not inserted:
        rebuilt[key] = value
    return rebuilt


def backfill_file(path: Path, force: bool, limit: Optional[int], use_ai: bool) -> int:
    if not path.exists():
        log(f"{path} not found - skipping")
        return 0
    jobs = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(jobs, list):
        log(f"{path} does not contain a list - skipping")
        return 0

    targets = [j for j in jobs if isinstance(j, dict) and needs_backfill(j, force)]
    if limit is not None:
        targets = targets[:limit]
    if not targets:
        log(f"{path.name}: all {len(jobs)} record(s) already carry Hindi metadata.")
        return 0

    log(f"{path.name}: backfilling {len(targets)} of {len(jobs)} record(s).")

    client = None
    models: List[str] = []
    if use_ai:
        client, models = _make_client()
    if use_ai and client is None:
        log("GEMINI_API_KEY / google-genai unavailable - using deterministic mode.")

    filled: Dict[str, Dict[str, str]] = {}
    ai_batches = 0
    if client is not None:
        for start in range(0, len(targets), BATCH_SIZE):
            batch = targets[start : start + BATCH_SIZE]
            result = _try_ai_batch(client, models, batch)
            if result:
                filled.update(result)
                ai_batches += 1
            else:
                log(
                    f"batch {start // BATCH_SIZE + 1} fell back to deterministic "
                    "translation."
                )

    ai_hits = 0
    det_hits = 0
    for job in targets:
        job_id = squash(job.get("id"))
        result = filled.get(job_id)
        if result:
            title_hi = result["title_hi"]
            summary_hi = result["summary_hi"]
            ai_hits += 1
        else:
            title_hi = deterministic_title(job)
            summary_hi = deterministic_summary(job)
            det_hits += 1
        record = _insert_after(job, "clean_title", "title_hi", title_hi)
        record = _insert_after(record, "role_summary", "summary_hi", summary_hi)
        job.clear()
        job.update(record)

    path.write_text(
        json.dumps(jobs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    log(
        f"{path.name}: wrote {len(targets)} bilingual record(s) "
        f"(AI: {ai_hits}, deterministic: {det_hits}, AI batches: {ai_batches})."
    )
    return len(targets)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--files", nargs="*", default=DEFAULT_FILES,
                        help="JSON files to process (default: jobs + archive).")
    parser.add_argument("--deterministic", action="store_true",
                        help="skip Gemini entirely; use the glossary/template.")
    parser.add_argument("--force", action="store_true",
                        help="regenerate fields even when already present.")
    parser.add_argument("--limit", type=int, default=None,
                        help="cap the number of records processed per file.")
    args = parser.parse_args(argv)

    if _PIPELINE is not None and hasattr(_PIPELINE, "load_env_file"):
        _PIPELINE.load_env_file()
    else:  # minimal fallback .env loader
        for candidate in (Path(".env"), REPO_ROOT / ".env"):
            if candidate.exists():
                for line in candidate.read_text(encoding="utf-8-sig").splitlines():
                    if "=" in line and not line.strip().startswith("#"):
                        key, _, value = line.partition("=")
                        os.environ.setdefault(key.strip(), value.strip())
                break

    total = 0
    for rel in args.files:
        path = Path(rel)
        if not path.is_absolute():
            path = REPO_ROOT / rel
        total += backfill_file(
            path,
            force=args.force,
            limit=args.limit,
            use_ai=not args.deterministic,
        )
    log(f"done. {total} record(s) updated. ({date.today().isoformat()})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
