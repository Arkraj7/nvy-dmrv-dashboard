#!/usr/bin/env python3
"""
Create employers.json from KNOWN_INDIAN_ORGS + all orgs in jobs.json/archive.json/global_jobs.json
Fixed: truncated IDs, correct domains, proper TNC/Mittal domains
"""
import json
import re
from pathlib import Path

# Load known orgs from fetch_and_humanize.py
with open('scripts/fetch_and_humanize.py', encoding='utf-8') as f:
    content = f.read()

start = content.find('KNOWN_INDIAN_ORGS: List[Tuple[str, str, str]] = [')
end = content.find('\n]', start)
known_section = content[start:end+1]
known_tuples = re.findall(r'\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)', known_section)

# Load actual job data
with open('public/jobs.json', encoding='utf-8') as f:
    jobs = json.load(f)
with open('public/archive.json', encoding='utf-8') as f:
    archive = json.load(f)
with open('public/global_jobs.json', encoding='utf-8') as f:
    global_jobs = json.load(f)

# Collect org -> (org_website, org_domain) from actual data
actual_orgs = {}
for job in jobs + archive + global_jobs:
    org = job.get('organization', '').strip()
    website = job.get('org_website', '').strip()
    domain = job.get('org_domain', '').strip()
    if org and website:
        if org not in actual_orgs:
            actual_orgs[org] = {'website': website, 'domain': domain}
        elif website and len(website) > len(actual_orgs[org]['website']):
            actual_orgs[org] = {'website': website, 'domain': domain}

# Build exact org name mapping (longest alias wins)
known_by_exact = {}
for alias, website, domain in known_tuples:
    key = alias.lower().strip()
    if key not in known_by_exact or len(alias) > len(list(known_by_exact.keys())[list(known_by_exact.values()).index(info)] if (info := known_by_exact.get(key)) else 0):
        known_by_exact[key] = {'website': website, 'domain': domain}

# EXACT_ORG_NAMES
exact_start = content.find('EXACT_ORG_NAMES: Dict[str, Tuple[str, str]] = {')
exact_end = content.find('\n}', exact_start)
exact_section = content[exact_start:exact_end+1]
exact_tuples = re.findall(r'"([^"]+)":\s*\("([^"]+)",\s*"([^"]+)"\)', exact_section)
for alias, website, domain in exact_tuples:
    key = alias.lower().strip()
    known_by_exact[key] = {'website': website, 'domain': domain}

