#!/usr/bin/env python3
"""Print audit report summary."""
import csv
import os
from collections import Counter

if os.path.exists('audit_report.csv'):
    rows = list(csv.DictReader(open('audit_report.csv')))
    print('Total:', len(rows))
    print('PASS:', sum(1 for r in rows if r['verdict'] == 'PASS'))
    print('FAIL:', sum(1 for r in rows if r['verdict'] == 'FAIL'))
    print('HTTP 200:', sum(1 for r in rows if r['http_status'] == '200'))
    rc = Counter(r['reason_code'] for r in rows)
    print('Reason codes:', dict(rc.most_common()))
    et = Counter(r['entry_type'] for r in rows)
    print('Entry types:', dict(et.most_common()))
    hc = Counter(r['final_host'] for r in rows if r['final_host'])
    print('Top hosts:', dict(hc.most_common(10)))
else:
    print('audit_report.csv not found')