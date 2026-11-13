#!/usr/bin/env python3
"""Build the seven SEO gap hubs (Nov 2026).

1. /forest-guard-ranger-jobs          - state forest department recruitment hub
   + /forest-department-jobs-<state>   - one page per state with forestry/gov listings
2. /campa-jobs                        - CAMPA jobs hub (National + state CAMPA)
3. /esg-fresher-salary                - ESG fresher roles + registry-derived salary stats
4. /gis-fresher-salary                - GIS fresher roles + registry-derived salary stats
5. /ngo-environment-jobs              - NGO, think-tank & policy jobs
6. /walk-in-environment-jobs          - walk-in interview listings
7. /un-multilateral-jobs-india        - UN / World Bank / ADB / multilateral roles
8. /environmental-consultant-jobs     - consultant roles

Pages reuse the registry design system (jobs.css + hub.css) and the shared
header/footer via build_expansion_hubs, so they stay visually consistent
with the homepage. Job lists are generated from the registries; salary
figures are computed only from disclosed compensation values in the
registry - nothing is invented.

Run after build_seo_pages.py:
    py scripts/build_new_hubs.py
"""

from __future__ import annotations

import json
import re
import statistics
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

import build_expansion_hubs as beh
import build_seo_pages as bsp

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
SITE = bsp.SITE
TODAY = date.today()


def esc(v: Any) -> str:
    return beh.esc(v)


def slugify(v: Any) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", str(v or "").lower()).strip("-") or "state"


def load(path: Path) -> List[Dict[str, Any]]:
    return beh.load(path)


def active(records) -> List[Dict[str, Any]]:
    return beh.active(records)


def text_of(job: Dict[str, Any]) -> str:
    return " ".join(str(job.get(k) or "") for k in
                    ("clean_title", "organization", "role_summary", "category")).lower()


def cards(jobs: List[Dict[str, Any]]) -> str:
    return beh.cards(jobs)


def hero(kicker: str, h1: str, sub: str, stats: List[tuple]) -> str:
    return beh.hero(kicker, h1, sub, stats)


def section(title: str, intro: str, inner: str, anchor: str = "") -> str:
    return beh.section(title, intro, inner, anchor)


def page(name: str, title: str, desc: str, body: str, faqs: List[tuple]) -> None:
    canonical = f"{SITE}/{name}"
    jsonld = bsp.breadcrumb_jsonld(title, canonical) + "\n    " + bsp.faq_jsonld(faqs)
    beh.write_page(name, beh.shell(title=title, description=desc, canonical=canonical,
                                   body=body, jsonld=jsonld))
    print(f"Wrote /{name}")


def hub_page(name, title, desc, kicker, h1, sub, stats, sections_html, faqs):
    body = f"""    {hero(kicker, h1, sub, stats)}

    <div class="hub-wrap">
{sections_html}
    </div>"""
    page(name, title, desc, body, faqs)


# ---------------------------------------------------------------------------
# Salary parsing (registry-disclosed values only)
# ---------------------------------------------------------------------------
def monthly_inr(comp: str):
    """Best-effort monthly INR figure from a compensation string, else None."""
    t = str(comp or "").replace("₹", "Rs. ").replace(",", "")
    vals = []
    m = re.search(r"Rs\.\s*([\d.]+)\s*(?:/\s*month|per month|monthly)", t, re.I)
    if m:
        vals.append(float(m.group(1)))
    m = re.search(r"Rs\.\s*([\d.]+)\s*-\s*([\d.]+)\s*per month", t, re.I)
    if m:
        vals.append((float(m.group(1)) + float(m.group(2))) / 2)
    m = re.search(r"Rs\.\s*([\d.]+)\s*LPA", t, re.I) or re.search(r"([\d.]+)\s*LPA", t, re.I)
    if m:
        vals.append(float(m.group(1)) * 100000 / 12)
    m = re.search(r"([\d.]+)\s*M\s*INR\s*/\s*yr", t, re.I)
    if m:
        vals.append(float(m.group(1)) * 1000000 / 12)
    m = re.search(r"Rs\.\s*([\d.]+)\s*(?:-|–|to)\s*([\d.]+)\s*LPA", t, re.I)
    if m:
        vals.append(((float(m.group(1)) + float(m.group(2))) / 2) * 100000 / 12)
    if not vals:
        return None
    return statistics.median(vals)


