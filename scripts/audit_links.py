#!/usr/bin/env python3
"""
audit_links.py - Retroactive audit of all job records against the link policy.

Runs verify_link over every active and archived record.
Outputs audit_report.csv with detailed results.
Prints summary: counts per verdict/reason, top 20 final hosts.
Does NOT modify data - report only.
"""
import json
import csv
import sys
import time
import re
from pathlib import Path
from collections import Counter
from verify_link import verify_link, load_employers_registry, LinkVerifier

def load_jobs(path: Path):
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get('jobs', [])
    return [row for row in data if isinstance(row, dict)]

def get_employer_id(job: dict, verifier: LinkVerifier) -> str:
    """Get employer ID for a job - try org_domain first, then name match."""
    org_domain = job.get('org_domain', '').strip()
    org_name = job.get('organization', '').strip()
    
    # Try exact domain match
    if org_domain:
        emp = verifier._find_employer_by_domain(org_domain)
        if emp:
            return emp['id']
    
    # Try name match
    if org_name:
        # Normalize name
        norm_name = org_name.lower()
        norm_name = norm_name.replace('(', '').replace(')', '').replace('&', 'and')
        norm_name = ' '.join(norm_name.split())
        
        for emp in verifier.employers.get('employers', []):
            emp_norm = emp['name'].lower().replace('(', '').replace(')', '').replace('&', 'and')
            emp_norm = ' '.join(emp_norm.split())
            if norm_name == emp_norm or norm_name in emp_norm or emp_norm in norm_name:
                return emp['id']
    
    return ''

def derive_source_portal(final_host: str, employer: dict = None) -> str:
    """Derive source_portal from final host and employer registry."""
    if not final_host:
        return 'unknown'
    
    host = final_host.lower().replace('www.', '')
    
    # Check if it's employer's primary domain
    if employer:
        for domain in employer.get('domains', []):
            if host == domain or host.endswith('.' + domain):
                return 'Official Organization Website'
        for ats in employer.get('ats_hosts', []):
            if host == ats or host.endswith('.' + ats):
                return 'Official Organization Website (ATS)'
    
    # Check government/academic
    if any(host.endswith(p) for p in ['.gov.in', '.nic.in', '.ac.in', '.res.in', '.edu.in', '.ernet.in']):
        return 'Official Institute Portal'
    
    # Check known job boards
    board_hosts = {
        'linkedin.com': 'LinkedIn',
        'indeed.com': 'Indeed',
        'naukri.com': 'Naukri',
        'glassdoor.com': 'Glassdoor',
        'foundit.in': 'Foundit',
        'timesjobs.com': 'TimesJobs',
        'freshersworld.com': 'Freshersworld',
        'internshala.com': 'Internshala',
        'unstop.com': 'Unstop',
        'reliefweb.int': 'ReliefWeb',
        'indiabioscience.org': 'IndiaBioscience',
        'freejobalert.com': 'FreeJobAlert',
        'news.google.com': 'News Announcement',
    }
    
    for board, label in board_hosts.items():
        if host == board or host.endswith('.' + board):
            return label
    
    return host

def is_manual_seed(job: dict) -> bool:
    """Determine if a job came from manual seed."""
    # Check for records that don't have standard source_portal values
    portal = job.get('source_portal', '').lower()
    if portal and portal not in ('linkedin', 'indeed', 'naukri', 'official organization website', 
                                  'official organisation website', 'official institute portal',
                                  'news announcement', 'reliefweb', 'indiabioscience'):
        return True
    return False

def trace_record_origin(slug: str):
    """Trace the origin of a record using git."""
    import subprocess
    result = subprocess.run(['git', 'log', '-S', slug, '--oneline', '-n', '5'], 
                          capture_output=True, text=True, cwd='C:\\Users\\arkra\\NVY DMRV\\nvy-dmrv-dashboard')
    return result.stdout.strip()

