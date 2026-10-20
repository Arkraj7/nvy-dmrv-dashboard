# Direct-link policy (v2, 20 October 2026)

**Golden rule:** show direct job links from any platform. Only remove links
that are **dead** or **not direct**. The platform list is editable config, not
code.

Config: `public/link_policy.json`
Code: `scripts/link_policy.py`, `scripts/verify_link.py`,
`scripts/ingestion_gate.py`, `scripts/link_guard.py`

## What is allowed

- Any employer domain.
- Allow-listed platforms: LinkedIn, Indeed, Naukri, FreeJobAlert, Foundit,
  Shine, TimesJobs, Internshala, Apna, Unstop, Glassdoor, Monster,
  Freshersworld, ReliefWeb, IndiaBioscience (edit `platforms` in the JSON to
  add more).
- Platform entries are accepted through **URL-pattern validation** only. Do not
  fetch or scrape LinkedIn, Indeed or Naukri; they block bots.

## Direct vs not direct

A link is DIRECT only when it points at one specific job or notice page:

| Platform | Direct pattern |
|---|---|
| LinkedIn | `/jobs/view/<id>` |
| Indeed | `viewjob?jk=<id>` |
| Naukri | `job-listings-...-<id>` |
| FreeJobAlert / others | the specific job or notice page |

Home pages, search/listing pages, `/careers` or `/recruitment` roots, category
pages and section pages are **NOT_DIRECT**. They are still shown, but in the
"Careers portals" section rather than as individual jobs.

## Always remove

- `news.google.com` and other news wrappers: resolve to the publisher article
  or job page first; drop only if unresolvable.
- URL shorteners: resolve first.
- Tracking parameters: `utm_*`, `fbclid`, `gclid`, `ref`, etc.
- Dead links.

## Dead vs unknown

**DEAD** (removed / archived, never deleted): HTTP 404 or 410, a confirmed
soft-404, or page text that says the job is closed or expired.

**UNKNOWN** (kept visible): 403, 429, 999, 401, timeouts, TLS errors, DNS
filtering, SSRF-guard blocks, login walls. Never fail closed on UNKNOWN.
Records are archived only after three consecutive confirmed-dead nightly
checks.

## Reason codes

`OK`, `DEAD_LINK`, `NOT_DIRECT_LINK`, `UNRESOLVED_WRAPPER`, `UNKNOWN_KEEP`.

## Layers

| Layer | Code | Behaviour |
|---|---|---|
| Ingestion | `scripts/ingestion_gate.py` | keeps UNKNOWN, archives DEAD, tags portals |
| Verification | `scripts/verify_link.py` | reason code + entry type |
| Restore/audit | `scripts/apply_link_policy.py` | re-applies policy to all records |
| Nightly recheck | `scripts/recheck_live_links.py` | 3 strikes → archive |
| Data CI | `scripts/link_guard.py` | fails build on wrapper/shortener or bad tagging |
| Built-site CI | `scripts/link_guard.py --dist dist` | fails on wrappers/shorteners/quarantine leaks |
| Tests | `tests/` | fail CI on policy regressions |

## Ingestion rules

1. Resolve wrappers/shorteners; drop only if unresolved.
2. Run `verify_link` (fail-open on UNKNOWN).
3. DEAD → archive with `date_archived`; data is preserved.
4. NOT_DIRECT → publish as `entry_type: "careers_portal"`.
5. Everything else → `entry_type: "posting"` (or `award_portal`).
6. If the page was fetched, blank any title/deadline/compensation/
   qualification/skill the model invented instead of generating it.
7. Dedupe hash: employer + normalised title + location + deadline (tracking
   stripped).
8. Expiry: archive on the deadline; no deadline → 30 days with a day-15
   re-check.

The employer registry (`public/employers.json`) now supplies naming and
domains only. A missing registry entry never blocks publishing.

## Front end

- Button: "Apply", or "Apply on <platform>", with the destination hostname and
  `rel="noopener noreferrer"`.
- Archived records render no outbound link; the apply host is plain text.
- "Report a broken link" stays.
- No listing is hidden because of its host.
- Dispatch copy says "every 72 hours".

## SSRF and TLS

Private-IP checks stay on for every fetch. Certificate verification stays on.
`verify=False` is forbidden.