def salary_stats(jobs: List[Dict[str, Any]]):
    vals = [v for j in jobs if (v := monthly_inr(j.get("compensation_or_fellowship"))) is not None]
    vals.sort()
    if not vals:
        return None
    def fmt(v):
        return f"Rs. {v:,.0f}"
    return {
        "n": len(vals),
        "min": fmt(vals[0]),
        "median": fmt(statistics.median(vals)),
        "max": fmt(vals[-1]),
    }


# ---------------------------------------------------------------------------
# 1. Forest guard / ranger hub + state pages
# ---------------------------------------------------------------------------
FOREST_PAT = re.compile(
    r"forest guard|forest ranger|forester|rfo\b|assistant conservator|indian forest service|ifs\b|"
    r"wildlife|forestry|afforestation|\bcampa\b|forest department|fsi\b|icfre|wildlife institute|"
    r"sacon|forest survey", re.I)

GOV_ORG_PAT = re.compile(
    r"forest department|forest survey|icfre|wildlife institute|sacon|moefcc|\bcampa\b|"
    r"government of|department of forest|forest & environment|forest and environment|"
    r"state forest|biodiversity board|pollution control", re.I)


def is_forest_gov(job: Dict[str, Any]) -> bool:
    t = text_of(job)
    cat = str(job.get("category") or "")
    return bool(FOREST_PAT.search(t)) and (
        job.get("category") == "Forestry, Wildlife & Afforestation" or bool(GOV_ORG_PAT.search(t)))


def build_forest_hub(india: List[Dict[str, Any]]) -> List[str]:
    pool = [j for j in india if is_forest_gov(j)]
    by_state: Counter[str] = Counter()
    for j in pool:
        st = str(j.get("state") or "").strip()
        if st and st not in ("Multiple States / Remote", "Global / Remote"):
            by_state[st] += 1
    states = [s for s, _ in by_state.most_common(16)]

    state_links = "\n".join(
        f'          <li><a href="/forest-department-jobs-{slugify(s)}">{esc(s)} forest department jobs</a> ({by_state[s]})</li>'
        for s in states)

    sections = section(
        "What this hub covers",
        "Forest guard, forester, forest ranger, RFO, ACF and IFS-track vacancies published by state forest "
        "departments, the Forest Survey of India, ICFRE institutes, the Wildlife Institute of India and "
        "CAMPA authorities - plus wildlife, ecology and conservation roles in the same public system. "
        "Every listing links to the official application page; expired calls move to the archive.",
        f"""        <div class="hub-list">
          <h3>State-wise forest department jobs</h3>
          <ul>
{state_links}
          </ul>
          <h3>Exam and eligibility guides</h3>
          <ul>
            <li><a href="/exams/forest-guard">Forest Guard exam: eligibility, physical tests and preparation</a></li>
            <li><a href="/exams/forest-range-officer">Forest Range Officer (RFO): eligibility and selection</a></li>
            <li><a href="/exams/indian-forest-service">Indian Forest Service (IFS): the All-India route</a></li>
            <li><a href="/exams/forest-survey-of-india">Forest Survey of India recruitment</a></li>
            <li><a href="/campa-jobs">CAMPA jobs: National and state CAMPA openings</a></li>
          </ul>
        </div>""",
        "coverage")

    sections += section(
        "Active forest department and wildlife roles",
        f"{len(pool)} verified listings across {len(states)} states/regions, ordered by publication date.",
        f'        <div class="hub-list">\n{cards(pool)}\n        </div>',
        "listings")

    faqs = [
        ("What is the qualification for Forest Guard recruitment?",
         "Forest Guard posts typically accept Class 10 or Class 12 from a recognised board, with state-specific physical standards and tests. Always verify the exact criteria in the official notification linked from each listing."),
        ("What is the qualification for Forest Ranger / RFO posts?",
         "Ranger and RFO posts generally require a graduate degree, often in science, agriculture, forestry or a related stream, plus a physical test. Check the linked notification for the state you are applying to."),
        ("How does IFS selection work?",
         "The Indian Forest Service is recruited through the UPSC Civil Services examination, followed by training at the Indira Gandhi National Forest Academy. See the IFS exam guide linked above."),
    ]
    hub_page(
        "forest-guard-ranger-jobs",
        "Forest Guard, Ranger & Forest Department Jobs in India 2026",
        "Verified forest guard, forester, forest ranger, RFO, ACF and IFS-track vacancies from Indian state forest departments, FSI, ICFRE, WII and CAMPA, with state-wise pages and exam guides.",
        "Government Forestry Track",
        "Forest Guard, Ranger & Forest Department Jobs in India 2026",
        "State forest department vacancies - forest guard, forester, ranger, RFO, ACF, IFS-track, wildlife and CAMPA roles - each linking to the official application page.",
        [("Active listings", str(len(pool))), ("States covered", str(len(states))),
         ("Updated", TODAY.strftime("%d %B %Y"))],
        sections, faqs)
    return states