def main():
    print("Loading employer registry...")
    registry = load_employers_registry('public/employers.json')
    verifier = LinkVerifier(registry)
    
    print("Loading job data...")
    jobs = load_jobs(Path('public/jobs.json'))
    archive = load_jobs(Path('public/archive.json'))
    global_jobs = load_jobs(Path('public/global_jobs.json'))
    global_archive = load_jobs(Path('public/global_archive.json'))
    
    all_records = []
    for job in jobs:
        job['_source_file'] = 'jobs.json'
        job['_status'] = 'active'
        all_records.append(job)
    for job in archive:
        job['_source_file'] = 'archive.json'
        job['_status'] = 'archived'
        all_records.append(job)
    for job in global_jobs:
        job['_source_file'] = 'global_jobs.json'
        job['_status'] = 'active'
        job['_is_global'] = True
        all_records.append(job)
    for job in global_archive:
        job['_source_file'] = 'global_archive.json'
        job['_status'] = 'archived'
        job['_is_global'] = True
        all_records.append(job)
    
    print(f"Total records to audit: {len(all_records)}")
    print(f"  Active India: {len(jobs)}")
    print(f"  Archived India: {len(archive)}")
    print(f"  Active Global: {len(global_jobs)}")
    print(f"  Archived Global: {len(global_archive)}")
    
    # Run audit
    results = []
    reason_counts = Counter()
    verdict_counts = Counter()
    host_counts = Counter()
    entry_type_counts = Counter()
    http_200_count = 0
    successful_fetches = []
    
    # Trace origins for specific records
    unreachable_slugs = [
        'jrf-tiger-ecology-landscape-connectivity-wii-dehradun',
        'jrf-air-quality-atmospheric-chemistry-iit-delhi',
        'jrf-avian-ecology-habitat-assessment-sacon-coimbatore',
        'postdoctoral-fellow-environmental-sustainability-climate-risk-iitkgp',
        'research-associate-biodiversity-ecological-genomics-ncbs',
        'phd-climate-dynamics-earth-system-modelling-iisc-bengaluru',
        'doctoral-fellowship-climate-policy-sustainable-development-teri',
        'young-professional-forest-policy-climate-finance-iifm-bhopal',
        'young-professional-climate-change-campa-moefcc',
        'project-associate-geospatial-modelling-urban-heat-island-nrsc',
        'project-associate-himalayan-ecology-climate-adaptation-gbpnihe',
    ]
    
    print("\n=== TRACING ORIGINS OF UNREACHABLE RECORDS ===")
    for slug in unreachable_slugs:
        origin = trace_record_origin(slug)
        if origin:
            print(f"\n{slug}:")
            print(origin)
    
    # Also trace archived records
    print("\n=== TRACING ORIGINS OF ARCHIVED RECORDS ===")
    for job in archive:
        slug = job.get('id', '')
        origin = trace_record_origin(slug)
        if origin:
            print(f"\n{slug}:")
            print(origin)
    
    for i, job in enumerate(all_records):
        slug = job.get('id', '')
        org = job.get('organization', '')
        apply_url = job.get('apply_url', '')
        date_added = job.get('date_added', '')
        status = job.get('_status', '')
        is_global = job.get('_is_global', False)
        manual = is_manual_seed(job)
        
        # Get employer ID
        employer_id = get_employer_id(job, verifier)
        employer = None
        if employer_id:
            employer = verifier._find_employer(employer_id)
        
        # Verify
        job_title = job.get('clean_title', '') or job.get('title', '')
        org_name = job.get('organization', '')
        
        print(f"[{i+1}/{len(all_records)}] {slug} ({org})...", end=' ')
        
        try:
            result = verify_link(apply_url, employer_id, job_title, org_name, registry)
            result_dict = result.to_dict()
        except Exception as e:
            result_dict = {
                'ok': False,
                'final_url': apply_url,
                'final_host': '',
                'http_status': 0,
                'redirect_chain': [apply_url],
                'verification_level': 'unverified',
                'host_class': 'error',
                'reason_code': 'VERIFICATION_ERROR',
                'evidence_snippet': str(e)[:200],
                'content_hash': '',
                'verified_at': '',
                'entry_type': 'unknown',
                'error_detail': f'{type(e).__name__}: {e}',
                'warnings': [str(e)]
            }
        
        # Derive source_portal and host_class from final host and registry
        final_host = result_dict.get('final_host', '')
        derived_source_portal = derive_source_portal(final_host, employer)
        derived_host_class = result_dict.get('host_class', '')
        
        # Record for CSV
        row = {
            'slug': slug,
            'employer': org,
            'employer_id': employer_id,
            'apply_url': apply_url,
            'final_url': result_dict.get('final_url', ''),
            'final_host': final_host,
            'http_status': result_dict.get('http_status', 0),
            'verdict': 'PASS' if result_dict.get('ok') else 'FAIL',
            'reason_code': result_dict.get('reason_code', 'ERROR'),
            'verification_level': result_dict.get('verification_level', ''),
            'host_class': derived_host_class,
            'entry_type': result_dict.get('entry_type', 'unknown'),
            'redirect_chain': ' -> '.join(result_dict.get('redirect_chain', [])),
            'evidence_snippet': result_dict.get('evidence_snippet', ''),
            'content_hash': result_dict.get('content_hash', ''),
            'source_portal_original': job.get('source_portal', ''),
            'source_portal_derived': derived_source_portal,
            'date_added': date_added,
            'status': status,
            'is_global': is_global,
            'is_manual_seed': manual,
            'error_detail': result_dict.get('error_detail', '')
        }
        results.append(row)
        
        # Update counters
        reason_counts[result_dict.get('reason_code', 'ERROR')] += 1
        verdict_counts[row['verdict']] += 1
        entry_type_counts[result_dict.get('entry_type', 'unknown')] += 1
        if result_dict.get('http_status', 0) == 200:
            http_200_count += 1
            successful_fetches.append(row)
        if final_host:
            host_counts[final_host] += 1
        
        print(f"{row['verdict']} ({result_dict.get('reason_code', 'ERROR')}) http={result_dict.get('http_status', 0)} entry={result_dict.get('entry_type', 'unknown')}")
        
        time.sleep(0.1)
    
    # Write audit_report.csv
    output_path = Path('audit_report.csv')
    fieldnames = [
        'slug', 'employer', 'employer_id', 'apply_url', 'final_url', 'final_host',
        'http_status', 'verdict', 'reason_code', 'verification_level', 'host_class',
        'entry_type', 'redirect_chain', 'evidence_snippet', 'content_hash',
        'source_portal_original', 'source_portal_derived',
        'date_added', 'status', 'is_global', 'is_manual_seed', 'error_detail'
    ]
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n\nAudit complete. Report written to {output_path}")
    
    # Print summary
    print("\n=== SUMMARY ===")
    print(f"Total records: {len(results)}")
    print(f"PASS: {verdict_counts.get('PASS', 0)}")
    print(f"FAIL: {verdict_counts.get('FAIL', 0)}")
    print(f"HTTP 200 successful fetches: {http_200_count}")
    
    print("\n--- Reason code counts ---")
    for reason, count in reason_counts.most_common():
        print(f"  {reason}: {count}")
    
    print("\n--- Entry type counts ---")
    for etype, count in entry_type_counts.most_common():
        print(f"  {etype}: {count}")
    
    print("\n--- Top 20 final hosts ---")
    for host, count in host_counts.most_common(20):
        print(f"  {host}: {count}")
    
    # Successful fetches detail
    print(f"\n--- Records with HTTP 200 ({len(successful_fetches)}) ---")
    for row in successful_fetches:
        print(f"  {row['slug']} ({row['employer']})")
        print(f"    final_host: {row['final_host']}, reason: {row['reason_code']}, entry_type: {row['entry_type']}")
        print(f"    evidence: {row['evidence_snippet'][:100]}...")
    
    # By employer grouping
    print("\n--- FAIL counts by employer (for bulk fixes) ---")
    employer_fails = Counter()
    for row in results:
        if row['verdict'] == 'FAIL':
            employer_fails[row['employer']] += 1
    for employer, count in employer_fails.most_common(20):
        print(f"  {employer}: {count} failures")
    
    # Manual seed section
    manual_seeds = [r for r in results if r['is_manual_seed']]
    print(f"\n--- Manual seed records ({len(manual_seeds)}) ---")
    for row in manual_seeds:
        print(f"  {row['slug']} ({row['employer']}) - {row['verdict']} ({row['reason_code']})")
    
    # Source portal mismatches
    print("\n--- Source portal mismatches (original vs derived) ---")
    mismatches = [r for r in results if r['source_portal_original'].lower() != r['source_portal_derived'].lower() and r['source_portal_original']]
    for row in mismatches[:20]:
        print(f"  {row['slug']}: original='{row['source_portal_original']}' derived='{row['source_portal_derived']}'")
    
    # Suspicious records flagging
    print("\n--- FLAGGED RECORDS (review required) ---")
    
    # Suspicious employer
    suspicious_orgs = [r for r in results if any(term in r['employer'].lower() 
        for term in ['unknown', 'confidential', 'undisclosed', 'not disclosed', 'leading client', 'various', 'recruiter'])]
    if suspicious_orgs:
        print(f"  Suspicious employers: {len(suspicious_orgs)}")
        for r in suspicious_orgs[:10]:
            print(f"    {r['slug']}: {r['employer']}")
    
    # Pay-to-apply / investment
    pay_keywords = ['invest', 'pay', 'fee', 'deposit', 'registration fee', 'training fee', 'security deposit']
    pay_records = [r for r in results if any(kw in (r.get('evidence_snippet', '') + ' ' + r.get('apply_url', '')).lower() for kw in pay_keywords)]
    if pay_records:
        print(f"  Pay-to-apply indicators: {len(pay_records)}")
        for r in pay_records[:10]:
            print(f"    {r['slug']}: {r['employer']}")
    
    # Duplicates (same employer, similar title)
    title_groups = {}
    for r in results:
        if r['status'] == 'active':
            key = (r['employer'], r['slug'].split('-')[0] if '-' in r['slug'] else r['slug'][:20])
            if key not in title_groups:
                title_groups[key] = []
            title_groups[key].append(r)
    
    dupes = {k: v for k, v in title_groups.items() if len(v) > 1}
    if dupes:
        print(f"  Potential duplicate titles: {len(dupes)} groups")
        for k, v in list(dupes.items())[:10]:
            print(f"    {k[0]}: {len(v)} records - {[x['slug'] for x in v]}")
    
    # Off-topic (not climate/forestry/ESG/GIS/sustainability)
    on_topic_keywords = ['climate', 'forest', 'environment', 'sustainab', 'esg', 'carbon', 'green', 
                         'wildlife', 'ecology', 'conservation', 'gis', 'remote sens', 'geospatial',
                         'jrf', 'srf', 'phd', 'fellowship', 'renewable', 'energy transition',
                         'water', 'wash', 'biodiversity', 'afforest', 'agroforest', 'mangrove',
                         'circular', 'waste', 'pollution', 'clean energy', 'solar', 'wind']
    
    off_topic = []
    for r in results:
        text = (r['slug'] + ' ' + r['employer']).lower()
        if not any(kw in text for kw in on_topic_keywords):
            off_topic.append(r)
    
    if off_topic:
        print(f"  Potentially off-topic: {len(off_topic)}")
        for r in off_topic[:10]:
            print(f"    {r['slug']}: {r['employer']}")
    
    # Quarantine patch preparation
    print("\n=== QUARANTINE PATCH (records that would be hidden) ===")
    quarantine_candidates = []
    for row in results:
        if row['verdict'] == 'FAIL':
            reason = row['reason_code']
            if reason in ('BLOCKED_HOST', 'GENERIC_LANDING_PAGE', 'HOST_NOT_IN_REGISTRY', 
                         'UNREACHABLE_FROM_RUNNER', 'EMPLOYER_NOT_IN_REGISTRY',
                         'HTTP_404', 'SOFT_404', 'CONTENT_MISMATCH'):
                quarantine_candidates.append(row)
    
    print(f"Total quarantine candidates: {len(quarantine_candidates)} out of {len(results)}")
    print(f"Would remain public: {len(results) - len(quarantine_candidates)}")
    
    quarantine_by_employer = {}
    for row in quarantine_candidates:
        emp = row['employer']
        if emp not in quarantine_by_employer:
            quarantine_by_employer[emp] = []
        quarantine_by_employer[emp].append(row)
    
    for emp, recs in sorted(quarantine_by_employer.items(), key=lambda x: -len(x[1])):
        print(f"\n  {emp} ({len(recs)} records):")
        for r in recs:
            print(f"    {r['slug']} - {r['reason_code']} ({r['entry_type']}) - {r['final_host']}")
    
    return results

if __name__ == '__main__':
    main()