# AGENTS.md

Guidance for coding agents working in this repository.

## What this repo is

Astro site (`src/`, `public/`) plus a Python daily pipeline (`scripts/`) that
publishes verified green-sector jobs for `urbanforestpark.com`. The site root is
`public/`; `npm run build` copies it into `dist/`, and Cloudflare Pages serves
extensionless URLs.

## Non-negotiable link policy

Read `docs/LINK_POLICY.md` before touching job data, the pipeline, the front end
or the sitemap. Short version:

- Employer-owned pages only. No job boards, aggregators or news wrappers in any
  public field.
- The ingestion gate verifies every candidate at source before writing. It is
  fail-closed; do not bypass, weaken or "temporarily disable" it.
- Quarantined records (`status: "quarantined"`) keep their data but are hidden
  from the site, hubs, snapshot, sitemap, JSON-LD, email and broadcasts. Never
  delete them and never reactivate them automatically.
- `apply_url`, `org_website`, `org_domain` come from the verified fetch +
  `public/employers.json`, not from model output.
- Do not edit `public/employers.json` domains without fetching the domain and
  confirming it belongs to that organisation. NXDOMAIN/unverifiable domains stay
  out.

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
