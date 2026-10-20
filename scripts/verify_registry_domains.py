"""Fetch each candidate registry domain and confirm org identity from page content.
Does NOT modify the registry - prints a verdict per domain.
"""
import os
import sys
import re

import certifi
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

import requests

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) UrbanForestPark-Verifier/1.0'}

# domain -> (employer name, required content keywords any-of, forbidden signals)
TARGETS = [
    ('https://www.nature.org/', 'The Nature Conservancy', ['nature conservancy', 'tnc']),
    ('https://mittalfamilyfoundation.org/', 'Mittal Family Foundation', ['mittal']),
    ('https://www.wri.org/', 'World Resources Institute', ['world resources institute', 'wri']),
    ('https://ias.unu.edu/', 'UNU-IAS', ['united nations university', 'unu-ias', 'unu']),
    ('https://sgp.undp.org/', 'UNDP SGP', ['small grants', 'sgp', 'undp']),
    ('https://jobs.undp.org/', 'UNDP jobs', ['undp', 'careers', 'jobs']),
]

session = requests.Session()
session.verify = certifi.where()
session.headers.update(HEADERS)

for url, name, keys in TARGETS:
    print('=' * 70)
    print(f'TARGET: {name}  URL: {url}')
    try:
        r = session.get(url, timeout=(15, 30), allow_redirects=True)
        html = r.text
        # title
        m = re.search(r'<title[^>]*>(.*?)</title>', html, re.I | re.S)
        title = re.sub(r'\s+', ' ', m.group(1)).strip()[:150] if m else '(no title)'
        text_lower = re.sub(r'<[^>]+>', ' ', html).lower()
        hits = [k for k in keys if k in text_lower]
        print(f'  status={r.status_code} final_url={r.url}')
        print(f'  title: {title}')
        print(f'  keyword hits: {hits}')
        print(f'  verdict: {"CONFIRMED" if r.status_code == 200 and hits else "CHECK-MANUALLY"}')
        # check if wri.org links to wri-india.org
        if 'wri.org' in url and 'wri-india' not in url:
            links_india = 'wri-india.org' in html.lower()
            print(f'  links to wri-india.org: {links_india}')
    except Exception as e:
        print(f'  ERROR: {type(e).__name__}: {e}')
        print('  verdict: FAILED')