def build_state_forest_pages(india: List[Dict[str, Any]], states: List[str]) -> List[str]:
    paths = []
    for state in states:
        pool = [j for j in india if is_forest_gov(j) and str(j.get("state") or "").strip() == state]
        if not pool:
            continue
        slug = slugify(state)
        sections = section(
            f"Active forest department roles in {state}",
            f"{len(pool)} verified listings with {state} organisations, ordered by publication date.",
            f'        <div class="hub-list">\n{cards(pool)}\n        </div>',
            "listings")
        sections += section(
            "Also explore",
            "Related pathways across the registry.",
            """        <div class="hub-list"><ul>
          <li><a href="/forest-guard-ranger-jobs">All forest department jobs (all states)</a></li>
          <li><a href="/campa-jobs">CAMPA jobs</a></li>
          <li><a href="/exams/forest-guard">Forest Guard exam guide</a></li>
          <li><a href="/government-environment-jobs">Government environment jobs tracker</a></li>
        </ul></div>""",
            "related")
        name = f"forest-department-jobs-{slug}"
        hub_page(
            name,
            f"Forest Department Jobs in {state} 2026 | Guard, Ranger, RFO",
            f"Verified forest guard, ranger, RFO and wildlife vacancies with {state} forest department and allied organisations, each linking to the official application page.",
            "State Forest Jobs",
            f"Forest Department Jobs in {state} 2026",
            f"Forest guard, ranger, forester and wildlife roles with {state} organisations - verified and linked to official sources.",
            [("Active listings", str(len(pool))), ("State", state), ("Updated", TODAY.strftime("%d %B %Y"))],
            sections,
            [("Where do I apply for these roles?",
              "Open the position dossier and follow the official application link. State forest department recruitments run through their own portals, walk-in interviews or email applications as stated in the advertisement."),
             ("Are forest guard qualifications the same in every state?",
              "No - eligibility, age limits and physical standards differ by state. Always verify the official notification for your state.")])
        paths.append(f"/{name}")
    return paths


# ---------------------------------------------------------------------------
# 2. CAMPA hub
# ---------------------------------------------------------------------------
def build_campa(india: List[Dict[str, Any]], global_jobs: List[Dict[str, Any]]):
    # \bcampa\b so "campaign" does not match.
    campa_pat = re.compile(r"\bcampa\b", re.I)
    pool = [j for j in india + global_jobs if campa_pat.search(text_of(j))]
    sections = section(
        "What is CAMPA?",
        "The Compensatory Afforestation Fund Management and Planning Authority (CAMPA) channels funds collected "
        "when forest land is diverted for non-forestry use into compensatory afforestation and related works, "
        "at national and state levels. Recruitment happens through the National Authority CAMPA (MoEFCC) and "
        "state CAMPA authorities - Young Professionals, project staff, foresters and support roles.",
        """        <div class="hub-list"><ul>
          <li><a href="/glossary/campa">CAMPA explained: fund, rules and where the term appears in hiring</a></li>
          <li><a href="https://moef.gov.in" target="_blank" rel="noopener noreferrer">MoEFCC - official ministry portal</a></li>
          <li><a href="/government-environment-jobs">Government environment jobs tracker</a></li>
        </ul></div>""",
        "about")
    sections += section(
        "Active CAMPA-linked roles",
        f"{len(pool)} verified listings mentioning CAMPA, ordered by publication date.",
        f'        <div class="hub-list">\n{cards(pool)}\n        </div>',
        "listings")
    hub_page(
        "campa-jobs",
        "CAMPA Jobs in India 2026 | National & State CAMPA Recruitment",
        "Verified CAMPA jobs: National Authority CAMPA (MoEFCC) and state CAMPA Young Professionals, project staff and forestry roles, each linking to the official application page.",
        "CAMPA Track",
        "CAMPA Jobs in India 2026",
        "National Authority CAMPA and state CAMPA vacancies - Young Professionals, project staff and forestry roles - verified and linked to official sources.",
        [("Active listings", str(len(pool))), ("Updated", TODAY.strftime("%d %B %Y"))],
        sections,
        [("Who recruits for CAMPA posts?",
          "The National Authority CAMPA under MoEFCC and state CAMPA authorities publish vacancies on their own portals and through walk-in interviews. Each listing here links to the official page."),
         ("What roles exist under CAMPA?",
          "Young Professionals, project associates, foresters, field staff and support roles on compensatory afforestation and plantation projects.")])
    return ["/campa-jobs"]


