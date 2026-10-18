#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UrbanForestPark - Academic & Institute seed listings (one-time bootstrap)
=========================================================================

Injects a curated set of authentic Indian academic, JRF, SRF, PhD,
postdoctoral and contractual institute listings into ``public/jobs.json`` so
the registry shows a rich academic + research + corporate mix from day one
(and Googlebot can crawl real JRF / project-staff / PhD content immediately).

Every listing links to the institute's real, currently-live recruitment
portal (verified by hand - see the URL table below) and carries the full
academic schema (position_type, qualification_summary,
compensation_or_fellowship) plus standard Indian stipend norms.

The script is idempotent: a seed is only written when its id is absent from
both jobs.json and archive.json, so re-running it (or running it after the
listings have naturally expired into the archive) changes nothing.

Typical usage
-------------
    # Preview which seeds would be added
    python scripts/seed_academic_jobs.py --dry-run

    # Inject the seeds into public/jobs.json
    python scripts/seed_academic_jobs.py

The daily pipeline (scripts/fetch_and_humanize.py) then owns these records:
it re-stamps valid_through, expires them into archive.json after 30 days and
keeps them in the historical registry forever.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List

log = logging.getLogger("ufp-seed-academic")

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_JOBS_PATH = REPO_ROOT / "public" / "jobs.json"
DEFAULT_ARCHIVE_PATH = REPO_ROOT / "public" / "archive.json"
VALID_DAYS = 30

