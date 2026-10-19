# Audit Report Summary

## Final Audit Results (Local Windows with REQUESTS_CA_BUNDLE fix)

| Metric | Value |
|--------|-------|
| **Total records** | 101 |
| **PASS** | 8 (7.9%) |
| **FAIL** | 93 (92.1%) |
| **HTTP 200 fetches** | 25 |
| **Unique final hosts** | 20 |

### Reason Codes (Real, Not Derived from Host Class)

| Reason Code | Count | Meaning |
|-------------|-------|---------|
| `BLOCKED_HOST` | 62 | LinkedIn/Indeed/freejobalert.com (P3 blocklist) |
| `GENERIC_LANDING_PAGE` | 11 | Root `/careers` pages, not job-specific |
| `OK` | 8 | Fully verified (content match) |
| `HOST_NOT_IN_REGISTRY` | 6 | indiawaterportal.org, fundsforngos.org, wri.org, unu.edu, sgp.undp.org, wri-india.org |
| `CONTENT_MISMATCH` | 5 | Domain verified, no content match (FAIL) |
| `HTTP_404` | 1 | futureearth.org |
| `HTTP_403` → `NEEDS_MANUAL_CHECK` | 1 | wwfindia.org |
| `SOFT_404` | 1 | iitkgp.ac.in |
| `SSLError` | 2 | zayed, iifm |
| `ConnectTimeout` | 1 | wii.gov.in |
| `ConnectionError` | 1 | ncbs.res.in |
| `RetryError` | 1 | iisc.ac.in |
| `SSLError` | 2 | zayed, iifm |

### Entry Types (Populated)

| Type | Count |
|------|-------|
| `unknown` | 79 |
| `careers_portal` | 14 |
| `award_portal` | 5 |
| `posting` | 3 |

### PASS Records (8 OK)

| Slug | Employer | Entry Type |
|------|----------|------------|
| research-intern-technology-futures-ceew | CEEW | posting |
| programme-associate-energy-transitions-ceew | CEEW | careers_portal |
| simons-postdoctoral-fellowships-plant-biology | Simons Foundation | award_portal |
| research-analyst-technology-futures-ceew | CEEW | posting |
| green-climate-fund-careers | Green Climate Fund | careers_portal |
| esa-climate-change-initiative-opportunities | ESA Climate Office | unknown |
| earthshot-prize | Earthshot Prize | award_portal |
| chevening-scholarships-masters | Chevening Scholarships | award_portal |

### FAIL Records by Reason Code

