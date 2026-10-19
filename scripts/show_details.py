import csv
rows = list(csv.DictReader(open('audit_report.csv')))

unreachable = [
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

archived = [
    'geospatial-analyst-forest-land-use-mapping-atree-bengaluru',
    'research-associate-climate-policy-governance-wri-india-bengaluru',
    'programme-officer-urban-forestry-green-cover-wwf-india-new-delhi',
    'consultant-esg-disclosures-brsr-reporting-ceew-new-delhi',
    'research-fellowship-environmental-policy-teri-new-delhi',
    'manager-carbon-credit-origination-eki-energy-services-indore',
]

all_trace = unreachable + archived

for r in rows:
    if r['slug'] in all_trace:
        print(f"{r['slug']}: {r['reason_code']} http={r['http_status']} entry={r['entry_type']} employer={r['employer']}")

print("\n=== TOTAL COUNT ===")
print(f"UNREACHABLE: {len(unreachable)}")
print(f"ARCHIVED: {len(archived)}")
print(f"TOTAL: {len(unreachable) + len(archived)}")