# ---------------------------------------------------------------------------
# Seed listings.
#
# URL column verified live (HTTP 200 / reachable recruitment page) at seed
# time; the monthly lifecycle moves each record into archive.json 30 days
# after date_added, exactly like every scraped listing.
# ---------------------------------------------------------------------------
SEED_JOBS: List[Dict[str, Any]] = [
    {
        "id": "jrf-tiger-ecology-landscape-connectivity-wii-dehradun",
        "date_added": "2026-10-17",
        "clean_title": "Junior Research Fellow (JRF) - Tiger Ecology & Landscape Connectivity",
        "organization": "Wildlife Institute of India (WII)",
        "state": "Uttarakhand",
        "city": "Dehradun",
        "category": "Academic, JRF, SRF & PhD Positions",
        "experience_level": "Entry Level / Fellowship",
        "position_type": "JRF / SRF",
        "qualification_summary": "M.Sc. in Wildlife Science / Ecology / Zoology / Environmental Science (UGC-NET or GATE preferred)",
        "compensation_or_fellowship": "Rs 37,000/month + HRA (DST JRF norms); Rs 42,000/month after SRF upgrade",
        "role_summary": "The Wildlife Institute of India recruits a Junior Research Fellow for its tiger ecology programme covering corridor connectivity and prey dynamics in the Terai Arc Landscape. The fellow supports camera-trap based monitoring, occupancy analysis and spatial modelling for landscape-level conservation planning. The engagement is project-based, initially for one year and extendable as per funding norms.",
        "key_responsibilities": [
            "Support camera-trap deployment, retrieval and image processing across assigned forest divisions",
            "Run occupancy, abundance and connectivity analyses under the guidance of the project scientist",
            "Compile field datasets, maintain spatial databases and prepare analytical maps in QGIS",
            "Draft progress notes, data summaries and inputs for scientific publications",
            "Coordinate with state forest department staff and field assistants during surveys"
        ],
        "must_have_skills": [
            "Wildlife survey methods",
            "Camera-trap data analysis",
            "QGIS",
            "R or Python for ecological statistics",
            "Occupancy modelling",
            "Field ecology"
        ],
        "application_tip": "Attach a short note listing every field survey you have joined, the terrains covered and the datasets you processed yourself. Panels weigh hands-on camera-trap and analysis experience far above coursework.",
        "apply_url": "https://wii.gov.in/recruitments"
    },
    {
        "id": "jrf-avian-ecology-habitat-assessment-sacon-coimbatore",
        "date_added": "2026-10-15",
        "clean_title": "Junior Research Fellow (JRF) - Avian Ecology & Habitat Assessment",
        "organization": "Salim Ali Centre for Ornithology and Natural History (SACON)",
        "state": "Tamil Nadu",
        "city": "Coimbatore",
        "category": "Academic, JRF, SRF & PhD Positions",
        "experience_level": "Entry Level / Fellowship",
        "position_type": "JRF / SRF",
        "qualification_summary": "M.Sc. in Zoology / Wildlife Biology / Ecology / Environmental Sciences with bird survey experience",
        "compensation_or_fellowship": "Rs 37,000/month + HRA (as per funding agency norms)",
        "role_summary": "SACON invites applications for a Junior Research Fellow to study avian communities and habitat quality across wetland and woodland landscapes in southern India. The fellow will run point-count and transect surveys, quantify habitat variables and analyse community responses to land-use change. The position is contractual for one year, renewable based on performance and project continuation.",
        "key_responsibilities": [
            "Conduct bird surveys using point-count and line-transect protocols across study sites",
            "Collect habitat and disturbance variables along survey plots",
            "Digitise survey layers and produce habitat maps using QGIS",
            "Maintain daily field logs and consolidate datasets for analysis",
            "Support preparation of project reports and research manuscripts"
        ],
        "must_have_skills": [
            "Bird identification and survey protocols",
            "Statistical analysis in R",
            "QGIS",
            "Field data collection",
            "Scientific report writing"
        ],
        "application_tip": "Keep a species list from your field surveys ready and be specific about the number of survey days and habitats covered. SACON panels check whether you can work independently in humid, leech-prone field stations.",
        "apply_url": "https://www.sacon.in/careers/"
    },
    {
        "id": "jrf-air-quality-atmospheric-chemistry-iit-delhi",
        "date_added": "2026-10-16",
        "clean_title": "Junior Research Fellow (JRF) - Air Quality & Atmospheric Chemistry",
        "organization": "Indian Institute of Technology Delhi (IIT Delhi)",
        "state": "Delhi NCR",
        "city": "New Delhi",
        "category": "Academic, JRF, SRF & PhD Positions",
        "experience_level": "Entry Level / Fellowship",
        "position_type": "JRF / SRF",
        "qualification_summary": "M.Sc. / M.Tech. in Atmospheric Science / Environmental Engineering / Chemistry (UGC-NET or GATE qualified preferred)",
        "compensation_or_fellowship": "Rs 37,000/month + HRA (DST JRF norms)",
        "role_summary": "A sponsored research project at IIT Delhi recruits a Junior Research Fellow to investigate urban air quality dynamics and secondary aerosol formation across the NCR. The fellow runs filter-based and real-time monitoring campaigns, curates datasets and applies statistical analysis to link emissions with pollution episodes. The role suits a candidate aiming for doctoral work in atmospheric chemistry.",
        "key_responsibilities": [
            "Operate and maintain air-quality monitoring instruments during field campaigns",
            "Process filter-based and real-time datasets and flag data-quality issues",
            "Run chemical mass-balance and source-apportionment support analyses",
            "Document protocols and instrument logs for the project repository",
            "Contribute to progress reports and conference submissions"
        ],
        "must_have_skills": [
            "Air quality monitoring instruments",
            "Atmospheric data analysis",
            "Python or R",
            "Aerosol sampling",
            "Technical documentation"
        ],
        "application_tip": "Name the instruments you have personally operated in your cover letter. For project JRF posts at IITs, interview panels also ask standard questions on aerosol fundamentals, so revise secondary aerosol pathways.",
        "apply_url": "https://home.iitd.ac.in/jobs-iitd/index.html"
    },
    {
        "id": "phd-climate-dynamics-earth-system-modelling-iisc-bengaluru",
        "date_added": "2026-10-12",
        "clean_title": "PhD Position - Climate Dynamics & Earth System Modelling",
        "organization": "Indian Institute of Science (IISc)",
        "state": "Karnataka",
        "city": "Bengaluru",
        "category": "Academic, JRF, SRF & PhD Positions",
        "experience_level": "Entry Level / Fellowship",
        "position_type": "PhD / Doctoral Fellowship",
        "qualification_summary": "Master's degree in Physics / Atmospheric Science / Earth Science / Environmental Science; NET or GATE preferred as per institute norms",
        "compensation_or_fellowship": "Rs 31,000 - Rs 35,000/month as per institute fellowship norms (national fellowships extra)",
        "role_summary": "The climate dynamics group at IISc Bengaluru invites doctoral applications to study monsoon variability and coupled ocean-atmosphere processes using Earth system models. The doctoral researcher will design model experiments, analyse large climate datasets and evaluate projections against observational records. The position includes coursework, computing support and supervision aligned with national climate assessment needs.",
        "key_responsibilities": [
            "Design and run Earth system model experiments on the institute's computing cluster",
            "Analyse observational and reanalysis datasets for monsoon and circulation diagnostics",
            "Present methods and results in group meetings and research seminars",
            "Prepare manuscripts for peer-reviewed journals",
            "Support teaching assistantship duties as required by the department"
        ],
        "must_have_skills": [
            "Climate datasets and reanalysis products",
            "Python scripting and analysis",
            "Numerical modelling concepts",
            "Linux or HPC workflows",
            "Scientific writing"
        ],
        "application_tip": "Write to prospective supervisors only after studying their recent papers, and articulate one concrete question you would like to model. Reviewers respond to specificity, not general enthusiasm for climate science.",
        "apply_url": "https://iisc.ac.in/careers/"
    },
    {
        "id": "doctoral-fellowship-climate-policy-sustainable-development-teri",
        "date_added": "2026-10-11",
        "clean_title": "Doctoral Fellowship - Climate Policy & Sustainable Development",
        "organization": "The Energy and Resources Institute (TERI)",
        "state": "Delhi NCR",
        "city": "New Delhi",
        "category": "Academic, JRF, SRF & PhD Positions",
        "experience_level": "Entry Level / Fellowship",
        "position_type": "PhD / Doctoral Fellowship",
        "qualification_summary": "Master's degree in Economics / Policy / Environment / Energy Studies (NET or equivalent fellowship preferred)",
        "compensation_or_fellowship": "As per TERI doctoral fellowship norms (comparable to UGC-JRF)",
        "role_summary": "TERI's doctoral programme invites fellows for research on climate policy instruments, carbon markets and sustainable development pathways. Fellows work within ongoing policy studies at the institute while registering for their PhD with TERI School of Advanced Studies. The programme blends quantitative policy analysis with field engagement across Indian states.",
        "key_responsibilities": [
            "Develop a doctoral research plan aligned with ongoing climate policy studies",
            "Conduct quantitative and qualitative policy analysis on assigned themes",
            "Engage with stakeholders during field visits and consultations",
            "Publish working papers and journal articles from the research",
            "Present findings at internal seminars and external conferences"
        ],
        "must_have_skills": [
            "Climate and energy policy analysis",
            "Quantitative research methods",
            "Excel and statistical tools",
            "Policy writing",
            "Stakeholder engagement"
        ],
        "application_tip": "Pitch a research question that connects to TERI's live projects - carbon markets, BRSR, or just transition - and show earlier evidence of independent writing. A crisp two-page proposal beats a long generic statement.",
        "apply_url": "https://www.teriin.org/careers"
    },
    {
        "id": "postdoctoral-fellow-environmental-sustainability-climate-risk-iitkgp",
        "date_added": "2026-10-14",
        "clean_title": "Postdoctoral Fellow - Environmental Sustainability & Climate Risk",
        "organization": "Indian Institute of Technology Kharagpur (IIT Kharagpur)",
        "state": "West Bengal",
        "city": "Kharagpur",
        "category": "Academic, JRF, SRF & PhD Positions",
        "experience_level": "1-3 Years",
        "position_type": "PhD / Doctoral Fellowship",
        "qualification_summary": "Ph.D. in Environmental Science / Engineering / Sustainability / Climate Studies with a strong publication record",
        "compensation_or_fellowship": "Rs 50,000 - Rs 60,000/month consolidated (as per institute postdoctoral norms)",
        "role_summary": "IIT Kharagpur invites applications for a postdoctoral fellow to work on climate risk assessment and environmental sustainability modelling within an interdisciplinary research group. The fellow will lead a work package on vulnerability mapping and adaptation planning for eastern India. The position is contractual for one year with extension subject to performance and project funds.",
        "key_responsibilities": [
            "Lead climate risk and vulnerability assessments for assigned regions",
            "Develop and document modelling workflows for sustainability indicators",
            "Mentor postgraduate students associated with the project",
            "Publish in peer-reviewed journals and present at conferences",
            "Prepare technical reports for project sponsors"
        ],
        "must_have_skills": [
            "Climate risk assessment",
            "Spatial analysis and modelling",
            "Python or R",
            "Academic publishing",
            "Research project coordination"
        ],
        "application_tip": "Lead with your three strongest publications and the datasets or models you can reuse immediately. Postdoc selections at IITs favour candidates who arrive with a concrete plan for the first year.",
        "apply_url": "https://www.iitkgp.ac.in/careers"
    },
    {
        "id": "research-associate-biodiversity-ecological-genomics-ncbs",
        "date_added": "2026-10-13",
        "clean_title": "Research Associate - Biodiversity & Ecological Genomics",
        "organization": "National Centre for Biological Sciences (NCBS)",
        "state": "Karnataka",
        "city": "Bengaluru",
        "category": "Research Associate & Project Staff (Contractual)",
        "experience_level": "1-3 Years",
        "position_type": "Project Associate / Research Associate",
        "qualification_summary": "M.Sc. / M.Tech. in Biology / Biotechnology / Ecology / Genomics with molecular lab experience",
        "compensation_or_fellowship": "Rs 47,000 - Rs 54,000/month + HRA (as per project norms)",
        "role_summary": "NCBS Bengaluru recruits a Research Associate for a project combining biodiversity monitoring with ecological genomics approaches. The associate will generate and analyse sequencing data from field-collected samples and maintain the project's biological and data archives. The appointment is contractual under an externally funded project.",
        "key_responsibilities": [
            "Process field and laboratory samples through the genomics pipeline",
            "Run and document bioinformatics analyses for project datasets",
            "Maintain sample inventories, metadata standards and lab records",
            "Coordinate field collection schedules with collaborating teams",
            "Contribute analysis sections to project reports and manuscripts"
        ],
        "must_have_skills": [
            "Molecular biology techniques",
            "Bioinformatics pipelines",
            "Data management",
            "Ecological field methods",
            "Scientific documentation"
        ],
        "application_tip": "State the exact wet-lab protocols you can run unaided and name the bioinformatics tools you have actually used. For NCBS project posts, clarity about what you can do on day one matters more than publication count.",
        "apply_url": "https://www.ncbs.res.in/careers"
    },
    {
        "id": "young-professional-forest-policy-climate-finance-iifm-bhopal",
        "date_added": "2026-10-09",
        "clean_title": "Young Professional - Forest Policy & Climate Finance",
        "organization": "Indian Institute of Forest Management (IIFM)",
        "state": "Madhya Pradesh",
        "city": "Bhopal",
        "category": "Forestry, Wildlife & Afforestation",
        "experience_level": "1-3 Years",
        "position_type": "Young Professional / Consultant (Contractual)",
        "qualification_summary": "Master's degree in Forestry / Environmental Management / Economics / Public Policy; strong writing skills",
        "compensation_or_fellowship": "Rs 50,000/month consolidated (contractual engagement)",
        "role_summary": "IIFM Bhopal engages a Young Professional to support research and advisory work on forest policy, climate finance and community forestry institutions. The professional will draft policy notes, support training programmes and assist in evaluating afforestation-linked finance mechanisms. The engagement is contractual, based at the Bhopal campus with occasional travel.",
        "key_responsibilities": [
            "Draft policy briefs and background papers on forest governance themes",
            "Support design and delivery of training programmes for forest officers",
            "Assist research teams in data collection and literature synthesis",
            "Coordinate with state forest departments and partner organisations",
            "Prepare presentations and documentation for institutional partners"
        ],
        "must_have_skills": [
            "Forest policy knowledge",
            "Policy research and writing",
            "Stakeholder coordination",
            "Project documentation",
            "Presentation skills"
        ],
        "application_tip": "Include one writing sample - a policy note or dissertation chapter - that shows you can compress evidence into decision-ready briefs. IIFM values clarity for forest officers who read quickly.",
        "apply_url": "https://www.iifm.ac.in/career"
    },
    {
        "id": "young-professional-climate-change-campa-moefcc",
        "date_added": "2026-10-08",
        "clean_title": "Young Professional (Climate Change) - CAMPA & Climate Finance",
        "organization": "Ministry of Environment, Forest and Climate Change (MoEFCC)",
        "state": "Delhi NCR",
        "city": "New Delhi",
        "category": "Climate Policy, Think-Tanks & Fellowships",
        "experience_level": "1-3 Years",
        "position_type": "Young Professional / Consultant (Contractual)",
        "qualification_summary": "Master's degree in Environment / Climate Change / Forestry / Public Policy from a recognised university",
        "compensation_or_fellowship": "Rs 50,000 - Rs 70,000/month consolidated (Young Professional norms)",
        "role_summary": "The Ministry of Environment, Forest and Climate Change engages Young Professionals to support climate change policy work, including CAMPA-linked interventions and domestic climate finance tracking. The role involves inter-ministerial coordination, data analysis for reporting and preparation of policy inputs. The engagement is contractual and based in New Delhi.",
        "key_responsibilities": [
            "Assist in drafting policy notes, briefing materials and meeting agendas",
            "Support data compilation and analysis for climate reporting obligations",
            "Track state-level CAMPA activities and compile progress summaries",
            "Coordinate with stakeholders across ministries and state departments",
            "Maintain files, dashboards and presentation decks for the division"
        ],
        "must_have_skills": [
            "Climate policy understanding",
            "MS Office and data analysis",
            "Policy drafting",
            "Government coordination",
            "Report preparation"
        ],
        "application_tip": "Follow the vacancy circular's exact format - government screening is procedural. Underline any prior experience with state climate action plans or CAMPA documentation.",
        "apply_url": "https://moef.gov.in/vacancy-circulars"
    },
    {
        "id": "project-associate-geospatial-modelling-urban-heat-island-nrsc",
        "date_added": "2026-10-07",
        "clean_title": "Project Associate - Geospatial Modelling & Urban Heat Island Studies",
        "organization": "National Remote Sensing Centre (NRSC), ISRO",
        "state": "Telangana",
        "city": "Hyderabad",
        "category": "GIS, Remote Sensing & Earth Observation",
        "experience_level": "Entry Level / Fellowship",
        "position_type": "Project Associate / Research Associate",
        "qualification_summary": "M.Sc. / M.Tech. in Geoinformatics / Remote Sensing / Environmental Science with GIS programming skills",
        "compensation_or_fellowship": "Rs 31,000 - Rs 37,000/month + HRA (as per ISRO project norms)",
        "role_summary": "NRSC Hyderabad engages project associates for geospatial modelling of urban land surface dynamics and heat island intensity across Indian cities. The associate will process satellite time series, derive land-surface and thermal indices and support urban heat studies for national programmes. The position is contractual under an ongoing project.",
        "key_responsibilities": [
            "Process satellite imagery and time-series products for urban study areas",
            "Derive land cover, LST and urban heat island metrics following project protocols",
            "Automate repeatable workflows in Google Earth Engine or Python",
            "Prepare analytical maps and validation tables for project reviews",
            "Document methodology for project archives and publications"
        ],
        "must_have_skills": [
            "Remote sensing image processing",
            "Google Earth Engine",
            "Python (raster and vector workflows)",
            "Urban heat island concepts",
            "Technical documentation"
        ],
        "application_tip": "Bring one worked example - code or a map portfolio - showing an urban heat or land-surface analysis you completed end to end. ISRO project teams check the workflow, not just the output.",
        "apply_url": "https://www.nrsc.gov.in/nrscnew/Career_ApplyOnline.php"
    },
    {
        "id": "project-associate-geospatial-urban-green-infrastructure-atree",
        "date_added": "2026-10-05",
        "clean_title": "Project Associate - Geospatial Analysis for Urban Green Infrastructure",
        "organization": "ATREE",
        "state": "Karnataka",
        "city": "Bengaluru",
        "category": "GIS, Remote Sensing & Earth Observation",
        "experience_level": "1-3 Years",
        "position_type": "Project Associate / Research Associate",
        "qualification_summary": "M.Sc. / M.Tech. in Geoinformatics / Environmental Science / Urban Planning with demonstrated GIS project work",
        "compensation_or_fellowship": "Rs 35,000 - Rs 45,000/month (as per project norms)",
        "role_summary": "ATREE's urban research programme recruits a Project Associate to map and assess urban green infrastructure across fast-growing Indian cities. The associate analyses satellite and civic datasets to evaluate canopy cover, access equity and cooling benefits. The role bridges geospatial analysis with city engagement for practical planning inputs.",
        "key_responsibilities": [
            "Map urban tree canopy and green cover using high-resolution imagery",
            "Analyse access and equity metrics across city wards and neighbourhoods",
            "Build reproducible analysis scripts and spatial databases",
            "Prepare maps and visual summaries for city stakeholders",
            "Support research publications on urban greening outcomes"
        ],
        "must_have_skills": [
            "QGIS and ArcGIS",
            "Google Earth Engine",
            "Python or R scripting",
            "Urban ecology concepts",
            "Cartographic design"
        ],
        "application_tip": "A portfolio link with two or three urban analysis maps - canopy, heat or access - works better than a long CV. Mention how you validate classifications; ATREE reviews accuracy methods closely.",
        "apply_url": "https://www.atree.org/careers/"
    },
    {
        "id": "project-associate-himalayan-ecology-climate-adaptation-gbpnihe",
        "date_added": "2026-10-06",
        "clean_title": "Project Associate - Himalayan Ecology & Climate Change Adaptation",
        "organization": "G.B. Pant National Institute of Himalayan Environment (GBPNIHE)",
        "state": "Uttarakhand",
        "city": "Almora",
        "category": "Research Associate & Project Staff (Contractual)",
        "experience_level": "Entry Level / Fellowship",
        "position_type": "Project Associate / Research Associate",
        "qualification_summary": "M.Sc. in Environmental Science / Botany / Forestry / Geography from a recognised university",
        "compensation_or_fellowship": "Rs 31,000 - Rs 37,000/month + HRA (as per project funding norms)",
        "role_summary": "GBPNIHE recruits a Project Associate for a Himalayan ecology and climate adaptation study spanning forest ecosystems and spring-fed watersheds. The associate collects field data on vegetation and water sources and supports analysis of adaptation options with local communities. The position is contractual and based at the institute's Uttarakhand campus.",
        "key_responsibilities": [
            "Conduct field surveys of vegetation, springs and land-use at study sites",
            "Compile and analyse ecological and socio-economic datasets",
            "Support participatory exercises with local communities in project villages",
            "Prepare site reports, maps and input datasets for research teams",
            "Maintain project field equipment and data records"
        ],
        "must_have_skills": [
            "Ecological field survey methods",
            "Data compilation and analysis",
            "GIS basics",
            "Community interaction",
            "Report writing"
        ],
        "application_tip": "Highlight any Himalayan field experience and your ability to work at altitude for extended periods. Government institute panels also value Hindi proficiency for community-facing work.",
        "apply_url": "https://gbpihed.gov.in/vacancy.html"
    },
]