# ---------------------------------------------------------------------------
# 3. Fresher salary pages (registry-derived)
# ---------------------------------------------------------------------------
def build_fresher_salary(name: str, title: str, desc: str, kicker: str, h1: str, sub: str,
                         pool: List[Dict[str, Any]], faqs: List[tuple]):
    stats = salary_stats(pool)
    disclosed = [j for j in pool if monthly_inr(j.get("compensation_or_fellowship")) is not None]
    if stats:
        stat_html = (f"From {stats['n']} fresher/entry listings with disclosed pay in the registry: "
                     f"lowest {stats['min']}/month, median {stats['median']}/month, highest {stats['max']}/month. "
                     "These are the figures stated in the official advertisements, not estimates.")
    else:
        stat_html = ("No fresher listings in this track disclose a numeric pay figure right now; "
                     "each dossier shows the official compensation wording where published.")
    sections = section(
        "What fresher roles actually pay (registry data)",
        stat_html,
        f'        <div class="hub-list">\n{cards(disclosed or pool)}\n        </div>',
        "listings")
    sections += section(
        "How to read these figures",
        "Only listings whose official advertisement states a numeric stipend or salary are counted. "
        "Many fresher roles say 'as per norms' or 'not disclosed' and are listed with that wording. "
        "Use the figures as a market signal, then verify the exact pay in the linked notification.",
        """        <div class="hub-list"><ul>
          <li><a href="/salary-guide">Full salary guide: every track, computed from the registry</a></li>
          <li><a href="/esg-jobs-for-freshers">ESG jobs for freshers</a></li>
          <li><a href="/green-internships">Green internships and entry-level roles</a></li>
        </ul></div>""",
        "method")
    hub_page(name, title, desc, kicker, h1, sub,
             [("Fresher listings", str(len(pool))), ("With disclosed pay", str(len(disclosed))),
              ("Updated", TODAY.strftime("%d %B %Y"))],
             sections, faqs)
    return [f"/{name}"]


# ---------------------------------------------------------------------------
# 4. NGO / think-tank hub
# ---------------------------------------------------------------------------
def build_ngo(india: List[Dict[str, Any]]):
    pool = [j for j in india if str(j.get("category") or "") == "Climate Policy, Think-Tanks & Fellowships"]
    sections = section(
        "Active NGO, think-tank and policy roles",
        f"{len(pool)} verified listings with NGOs, research organisations and policy institutions, ordered by publication date.",
        f'        <div class="hub-list">\n{cards(pool)}\n        </div>',
        "listings")
    hub_page(
        "ngo-environment-jobs",
        "NGO & Think-Tank Environment Jobs in India 2026",
        "Verified environment and climate jobs with NGOs, think-tanks and policy organisations in India - research, programmes, communications and fellowships, each linking to the official application page.",
        "NGO & Policy Track",
        "NGO & Think-Tank Environment Jobs in India 2026",
        "Climate, environment and sustainability roles with NGOs, think-tanks and policy institutions across India.",
        [("Active listings", str(len(pool))), ("Updated", TODAY.strftime("%d %B %Y"))],
        sections,
        [("What kinds of roles are listed?",
          "Research associates, programme staff, communications and policy roles with NGOs, think-tanks and climate policy organisations."),
         ("How do I apply?",
          "Open the dossier and follow the official application link. The registry never charges fees.")])
    return ["/ngo-environment-jobs"]


