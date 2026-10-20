# Official-link policy

**Golden rule:** a public listing may only link to the employer's own page.
Job boards, aggregators, news wrappers and "apply via" intermediaries are
discovery sources, never destinations.

This policy is enforced in code, not by convention:

| Layer | Code | Failure mode |
|---|---|---|
| Ingestion | `scripts/ingestion_gate.py` | candidate quarantined (or dropped) |
| Verification | `scripts/verify_link.py` | reason code + `status: "quarantined"` |
| Nightly recheck | `scripts/recheck_live_links.py` | 3 strikes → quarantine; 404 → archive |
| Data CI | `scripts/link_guard.py` | build fails |
| Built-site CI | `scripts/link_guard.py --dist dist` | build fails |
| Tests | `tests/` (pytest) | CI fails |

## 1. Registry is the source of truth

`public/employers.json` holds every approved employer with its own domains and
ATS hosts. A domain is added only after it has been fetched and confirmed to be
that organisation's own site. Never add job boards, aggregators, news sites,
`fundsforngos`, `indiawaterportal` or similar.

Adding an employer/domain:

1. Fetch the domain and confirm it belongs to the organisation (content, logo,
   contact page, registration details).
2. Add `domains` (primary first), `ats_hosts` if the employer uses a first-party
   ATS vanity host, and `website`.
3. If the site redirects to another host that belongs to the same organisation,
   record **both** hosts (`ias.unu.edu` → `unu.edu/ias`).
4. Run `python scripts/create_employers_registry.py` only if you also update its
   overrides — the generator rewrites the file.
5. Run `python -m pytest tests -q` and `python scripts/link_guard.py`.

Unverified or NXDOMAIN domains are not added. Records for those employers stay
quarantined until a working official domain is confirmed.

## 2. Ingestion gate (fail closed)

Order of checks in `gate_candidate`:

1. **P3 blocklist** — before any network call. Blocklisted hosts are dropped as
   leads (never written to a public field). Google News wrappers are unwrapped;
   if they cannot be resolved, the lead is dropped.
2. **Registry** — the organisation must match an approved employer. Unknown
   employers are quarantined with `EMPLOYER_NOT_IN_REGISTRY`.
3. **Fetch** — the URL is fetched with certificate verification on. TLS/DNS
   failures become `NEEDS_MANUAL_CHECK`; 404/410 become `HTTP_404`.
4. **Landing page** — generic careers pages and non-job content are rejected
   (`GENERIC_LANDING_PAGE`, `CONTENT_MISMATCH`).
5. **Content match** — the page must still be open and must contain every
   claim.

Only `verification_level == "page_verified"` may publish. Everything else is
quarantined; records are never deleted.

### Field-in-source rule

The LLM may restructure text but may not invent it. These fields must appear on
the fetched page, exactly or with fuzzy similarity ≥ 0.9:

- `clean_title`
- `deadline_or_window`
- `compensation_or_fellowship`
- `qualification_summary`
- every entry in `must_have_skills`

Numbers must match: `INR 60,000` is not accepted when the page says
`INR 99,000`. A missing field quarantines the record with
`FIELD_NOT_IN_SOURCE` and lists the failed fields in
`quarantine.fields`.

`apply_url`, `org_website` and `org_domain` are written **only** from the
verified final URL plus the registry — never from model output.

## 3. Quarantine semantics

A quarantined record keeps all of its data and gains:

```json
{
  "status": "quarantined",
  "status_before_quarantine": "active",
  "quarantine": {
    "reason_code": "BLOCKED_HOST",
    "final_url": "...",
    "final_host": "...",
    "http_status": 0,
    "entry_type": "posting",
    "host_class": "blocklisted",
    "error_detail": "...",
    "verified_at": "2026-10-20T00:00:00Z",
    "audit": "ingestion_gate"
  }
}
```

Quarantined records are:

- kept in `jobs.json` / `global_jobs.json` / `archive.json` (never deleted);
- hidden from cards, hubs, snapshot, sitemap, JSON-LD, email, WhatsApp/Telegram;
- never reactivated or aged into the archive automatically;
- excluded from stats and broadcasts.

`public/quarantine_report.json` groups them by employer and reason code with
fix hints.

## 4. Placement

| `entry_type` | Section |
|---|---|
| `posting` | Jobs |
| `careers_portal` | Careers portals |
| `award_portal` | Fellowships & programmes |
| `unknown` | hidden |

`unknown` records stay in the data but are hidden everywhere public.

## 5. Deduplication

Hash = `employer_id + normalised title + location + deadline`
(`sha256` prefix). No URL is part of the hash, so tracking parameters and
different wrappers cannot create duplicates.

## 6. Lifecycle

- Stated deadline → `valid_through` = deadline; archived when it passes.
- No deadline → 30-day cap from `date_added`, with `reverify_after` on day 15.
- Dead page (HTTP 404/SOFT_404) or "applications closed" → archive immediately.
- Any other failure → consecutive-failure counter; the 3rd consecutive failure
  quarantines the record.

## 7. Front end

- Cards, hubs, snapshot and sitemap link to dossier URLs (`/?job=<id>`) only.
- Dossier primary button: **Apply on official site**, with the apply hostname
  beside it and `rel="noopener noreferrer"`.
- Trust line: **Verified at source on &lt;date&gt;**.
- **Report a broken link** opens a pre-filled mailto to the registry.
- Archived records render **no outbound link**; the original apply host is plain
  text.
- JSON-LD never emits `applyUrl` for archived or quarantined records.
- Broadcast/email copy carries dossier URLs only (no `apply_url`,
  `org_website` or `org_domain`).

## 8. Running the checks

```bash
py -m pytest tests -q
py scripts/link_guard.py                 # data policy
npm run build
py scripts/link_guard.py --dist dist     # built site policy
py scripts/recheck_live_links.py         # nightly recheck (manual run)
```

Any violation fails the build. Fix the data or the registry; never bypass the
guard.

## 9. Remediation runbook

1. Open `public/quarantine_report.json` and pick an employer group.
2. Find the official posting page (not a board).
3. Confirm `entry_type` and re-verify the fields in the page text.
4. Correct `apply_url` / org identity.
5. Remove `quarantine` and `status_before_quarantine`, set `status: "active"`,
   and add `verification` metadata.
6. Run pytest + both guards before committing.

Bulk changes should go through `scripts/apply_quarantine.py` (idempotent) rather
than hand-edited status fields.
