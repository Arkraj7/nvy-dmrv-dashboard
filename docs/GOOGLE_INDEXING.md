# Google indexing automation

## What can and cannot be automated

Google has **no public API** for the Search Console **“Request indexing”** button.
The 51 hub URLs cannot be pushed through an API.

Two supported routes are automated here:

| Route | What it covers | API |
|---|---|---|
| Sitemap submission | Every URL in `public/sitemap.xml`, including all hubs and job pages | Search Console API `sitemaps.submit` |
| Job URL notification | `/jobs/<id>` pages only (they carry `JobPosting` JSON-LD) | Indexing API `urlNotifications.publish` |

Do **not** send hub pages through the Indexing API. Google accepts that API only
for `JobPosting` and `BroadcastEvent` pages. The sitemap is the supported route
for hubs.

IndexNow (Bing/Yandex) is already handled by `scripts/ping_search_engines.py`.
Google does not use IndexNow.

## One-time setup

1. Open [Google Cloud Console](https://console.cloud.google.com/) and create or
   select a project.
2. **APIs & Services → Library** → enable:
   - **Indexing API**
   - **Google Search Console API**
3. **IAM & Admin → Service Accounts** → create a service account
   (for example `ufp-indexing`) → **Keys → Add key → JSON** → download it.
4. Open [Google Search Console](https://search.google.com/search-console) for
   `https://www.urbanforestpark.com/`:
   - **Settings → Users and permissions → Add user**
   - Paste the service-account email (`...@....iam.gserviceaccount.com`)
   - Permission: **Owner**
5. In GitHub: **Settings → Secrets and variables → Actions → New repository secret**
   - `GOOGLE_INDEXING_SERVICE_ACCOUNT_JSON` — the entire JSON key file contents
   - `GSC_PROPERTY` — `https://www.urbanforestpark.com/`
     (use `sc-domain:urbanforestpark.com` only if your Search Console property is
     a Domain property)
6. Never commit the JSON key. The repository only reads it from the secret.

## Run it

### Manual workflow

Actions → **Google Indexing (sitemap + job pages)** → **Run workflow**

- `mode`: `all`, `sitemap`, or `jobs`
- `dry_run`: `true` first to see the URL count without calling Google
- `force`: ignore saved state and submit every active job

The first real `all` run submits the sitemap and up to 200 job URLs. Later runs
submit only new or changed job pages. The state lives in
`scripts/google_indexing_state.json` and is committed by the workflow.

### Daily automation

`.github/workflows/daily_jobs.yml` already runs:

```bash
python scripts/google_indexing.py --all
```

after the Cloudflare deploy. It is `continue-on-error: true`, so a Google quota
or permission problem never fails the publishing pipeline.

### Local

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\service-account.json"
py scripts/google_indexing.py --dry-run --all
py scripts/google_indexing.py --all
```

Or pass the key directly:

```powershell
py scripts/google_indexing.py --all --credentials C:\path\to\key.json
```

## Limits and troubleshooting

- **Indexing API quota:** 200 URLs/day by default. The script caps at
  `--limit 200` and stops on HTTP 429.
- **Sitemap submission is not the same as indexing.** It tells Google to re-read
  the sitemap; Google still schedules the crawl.
- **403 / permission error:** the service-account email is not an Owner of the
  Search Console property, or `GSC_PROPERTY` does not match the property exactly.
- **`Sitemap submission failed`:** confirm the property string. URL-prefix
  properties use `https://www.urbanforestpark.com/`; Domain properties use
  `sc-domain:urbanforestpark.com`.
- **Hub pages not indexed after a few days:** the sitemap is valid and submitted.
  Manual URL Inspection remains the only way to request a specific hub sooner.
  Do not resend the same URL every day.
- **Do not submit:** `?job=`, `?state=`, `?category=`, `?view=archive`, `.html`
  variants, `github.io` URLs, 301s, or noindex utility pages.
