"""Inspect registry entries for the 5 target employers + UNDP/GEF."""
import json

reg = json.load(open('public/employers.json', encoding='utf-8'))
emps = reg['employers']
print('total employers:', len(emps))
print()
keys = ['nature', 'mittal', 'wri', 'unu', 'undp', 'sgp', 'gef']
for e in emps:
    d = ' '.join(e.get('domains', [])) + ' ' + ' '.join(e.get('ats_hosts', []))
    name = e.get('name', '')
    if any(k in d.lower() for k in keys) or any(k in name.lower() for k in ['nature conservancy', 'mittal', 'wri', 'united nations university', 'undp', 'small grants', 'waste', 'unaccc']):
        print(f"{e['id']}\n  name={name}\n  domains={e.get('domains')}\n  ats={e.get('ats_hosts')}\n  region={e.get('region')}  type={e.get('type')}  approved={e.get('approved')}\n")

# check HOST_NOT_IN_REGISTRY records from audit
import csv
print('=== HOST_NOT_IN_REGISTRY records in audit ===')
for r in csv.DictReader(open('audit_report.csv', encoding='utf-8')):
    if r['reason_code'] == 'HOST_NOT_IN_REGISTRY':
        print(f"  slug={r['slug']}\n    employer={r['employer']} ({r['employer_id']})\n    host={r['final_host']}\n    url={r['apply_url'][:120]}")