# ---------------------------------------------------------------------------
# 5. Walk-in hub
# ---------------------------------------------------------------------------
def build_walkin(india: List[Dict[str, Any]], global_jobs: List[Dict[str, Any]]):
    pool = [j for j in india + global_jobs
            if re.search(r"walk[- ]?in", str(j.get("deadline_or_window") or ""), re.I)]
    sections = section(
        "Active walk-in interview listings",
        f"{len(pool)} verified listings whose advertisement specifies a walk-in interview. Carry your "
        "originals and attested copies, and reach the venue before the reporting time stated in the notice.",
        f'        <div class="hub-list">\n{cards(pool)}\n        </div>',
        "listings")
    hub_page(
        "walk-in-environment-jobs",
        "Walk-in Interview Jobs in Environment & Forestry India 2026",
        "Verified environment, forestry, JRF and ESG jobs with walk-in interviews in India, each linking to the official notification with venue, date and document requirements.",
        "Walk-in Track",
        "Walk-in Interview Jobs in Environment & Forestry India 2026",
        "Government and research walk-in interviews in environment, forestry, JRF and ESG - with official notification links for venue and documents.",
        [("Active listings", str(len(pool))), ("Updated", TODAY.strftime("%d %B %Y"))],
        sections,
        [("What should I carry to a walk-in interview?",
          "Typically originals and attested copies of degrees, certificates, ID and photographs, plus the application form if the notice asks for one. The linked notification lists the exact documents."),
         ("Are walk-in posts contractual?",
          "Most are project-based or contractual, with consolidated monthly pay stated in the advertisement.")])
    return ["/walk-in-environment-jobs"]


# ---------------------------------------------------------------------------
# 6. UN / multilateral India hub
# ---------------------------------------------------------------------------
MULTI_PAT = re.compile(
    r"\bUN (Environment|Children|Development|Women|OPS|HCR|ESCO|Habitat|FCCC|CCD|DP)|United Nations|"
    r"World Bank|IFC\b|Asian Development Bank|\bADB\b|UNDP|FAO\b|UNEP|UNICEF|GEF\b|GCF\b|"
    r"Green Climate Fund|UNESCO|UNCCD|CTCN|NIB\b|Nordic Investment|Multilateral|Bilateral|"
    r"Australia Awards|Chevening|DAAD|Fulbright|Erasmus", re.I)


def build_un_india(india: List[Dict[str, Any]], global_jobs: List[Dict[str, Any]]):
    pool = [j for j in india if MULTI_PAT.search(text_of(j))]
    gpool = [j for j in global_jobs
             if MULTI_PAT.search(text_of(j))
             and (str(j.get("country") or "").lower().find("india") >= 0
                  or re.search(r"india", text_of(j)))]
    sections = section(
        "Active multilateral roles in India",
        f"{len(pool)} India listings with UN agencies, the World Bank group and bilateral programmes, "
        "plus global-listed multilateral roles tagged to India.",
        f'        <div class="hub-list">\n{cards(pool + gpool)}\n        </div>',
        "listings")
    hub_page(
        "un-multilateral-jobs-india",
        "UN, World Bank & Multilateral Jobs in India 2026",
        "Verified climate and environment jobs with the UN system, World Bank, ADB and bilateral programmes recruiting in India, each linking to the official application page.",
        "Multilateral Track",
        "UN, World Bank & Multilateral Jobs in India 2026",
        "UN, World Bank, ADB and bilateral climate/environment roles connected to India - verified and linked to official sources.",
        [("Active listings", str(len(pool + gpool))), ("Updated", TODAY.strftime("%d %B %Y"))],
        sections,
        [("Which organisations are covered?",
          "UN agencies (UNEP, UNDP, UNICEF, FAO, UNOPS and others), the World Bank group, ADB and bilateral scholarship/programme bodies."),
         ("How do I apply?",
          "Open the dossier and follow the official application link on the organisation's careers portal.")])
    return ["/un-multilateral-jobs-india"]


