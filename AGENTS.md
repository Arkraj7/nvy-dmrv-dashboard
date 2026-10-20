# AGENTS.md

Guidance for coding agents working in this repository.

## What this repo is

Astro site (`src/`, `public/`) plus a Python daily pipeline (`scripts/`) that
publishes verified green-sector jobs for `urbanforestpark.com`. The site root is
`public/`; `npm run build` copies it into `dist/`, and Cloudflare Pages serves
extensionless URLs.

## Non-negotiable link policy

Read `docs/LINK_POLICY.md` and `public/link_policy.json` before touching job
data, the pipeline, the front end or the sitemap. Short version:

- Show direct job links from any platform (employer sites, LinkedIn, Indeed,
  Naukri, FreeJobAlert, Foundit, Shine and peers). The platform list is config.
- A link is direct only when it points at one specific job/notice page. Home,
  search, listing, category and section roots are "Careers portals".
- Remove only dead links (404/410, confirmed soft-404, closed/expired text) or
  unresolvable news wrappers/shorteners. Archive dead records; never delete.
- UNKNOWN is not dead. 403, 429, 999, timeouts and TLS errors keep the listing.
  Never fetch or scrape LinkedIn, Indeed or Naukri; validate URL patterns only.
- `apply_url` comes from the candidate/source, never from model output. Blank
  invented title, deadline, pay, qualification or skill fields.
- The employer registry supplies naming/domains only; a missing entry never
  blocks publishing.
- Front end: "Apply" / "Apply on <platform>" + hostname, noopener noreferrer,
  "Report a broken link", archived records render no outbound link.
- Keep SSRF checks and certificate verification on. `verify=False` is forbidden.

## Commands (Windows)

```powershell
py -m pytest tests -q
py scripts/link_guard.py
npm run build
py scripts/link_guard.py --dist dist
py scripts/fetch_and_humanize.py --no-broadcast   # daily pipeline, hold messages
py scripts/recheck_live_links.py                  # nightly link recheck
```

`pip` needs `REQUESTS_CA_BUNDLE` pointing at certifi on this machine:

```powershell
cmd /c "set REQUESTS_CA_BUNDLE=C:\Users\arkra\AppData\Local\Programs\Python\Python312\Lib\site-packages\certifi\cacert.pem && py -m pip install -r scripts/requirements.txt"
```

## Data files

- `public/jobs.json` — India active (including quarantined review queue)
- `public/global_jobs.json` — global active (including quarantine)
- `public/archive.json`, `public/global_archive.json` — archived records
- `public/stats.json` — telemetry (published records only)
- `public/quarantine_report.json` — grouped quarantine report
- `scripts/link_recheck_state.json` — nightly failure counters (committed by CI)

Do not hand-edit status fields in bulk; use `scripts/apply_quarantine.py`.
Preserve `status`, `status_before_quarantine` and `quarantine` blocks when
normalising records.

## Gotchas

- Use `py`, not `python`, on this machine.
- `.env` holds local secrets; never print or commit values.
- Cloudflare 308s `.html` URLs — canonicals, links and sitemaps use extensionless
  paths.
- `normalize_job_fields`/`finalize_org_identity` must not overwrite identity on
  records carrying a `verification` block.
- A build or test failure is a stop condition: fix it or report it; do not ship
  around it.