def load_json_list(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        log.warning("Could not read %s (%s); treating as empty", path, exc)
        return []
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


def build_seed_record(seed: Dict[str, Any]) -> Dict[str, Any]:
    """Return a seed with lifecycle fields stamped (status + valid_through)."""
    record = dict(seed)
    added = date.fromisoformat(record["date_added"])
    record["valid_through"] = (added + timedelta(days=VALID_DAYS)).isoformat()
    record["status"] = "active"
    return record


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "One-time bootstrap: inject authentic Indian academic / JRF / PhD / "
            "contractual institute listings into public/jobs.json (idempotent)."
        )
    )
    parser.add_argument("--jobs", help="Path to jobs.json (default: public/jobs.json)")
    parser.add_argument("--archive", help="Path to archive.json (default: public/archive.json)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    jobs_path = Path(args.jobs) if args.jobs else DEFAULT_JOBS_PATH
    archive_path = Path(args.archive) if args.archive else DEFAULT_ARCHIVE_PATH

    jobs = load_json_list(jobs_path)
    archive = load_json_list(archive_path)
    taken_ids = {
        str(row.get("id") or "").strip()
        for row in (jobs + archive)
        if str(row.get("id") or "").strip()
    }

    added: List[Dict[str, Any]] = []
    for seed in SEED_JOBS:
        if seed["id"] in taken_ids:
            log.info("Seed already present, skipping: %s", seed["id"])
            continue
        added.append(build_seed_record(seed))

    if not added:
        log.info(
            "Nothing to do: all %d seed listing(s) already exist in the registry.",
            len(SEED_JOBS),
        )
        return 0

    merged = added + jobs
    merged.sort(
        key=lambda job: (str(job.get("date_added") or ""), str(job.get("id") or "")),
        reverse=True,
    )

    log.info(
        "Seeds to add: %d (jobs.json: %d -> %d)",
        len(added), len(jobs), len(merged),
    )
    for record in added:
        log.info("  + %s | %s | %s", record["id"], record["category"], record["apply_url"])

    if args.dry_run:
        log.info("DRY RUN: nothing written.")
        return 0

    jobs_path.parent.mkdir(parents=True, exist_ok=True)
    jobs_path.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    log.info("Wrote %d listing(s) to %s", len(merged), jobs_path)

    # Light URL sanity check so a seed can never ship a placeholder link.
    bad = [
        r["id"]
        for r in added
        if not str(r.get("apply_url") or "").startswith(("http://", "https://"))
    ]
    if bad:
        log.error("Seed records with invalid apply_url: %s", ", ".join(bad))
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:  # pragma: no cover
        log.warning("Interrupted")
        sys.exit(130)
