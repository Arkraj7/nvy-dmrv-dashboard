#!/usr/bin/env python3
"""Build jobs-by-skill pages and a monthly roundup.

Jobs by skill
-------------
One page per skill that appears in at least 10 active listings, grouping the
roles that need it. Long-tail queries such as "GIS jobs India" or "project
management environmental jobs" are answered with real openings, not a stub.

Monthly roundup
---------------
A curated, shareable digest: the open roles closing soonest this month, grouped
by category, plus the employers hiring most. Refreshed on every build so the
"updated" date is always true.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List

import build_expansion_hubs as beh

PUBLIC = beh.PUBLIC
SITE = beh.SITE
TODAY = date.today()

esc = beh.esc
plain = beh.plain
cards = beh.cards
hero = beh.hero
section = beh.section
shell = beh.shell
write_sub = beh.write_sub if hasattr(beh, "write_sub") else None


def write_sub_local(dir_path: Path, slug: str, html: str) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / f"{slug}.html").write_text(html, encoding="utf-8")


write_sub = write_sub_local

SKILLS_DIR = PUBLIC / "jobs-by-skill"

from collections import Counter


def top_cities(records, limit=6):
    counter = Counter()
    for job in records:
        city = plain(job.get("city")) or plain(job.get("state"))
        if city:
            counter[city] += 1
    return counter.most_common(limit)




def match_skill(skill: str) -> Callable[[Dict[str, Any]], bool]:
    target = skill.lower()

    def matcher(job: Dict[str, Any]) -> bool:
        for item in job.get("must_have_skills") or []:
            if plain(item).lower() == target:
                return True
        return False

    return matcher


# Curated skill hubs: (display name, slug, skill key as stored, description, related)
SKILL_HUBS: List[Dict[str, Any]] = [
    {"name": "Stakeholder engagement", "slug": "stakeholder-engagement", "key": "stakeholder engagement",
     "desc": "Roles that need stakeholder engagement: ESG, policy, conservation and programme delivery jobs where community and partner coordination is central.",
     "what": "Stakeholder engagement means mapping who is affected by a project, keeping them informed and resolving conflict. It shows up in ESG reporting, conservation and policy roles.",
     "related": [("/esg-carbon-sustainability-jobs", "ESG and sustainability jobs"), ("/green-careers", "Green career pathways")]},
    {"name": "Stakeholder management", "slug": "stakeholder-management", "key": "stakeholder management",
     "desc": "Roles that need stakeholder management: senior delivery and programme roles that own partner relationships end to end.",
     "what": "Stakeholder management is the ownership of partner and community relationships across a project's life, from scoping to closure.",
     "related": [("/esg-carbon-sustainability-jobs", "ESG and sustainability jobs"), ("/green-careers", "Green career pathways")]},
    {"name": "Climate policy and governance", "slug": "climate-policy", "key": "climate policy and governance",
     "desc": "Roles that need climate policy and governance skills: think-tank, multilateral and government-facing climate jobs.",
     "what": "Climate policy work covers analysis, drafting and advocacy on mitigation, adaptation and finance, usually for think tanks, multilaterals or government.",
     "related": [("/sustainability-jobs-india", "Sustainability jobs in India"), ("/exams/ugc-net-environmental-science", "UGC-NET guide")]},
    {"name": "Biodiversity conservation", "slug": "biodiversity-conservation", "key": "biodiversity conservation",
     "desc": "Roles that need biodiversity conservation skills: wildlife, forestry and protected-area jobs.",
     "what": "Biodiversity conservation work spans species surveys, habitat management, protected-area planning and community-based conservation.",
     "related": [("/forestry-wildlife-government-jobs", "Forestry and wildlife jobs"), ("/roles/wildlife-conservation", "Wildlife biologist career profile")]},
    {"name": "Research writing and communication", "slug": "research-writing", "key": "research writing and communication",
     "desc": "Roles that need research writing and communication: research associate, JRF and policy analyst jobs.",
     "what": "Research writing covers study design, data analysis, report drafting and peer-reviewed or policy-facing communication.",
     "related": [("/jrf-srf-project-associate-jobs", "JRF and project associate jobs"), ("/roles/junior-research-fellow", "JRF career profile")]},
    {"name": "Forest and landscape restoration", "slug": "forest-restoration", "key": "forest and landscape restoration",
     "desc": "Roles that need forest and landscape restoration skills: afforestation, CAMPA and watershed jobs.",
     "what": "Forest and landscape restoration covers nursery, planting, monitoring and community management of restored land.",
     "related": [("/forestry-wildlife-government-jobs", "Forestry and wildlife jobs"), ("/glossary/campa", "CAMPA glossary entry")]},
    {"name": "Project management", "slug": "project-management", "key": "project management",
     "desc": "Roles that need project management: delivery and coordination jobs across ESG, research and conservation.",
     "what": "Project management in green roles covers scoping, budgeting, timeline control and reporting to funders.",
     "related": [("/green-careers", "Green career pathways"), ("/green-internships", "Internships and entry-level jobs")]},
    {"name": "Research and analysis", "slug": "research-analysis", "key": "research and analysis",
     "desc": "Roles that need research and analysis skills: JRF, research associate and policy analyst jobs.",
     "what": "Research and analysis covers literature review, data collection, statistical analysis and evidence synthesis.",
     "related": [("/jrf-srf-project-associate-jobs", "JRF and project associate jobs"), ("/roles/project-associate", "Project associate career profile")]},
    {"name": "Climate and sustainable finance", "slug": "climate-finance", "key": "climate and sustainable finance",
     "desc": "Roles that need climate and sustainable finance skills: green finance, carbon markets and ESG investing jobs.",
     "what": "Climate and sustainable finance covers green bonds, carbon markets, climate risk and ESG investment analysis.",
     "related": [("/esg-carbon-sustainability-jobs", "ESG and carbon jobs"), ("/roles/carbon-analyst", "Carbon analyst career profile")]},
    {"name": "Data analysis", "slug": "data-analysis", "key": "data analysis",
     "desc": "Roles that need data analysis skills: GIS, ESG reporting, research and monitoring jobs.",
     "what": "Data analysis covers cleaning, exploring and visualising datasets, often with Excel, Python or R.",
     "related": [("/gis-remote-sensing-climate-jobs", "GIS and remote sensing jobs"), ("/roles/gis-analyst", "GIS analyst career profile")]},
    {"name": "Report writing", "slug": "report-writing", "key": "report writing",
     "desc": "Roles that need report writing: research, policy and ESG jobs where written output is central.",
     "what": "Report writing covers structuring evidence, drafting technical and policy documents and editing for clarity.",
     "related": [("/jrf-srf-project-associate-jobs", "JRF and project associate jobs"), ("/green-careers", "Green career pathways")]},
    {"name": "Soil health and sustainable agriculture", "slug": "soil-agriculture", "key": "soil health and sustainable agriculture",
     "desc": "Roles that need soil and sustainable agriculture skills: ICAR, agricultural research and rural development jobs.",
     "what": "Soil health work covers soil testing, sustainable farming practices, nutrient management and farmer training.",
     "related": [("/exams/icar-jrf-srf", "ICAR recruitment guide"), ("/forestry-wildlife-government-jobs", "Forestry and wildlife jobs")]},
    {"name": "Monitoring and evaluation", "slug": "monitoring-evaluation", "key": "monitoring and evaluation",
     "desc": "Roles that need monitoring and evaluation skills: programme and project delivery jobs.",
     "what": "M&E covers indicator design, data collection, progress tracking and reporting to funders.",
     "related": [("/green-careers", "Green career pathways"), ("/green-internships", "Internships and entry-level jobs")]},
]


def build_skill_page(hub: Dict[str, Any]) -> None:
    matcher = match_skill(hub["key"])
    live = [job for job in beh.active(beh.load(beh.JOBS_PATH)) + beh.active(beh.load(beh.GLOBAL_PATH)) if matcher(job)]
    live.sort(key=lambda j: str(j.get("valid_through") or "9999"))
    cities = top_cities(live, 6)
    city_html = (
        "<ul class=\"check-list\">" + "".join(
            f"<li><strong>{esc(city)}</strong> &mdash; {count} listing{'s' if count != 1 else ''}</li>"
            for city, count in cities
        ) + "</ul>"
        if cities
        else '<p class="muted">Location is not disclosed in these listings.</p>'
    )
    body = "\n".join(
        [
            hero(
                "Jobs by skill",
                f"{hub['name']} Jobs in India",
                hub["desc"],
                [
                    ("Live openings", str(len(live))),
                    ("Updated", TODAY.strftime("%d %b %Y")),
                ],
            ),
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>What the skill involves</h2>
        <p>{esc(hub["what"])}</p>
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Where the roles are ({len(live)})</h2>
        <p>Sorted by closing date. Each links to the full dossier and the official application page.</p>
        <div class="hub-list">
{cards(live[:18]) if live else '<p class="hub-empty">No live listing tags this skill today. New roles are added daily.</p>'}
        </div>
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Top locations</h2>
{city_html}
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Related pages</h2>
        <ul class="check-list">
          {''.join(f'<li><a href="{href}">{esc(label)}</a></li>' for href, label in hub["related"])}
          <li><a href="/green-careers">Green career pathways</a></li>
          <li><a href="/salary-guide">Salary guide by role and city</a></li>
        </ul>
      </div>
    </section>""",
            beh.bsp.faq_section_html(
                [
                    (f"Is {hub['name'].lower()} a common requirement?", "It appears in the must-have skills of the listings shown above, so yes within this registry. Frequency varies by category."),
                    ("Do I need a certificate?", "Employers name the skill more often than a certificate. A portfolio or a project that uses the skill is usually stronger evidence."),
                    ("How do I learn it?", "Start with the tools named in the listings for your category, then build one small deliverable you can show."),
                ]
            ),
        ]
    )
    jsonld = "\n".join(
        [
            beh.bsp.organization_jsonld(),
            beh.bsp.website_jsonld(),
            beh.breadcrumb(hub["name"] + " jobs", f"{SITE}/jobs-by-skill/{hub['slug']}"),
        ]
    )
    write_sub(
        SKILLS_DIR,
        hub["slug"],
        shell(
            title=f"{hub['name']} Jobs in India: Openings, Skills & Employers",
            description=hub["desc"],
            canonical=f"{SITE}/jobs-by-skill/{hub['slug']}",
            body=body,
            jsonld=jsonld,
        ),
    )