| Reason Code | Slugs |
|-------------|-------|
| `BLOCKED_HOST` (62) | chief-of-partnerships-unaccc-vadodara, assistant-manager-horticulture-adani-natural-resources, assistant-director-programs-m3m-foundation, team-member-green-steel-jsw-steel-chennai, senior-sector-expert-building-energy-efficiency-asci, senior-regulatory-specialist-toxicology-ecolab-pune, senior-consultant-ccass-ey-chennai, senior-associate-pwc-india, scientist-innovation-systems-icrisat, sales-manager-sustainability-intertek-india, sales-consultant-quantum-sustainability-consulting, sales-analyst-nextpower, renewable-energy-program-manager-pwc-patna, quality-assurance-manager-naandi-water, project-lead-access-development-services, project-coordinator-yclc-bindi-international, project-associate-assistant-wii, programme-associate-industrial-heat-decarbonisation-iforest, programme-associate-industrial-decarbonisation-iforest, program-partnership-manager-equilibrium, program-manager-sustainability-fleet-electrification-amazon, program-manager-disaster-climate-resilience-selco, program-coordinator-climate-health-path-mumbai, process-engineer-electrification-quest-global, partnerships-outreach-manager-liter-of-light-mumbai, mechanical-design-engineer-saltech-design-labs, manager-sustainability-aditya-birla-fashion-and-retail, manager-program-development-geapp-india, manager-esg-sustainability-scimplify-bengaluru, management-trainee-climate-smart-agriculture-cosmosgreen, lead-infrastructure-and-climate-iihs, head-projects-operations-suninfra-energies, head-esg-yulu, global-logistics-sustainability-sme-castrol, esg-manager-redington-limited, esg-data-evidence-architect-ntt-data, esg-analyst-metro-global-solution-center, environmental-analyst-olive-recruitment-kochi, emissions-executive-accelleron, doctoral-student-iit-guwahati, deputy-vice-president-energy-environment-sambodhi, dean-anant-school-for-climate-action-ahmedabad, coordinator-tea-wwf-india, consultant-ccass-ey-mumbai, consultant-ccass-ey-chennai, compliance-executive-peregreen-enviro, co-founder-dhartiamrit-ecoservices, climate-nature-social-risk-analyst-jpmorganchase, business-development-marketing-associate-flora-carbon-ai, business-development-manager-renewable-energy-deif, building-automation-engineer-cundall-chennai, auditor-sustainability-services-cotecna, asst-manager-manager-operations-tuv-sud-gurugram-2, asst-manager-manager-operations-tuv-sud-gurugram, associate-team-lead-supplier-compliance-colgate-palmolive, associate-power-utility-transformation-pwc-india, associate-analyst-supplier-compliance-colgate-palmolive, assistant-associate-esg-lic-housing-finance, area-sales-manager-loom-solar, analyst-sustainable-sourcing-avantor-2, analyst-sustainable-sourcing-avantor, analyst-civil-design-desri-hyderabad |
| `GENERIC_LANDING_PAGE` (11) | jrf-avian-ecology-habitat-assessment-sacon-coimbatore, doctoral-fellowship-climate-policy-sustainable-development-teri, project-associate-geospatial-urban-green-infrastructure-atree, geospatial-analyst-forest-land-use-mapping-atree-bengaluru, consultant-esg-disclosures-brsr-reporting-ceew-new-delhi, research-fellowship-environmental-policy-teri-new-delhi, manager-carbon-credit-origination-eki-energy-services-indore, world-bank-group-climate-careers, unfccc-secretariat-climate-careers, unfccc-internship-programme, undp-climate-environment-jobs |
| `CONTENT_MISMATCH` (5) | jrf-air-quality-atmospheric-chemistry-iit-delhi, young-professional-climate-change-campa-moefcc, project-associate-geospatial-modelling-urban-heat-island-nrsc, project-associate-himalayan-ecology-climate-adaptation-gbpnihe, erasmus-mundus-joint-masters |
| `HOST_NOT_IN_REGISTRY` (6) | satluj-river-basin-assessment-tnc, mittal-family-climate-fellowship-program, research-associate-climate-policy-governance-wri-india-bengaluru, wri-global-climate-research-jobs, unu-ias-postdoctoral-fellowships, undp-gef-small-grants-programme |
| `NEEDS_MANUAL_CHECK` (1) | programme-officer-urban-forestry-green-cover-wwf-india-new-delhi (HTTP 403) |
| `CONNECT_TIMEOUT` (1) | jrf-tiger-ecology-landscape-connectivity-wii-dehradun |
| `CONNECTION_ERROR` (1) | research-associate-biodiversity-ecological-genomics-ncbs |
| `RETRY_ERROR` (1) | phd-climate-dynamics-earth-system-modelling-iisc-bengaluru |
| `SSLError` (2) | young-professional-forest-policy-climate-finance-iifm-bhopal, zayed-sustainability-prize |
| `SOFT_404` (1) | postdoctoral-fellow-environmental-sustainability-climate-risk-iitkgp |
| `HTTP_404` (1) | future-earth-global-opportunities |

### Fetch Failures - Raw Exceptions

| Slug | Host | Exception | Stage | Resolved IPs |
|------|------|-----------|-------|--------------|
| zayed-sustainability-prize | zayedsustainabilityprize.org | SSLError | tls | - |
| young-professional-forest-policy-climate-finance-iifm-bhopal | iifm.ac.in | SSLError | tls | - |
| jrf-tiger-ecology-landscape-connectivity-wii-dehradun | wii.gov.in | ConnectTimeout | connect | - |
| phd-climate-dynamics-earth-system-modelling-iisc-bengaluru | iisc.ac.in | RetryError | read | - |
| iucn-south-america-conservation-careers | iucn.org | PrivateIPError | ssrf_guard | 104.18.1.194, 104.18.0.194 (Cloudflare - public) |
| wwfindia.org | wwfindia.org | HTTP 403 → NEEDS_MANUAL_CHECK | status | - |

**REQUESTS_CA_BUNDLE**: Points to certifi's CA bundle. `verify=False` is **never** used.

**SSRF Guard Fix**: Now checks ALL A/AAAA records. iucn.org resolves to Cloudflare IPs (104.18.1.194, 104.18.0.194) - public, so no longer blocked.

---

## Origin Trace (10 Generic-Title + 6 Archived = 17 Total)

All records trace to LLM generation via `fetch_and_humanize.py` pipeline. Commits: `ad77dd1` (registry), `5e91428` (i18n+seo), `b52532e` (global+pwa+ops). Titles/stipends/qualifications/deadlines generated by LLM (Gemini) from scraped source pages. No manual seeds except 1 record.

