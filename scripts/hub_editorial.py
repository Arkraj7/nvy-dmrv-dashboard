#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Data-driven editorial blocks for career-pathway hub pages.

Many hubs are scaffolded before they accumulate enough live listings to pass
the job-count streak gate. Rather than publishing a thin, near-duplicate page,
each hub now gets:

* a hiring snapshot computed from the live registry (counts, tracks,
  employers, experience mix, remote share);
* a short local or track-specific context paragraph;
* substantive FAQs that answer what candidates actually ask.

The editorial block is what makes a low-listing hub worth indexing. It is
rendered by ``build_seo_pages.build_hub_page`` and also feeds the FAQPage
JSON-LD, so the structured data always matches visible copy.
"""
from __future__ import annotations

import html
from collections import Counter
from datetime import date
from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Local context
# ---------------------------------------------------------------------------

CITY_CONTEXT: Dict[str, str] = {
    "ahmedabad": (
        "Ahmedabad combines a large environmental-consulting market with "
        "Gujarat's industrial compliance system. The Space Applications Centre, "
        "an ISRO earth-observation facility, also gives the city an unusually "
        "deep geospatial talent pool."
    ),
    "bengaluru": (
        "Bengaluru concentrates India's environmental research and climate-policy "
        "ecosystem: IISc, ATREE, WRI India and CSTEP all run programmes from the "
        "city. ESG teams at its IT, consulting and financial firms add a steady "
        "stream of corporate sustainability roles."
    ),
    "bhopal": (
        "Bhopal is a forestry and conservation hub. The Indian Institute of Forest "
        "Management and the state's Environmental Planning and Coordination "
        "Organisation are based here, and the surrounding landscape supports "
        "wildlife, watershed and rural-livelihood work."
    ),
    "chennai": (
        "Chennai pairs coastal and marine research with a dense manufacturing base. "
        "IIT Madras, Anna University and the M. S. Swaminathan Research Foundation "
        "are here, while the Tamil Nadu Pollution Control Board anchors compliance "
        "hiring."
    ),
    "coimbatore": (
        "Coimbatore's environmental market runs through agriculture, textiles and "
        "conservation science. Tamil Nadu Agricultural University and the Salim Ali "
        "Centre for Ornithology and Natural History are both based in the district."
    ),
    "dehradun": (
        "Dehradun is India's forestry and remote-sensing capital. The Forest "
        "Research Institute, Wildlife Institute of India and Indian Institute of "
        "Remote Sensing are all headquartered here, which keeps field, GIS and "
        "policy roles concentrated in one city."
    ),
    "delhi": (
        "Delhi is the policy and regulatory centre of the sector. The Ministry of "
        "Environment, Forest and Climate Change, the Central Pollution Control "
        "Board, TERI, CSE and the India offices of UNDP and WRI all hire from the "
        "capital."
    ),
    "gurugram": (
        "Gurugram's environmental hiring is corporate-first. Sustainability and ESG "
        "teams across the NCR office market, renewable-energy developers and "
        "consultancies serving industrial clients account for most openings."
    ),
    "hyderabad": (
        "Hyderabad mixes agricultural research, life sciences and corporate ESG. "
        "ICRISAT operates from Patancheru on the city's edge, and the Telangana "
        "Pollution Control Board and the pharma sector drive compliance and EHS "
        "roles."
    ),
    "jaipur": (
        "Jaipur's green-economy hiring is shaped by Rajasthan's solar and wind "
        "build-out. The state pollution control board, environmental consultancies "
        "and a growing renewable-energy services sector account for most roles."
    ),
    "kochi": (
        "Kochi's environmental work is coastal and marine. The Central Marine "
        "Fisheries Research Institute, Cochin University of Science and Technology "
        "and the Kerala Pollution Control Board anchor research, fisheries and "
        "compliance roles."
    ),
    "kolkata": (
        "Kolkata combines wetland and delta research with industrial compliance. "
        "Jadavpur University, the West Bengal Pollution Control Board and "
        "conservation groups working across the Sundarbans support a mix of field, "
        "lab and policy work."
    ),
    "mumbai": (
        "Mumbai's environmental market spans finance, consulting and coastal "
        "regulation. ESG teams at banks and consultancies, the Maharashtra "
        "Pollution Control Board and research groups such as WRI India and TERI "
        "generate openings across the spectrum."
    ),
    "noida": (
        "Noida's environmental hiring is dominated by corporate ESG and consulting "
        "teams serving the NCR. Industrial compliance roles tied to the Yamuna belt "
        "and the city's manufacturing clusters add to the mix."
    ),
    "patna": (
        "Patna's environmental work centres on flood and water management. The "
        "Bihar Pollution Control Board and NGO-led rural development programmes are "
        "the main employers, with growing demand for GIS and disaster-risk skills."
    ),
    "pune": (
        "Pune combines automotive and manufacturing sustainability with research. "
        "IISER Pune, TERI's Pune office and the Maharashtra Pollution Control Board "
        "support a steady flow of EHS, ESG and geospatial roles."
    ),
}

STATE_CONTEXT: Dict[str, str] = {
    "bihar": (
        "Bihar's environmental hiring is concentrated in flood management, water "
        "resources, agriculture and state pollution control. NGO and donor-funded "
        "programmes are active across the Gangetic plain."
    ),
    "gujarat": (
        "Gujarat's industrial corridor drives EIA, compliance and ESG roles, while "
        "solar and wind capacity in Kutch and Saurashtra supports renewable-energy "
        "hiring."
    ),
    "karnataka": (
        "Karnataka combines Bengaluru's research and ESG ecosystem with "
        "renewable-energy and forestry work across the Western Ghats."
    ),
    "kerala": (
        "Kerala's environmental market is coastal and biodiversity-rich, spanning "
        "marine research, disaster resilience and local self-government programmes."
    ),
    "madhya-pradesh": (
        "Madhya Pradesh runs some of India's largest forestry, wildlife and "
        "watershed programmes, with Bhopal as the administrative and research base."
    ),
    "rajasthan": (
        "Rajasthan leads India's solar and wind build-out, and its environmental "
        "hiring reflects that: renewable energy, water management and desert "
        "ecology."
    ),
    "tamil-nadu": (
        "Tamil Nadu pairs coastal and marine research with a large manufacturing "
        "base, generating demand for EHS, ESG and environmental-compliance roles."
    ),
    "telangana": (
        "Telangana's environmental hiring spans agricultural research, life "
        "sciences and corporate sustainability in and around Hyderabad."
    ),
    "uttarakhand": (
        "Uttarakhand's forest cover and Himalayan ecosystems support forestry, "
        "wildlife, disaster-risk and remote-sensing work, with Dehradun as the hub."
    ),
    "west-bengal": (
        "West Bengal's environmental work spans delta and wetland ecology, "
        "industrial compliance in the Kolkata belt and conservation across the "
        "Sundarbans."
    ),
    "delhi-ncr": (
        "Delhi NCR concentrates policy, regulation and corporate sustainability. "
        "The capital's ministries and pollution-control bodies sit alongside ESG "
        "teams and consultancies across Gurugram and Noida."
    ),
    "maharashtra": (
        "Maharashtra combines Mumbai's finance and consulting market with "
        "industrial compliance in Pune and the state's manufacturing belt."
    ),
}

CATEGORY_CONTEXT: Dict[str, str] = {
    "workshops-training-capacity-building": (
        "Workshops and training programmes are the fastest route into the sector "
        "for candidates without a direct research background. Providers range from "
        "government academies and pollution-control boards to NGOs, universities "
        "and consultancies. Most are short, applied and priced low or free."
    ),
    "conferences-summits-events": (
        "Conferences and summits are where hiring leads, research collaborations "
        "and policy updates surface first. Indian editions range from single-day "
        "city meet-ups to multi-day international summits, and many are free for "
        "students."
    ),
    "visiting-fellowships-short-term-research": (
        "Visiting fellowships let mid-career researchers spend three to twelve "
        "months with a host institution. They are useful for building a publication "
        "record, learning a new method or bridging between a PhD and a permanent "
        "post."
    ),
    "ambassador-fellowship-programs": (
        "Ambassador programmes are part-time, remote-friendly roles that combine "
        "outreach, community building and content. They suit students and "
        "early-career professionals who want sector exposure without a full-time "
        "commitment."
    ),
    "memberships-community-programs": (
        "Professional memberships signal specialisation and unlock networks, "
        "journals and event discounts. Many Indian and international bodies offer "
        "student and early-career rates."
    ),
    "webinars-live-events": (
        "Webinars and live events are low-commitment ways to build sector knowledge "
        "and meet practitioners. Most are free, recorded and open to candidates "
        "outside the host city."
    ),
    "entry-level-environmental-jobs": (
        "Entry-level environmental roles span field assistant, research trainee, "
        "EHS associate, GIS analyst and sustainability analyst positions. Employers "
        "usually value a relevant master's degree, a short internship and "
        "demonstrable field or software skills."
    ),
    "esg-jobs-for-freshers": (
        "ESG fresher roles cluster around BRSR and GRI reporting, carbon "
        "accounting, EHS compliance and climate-risk analysis. Consultancies and "
        "listed companies hire graduates from environmental science, engineering, "
        "commerce and management backgrounds."
    ),
    "gis-remote-sensing-climate-jobs": (
        "GIS and remote-sensing roles turn satellite and field data into land-use, "
        "forest, water and disaster-risk information. Employers include research "
        "institutes, government mapping agencies, consultancies and agri-tech or "
        "climate-tech companies."
    ),
    "phd-fellowships-climate-sustainability": (
        "PhD fellowships fund three to five years of full-time research and usually "
        "include a stipend, travel support and a host-institution affiliation. "
        "Competition is high; a clear research question and a supervisor who has "
        "already agreed to host you matter more than a long CV."
    ),
    "remote-environmental-jobs": (
        "Remote environmental roles are concentrated in research, data analysis, "
        "GIS, reporting and communications. They suit candidates who can work "
        "independently and document their output clearly; field roles are rarely "
        "fully remote."
    ),
}

CITY_LABELS = {
    "ahmedabad": "Ahmedabad",
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "bhopal": "Bhopal",
    "chennai": "Chennai",
    "coimbatore": "Coimbatore",
    "dehradun": "Dehradun",
    "delhi": "Delhi",
    "gurugram": "Gurugram",
    "hyderabad": "Hyderabad",
    "jaipur": "Jaipur",
    "kochi": "Kochi",
    "kolkata": "Kolkata",
    "mumbai": "Mumbai",
    "noida": "Noida",
    "patna": "Patna",
    "pune": "Pune",
}

STATE_LABELS = {
    "bihar": "Bihar",
    "gujarat": "Gujarat",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "madhya-pradesh": "Madhya Pradesh",
    "rajasthan": "Rajasthan",
    "tamil-nadu": "Tamil Nadu",
    "telangana": "Telangana",
    "uttarakhand": "Uttarakhand",
    "west-bengal": "West Bengal",
    "delhi-ncr": "Delhi NCR",
    "maharashtra": "Maharashtra",
}

CATEGORY_LABELS = {
    "workshops-training-capacity-building": "workshops and training",
    "conferences-summits-events": "conferences and summits",
    "visiting-fellowships-short-term-research": "visiting fellowships",
    "ambassador-fellowship-programs": "ambassador programmes",
    "memberships-community-programs": "memberships",
    "webinars-live-events": "webinars and live events",
    "entry-level-environmental-jobs": "entry-level environmental jobs",
    "esg-jobs-for-freshers": "ESG fresher roles",
    "gis-remote-sensing-climate-jobs": "GIS and remote-sensing jobs",
    "phd-fellowships-climate-sustainability": "PhD fellowships",
    "remote-environmental-jobs": "remote environmental jobs",
}

CATEGORY_NOUNS = {
    "workshops-training-capacity-building": "workshops and training programmes",
    "conferences-summits-events": "conferences, summits and events",
    "visiting-fellowships-short-term-research": "visiting fellowships",
    "ambassador-fellowship-programs": "ambassador programmes",
    "memberships-community-programs": "memberships and community programmes",
    "webinars-live-events": "webinars and live events",
    "entry-level-environmental-jobs": "entry-level environmental jobs",
    "esg-jobs-for-freshers": "ESG fresher roles",
    "gis-remote-sensing-climate-jobs": "GIS and remote-sensing jobs",
    "phd-fellowships-climate-sustainability": "PhD fellowships",
    "remote-environmental-jobs": "remote environmental jobs",
}

_CITY_PREFIXES = ("environmental-jobs-", "esg-jobs-", "esg-sustainability-jobs-")

# The ESG city slug uses the older spelling; the context block is keyed on the
# current official name.
CITY_ALIASES = {"bangalore": "bengaluru"}


def _city_key(slug: str) -> str:
    return CITY_ALIASES.get(slug, slug)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _plain(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _esc(value: Any) -> str:
    return html.escape(_plain(value), quote=True)


def _classify(hub_file: str) -> Tuple[str, str]:
    """Return (kind, slug) where kind is city, state or category."""
    stem = hub_file.removesuffix(".html")
    if stem.startswith("environmental-jobs-"):
        return "city", stem[len("environmental-jobs-"):]
    if stem.startswith("esg-jobs-"):
        slug = stem[len("esg-jobs-"):]
        if slug == "for-freshers":
            return "category", "esg-jobs-for-freshers"
        return "city", slug
    if stem.startswith("esg-sustainability-jobs-"):
        return "state", stem[len("esg-sustainability-jobs-"):]
    return "category", stem


def _place_label(hub: Dict[str, Any], kind: str, slug: str) -> str:
    if kind == "city":
        return CITY_LABELS.get(slug, slug.replace("-", " ").title())
    if kind == "state":
        return STATE_LABELS.get(slug, slug.replace("-", " ").title())
    return CATEGORY_LABELS.get(slug, _plain(hub.get("h1")) or "this track")


def _track_noun(hub_file: str, kind: str, slug: str) -> str:
    if kind == "city":
        if hub_file.startswith("esg-"):
            return "ESG and sustainability jobs"
        return "environmental and climate jobs"
    if kind == "state":
        return "ESG and sustainability jobs"
    return CATEGORY_NOUNS.get(slug, "roles")


def _context(kind: str, slug: str) -> str:
    if kind == "city":
        return CITY_CONTEXT.get(_city_key(slug), "")
    if kind == "state":
        return STATE_CONTEXT.get(slug, "")
    return CATEGORY_CONTEXT.get(slug, "")


def _top(counter: Counter, limit: int) -> List[Tuple[str, int]]:
    return [(value, count) for value, count in counter.most_common(limit) if value]


def _remote_count(jobs: List[Dict[str, Any]]) -> int:
    remote = 0
    for job in jobs:
        haystack = " ".join(
            _plain(job.get(key))
            for key in ("city", "state", "region", "employment_type", "clean_title")
        ).casefold()
        if "remote" in haystack or "hybrid" in haystack or "work from home" in haystack:
            remote += 1
    return remote


def _join(values: List[str]) -> str:
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    return ", ".join(values[:-1]) + " and " + values[-1]


def _faq_city(
    place: str,
    track: str,
    jobs: List[Dict[str, Any]],
    today: date,
) -> List[Tuple[str, str]]:
    count = len(jobs)
    employers = [org for org, _ in _top(Counter(_plain(j.get("organization")) for j in jobs), 4)]
    remote = _remote_count(jobs)
    role_word = "role is" if count == 1 else "roles are"
    faqs: List[Tuple[str, str]] = [
        (
            f"How many {track} are open in {place} right now?",
            f"{count} verified {role_word} live in this hub as of {today:%d %B %Y}. "
            "The registry refreshes every morning at 7 AM IST, so the count changes "
            "as roles open and deadlines pass.",
        ),
        (
            f"Which organisations are hiring for {track} in {place}?",
            (
                f"Current listings include {_join(employers)}. Each card links to the "
                "employer's official notice or application page, where you can confirm "
                "the reporting line, location and closing date."
                if employers
                else f"No employer is listed in this hub today. New openings are added "
                "daily; in the meantime, browse the full registry for all-India and "
                "remote roles in the same track."
            ),
        ),
        (
            "What qualifications do these roles usually require?",
            (
                "ESG roles usually ask for a degree in environmental science, "
                "engineering, commerce or management, plus familiarity with BRSR or "
                "GRI reporting, carbon accounting or EHS compliance. Each card states "
                "the exact requirement from the official notice."
                if track.startswith("ESG")
                else "Most listings ask for a master's degree in environmental science, "
                "forestry, ecology, geography, engineering or management, plus relevant "
                "field, compliance or software experience. Each card states the exact "
                "requirement from the official notice, so check it before applying."
            ),
        ),
        (
            f"Are remote or hybrid roles available in {place}?",
            (
                f"{remote} of the {count} current listings are remote or hybrid."
                if count
                else "Remote and hybrid roles appear in the dedicated remote track; "
                "this hub lists on-site and city-based positions."
            ),
        ),
        (
            f"How do I apply for a role in {place}?",
            "Open the card, review the eligibility and deadline, then use the apply "
            "link to reach the official page or email address. The registry never "
            "asks for a fee and does not act as an intermediary.",
        ),
    ]
    return faqs


def _faq_category(
    label: str,
    noun: str,
    jobs: List[Dict[str, Any]],
    today: date,
) -> List[Tuple[str, str]]:
    count = len(jobs)
    employers = [org for org, _ in _top(Counter(_plain(j.get("organization")) for j in jobs), 4)]
    faqs: List[Tuple[str, str]] = [
        (
            f"How many {noun} are open right now?",
            f"{count} verified {'listing is' if count == 1 else 'listings are'} live in "
            f"this hub as of {today:%d %B %Y}. The registry refreshes every morning "
            "at 7 AM IST, so the count changes as deadlines pass and new calls open.",
        ),
        (
            f"Who runs {label} in India?",
            (
                f"Current listings come from {_join(employers)}. Each card links to the "
                "organiser's official page so you can confirm eligibility, fees and "
                "the exact schedule."
                if employers
                else "No organiser is listed today. New calls are added daily; browse "
                "the full registry for related opportunities in the same track."
            ),
        ),
        (
            "What should I check before applying?",
            (
                "Confirm the date, city or time zone, fee and registration deadline. "
                if label in (
                    "workshops and training",
                    "conferences and summits",
                    "webinars and live events",
                )
                else "Confirm the host institution, duration, stipend and application "
                "window. "
                if label in ("visiting fellowships", "PhD fellowships")
                else "Confirm the commitment, eligibility and fee. "
                if label in ("ambassador programmes", "memberships")
                else "Confirm the format, fee or stipend, eligibility and closing date. "
            )
            + "Cards state these from the official notice; if a detail is missing, "
            "use the organiser's page rather than assuming.",
        ),
        (
            "Is there a cost to use this registry?",
            "No. Urban Forest Park lists verified opportunities and links to the "
            "official application page or email address. It never charges candidates "
            "and does not act as an intermediary.",
        ),
    ]
    return faqs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def is_editorial_ready(hub_file: str) -> bool:
    """True when the hub has a real context block and generated FAQs."""
    kind, slug = _classify(hub_file)
    if kind == "city":
        return _city_key(slug) in CITY_CONTEXT
    if kind == "state":
        return slug in STATE_CONTEXT
    return slug in CATEGORY_CONTEXT


def editorial_for(
    hub: Dict[str, Any],
    jobs: List[Dict[str, Any]],
    today: date,
) -> Dict[str, Any]:
    """Return {html, faqs, ready} for a hub page."""
    hub_file = _plain(hub.get("file"))
    kind, slug = _classify(hub_file)
    place = _place_label(hub, kind, slug)
    track = _track_noun(hub_file, kind, slug)
    context = _context(kind, slug)
    count = len(jobs)
    ready = bool(context)

    categories = _top(Counter(_plain(j.get("category")) for j in jobs), 3)
    employers = _top(Counter(_plain(j.get("organization")) for j in jobs), 4)
    experience = _top(Counter(_plain(j.get("experience_level")) for j in jobs), 3)
    remote = _remote_count(jobs)

    snapshot: List[str] = []
    if count:
        snapshot.append(
            f"<li><strong>{count}</strong> verified "
            f"{'role' if count == 1 else 'roles'} open right now</li>"
        )
        if categories:
            detail = "; ".join(f"{_esc(name)} ({n})" for name, n in categories)
            snapshot.append(f"<li><strong>Top tracks:</strong> {detail}</li>")
        if employers:
            detail = ", ".join(_esc(name) for name, _ in employers)
            snapshot.append(f"<li><strong>Hiring organisations:</strong> {detail}</li>")
        if experience:
            detail = "; ".join(f"{_esc(name)} ({n})" for name, n in experience)
            snapshot.append(f"<li><strong>Experience mix:</strong> {detail}</li>")
        snapshot.append(
            f"<li><strong>Remote / hybrid:</strong> {remote} of {count}</li>"
        )
    else:
        snapshot.append(
            "<li><strong>0</strong> verified roles open today &mdash; new openings "
            "are added daily</li>"
        )
    snapshot.append(
        f"<li><strong>Last refreshed:</strong> {today:%d %B %Y} IST</li>"
    )

    if kind in ("city", "state"):
        if hub_file.startswith("esg-"):
            work = (
                f"ESG roles in {_esc(place)} cluster around BRSR and GRI reporting, "
                "carbon accounting, EHS compliance and climate-risk analysis. "
                "Employers range from listed companies and consultancies to banks "
                "and asset managers."
            )
        else:
            work = (
                f"Roles in {_esc(place)} range from field ecology and forestry to "
                "environmental impact assessment, pollution monitoring, GIS and "
                "sustainability reporting. Field posts usually ask for a master's in "
                "environmental science, forestry, ecology or a related discipline; "
                "consulting and corporate roles add compliance, data and reporting "
                "skills."
            )
        how = (
            "Use the cards below to compare employers, eligibility and deadlines. "
            "Every listing links to the official application page or email address. "
            "The registry does not charge candidates or act as an intermediary, and "
            "closed roles move to the archive instead of disappearing."
        )
    else:
        work = (
            f"This hub tracks {_esc(track)} across India. Listings are checked against "
            "the organiser's official page before publishing, and expired calls are "
            "moved to the archive rather than left online."
        )
        if slug in (
            "workshops-training-capacity-building",
            "conferences-summits-events",
            "webinars-live-events",
        ):
            how = (
                "Check the date, city or time zone, fee and registration deadline "
                "before committing. Cards link to the organiser's page; the registry "
                "does not charge candidates or act as an intermediary."
            )
        elif slug in (
            "visiting-fellowships-short-term-research",
            "phd-fellowships-climate-sustainability",
        ):
            how = (
                "Check the host institution, duration, stipend and application window "
                "before applying. Cards link to the official call; the registry does "
                "not charge candidates or act as an intermediary."
            )
        elif slug in (
            "ambassador-fellowship-programs",
            "memberships-community-programs",
        ):
            how = (
                "Check the commitment, eligibility and fee before applying. Cards link "
                "to the official programme page; the registry does not charge "
                "candidates or act as an intermediary."
            )
        else:
            how = (
                "Use the cards below to compare employers, eligibility and deadlines. "
                "Every listing links to the official application page or email "
                "address; the registry does not charge candidates or act as an "
                "intermediary."
            )

    if count:
        market = (
            f"The current mix is weighted toward {_esc(categories[0][0])} "
            f"({categories[0][1]} {'role' if categories[0][1] == 1 else 'roles'})"
            if categories
            else "The current mix spans several tracks"
        )
        if employers:
            market += f", with {_esc(employers[0][0])} among the employers listed"
        market += "."
        if len(experience) > 1:
            market += (
                f" The experience mix includes {_esc(experience[0][0])} and "
                f"{_esc(experience[1][0])} roles."
            )
        market += (
            " Counts move as roles open and close, so treat this as a snapshot "
            "rather than a fixed establishment."
        )
    elif kind in ("city", "state"):
        market = (
            f"No roles are listed in {_esc(place)} today. The hub stays live because "
            "the local market is active; new openings are added daily and the archive "
            "shows what closed recently."
        )
    else:
        market = (
            "No listings are open in this track today. The hub stays live because "
            "calls are cyclical; new ones are added daily and the archive shows what "
            "closed recently."
        )

    html_block = f"""      <section class="hub-editorial" aria-labelledby="hub-editorial-title">
        <h2 id="hub-editorial-title">{_esc(place)} hiring snapshot</h2>
        <p>{_esc(context)}</p>
        <ul class="hub-snapshot">
          {''.join(snapshot)}
        </ul>
        <p>{market}</p>
        <h3>What the work looks like</h3>
        <p>{work}</p>
        <h3>How to use this page</h3>
        <p>{how}</p>
      </section>"""

    if kind in ("city", "state"):
        generated = _faq_city(place, track, jobs, today)
    else:
        generated = _faq_category(place, track, jobs, today)

    existing = [
        (q, a)
        for q, a in (hub.get("faqs") or [])
        if "scaffolded" not in _plain(a).casefold()
        and "is this hub currently live" not in _plain(q).casefold()
    ]
    seen = set()
    faqs: List[Tuple[str, str]] = []
    for question, answer in existing + generated:
        key = _plain(question).casefold()
        if key and key not in seen:
            seen.add(key)
            faqs.append((question, answer))
    faqs = faqs[:6]

    return {"html": html_block, "faqs": faqs, "ready": ready}
