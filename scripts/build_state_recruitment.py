#!/usr/bin/env python3
"""Build state-wise recruitment calendar pages.

Each page lists the major recruiting bodies in that state for green/environment
roles, with their portal, typical cycle and live openings from the registry.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import build_expansion_hubs as beh

PUBLIC = beh.PUBLIC
SITE = beh.SITE
TODAY = __import__("datetime").date.today()

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

JOBS = beh.active(beh.load(beh.JOBS_PATH))


STATE_BODIES = {
    "madhya-pradesh": {
        "name": "Madhya Pradesh",
        "bodies": [
            ("MP Forest Department", "Forest guard, ranger and field recruitment", "mpforest.gov.in", "https://www.mpforest.gov.in"),
            ("MP Public Service Commission (MPPSC)", "State forest service, environment officer", "mppsc.mp.gov.in", "https://mppsc.mp.gov.in"),
            ("MP Pollution Control Board (MPPCB)", "Scientist, environmental engineer", "mppcb.mp.gov.in", "https://mppcb.mp.gov.in"),
            ("IIFM Bhopal", "Young professional, project staff", "iifm.ac.in", "https://www.iifm.ac.in"),
        ],
    },
    "uttarakhand": {
        "name": "Uttarakhand",
        "bodies": [
            ("Uttarakhand Forest Department", "Forest guard, ranger, forester", "forest.uk.gov.in", "https://forest.uk.gov.in"),
            ("UKPSC", "State forest service, ACF", "ukpsc.gov.in", "https://ukpsc.gov.in"),
            ("WII (Dehradun)", "JRF, project staff, PG diploma", "wii.gov.in", "https://wii.gov.in"),
            ("IIRS/ISRO (Dehradun)", "GIS and remote sensing posts", "iirs.gov.in", "https://www.iirs.gov.in"),
            ("GBPNIHE (Almora)", "Research associate, project staff", "gbpihed.gov.in", "https://gbpihed.gov.in"),
        ],
    },
    "karnataka": {
        "name": "Karnataka",
        "bodies": [
            ("Karnataka Forest Department", "Forest guard, ranger, forester", "aranya.gov.in", "https://aranya.gov.in"),
            ("KPSC", "State forest service, environment officer", "kpsc.kar.nic.in", "https://kpsc.kar.nic.in"),
            ("KSPCB", "Scientist, environmental engineer", "kspcb.gov.in", "https://kspcb.gov.in"),
            ("IISc (Bengaluru)", "JRF, PhD, project staff", "iisc.ac.in", "https://www.iisc.ac.in"),
            ("ATREE (Bengaluru)", "Research associate, project staff", "atree.org", "https://www.atree.org"),
        ],
    },
    "maharashtra": {
        "name": "Maharashtra",
        "bodies": [
            ("Maharashtra Forest Department", "Forest guard, ranger, forester", "mahaforest.gov.in", "https://mahaforest.gov.in"),
            ("MPSC", "State forest service, environment officer", "mpsc.gov.in", "https://mpsc.gov.in"),
            ("MPCB", "Scientist, environmental engineer", "mpcb.gov.in", "https://mpcb.gov.in"),
            ("Tadoba Tiger Reserve", "Field biologist, research posts", "mahaforest.gov.in", "https://mahaforest.gov.in"),
        ],
    },
    "tamil-nadu": {
        "name": "Tamil Nadu",
        "bodies": [
            ("Tamil Nadu Forest Department", "Forest guard, ranger, forester", "tnforest.gov.in", "https://www.tnforest.gov.in"),
            ("TNPSC", "State forest service, environment officer", "tnpsc.gov.in", "https://www.tnpsc.gov.in"),
            ("TNPCB", "Scientist, environmental engineer", "tnpcb.gov.in", "https://tnpcb.gov.in"),
            ("ATREE / IIT Madras", "Research associate, project staff", "atree.org", "https://www.atree.org"),
        ],
    },
    "gujarat": {
        "name": "Gujarat",
        "bodies": [
            ("Gujarat Forest Department", "Forest guard, ranger, forester", "forest.gujarat.gov.in", "https://forest.gujarat.gov.in"),
            ("GPSC", "State forest service, environment officer", "gpsc.gujarat.gov.in", "https://gpsc.gujarat.gov.in"),
            ("GPCB", "Scientist, environmental engineer", "gpcb.gov.in", "https://gpcb.gov.in"),
            ("SPIPA", "CM Fellowship, governance fellow", "spipa.gujarat.gov.in", "https://spipa.gujarat.gov.in"),
        ],
    },
    "delhi": {
        "name": "Delhi (NCR)",
        "bodies": [
            ("Delhi Forest Department", "Forest guard, ranger", "forest.delhi.gov.in", "https://forest.delhi.gov.in"),
            ("UPSC", "IFS, central government posts", "upsc.gov.in", "https://upsc.gov.in"),
            ("CPCB (HQ Delhi)", "Scientist, engineer", "cpcb.nic.in", "https://cpcb.nic.in"),
            ("TERI, CEEW, WRI India", "Research associate, policy analyst", "teriin.org", "https://www.teriin.org"),
        ],
    },
    "west-bengal": {
        "name": "West Bengal",
        "bodies": [
            ("West Bengal Forest Department", "Forest guard, ranger, forester", "forest.wb.gov.in", "https://forest.wb.gov.in"),
            ("WBPSC", "State forest service, environment officer", "wbpsc.gov.in", "https://wbpsc.gov.in"),
            ("WBPCB", "Scientist, environmental engineer", "wbpcb.gov.in", "https://wbpcb.gov.in"),
            ("IISER Kolkata", "JRF, PhD, project staff", "iiserkol.ac.in", "https://www.iiserkol.ac.in"),
        ],
    },
}


def build_state_page(slug: str, data: Dict[str, Any]) -> None:
    state_name = data["name"]
    bodies = data["bodies"]
    # match jobs by state
    state_jobs = [j for j in JOBS if str(j.get("state") or "").lower() == state_name.lower() or state_name.lower() in str(j.get("state") or "").lower()]
    state_jobs.sort(key=lambda j: str(j.get("valid_through") or "9999"))

    body_rows = "\n".join(
        f'            <tr><td><strong>{esc(b[0])}</strong></td><td>{esc(b[1])}</td><td>Notification-driven; check portal</td><td><a href="{b[3]}" target="_blank" rel="noopener noreferrer">{esc(b[2])} &nearr;</a></td></tr>'
        for b in bodies
    )

    body = "\n".join([
        hero("State recruitment", f"Green Job Recruitment in {state_name}", f"Recruiting bodies, portals and live openings for environment, forestry and sustainability roles in {state_name}.", [("Bodies tracked", str(len(bodies))), ("Live openings", str(len(state_jobs))), ("Updated", TODAY.strftime("%d %b %Y"))]),
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Recruiting bodies in {esc(state_name)}</h2>
        <p>Each row points to the official portal. Notification dates change every cycle.</p>
        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>Body</th><th>What they recruit</th><th>Cycle</th><th>Portal</th></tr></thead>
            <tbody>
{body_rows}
            </tbody>
          </table>
        </div>
      </div>
    </section>""",
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Live openings in {esc(state_name)} ({len(state_jobs)})</h2>
        <p>Sorted by closing date.</p>
        <div class="hub-list">
{cards(state_jobs[:12]) if state_jobs else '<p class="hub-empty">No live opening in this state today. New vacancies are added daily.</p>'}
        </div>
      </div>
    </section>""",
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Related pages</h2>
        <ul class="check-list">
          <li><a href="/bharat-regional-green-jobs">All states</a></li>
          <li><a href="/government-environment-jobs">Government recruitment tracker</a></li>
          <li><a href="/exams">Exam and eligibility guides</a></li>
          <li><a href="/green-careers">Green career pathways</a></li>
        </ul>
      </div>
    </section>""",
        beh.bsp.faq_section_html([
            (f"Is there a single exam for {state_name}?", "No. Each body runs its own recruitment. State PSCs conduct gazetted posts; departments conduct field posts."),
            ("How do I stay updated?", "Check the portals listed above weekly during recruitment season. The registry lists vacancies as they are published."),
            ("Are these government jobs?", "Most are state government posts. Some are contractual project positions funded by central schemes."),
        ]),
    ])
    jsonld = "\n".join([
        beh.bsp.organization_jsonld(),
        beh.bsp.website_jsonld(),
        beh.breadcrumb(f"Green jobs in {state_name}", f"{SITE}/state-recruitment/{slug}"),
    ])
    write_sub(PUBLIC, f"state-recruitment/{slug}", shell(
        title=f"Green Job Recruitment in {state_name}: Bodies, Portals & Openings",
        description=f"Recruiting bodies, official portals and live openings for environment, forestry and sustainability roles in {state_name}.",
        canonical=f"{SITE}/state-recruitment/{slug}",
        body=body,
        jsonld=jsonld,
    ))