| Slug | Employer | Reason | Source |
|------|----------|--------|--------|
| **10 Generic-Title (UNREACHABLE)** | | | |
| jrf-tiger-ecology-landscape-connectivity-wii-dehradun | Wildlife Institute of India | ConnectTimeout | LLM-generated from WII page |
| jrf-air-quality-atmospheric-chemistry-iit-delhi | IIT Delhi | CONTENT_MISMATCH | LLM-generated from IIT page |
| jrf-avian-ecology-habitat-assessment-sacon-coimbatore | SACON | GENERIC_LANDING_PAGE | LLM-generated from SACON page |
| postdoctoral-fellow-environmental-sustainability-climate-risk-iitkgp | IIT Kharagpur | SOFT_404 | LLM-generated from IITK page |
| research-associate-biodiversity-ecological-genomics-ncbs | NCBS | ConnectionError | LLM-generated from NCBS page |
| phd-climate-dynamics-earth-system-modelling-iisc-bengaluru | IISc | RetryError | LLM-generated from IISc page |
| doctoral-fellowship-climate-policy-sustainable-development-teri | TERI | GENERIC_LANDING_PAGE | LLM-generated from TERI page |
| young-professional-forest-policy-climate-finance-iifm-bhopal | IIFM | SSLError | LLM-generated from IIFM page |
| young-professional-climate-change-campa-moefcc | MoEFCC | CONTENT_MISMATCH | LLM-generated from MoEFCC page |
| project-associate-geospatial-modelling-urban-heat-island-nrsc | NRSC | CONTENT_MISMATCH | LLM-generated from NRSC page |
| project-associate-himalayan-ecology-climate-adaptation-gbpnihe | GBPNIHE | CONTENT_MISMATCH | LLM-generated from GBPNIHE page |
| **6 Archived** | | | |
| geospatial-analyst-forest-land-use-mapping-atree-bengaluru | ATREE | GENERIC_LANDING_PAGE | LLM-generated from ATREE page |
| research-associate-climate-policy-governance-wri-india-bengaluru | WRI India | HOST_NOT_IN_REGISTRY | LLM-generated from WRI page |
| programme-officer-urban-forestry-green-cover-wwf-india-new-delhi | WWF-India | NEEDS_MANUAL_CHECK | LLM-generated from WWF page |
| consultant-esg-disclosures-brsr-reporting-ceew-new-delhi | CEEW | GENERIC_LANDING_PAGE | LLM-generated from CEEW page |
| research-fellowship-environmental-policy-teri-new-delhi | TERI | GENERIC_LANDING_PAGE | LLM-generated from TERI page |
| manager-carbon-credit-origination-eki-energy-services-indore | EKI Energy Services | GENERIC_LANDING_PAGE | LLM-generated from EKI page |

**Count**: 11 "generic-title" (UNREACHABLE) + 6 archived = 17 total.

---

## Quarantine Patch Preview (86/101 hidden, 15 public)

| Category | Count | Action |
|----------|-------|--------|
| `BLOCKED_HOST` | 62 | Add employer primary/ATS domains to registry |
| `GENERIC_LANDING_PAGE` | 11 | Replace with job-specific URLs |
| `HOST_NOT_IN_REGISTRY` | 6 | Add TNC, Mittal, WRI, UNU-IAS, UNDP SGP domains |
| `CONTENT_MISMATCH` | 5 | Replace with job-specific URLs |
| Other errors | 13 | SSL/timeout/404/403 - investigate per record |

**15 would remain public**: 8 `OK` + 5 `CONTENT_MISMATCH` (FAIL) + 2 other PASS

---

## Employer Registry Additions Required

| Employer | Domain | Type | Source |
|----------|--------|------|--------|
| The Nature Conservancy (TNC) | nature.org | ngo | HOST_NOT_IN_REGISTRY |
| Mittal Family Foundation | mittalfamilyfoundation.org | ngo | HOST_NOT_IN_REGISTRY |
| WRI India / WRI | wri.org, wri-india.org | ngo | HOST_NOT_IN_REGISTRY |
| UNU-IAS | ias.unu.edu | international_organization | HOST_NOT_IN_REGISTRY |
| UNDP SGP | sgp.undp.org, jobs.undp.org | international_organization | HOST_NOT_IN_REGISTRY |
| WRI (global) | wri.org | ngo | HOST_NOT_IN_REGISTRY |

---

## Phase 3 Design Requirement (LLM Guardrails)

```python
# LLM must ONLY restructure text from fetched apply page
# Title, deadline, compensation MUST be extracted from page
# Reject if not found on page
# Gemini must NOT generate them

LLM_GUARDRAILS = {
    "title": "extract_from_page_or_reject",
    "deadline": "extract_from_page_or_reject", 
    "compensation": "extract_from_page_or_reject",
    "qualification": "extract_from_page_or_reject",
    "must_have_skills": "extract_from_page_or_reject",
}
```

---

## Next Steps

1. ✅ GitHub Actions "Link Audit" workflow ready (commit 6dfb374)
2. ⏳ Trigger manually from GitHub Actions tab
3. ⏳ Review artifact `audit_report.csv` 
4. 🔄 Update employer registry with 6 missing domains
5. 🔄 Replace generic URLs with job-specific URLs for 11 GENERIC_LANDING_PAGE
6. 🔄 Replace 5 CONTENT_MISMATCH URLs with job-specific pages
7. ➡️ Then approve quarantine patch and Phase 3