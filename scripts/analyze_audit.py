"""Quick analysis of audit_report.csv - verdict counts, pass list, employer breakdown."""
import csv
import collections

rows = list(csv.DictReader(open('audit_report.csv', encoding='utf-8')))
print('total', len(rows))
v = collections.Counter(r['verdict'] for r in rows)
print('verdicts:', dict(v))
rc = collections.Counter(r['reason_code'] for r in rows)
print('reasons:', dict(rc))
print()
print('PASS records:')
for r in rows:
    if r['verdict'] == 'PASS':
        print(' ', r['slug'], '|', r['entry_type'], '|', r['final_host'])
print()
print('FAIL by employer (top 12):')
tc = collections.Counter(r['employer'] for r in rows if r['verdict'] == 'FAIL')
for e, c in tc.most_common(12):
    print(f'  {c:3d}  {e}')
print()
print('FAIL by reason + entry_type:')
rc2 = collections.Counter((r['reason_code'], r['entry_type']) for r in rows if r['verdict'] == 'FAIL')
for (reason, et), c in rc2.most_common():
    print(f'  {c:3d}  {reason:24s} {et}')