# ---------------------------------------------------------------------------
# 7. Consultancy hub
# ---------------------------------------------------------------------------
def build_consultant(india: List[Dict[str, Any]], global_jobs: List[Dict[str, Any]]):
    pool = [j for j in india + global_jobs if re.search(r"consultant", str(j.get("clean_title") or ""), re.I)]
    sections = section(
        "Active consultant roles",
        f"{len(pool)} verified consultant listings across ESG, climate, GIS and environment consulting, ordered by publication date.",
        f'        <div class="hub-list">\n{cards(pool)}\n        </div>',
        "listings")
    hub_page(
        "environmental-consultant-jobs",
        "Environmental Consultant Jobs in India 2026 | ESG, Climate, GIS",
        "Verified environmental, ESG, climate and GIS consultant jobs in India - EIA, carbon, sustainability and geospatial consulting roles, each linking to the official application page.",
        "Consultancy Track",
        "Environmental Consultant Jobs in India 2026",
        "Consultant roles in environmental assessment, ESG and carbon consulting, climate advisory and GIS consulting, verified and linked to official sources.",
        [("Active listings", str(len(pool))), ("Updated", TODAY.strftime("%d %B %Y"))],
        sections,
        [("What do environmental consultants do?",
          "They assess environmental impacts, support clearances and compliance, and advise organisations on ESG, carbon and sustainability strategy. Listings here span EIA, ESG reporting, carbon markets and GIS consulting."),
         ("What experience do consultant roles ask for?",
          "Most ask for domain experience (EIA sectors, ESG reporting frameworks, GIS tools) plus client-facing skills. Check the dossier for the exact requirements.")])
    return ["/environmental-consultant-jobs"]


def main() -> None:
    india = active(load(beh.JOBS_PATH))
    global_jobs = active(load(beh.GLOBAL_PATH))

    paths: List[str] = []
    states = build_forest_hub(india)
    paths += build_state_forest_pages(india, states)
    paths += build_campa(india, global_jobs)

    esg_fresher = [j for j in india if str(j.get("experience_level") or "") == "Entry Level / Fellowship"
                   and str(j.get("category") or "") == "ESG, Carbon Markets & Corporate Sustainability"]
    gis_fresher = [j for j in india if str(j.get("experience_level") or "") == "Entry Level / Fellowship"
                   and str(j.get("category") or "") == "GIS, Remote Sensing & Earth Observation"]
    paths += build_fresher_salary(
        "esg-fresher-salary",
        "ESG Fresher Salary in India 2026 | Entry-Level Pay Guide",
        "What ESG fresher and entry-level roles pay in India, computed from disclosed pay in verified registry listings, with the live fresher ESG openings.",
        "Fresher Salary Track",
        "ESG Fresher Salary in India 2026",
        "Entry-level ESG analyst and sustainability roles: what they pay, from the registry's disclosed figures.",
        esg_fresher,
        [("What does an ESG fresher earn in India?",
          "It varies by employer and city. This page shows only figures stated in official advertisements, with the median across disclosed fresher listings."),
         ("Which ESG roles hire freshers?",
          "Analyst, associate and trainee roles in ESG reporting, data and sustainability teams. See the live listings below.")])
    paths += build_fresher_salary(
        "gis-fresher-salary",
        "GIS Fresher Salary in India 2026 | Entry-Level Pay Guide",
        "What GIS analyst, trainee and fresher roles pay in India, computed from disclosed pay in verified registry listings, with the live fresher GIS openings.",
        "Fresher Salary Track",
        "GIS Fresher Salary in India 2026",
        "Entry-level GIS and remote sensing roles: what they pay, from the registry's disclosed figures.",
        gis_fresher,
        [("What does a GIS fresher earn in India?",
          "It varies by employer and city. This page shows only figures stated in official advertisements, with the median across disclosed fresher listings."),
         ("Which GIS roles hire freshers?",
          "GIS Analyst, GIS Trainee and Cartographer roles. See the live listings below.")])

    paths += build_ngo(india)
    paths += build_walkin(india, global_jobs)
    paths += build_un_india(india, global_jobs)
    paths += build_consultant(india, global_jobs)

    added = beh.update_sitemap(paths)
    print(f"Wrote {len(paths)} new hub pages; sitemap +{added}")


if __name__ == "__main__":
    main()
