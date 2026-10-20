"""Apply the quarantine patch approved 2026-10-20.

- Every verdict=FAIL record in audit_report.csv gets status="quarantined" in
  jobs.json, global_jobs.json and archive.json.
- Data is never deleted: apply_url etc. stay in the files.
- Writes public/quarantine_report.json grouped by employer with reason codes.
"""
import csv
import json
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from pathlib import Path

FILES = [
    ('public/jobs.json', 'active_india'),
    ('public/archive.json', 'archived_india'),
    ('public/global_jobs.json', 'active_global'),
    ('public/global_archive.json', 'archived_global'),
]

rows = list(csv.DictReader(open('audit_report.csv', encoding='utf-8')))
fail = {r['slug']: r for r in rows if r['verdict'] == 'FAIL'}
pass_rows = {r['slug']: r for r in rows if r['verdict'] == 'PASS'}
print(f'audit: {len(rows)} records, {len(fail)} FAIL, {len(pass_rows)} PASS')

verified_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

quarantined_records = []
touched_files = []

for path, kind in FILES:
    p = Path(path)
    if not p.exists():
        print(f'skip missing {path}')
        continue
    data = json.loads(p.read_text(encoding='utf-8'))
    n = 0
    for rec in data:
        rid = rec.get('id', '')
        if rid in fail:
            info = fail[rid]
            if rec.get('status') != 'quarantined':
                rec['status_before_quarantine'] = rec.get('status', '')
            rec['status'] = 'quarantined'
            rec['quarantine'] = {
                'reason_code': info['reason_code'],
                'final_url': info['final_url'],
                'final_host': info['final_host'],
                'http_status': int(info['http_status'] or 0),
                'entry_type': info['entry_type'],
                'host_class': info['host_class'],
                'error_detail': info['error_detail'][:200],
                'verified_at': verified_at,
                'audit': 'audit_report.csv',
            }
            n += 1
            quarantined_records.append({
                'slug': rid,
                'file': path,
                'kind': kind,
                'employer': info['employer'],
                'employer_id': info['employer_id'],
                'reason_code': info['reason_code'],
                'final_host': info['final_host'],
                'apply_url': info['apply_url'],
                'entry_type': info['entry_type'],
                'date_added': info['date_added'],
                'is_manual_seed': info['is_manual_seed'] == 'True',
            })
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    touched_files.append((path, len(data), n))
    print(f'{path}: {len(data)} records, {n} quarantined')

# ---- grouped report ----
by_employer = OrderedDict()
for rec in sorted(quarantined_records, key=lambda r: (r['employer'].lower(), r['slug'])):
    by_employer.setdefault(rec['employer'], []).append(rec)

employer_groups = [
    {
        'employer': emp,
        'employer_id': recs[0]['employer_id'],
        'count': len(recs),
        'reason_codes': dict(Counter(r['reason_code'] for r in recs)),
        'records': [
            {
                'slug': r['slug'],
                'file': r['file'],
                'reason_code': r['reason_code'],
                'final_host': r['final_host'],
                'apply_url': r['apply_url'],
                'entry_type': r['entry_type'],
                'date_added': r['date_added'],
                'manual_seed': r['is_manual_seed'],
            } for r in recs
        ],
    }
    for emp, recs in sorted(by_employer.items(), key=lambda kv: (-len(kv[1]), kv[0].lower()))
]

reason_counts = Counter(r['reason_code'] for r in quarantined_records)

hints = {
    'BLOCKED_HOST': 'Replace with the employer\'s own posting/careers URL from the registry (job-board links may only be used for discovery).',
    'GENERIC_LANDING_PAGE': 'Replace the portal URL with the specific posting URL (job title must appear on the page).',
    'CONTENT_MISMATCH': 'Replace with the page that carries this exact posting, or add the correct domain/ATS host to the registry.',
    'NEEDS_MANUAL_CHECK': 'Manual review: TLS/403 host. Open in a browser inside India, capture the true posting URL, then re-run verify_link.',
    'HOST_NOT_IN_REGISTRY': 'Lead came from an aggregator (indiawaterportal/fundsforngos). Resolve to the employer\'s own page; never store the aggregator URL.',
    'HTTP_404': 'Dead link - find the current posting URL or drop the record.',
    'SOFT_404': 'Page says "404 / not found" though HTTP=200 - find the current posting URL.',
    'MissingSchema': 'Fetch broke on a relative redirect - retry/replace URL.',
}

report = {
    'generated_at': verified_at,
    'source': 'audit_report.csv (11 PASS / 90 FAIL)',
    'policy': 'docs/LINK_POLICY.md',
    'tag': 'pre-gate-2026-10-20',
    'totals': {
        'records': len(rows),
        'quarantined': len(quarantined_records),
        'public': len(pass_rows),
    },
    'by_reason': dict(reason_counts.most_common()),
    'fix_hints': {k: hints[k] for k in reason_counts if k in hints},
    'by_employer': employer_groups,
}

Path('public/quarantine_report.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

print()
print('=== quarantine_report.json ===')
print('quarantined:', len(quarantined_records))
print('by reason:', dict(reason_counts.most_common()))
print()
print('Top 10 employers by quarantined count:')
for g in employer_groups[:10]:
    print(f"  {g['count']:2d}  {g['employer']}  {g['reason_codes']}")