def build_state_index() -> None:
    state_cards = "\n".join(
        f"""        <article class="hub-card">
          <h3 class="hub-card-title"><a href="/state-recruitment/{slug}">{esc(data['name'])}</a></h3>
          <p class="hub-card-sum">{len(data['bodies'])} recruiting bodies tracked.</p>
          <p class="hub-card-foot"><span>{len([j for j in JOBS if str(j.get('state') or '').lower() == data['name'].lower() or data['name'].lower() in str(j.get('state') or '').lower()])} live opening(s)</span>
            <a href="/state-recruitment/{slug}">View &rarr;</a></p>
        </article>"""
        for slug, data in STATE_BODIES.items()
    )
    body = "\n".join([
        hero("State recruitment", "State-Wise Green Job Recruitment in India", "Recruiting bodies, portals and live openings for environment, forestry and sustainability roles, state by state.", [("States", str(len(STATE_BODIES))), ("Updated", TODAY.strftime("%d %b %Y"))]),
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Choose a state</h2>
        <p>Each page lists the bodies that recruit in that state, their portals and the live openings in the registry.</p>
        <div class="hub-list">
{state_cards}
        </div>
      </div>
    </section>""",
        beh.bsp.faq_section_html([
            ("Why only 8 states?", "These are the states with the most green-job activity and verified recruiting bodies. More states will be added as listings accumulate."),
            ("Are these government jobs only?", "Mostly state government and public sector, but private and NGO roles in that state are also listed."),
            ("How do I stay updated?", "Check the portals weekly during recruitment season. The registry lists vacancies as they are published."),
        ]),
    ])
    # write to subdirectory
    (PUBLIC / "state-recruitment").mkdir(parents=True, exist_ok=True)
    write_sub(PUBLIC, "state-recruitment-index", shell(
        title="State-Wise Green Job Recruitment in India",
        description="Recruiting bodies, official portals and live openings for environment, forestry and sustainability roles, state by state.",
        canonical=f"{SITE}/state-recruitment",
        body=body,
        jsonld="\n".join([beh.bsp.organization_jsonld(), beh.bsp.website_jsonld(), beh.breadcrumb("State-Wise Recruitment", f"{SITE}/state-recruitment")]),
    ))
    # rename the file
    src = PUBLIC / "state-recruitment-index.html"
    dst = PUBLIC / "state-recruitment" / "index.html"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.exists():
        if dst.exists():
            dst.unlink()
        src.rename(dst)


def main() -> None:
    (PUBLIC / 'state-recruitment').mkdir(parents=True, exist_ok=True)
    for slug, data in STATE_BODIES.items():
        build_state_page(slug, data)
    build_state_index()
    paths = ["/state-recruitment"] + [f"/state-recruitment/{s}" for s in STATE_BODIES]
    beh.update_sitemap(paths)
    print(f"Wrote {len(STATE_BODIES)} state recruitment pages + index")


if __name__ == "__main__":
    main()
