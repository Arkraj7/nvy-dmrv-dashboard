"""Apply approved registry additions to public/employers.json.

Approved (verified from page content 2026-10-20):
  - TNC: nature.org (already present, confirmed)
  - WRI: wri.org + wri-india.org (wri.org links to wri-india.org -> keep both)
  - UNU-IAS: ias.unu.edu + unu.edu (ias.unu.edu redirects to unu.edu/ias, same org site)
  - UNDP SGP: sgp.undp.org (confirmed "GEF Small Grants Programme")
  - UNDP: jobs.undp.org under UNDP (already present, confirmed)
  - Mittal Family Foundation: SKIPPED - mittalfamilyfoundation.org is NXDOMAIN

Also scans all employer ids for truncation.
"""
import json
import re

REG = 'public/employers.json'

with open(REG, encoding='utf-8') as f:
    reg = json.load(f)

emps = reg['employers']
by_id = {e['id']: e for e in emps}

changed = []


def set_domains(emp, domains, note):
    old = list(emp.get('domains', []))
    emp['domains'] = domains
    changed.append((emp['id'], old, domains, note))


# --- WRI ---
wri = by_id.get('world-resources-institute-wri')
if wri:
    set_domains(wri, ['wri.org', 'wri-india.org'], 'wri.org primary + wri-india.org (wri.org links to it)')

# --- UNU-IAS ---
unu = by_id.get('united-nations-university-institute-for-the-advanced-study-of-sustainability-unuias')
if unu:
    set_domains(unu, ['ias.unu.edu', 'unu.edu'], 'ias.unu.edu redirects to unu.edu/ias (same org site)')

# --- UNDP SGP ---
sgp = by_id.get('global-environment-facility-small-grants-programme-sgp-implemented-by-undp')
if sgp:
    set_domains(sgp, ['sgp.undp.org'], 'sgp.undp.org verified as SGP own site')

# --- UNDP: ensure jobs.undp.org under UNDP ---
undp = by_id.get('united-nations-development-programme-undp')
if undp:
    if 'jobs.undp.org' not in undp.get('ats_hosts', []):
        undp.setdefault('ats_hosts', []).append('jobs.undp.org')
    if 'undp.org' not in undp.get('domains', []):
        undp.setdefault('domains', []).append('undp.org')

# --- TNC: confirm nature.org present ---
tnc = by_id.get('the-nature-conservancy-tnc')
tnc_ok = tnc and 'nature.org' in tnc.get('domains', [])

# --- scan IDs for truncation ---
print('=== ID truncation scan ===')
suspicious = []
for e in emps:
    name = e['name']
    slug = re.sub(r'[^\w\s]', '', name.lower())
    slug = re.sub(r'\s+', '-', slug).strip('-')
    slug = re.sub(r'-+', '-', slug)
    bare = slug.replace('-india', '').replace('-limited', '').replace('-private', '').replace('-pvt', '')
    bare = re.sub(r'-+', '-', bare).strip('-')
    eid = e['id']
    # truncated if the id is a strict prefix of the canonical slug/bare and shorter
    is_prefix = (bare.startswith(eid) and eid != bare) or (slug.startswith(eid) and eid != slug)
    if is_prefix and len(eid) < len(bare) - 2:
        suspicious.append((eid, name, bare))
for eid, name, bare in suspicious:
    print(f'  TRUNCATED? {eid}  (name={name!r}, full={bare!r})')
if not suspicious:
    print('  none found')

reg['updated'] = '2026-10-20'
with open(REG, 'w', encoding='utf-8') as f:
    json.dump(reg, f, ensure_ascii=False, indent=2)

print()
print('=== Changes applied ===')
for eid, old, new, note in changed:
    print(f'  {eid}: {old} -> {new}  ({note})')
print(f'TNC nature.org present: {tnc_ok}')
print(f'Employers total: {len(emps)}')