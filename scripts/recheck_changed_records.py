"""Re-verify records whose hosts changed status due to registry updates."""
import os
import sys

import certifi
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.path.insert(0, 'scripts')
from verify_link import verify_link, load_employers_registry

import json

registry = load_employers_registry('public/employers.json')

jobs = json.load(open('public/jobs.json', encoding='utf-8'))
archive = json.load(open('public/archive.json', encoding='utf-8'))
global_jobs = json.load(open('public/global_jobs.json', encoding='utf-8'))

all_recs = [(j, 'india') for j in jobs] + [(j, 'archive') for j in archive] + [(j, 'global') for j in global_jobs]
by_slug = {j.get('id'): (j, kind) for j, kind in all_recs}

targets = [
    'research-associate-climate-policy-governance-wri-india-bengaluru',
    'wri-global-climate-research-jobs',
    'unu-ias-postdoctoral-fellowships',
    'undp-gef-small-grants-programme',
]

for slug in targets:
    if slug not in by_slug:
        print(f'MISSING: {slug}')
        continue
    rec, kind = by_slug[slug]
    url = rec.get('apply_url') or rec.get('url') or ''
    title = rec.get('title', '')
    employer_id = rec.get('employer_id', '')
    org = rec.get('organization', '')
    r = verify_link(url, employer_id, title, org, employers_registry=registry)
    print(f'{slug}')
    print(f'   url={url[:100]}')
    print(f'   -> {r.verdict if hasattr(r, "verdict") else ("PASS" if r.ok else "FAIL")} | {r.reason_code} | {r.verification_level} | http={r.http_status} | entry_type={r.entry_type} | host_class={r.host_class}')
    print(f'   final_url={r.final_url[:110]}')
    print(f'   error_detail={r.error_detail[:150]}')
    print()