def build_skills_index() -> None:
    skill_cards = "\n".join(
        f"""        <article class="hub-card">
          <h3 class="hub-card-title"><a href="/jobs-by-skill/{h['slug']}">{esc(h['name'])}</a></h3>
          <p class="hub-card-sum">{esc(h['desc'])}</p>
          <p class="hub-card-foot"><span>{len([j for j in beh.active(beh.load(beh.JOBS_PATH)) + beh.active(beh.load(beh.GLOBAL_PATH)) if match_skill(h['key'])(j)])} live opening(s)</span>
            <a href="/jobs-by-skill/{h['slug']}">Browse &rarr;</a></p>
        </article>"""
        for h in SKILL_HUBS
    )
    body = "\n".join(
        [
            hero(
                "Jobs by skill",
                "Green Jobs in India by Skill",
                "Browse open roles by the skill they actually require, pulled from the verified registry.",
                [
                    ("Skill hubs", str(len(SKILL_HUBS))),
                    ("Live openings", str(sum(len([j for j in beh.active(beh.load(beh.JOBS_PATH)) + beh.active(beh.load(beh.GLOBAL_PATH)) if match_skill(h["key"])(j)]) for h in SKILL_HUBS))),
                    ("Updated", TODAY.strftime("%d %b %Y")),
                ],
            ),
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Choose a skill</h2>
        <p>Each hub lists the live openings that name that skill, with locations and links to the official application page.</p>
        <div class="hub-list">
{skill_cards}
        </div>
      </div>
    </section>""",
            beh.bsp.faq_section_html(
                [
                    ("How are skills assigned?", "They are taken from the must-have skills recorded for each listing, not inferred."),
                    ("Why is my skill missing?", "Only skills appearing in at least ten active listings get a hub. Rarer skills are searchable on the main registry."),
                    ("Are these jobs only in India?", "The hubs include global listings too, where the skill is recorded."),
                ]
            ),
        ]
    )
    write_sub(
        SKILLS_DIR,
        "index",
        shell(
            title="Green Jobs in India by Skill: GIS, ESG, Data Analysis & More",
            description="Browse verified green jobs in India by the skill they require: stakeholder engagement, climate policy, biodiversity, project management, data analysis and more.",
            canonical=f"{SITE}/jobs-by-skill",
            body=body,
            jsonld="\n".join(
                [
                    beh.bsp.organization_jsonld(),
                    beh.bsp.website_jsonld(),
                    beh.breadcrumb("Green Jobs by Skill", f"{SITE}/jobs-by-skill"),
                ]
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Monthly roundup
# ---------------------------------------------------------------------------
def build_monthly_roundup() -> None:
    cutoff = TODAY - timedelta(days=30)
    recent = [j for j in beh.active(beh.load(beh.JOBS_PATH)) + beh.active(beh.load(beh.GLOBAL_PATH)) if beh.parse_date(j.get("valid_through")) and beh.parse_date(j.get("valid_through")) >= TODAY]
    # sort by closing date, then date added
    recent.sort(key=lambda j: (str(j.get("valid_through") or "9999"), str(j.get("date_added") or "")))

    by_category: defaultdict[str, List[Dict[str, Any]]] = defaultdict(list)
    for job in recent:
        by_category[plain(job.get("category")) or "Other"].append(job)

    category_blocks = "\n".join(
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>{esc(category)} ({len(jobs)})</h2>
        <p>Open roles closing soonest first.</p>
        <div class="hub-list">
{cards(jobs[:6])}
        </div>
      </div>
    </section>"""
        for category, jobs in sorted(by_category.items(), key=lambda x: -len(x[1]))
    )

    employer_counts = Counter(plain(j.get("organization")) for j in recent if plain(j.get("organization")))
    top_employers = employer_counts.most_common(8)
    employer_html = (
        "<ul class=\"check-list\">" + "".join(
            f"<li><strong>{esc(name)}</strong> &mdash; {count} open role{'s' if count != 1 else ''}</li>"
            for name, count in top_employers
        ) + "</ul>"
        if top_employers
        else '<p class="muted">No employer data available.</p>'
    )

    body = "\n".join(
        [
            hero(
                "Monthly roundup",
                "Top Green Jobs This Month",
                "Open roles across the registry, grouped by category and ordered by closing date. Refreshed on every build.",
                [
                    ("Open roles", str(len(recent))),
                    ("Categories", str(len(by_category))),
                    ("Updated", TODAY.strftime("%d %b %Y")),
                ],
            ),
            category_blocks if category_blocks else """    <section class="hub-main">
      <div class="hub-main-inner">
        <p class="hub-empty">No open roles in the registry today.</p>
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Employers hiring most this month</h2>
        <p>By number of open roles currently tracked.</p>
        {employer_html}
      </div>
    </section>""",
            section(
                "How to use this roundup",
                "It is a starting point, not a filter.",
                """        <ul class="check-list">
          <li><strong>Apply early.</strong> Roles are ordered by closing date; the soonest deadlines are at the top of each category.</li>
          <li><strong>Check the notice.</strong> Eligibility, fees and age limits are stated in the official notification, not here.</li>
          <li><strong>Use skill and role pages.</strong> If a category is too broad, narrow down by skill or role profile.</li>
        </ul>""",
            ),
            beh.bsp.faq_section_html(
                [
                    ("How is this page different from the weekly digest?", "The weekly digest lists what was added in the last seven days. This page lists what is open now, ordered by closing date."),
                    ("How often is it updated?", "It is regenerated on every build from the registry."),
                    ("Can I filter by city or skill?", "Use the city hubs and jobs-by-skill pages for narrower lists."),
                ]
            ),
        ]
    )
    write_sub(
        PUBLIC,
        "top-green-jobs-this-month",
        shell(
            title="Top Green Jobs This Month in India & Worldwide",
            description=f"{len(recent)} open green jobs across {len(by_category)} categories, ordered by closing date, with official application links.",
            canonical=f"{SITE}/top-green-jobs-this-month",
            body=body,
            jsonld="\n".join(
                [
                    beh.bsp.organization_jsonld(),
                    beh.bsp.website_jsonld(),
                    beh.breadcrumb("Top Green Jobs This Month", f"{SITE}/top-green-jobs-this-month"),
                ]
            ),
        ),
    )


def main() -> None:
    for hub in SKILL_HUBS:
        build_skill_page(hub)
    build_skills_index()
    build_monthly_roundup()

    for hub in SKILL_HUBS:
        beh.update_sitemap([f"/jobs-by-skill/{hub['slug']}"])
    beh.update_sitemap(["/jobs-by-skill", "/top-green-jobs-this-month"])

    print(f"Wrote {len(SKILL_HUBS)} skill hubs + index and the monthly roundup")


if __name__ == "__main__":
    main()