# Manual overrides for orgs in actual data that need correction
manual_overrides = {
    'The Nature Conservancy (TNC)': {'website': 'https://www.nature.org', 'domain': 'nature.org'},
    'Mittal Family Foundation': {'website': 'https://mittalfamilyfoundation.org', 'domain': 'mittalfamilyfoundation.org'},
    'Mittal Family Climate Fellowship Program': {'website': 'https://mittalfamilyfoundation.org', 'domain': 'mittalfamilyfoundation.org'},
    'Council on Energy, Environment and Water (CEEW)': {'website': 'https://www.ceew.in', 'domain': 'ceew.in'},
    'CEEW': {'website': 'https://www.ceew.in', 'domain': 'ceew.in'},
    'The Energy and Resources Institute (TERI)': {'website': 'https://www.teriin.org', 'domain': 'teriin.org'},
    'TERI': {'website': 'https://www.teriin.org', 'domain': 'teriin.org'},
    'Wildlife Institute of India': {'website': 'https://wii.gov.in', 'domain': 'wii.gov.in'},
    'Wildlife Institute of India (WII)': {'website': 'https://wii.gov.in', 'domain': 'wii.gov.in'},
    'World Resources Institute (WRI)': {'website': 'https://wri-india.org', 'domain': 'wri-india.org'},
    'WRI India': {'website': 'https://wri-india.org', 'domain': 'wri-india.org'},
    'WWF-India': {'website': 'https://www.wwfindia.org', 'domain': 'wwfindia.org'},
    'WWF India': {'website': 'https://www.wwfindia.org', 'domain': 'wwfindia.org'},
    'G.B. Pant National Institute of Himalayan Environment (GBPNIHE)': {'website': 'https://gbpihed.gov.in', 'domain': 'gbpihed.gov.in'},
    'Indian Institute of Technology Delhi (IIT Delhi)': {'website': 'https://home.iitd.ac.in', 'domain': 'iitd.ac.in'},
    'Indian Institute of Technology Kharagpur (IIT Kharagpur)': {'website': 'https://www.iitkgp.ac.in', 'domain': 'iitkgp.ac.in'},
    'Indian Institute of Technology, Guwahati': {'website': 'https://www.iitg.ac.in', 'domain': 'iitg.ac.in'},
    'Indian Institute of Forest Management (IIFM)': {'website': 'https://www.iifm.ac.in', 'domain': 'iifm.ac.in'},
    'Indian Institute of Science (IISc)': {'website': 'https://iisc.ac.in', 'domain': 'iisc.ac.in'},
    'National Centre for Biological Sciences (NCBS)': {'website': 'https://www.ncbs.res.in', 'domain': 'ncbs.res.in'},
    'National Remote Sensing Centre (NRSC), ISRO': {'website': 'https://www.nrsc.gov.in', 'domain': 'nrsc.gov.in'},
    'International Crops Research Institute for the Semi-Arid Tropics': {'website': 'https://www.icrisat.org', 'domain': 'icrisat.org'},
    'International Forum for Environment, Sustainability & Technology (iFOREST)': {'website': 'https://iforest.in', 'domain': 'iforest.in'},
    'International Union for Conservation of Nature (IUCN) - South America': {'website': 'https://www.iucn.org', 'domain': 'iucn.org'},
    'United Nations Development Programme (UNDP)': {'website': 'https://www.undp.org', 'domain': 'undp.org'},
    'United Nations Framework Convention on Climate Change (UNFCCC)': {'website': 'https://unfccc.int', 'domain': 'unfccc.int'},
    'United Nations University - Institute for the Advanced Study of Sustainability (UNU-IAS)': {'website': 'https://ias.unu.edu', 'domain': 'ias.unu.edu'},
    'Green Climate Fund (GCF)': {'website': 'https://greenclimate.fund', 'domain': 'greenclimate.fund'},
    'Global Environment Facility Small Grants Programme (SGP), implemented by UNDP': {'website': 'https://www.thegef.org', 'domain': 'thegef.org'},
    'The Earthshot Prize (Royal Foundation)': {'website': 'https://earthshotprize.org', 'domain': 'earthshotprize.org'},
    'Zayed Sustainability Prize (UAE)': {'website': 'https://zayedsustainabilityprize.org', 'domain': 'zayedsustainabilityprize.org'},
    'Chevening Scholarships - UK Government (FCDO)': {'website': 'https://www.chevening.org', 'domain': 'chevening.org'},
    'European Commission - Erasmus+ (EACEA)': {'website': 'https://eacea.ec.europa.eu', 'domain': 'eacea.ec.europa.eu'},
    'European Space Agency (ESA) Climate Office': {'website': 'https://climate.esa.int', 'domain': 'esa.int'},
    'Future Earth': {'website': 'https://futureearth.org', 'domain': 'futureearth.org'},
    'World Bank Group': {'website': 'https://www.worldbank.org', 'domain': 'worldbank.org'},
}

# Build unified org list with best info
org_info = {}
all_jobs = jobs + archive + global_jobs
for job in all_jobs:
    org = job.get('organization', '').strip()
    if not org:
        continue
    is_global = bool(job.get('global', False) or job.get('region', ''))
    website = job.get('org_website', '').strip()
    domain = job.get('org_domain', '').strip()
    
    if org not in org_info:
        org_info[org] = {'website': website, 'domain': domain, 'is_global': is_global, 'count': 1}
    else:
        org_info[org]['count'] += 1
        if website and not org_info[org]['website']:
            org_info[org]['website'] = website
            org_info[org]['domain'] = domain
        if is_global:
            org_info[org]['is_global'] = True

# Apply manual overrides
for org_name, info in manual_overrides.items():
    if org_name in org_info:
        org_info[org_name]['website'] = info['website']
        org_info[org_name]['domain'] = info['domain']

# Deduplicate: find canonical org names (handle variants like "CEEW" vs "Council on Energy...")
# Strategy: prefer the longest name that maps to same domain
domain_to_canonical = {}
for org_name, info in org_info.items():
    domain = info['domain']
    if domain and domain not in domain_to_canonical:
        domain_to_canonical[domain] = org_name
    elif domain and len(org_name) > len(domain_to_canonical[domain]):
        domain_to_canonical[domain] = org_name

# Known ATS hosts per employer domain
known_ats = {
    'wii.gov.in': [],
    'ceew.in': [],
    'icfre.gov.in': [],
    'iisc.ac.in': [],
    'iitd.ac.in': ['home.iitd.ac.in'],
    'iitb.ac.in': ['www.iitb.ac.in'],
    'iitm.ac.in': ['www.iitm.ac.in'],
    'iitkgp.ac.in': ['www.iitkgp.ac.in'],
    'iitr.ac.in': ['www.iitr.ac.in'],
    'iitk.ac.in': ['www.iitk.ac.in'],
    'iitg.ac.in': ['www.iitg.ac.in'],
    'teriin.org': [],
    'atree.org': [],
    'cseindia.org': [],
    'cstep.in': [],
    'wri-india.org': [],
    'wwfindia.org': [],
    'undp.org': ['jobs.undp.org'],
    'unep.org': [],
    'worldbank.org': ['careers.worldbank.org'],
    'ey.com': ['careers.ey.com'],
    'kpmg.com': ['careers.kpmg.com'],
    'deloitte.com': ['careers.deloitte.com'],
    'pwc.in': ['careers.pwc.in'],
    'tatasteel.com': [],
    'jsw.in': [],
    'adani.com': [],
    'amazon.in': ['amazon.jobs'],
    'intertek.com': [],
    'ecolab.com': [],
    'tuvsud.com': [],
    'nature.org': [],
    'mittalfamilyfoundation.org': [],
    'gbpihed.gov.in': [],
    'nrsc.gov.in': [],
    'iicrisat.org': [],  # Note: icrisat.org
    'iforest.in': [],
    'iucn.org': [],
    'unfccc.int': [],
    'undp.org': ['jobs.undp.org'],
    'ias.unu.edu': [],
    'greenclimate.fund': [],
    'thegef.org': [],
    'earthshotprize.org': [],
    'chevening.org': [],
    'eacea.ec.europa.eu': [],
    'esa.int': [],
    'futureearth.org': [],
    'worldbank.org': ['careers.worldbank.org'],
}

# Build final canonical list
canonical_orgs = {}
for domain, canonical_name in domain_to_canonical.items():
    info = org_info[canonical_name]
    is_global = info['is_global']
    
    # Determine type
    if any(x in domain for x in ['.gov.in', '.nic.in', '.ac.in', '.res.in', '.edu.in', '.ernet.in']):
        org_type = 'government_institute'
    elif '.org' in domain or '.org.in' in domain or '.ngo' in domain:
        org_type = 'ngo'
    elif is_global:
        org_type = 'international_organization'
    else:
        org_type = 'corporate'
    
    # Generate clean ID (no truncation)
    emp_id = re.sub(r'[^\w\s]', '', canonical_name.lower())
    emp_id = re.sub(r'\s+', '-', emp_id).strip('-')
    emp_id = re.sub(r'-+', '-', emp_id)
    # Remove common suffixes that make IDs long
    emp_id = emp_id.replace('-india', '').replace('-limited', '').replace('-private', '').replace('-pvt', '')
    emp_id = re.sub(r'-+', '-', emp_id).strip('-')
    
    # Ensure unique ID
    counter = 1
    orig_id = emp_id
    while emp_id in canonical_orgs:
        counter += 1
        emp_id = f"{orig_id}-{counter}"
    
    canonical_orgs[emp_id] = {
        'id': emp_id,
        'name': canonical_name,
        'domains': [domain],
        'ats_hosts': known_ats.get(domain, []),
        'type': org_type,
        'region': 'global' if is_global else 'india',
        'website': info['website'],
        'approved': True,
        'approved_at': '2026-10-20T00:00:00Z',
        'approved_by': 'seed'
    }

# Also include known orgs that don't have jobs yet (for future matching)
# but mark them as not having active jobs
for alias, info in known_by_exact.items():
    domain = info['domain']
    if domain not in domain_to_canonical:
        # Find a reasonable name
        name = alias.title()
        emp_id = re.sub(r'[^\w\s]', '', name.lower())
        emp_id = re.sub(r'\s+', '-', emp_id).strip('-')
        emp_id = re.sub(r'-+', '-', emp_id)
        
        counter = 1
        orig_id = emp_id
        while emp_id in canonical_orgs:
            counter += 1
            emp_id = f"{orig_id}-{counter}"
        
        org_type = 'government_institute' if any(x in domain for x in ['.gov.in', '.nic.in', '.ac.in', '.res.in', '.edu.in']) else 'ngo' if '.org' in domain else 'corporate'
        
        canonical_orgs[emp_id] = {
            'id': emp_id,
            'name': name,
            'domains': [domain],
            'ats_hosts': known_ats.get(domain, []),
            'type': org_type,
            'region': 'india',
            'website': info['website'],
            'approved': False,
            'approved_at': None,
            'approved_by': None
        }

# Write employers.json
output = {
    'version': 1,
    'updated': '2026-10-20',
    'employers': list(canonical_orgs.values())
}

with open('public/employers.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'Created employers.json with {len(canonical_orgs)} employers')
print(f'India: {sum(1 for e in canonical_orgs.values() if e["region"] == "india")}')
print(f'Global: {sum(1 for e in canonical_orgs.values() if e["region"] == "global")}')

# Print for verification
for emp in sorted(canonical_orgs.values(), key=lambda x: x['name']):
    approved = 'YES' if emp['approved'] else 'NO'
    print(f'  [{approved}] {emp["id"]}: {emp["name"]} ({emp["region"]}) - {emp["domains"][0]} [{emp["type"]}]')