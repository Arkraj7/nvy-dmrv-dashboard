#!/usr/bin/env python3
"""Build the evergreen exam guides (/exams) and role salary profiles (/roles).

Why this exists
---------------
Two search clusters the registry cannot answer on its own:

* people search "forest guard recruitment eligibility" for months before a
  notification exists, and
* people search "ESG analyst salary" without wanting a job card.

Both pages are still generated from the same verified registry. Exam guides
never assert a cycle date or a pay figure that is not published: they point at
the official portal and say so. Role profiles reproduce advertised pay verbatim
and state how many listings actually disclose a number.

Run after build_expansion_hubs.py:

    py scripts/build_exam_role_pages.py
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

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

EXAMS_DIR = PUBLIC / "exams"
ROLES_DIR = PUBLIC / "roles"
INDIA = beh.active(beh.load(beh.JOBS_PATH))
GLOBAL = beh.active(beh.load(beh.GLOBAL_PATH))
POOL = INDIA + GLOBAL


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def job_text(job: Dict[str, Any], *keys: str) -> str:
    return " ".join(str(job.get(key) or "") for key in keys).lower()


def title_of(job: Dict[str, Any]) -> str:
    return str(job.get("clean_title") or "").lower()


def org_of(job: Dict[str, Any]) -> str:
    return str(job.get("organization") or "").lower()


def match_any(*patterns: str) -> Callable[[Dict[str, Any]], bool]:
    compiled = [re.compile(pattern) for pattern in patterns]

    def matcher(job: Dict[str, Any]) -> bool:
        text = job_text(job, "clean_title", "category", "organization", "role_summary")
        return any(regex.search(text) for regex in compiled)

    return matcher


def match_org(*patterns: str) -> Callable[[Dict[str, Any]], bool]:
    compiled = [re.compile(pattern) for pattern in patterns]

    def matcher(job: Dict[str, Any]) -> bool:
        return any(regex.search(org_of(job)) for regex in compiled)

    return matcher


def discloses_pay(job: Dict[str, Any]) -> bool:
    text = plain(job.get("compensation_or_fellowship"))
    if not text:
        return False
    return not text.lower().startswith(("not disclosed", "as per", "no fee", "free"))


def pay_table(records: List[Dict[str, Any]], empty_note: str) -> str:
    paid = [j for j in records if discloses_pay(j)]
    if not paid:
        return f'        <p class="hub-empty">{esc(empty_note)}</p>'
    rows = []
    paid.sort(key=lambda j: str(j.get("date_added") or ""), reverse=True)
    for job in paid[:24]:
        title = plain(job.get("clean_title") or job.get("title")) or "Untitled listing"
        org = plain(job.get("organization")) or "Organisation not stated"
        place = plain(job.get("city")) or plain(job.get("state")) or "India"
        comp = plain(job.get("compensation_or_fellowship"))
        rows.append(
            f"""          <tr>
            <td><a href="{beh.bsp.job_url(job)}"><strong>{esc(beh.bsp.trim(title, 74))}</strong></a></td>
            <td>{esc(beh.bsp.trim(org, 44))}</td>
            <td>{esc(place)}</td>
            <td>{esc(beh.bsp.trim(comp, 96))}</td>
          </tr>"""
        )
    return f"""        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>Opportunity</th><th>Employer</th><th>Location</th><th>Pay as advertised</th></tr></thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
        </div>"""


def top_skills(records: List[Dict[str, Any]], limit: int = 10) -> List[str]:
    counter: Counter[str] = Counter()
    for job in records:
        for skill in job.get("must_have_skills") or []:
            value = plain(skill)
            if value:
                counter[value] += 1
    return [value for value, _count in counter.most_common(limit)]


def top_cities(records: List[Dict[str, Any]], limit: int = 6) -> List[Tuple[str, int]]:
    counter: Counter[str] = Counter()
    for job in records:
        city = plain(job.get("city")) or plain(job.get("state"))
        if city:
            counter[city] += 1
    return counter.most_common(limit)


def cards_block(jobs: List[Dict[str, Any]], empty_note: str) -> str:
    if not jobs:
        return f'        <p class="hub-empty">{esc(empty_note)}</p>'
    return '        <div class="hub-list">\n' + cards(jobs) + '\n        </div>'


def bullet_list(items: List[str]) -> str:    return "        <ul class=\"check-list\">\n" + "\n".join(
        f"          <li>{item}</li>" for item in items
    ) + "\n        </ul>"


def write_sub(dir_path: Path, slug: str, html: str) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / f"{slug}.html").write_text(html, encoding="utf-8")


def inject(html: str, marker: str, block: str) -> str:
    if marker in html:
        return html.replace(marker, block)
    return html.replace("</main>", block + "\n  </main>", 1)


def set_url(path: str, changefreq: str, priority: str) -> None:
    sitemap = PUBLIC / "sitemap.xml"
    text = sitemap.read_text(encoding="utf-8")
    loc = SITE + path
    entry = (
        f"  <url><loc>{loc}</loc><lastmod>{TODAY.isoformat()}</lastmod>"
        f"<changefreq>{changefreq}</changefreq><priority>{priority}</priority></url>"
    )
    pattern = re.compile(
        r"\s*<url><loc>" + re.escape(loc) + r"</loc>.*?</url>", re.S
    )
    if pattern.search(text):
        text = pattern.sub("\n" + entry, text, count=1)
    else:
        text = text.replace("</urlset>", entry + "\n</urlset>")
    sitemap.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Exam guides
# ---------------------------------------------------------------------------
EXAMS: List[Dict[str, Any]] = [
    {
        "slug": "indian-forest-service",
        "answer": "The Indian Forest Service is an All India Service recruited through the UPSC Civil Services Examination. A bachelor's degree in any discipline is required; selection runs prelims, mains, interview, medical, then training at IGNFA.",
        "name": "Indian Forest Service (IFS)",
        "short": "IFS exam",
        "h1": "Indian Forest Service (IFS) Exam: Eligibility, Stages & Notification",
        "title": "IFS Exam 2026: Eligibility, Selection Stages & Notification",
        "desc": (
            "How the Indian Forest Service is recruited through UPSC: eligibility, the "
            "prelims-mains-interview sequence, where the notification appears, and live forestry openings."
        ),
        "kicker": "National civil service",
        "sub": (
            "The Indian Forest Service is one of the All India Services. Officers are recruited "
            "through the Civil Services Examination and serve in state forest departments after training."
        ),
        "facts": [
            ("Recruiting body", "Union Public Service Commission (UPSC)"),
            ("Service type", "All India Service, Group A"),
            ("Where officers serve", "State forest departments, MoEFCC and attached institutions"),
            ("Application mode", "Online, through the UPSC portal"),
            ("Official portal", "upsc.gov.in"),
            ("Cycle", "Annual, listed in the UPSC examination calendar"),
        ],
        "eligibility_intro": (
            "The Civil Services Examination notification is the only authoritative source. "
            "These are the rules it has carried in recent cycles."
        ),
        "eligibility": [
            "<strong>Degree:</strong> a bachelor's degree in any discipline from a recognised university. Forestry is not a prerequisite at the application stage.",
            "<strong>Age and attempts:</strong> the notification fixes the age band, the number of attempts and category relaxations each year. Read the current PDF rather than an old blog post.",
            "<strong>Physical standards:</strong> the Indian Forest Service has its own medical and physical requirements, separate from the written examination.",
            "<strong>Deadline discipline:</strong> eligibility is judged on the closing date printed in the notice, not on the exam date.",
        ],
        "stages": [
            ("Preliminary examination", "Two objective papers: General Studies and CSAT. CSAT is qualifying; the General Studies score decides who reaches the mains."),
            ("Main examination", "Written papers covering essay, general studies, an optional subject and the language papers."),
            ("Personality test", "Interview at UPSC, weighted alongside the mains."),
            ("Medical examination", "IFS-specific physical and medical standards are applied after selection."),
            ("Training", "Foundation course followed by professional forestry training before posting."),
        ],
        "syllabus_intro": (
            "The syllabus is published inside the examination notification. It is not reproduced here "
            "because it is long and the optional-subject list changes."
        ),
        "syllabus": [
            "General studies papers cover history, polity, geography, economy, environment and current affairs.",
            "One optional subject is chosen from the commission's list; forestry, botany, zoology and agriculture are common choices, not requirements.",
            "Language papers test English and one Indian language at a qualifying standard.",
            "Previous-year papers and the syllabus PDF are published on upsc.gov.in.",
        ],
        "pay_note": (
            "Pay is fixed by the 7th CPC matrix for the service and stated in the notification; allowances "
            "depend on the posting. No IFS salary figure is asserted on this page because the registry does "
            "not carry a current, verifiable one."
        ),
        "watch": [
            "UPSC examination calendar and the active examinations list on upsc.gov.in",
            "The annual Civil Services Examination notification",
            "Employment News / Rozgar Samachar, where the notification is also published",
            "State forest department notices for deputation and specialist posts",
        ],
        "match": match_org(r"\bupsc\b"),
        "related_exam": "forest-range-officer",
        "related_role": "forest-guard",
        "faqs": [
            ("Is the IFS the same as a forest guard job?",
             "No. The Indian Forest Service is a national gazetted service recruited by UPSC. Forest guard and forester posts are state-level recruitments with their own written tests and physical standards."),
            ("Can I apply with a non-forestry degree?",
             "Yes. The examination is open to graduates of any discipline; forestry knowledge helps in the optional subject and interview, but it is not an application requirement."),
            ("When is the notification released?",
             "UPSC publishes an annual calendar, but the exact notification date changes each year. Check the portal rather than relying on a date from a previous cycle."),
        ],
    },
    {
        "slug": "forest-guard",
        "answer": "Forest guard is a state-level field post recruited by state forest departments. Eligibility is usually Class 10 or 12 plus physical standards; selection is a written test and a physical efficiency test.",
        "name": "Forest Guard",
        "short": "Forest guard",
        "h1": "Forest Guard Recruitment: Eligibility, Physical Test & Notification",
        "title": "Forest Guard Recruitment 2026: Eligibility, Physical Test & Dates",
        "desc": (
            "State-wise forest guard recruitment explained: written test, physical efficiency test, "
            "eligibility, where each state publishes its notification, and live field openings."
        ),
        "kicker": "State field post",
        "sub": (
            "Forest guard is the entry-level protection and field post in state forest departments. "
            "Every state runs its own recruitment, so eligibility and test pattern differ by state."
        ),
        "facts": [
            ("Recruiting body", "State forest departments (for example MP Forest, Odisha Forest)"),
            ("Service type", "State field post, usually non-gazetted"),
            ("Application mode", "State recruitment portal or district office, as notified"),
            ("Official portals", "mpforest.gov.in · forest.odisha.gov.in"),
            ("Cycle", "State-wise; some states recruit annually, others every few years"),
            ("Core duties", "Patrol, fire watch, plantation and nursery work, wildlife protection support"),
        ],
        "eligibility_intro": (
            "There is no national rule. These are the criteria states publish most often; the state "
            "notification for the current cycle overrides everything here."
        ),
        "eligibility": [
            "<strong>School qualification:</strong> usually Class 10 or Class 12. Some states accept either; a few ask for a forestry or agriculture certificate.",
            "<strong>Age:</strong> commonly 18 to 30 with category and state relaxations. The exact band is in the notification.",
            "<strong>Physical standards:</strong> height, chest and a running or walking test are standard. Measurements differ between states and between male and female candidates.",
            "<strong>Local requirements:</strong> some states require domicile, local language proficiency or a specified district preference.",
            "<strong>Documents:</strong> caste, domicile, education and physical-fitness certificates are checked before the appointment order.",
        ],
        "stages": [
            ("Written test", "Objective paper on general studies, environment and forestry awareness, arithmetic, reasoning and the state language."),
            ("Physical efficiency test", "Running or walking to a fixed distance within a time limit, plus measurement checks."),
            ("Document verification", "Original certificates, domicile and category proofs."),
            ("Medical examination", "Fitness for field duty, including vision and general health."),
        ],
        "syllabus_intro": (
            "States publish their own syllabus with the notification. The pattern below is the common core."
        ),
        "syllabus": [
            "General awareness with a state-specific section: geography, forests, wildlife and current schemes.",
            "Basic arithmetic and reasoning at school-leaving level.",
            "Language paper in the state's official language.",
            "Physical preparation matters as much as the written paper: start running to the state's standard months before the test.",
        ],
        "pay_note": (
            "Forest guard pay follows the state pay matrix for the post, plus allowances. The figure is "
            "printed in the notification. There is no national salary for this post, and no number is "
            "asserted here."
        ),
        "watch": [
            "The state forest department recruitment page (for example mpforest.gov.in)",
            "The state public service commission, when it conducts the recruitment",
            "District forest office notices for local vacancies",
            "Employment News and the state gazette",
        ],
        "match": match_any(r"forest guard", r"\bforester\b", r"\branger\b"),
        "related_exam": "forest-range-officer",
        "related_role": "forest-guard",
        "faqs": [
            ("Is forest guard a central government job?",
             "No. Forest guard posts are recruited by state forest departments under state rules, so pay, eligibility and test pattern vary by state."),
            ("Can I prepare for the physical test in a few weeks?",
             "Usually not. Most states set a running or walking standard that needs a few months of steady practice, so start well before the notification."),
            ("Do I need a forestry degree?",
             "For forest guard, no. A school-leaving certificate is the usual minimum. Forestry qualifications matter more for ranger and range officer posts."),
        ],
    },
    {
        "slug": "forest-range-officer",
        "answer": "Forest Range Officer is a gazetted state forest service post recruited through state PSCs. A bachelor's degree, often in science or forestry, is required, followed by a written exam, physical test and interview.",
        "name": "Forest Range Officer / ACF",
        "short": "RFO / ACF",
        "h1": "Forest Range Officer (RFO) & ACF Recruitment: Eligibility & Stages",
        "title": "Forest Range Officer (RFO) Recruitment 2026: Eligibility & Exam",
        "desc": (
            "State Forest Range Officer and Assistant Conservator of Forests recruitment: degree "
            "requirements, written exam and physical stages, and where each state publishes the notice."
        ),
        "kicker": "State forest service",
        "sub": (
            "Range officers run a forest range: enforcement, plantation targets, fire control and staff "
            "supervision. In most states the post is gazetted and recruited through the state PSC."
        ),
        "facts": [
            ("Recruiting body", "State public service commission or forest department"),
            ("Service type", "State Forest Service, usually gazetted"),
            ("Typical entry post", "Forest Range Officer / Assistant Conservator of Forests"),
            ("Application mode", "Online through the state PSC portal"),
            ("Example portal", "mpforest.gov.in"),
            ("Cycle", "State-wise; usually aligned to the state PSC calendar"),
        ],
        "eligibility_intro": (
            "States set their own rules. The recurring requirements are below; confirm the current "
            "advertisement before applying."
        ),
        "eligibility": [
            "<strong>Degree:</strong> a bachelor's degree, commonly in science, forestry, agriculture or engineering. Some states accept any discipline with a forestry diploma.",
            "<strong>Age:</strong> typically 21 to 30 with relaxations; the state notification fixes the band.",
            "<strong>Physical standards:</strong> height, chest and endurance tests, similar in spirit to forest guard but benchmarked separately.",
            "<strong>Experience:</strong> not usually required at entry, though field or research experience strengthens the interview.",
        ],
        "stages": [
            ("Preliminary test", "Objective screening where the state holds one."),
            ("Main written examination", "General studies plus forestry, environment and an optional science subject."),
            ("Physical test", "Endurance and measurement checks."),
            ("Interview", "Personality and subject interview before the commission."),
            ("Medical and training", "Fitness check followed by departmental training."),
        ],
        "syllabus_intro": (
            "The state PSC publishes the syllabus with the advertisement. These are the recurring subjects."
        ),
        "syllabus": [
            "General studies, state geography and current affairs.",
            "Forestry, silviculture, forest management and forest law.",
            "Botany, zoology or agriculture, depending on the optional paper offered.",
            "Environmental science and wildlife conservation basics.",
        ],
        "pay_note": (
            "Pay follows the state pay matrix for a gazetted forest post and is stated in the "
            "advertisement. No state-neutral figure exists, so none is asserted here."
        ),
        "watch": [
            "State public service commission notification page",
            "State forest department recruitment section",
            "State gazette and Employment News",
            "Departmental circulars for limited competitive exams for serving staff",
        ],
        "match": match_any(r"range officer", r"\brfo\b", r"assistant conservator"),
        "related_exam": "indian-forest-service",
        "related_role": "forest-guard",
        "faqs": [
            ("Is RFO the same as ACF?",
             "They are different posts in the same state forest service. ACF is generally the entry gazetted post in the state forest service, and RFO is the range-level post; the naming and ladder vary by state."),
            ("Can serving forest guards apply?",
             "Many states run a departmental or limited competitive examination for serving staff. Check the state's rules and circulars."),
            ("Is a forestry degree compulsory?",
             "Not everywhere. Several states accept science graduates, and some accept any degree with a forestry diploma. The advertisement decides."),
        ],
    },
    {
        "slug": "csir-jrf",
        "answer": "CSIR recruits Junior Research Fellows through the CSIR-UGC NET and project associates through institute advertisements. A master's in a relevant science subject is required; stipends follow funding-agency norms.",
        "name": "CSIR JRF & Project Associate",
        "short": "CSIR JRF",
        "h1": "CSIR JRF & Project Associate Recruitment: Eligibility & Selection",
        "title": "CSIR JRF 2026: Eligibility, CSIR-UGC NET & Project Associate Posts",
        "desc": (
            "How CSIR recruits Junior Research Fellows and project associates: CSIR-UGC NET "
            "eligibility, institute-wise interviews, stipend basis and live CSIR openings."
        ),
        "kicker": "National research fellowship",
        "sub": (
            "CSIR laboratories recruit research fellows through the national eligibility test and "
            "project staff through institute-level advertisements and walk-in interviews."
        ),
        "facts": [
            ("Recruiting body", "CSIR laboratories and institutes"),
            ("Qualifying exam", "CSIR-UGC NET, conducted by NTA"),
            ("Official portal", "csir.res.in"),
            ("Application mode", "Online test application; institute advertisements for project posts"),
            ("Cycle", "Exam cycle announced by NTA; institute posts advertised year-round"),
            ("Typical posts", "Junior Research Fellow, Senior Research Fellow, Project Associate"),
        ],
        "eligibility_intro": (
            "Two routes exist and they are often confused: the national fellowship route and the "
            "institute project route. The advertisement for the specific post is authoritative."
        ),
        "eligibility": [
            "<strong>For JRF:</strong> a master's degree in a relevant science subject plus a valid CSIR-UGC NET qualification, or an equivalent national test accepted by the institute.",
            "<strong>For project associate:</strong> a master's degree with the percentage and discipline stated in that institute's advertisement; some posts accept a bachelor's degree.",
            "<strong>Age:</strong> the CSIR-UGC NET information bulletin states the fellowship age limit and relaxations.",
            "<strong>Registration:</strong> a valid PhD registration may be required for SRF-level positions.",
        ],
        "stages": [
            ("National eligibility test", "CSIR-UGC NET for the JRF route; some institutes accept GATE or a PhD entrance score."),
            ("Institute shortlisting", "Applications screened against the advertisement's discipline and percentage rules."),
            ("Interview or walk-in", "A technical interview, sometimes combined with a written screening test."),
            ("Document verification", "Degree certificates, NET scorecard and category proofs."),
        ],
        "syllabus_intro": (
            "The CSIR-UGC NET syllabus is subject-specific and published by NTA with the information bulletin."
        ),
        "syllabus": [
            "Paper I covers aptitude, reasoning and research orientation.",
            "Paper II covers the chosen science subject in depth.",
            "For institute interviews, expect questions on your dissertation, lab techniques and the project's subject area.",
        ],
        "pay_note": (
            "Fellowship amounts follow the funding agency's norms and are printed in each advertisement; "
            "project associate pay is fixed by the institute's project rules. The registry reproduces the "
            "advertised figure for each post rather than a market average."
        ),
        "watch": [
            "CSIR institute websites and the central CSIR recruitment page",
            "NTA announcements for CSIR-UGC NET",
            "Institute notice boards and walk-in interview notices",
            "The registry's academic and research category",
        ],
        "match": match_org(r"\bcsir\b"),
        "related_exam": "icar-jrf-srf",
        "related_role": "junior-research-fellow",
        "faqs": [
            ("Do I need CSIR-UGC NET for a project associate post?",
             "Usually not. Project associate posts are institute advertisements and typically ask for a master's degree with a stated percentage. NET is required for the JRF fellowship route."),
            ("Is the CSIR JRF stipend taxable?",
             "Fellowships are generally treated differently from salary for tax purposes, but the rules depend on the funding agency and your filing. Confirm with the institute and a tax adviser."),
            ("Can I hold a JRF without PhD registration?",
             "Yes for the initial JRF period. Most institutes require registration for a PhD before upgrading to SRF."),
        ],
    },
    {
        "slug": "icar-jrf-srf",
        "answer": "ICAR recruits scientists through the ARS competitive examination and fills JRF, SRF and project posts institute by institute. A relevant master's degree is required.",
        "name": "ICAR JRF / SRF & ARS",
        "short": "ICAR",
        "h1": "ICAR JRF, SRF & ARS Recruitment: Eligibility & Selection",
        "title": "ICAR JRF/SRF & ARS 2026: Eligibility, Exam & Vacancies",
        "desc": (
            "ICAR recruitment explained: the Agricultural Research Service examination, institute-wise "
            "JRF/SRF and Young Professional posts, eligibility, and live ICAR vacancies."
        ),
        "kicker": "Agricultural research",
        "sub": (
            "ICAR recruits scientists through a national competitive examination and fills project "
            "and fellowship posts institute by institute."
        ),
        "facts": [
            ("Recruiting body", "Indian Council of Agricultural Research and its institutes"),
            ("National exam", "ICAR All India Competitive Examination for the Agricultural Research Service"),
            ("Official portal", "icar.org.in/en/archive-vacancies"),
            ("Application mode", "Online for the national exam; email or portal for institute posts"),
            ("Cycle", "Institute vacancies year-round; ARS examination announced separately"),
            ("Typical posts", "JRF, SRF, Young Professional, Project Associate, Scientist"),
        ],
        "eligibility_intro": (
            "Eligibility is discipline-specific. The advertisement lists the exact degree, percentage "
            "and desirability criteria; these are the recurring requirements."
        ),
        "eligibility": [
            "<strong>ARS:</strong> a relevant master's or equivalent degree in the advertised discipline, with the percentage stated in that year's examination notice.",
            "<strong>JRF/SRF:</strong> a master's degree in the project's discipline; some institutes accept a bachelor's degree for project assistant roles.",
            "<strong>Young Professional:</strong> a professional degree or master's, engaged on a fixed-term contract under ICAR norms.",
            "<strong>Age:</strong> the ARS notice and each institute advertisement state the limit and relaxations.",
        ],
        "stages": [
            ("Written competitive examination", "For ARS, a national paper covering the discipline and general agriculture."),
            ("Institute shortlisting", "For project posts, screening against the advertisement's essential and desirable criteria."),
            ("Interview", "Subject interview, often with a short presentation for research posts."),
            ("Document verification", "Degree, experience and category certificates."),
        ],
        "syllabus_intro": (
            "The ARS syllabus is published with the examination notice; institute posts test the project's subject area."
        ),
        "syllabus": [
            "Discipline-specific agricultural science, including soil, crop, horticulture or natural-resource subjects as applicable.",
            "General agriculture, environment and current schemes.",
            "Research methods, statistics and field trial design for scientist-level posts.",
        ],
        "pay_note": (
            "ICAR posts follow ICAR pay norms and the advertised fellowship or contract rate. The exact "
            "figure is printed in each advertisement and reproduced in the registry listing."
        ),
        "watch": [
            "icar.org.in vacancy archive",
            "Individual ICAR institute websites and notice boards",
            "Employment News for the ARS examination notice",
            "The registry's research associate and project staff category",
        ],
        "match": match_org(r"\bicar\b"),
        "related_exam": "csir-jrf",
        "related_role": "project-associate",
        "faqs": [
            ("Is ICAR JRF the same as the ARS exam?",
             "No. JRF is a research fellowship attached to a project or postgraduate programme. ARS is the national examination for scientist posts in ICAR."),
            ("Can state agricultural university graduates apply?",
             "Yes, provided the degree and discipline match the advertisement. Some posts list preferred institutions but the essential criteria decide eligibility."),
            ("Are ICAR project posts permanent?",
             "Usually not. Project associate and Young Professional engagements are contract-based and co-terminous with the project."),
        ],
    },
    {
        "slug": "ugc-net-environmental-science",
        "answer": "UGC-NET is a two-paper computer-based test conducted by NTA. It qualifies candidates for Junior Research Fellowship and Assistant Professor eligibility in subjects including Environmental Science.",
        "name": "UGC-NET Environmental Science",
        "short": "UGC-NET",
        "h1": "UGC-NET Environmental Science: Eligibility, Pattern & JRF",
        "title": "UGC-NET Environmental Science 2026: Eligibility, Pattern & JRF",
        "desc": (
            "UGC-NET Environmental Science explained: eligibility for JRF and Assistant Professor, "
            "the two-paper pattern, syllabus areas and how the qualification is used in green jobs."
        ),
        "kicker": "Eligibility test",
        "sub": (
            "UGC-NET is the eligibility test behind most JRF and Assistant Professor appointments. "
            "Environmental Science is one of its subjects and a common route into research posts."
        ),
        "facts": [
            ("Conducting body", "National Testing Agency, on behalf of UGC"),
            ("Official portal", "nta.ac.in"),
            ("Used for", "Junior Research Fellowship and Assistant Professor eligibility"),
            ("Paper structure", "Paper I: teaching and research aptitude. Paper II: the chosen subject"),
            ("Mode", "Computer-based test"),
            ("Validity", "The scorecard validity is stated in the current information bulletin"),
        ],
        "eligibility_intro": (
            "UGC sets the eligibility in the information bulletin issued for each cycle. These are the "
            "recurring rules."
        ),
        "eligibility": [
            "<strong>Degree:</strong> a master's degree in Environmental Science or an allied subject from a recognised university.",
            "<strong>Final-year students:</strong> candidates still completing the master's are usually allowed to appear; the bulletin states the conditions.",
            "<strong>Category relaxations:</strong> reserved categories receive the relaxation published in the bulletin, not a fixed number carried over from older cycles.",
            "<strong>Subject choice:</strong> the paper must match the subject list in the bulletin; Environmental Science sits alongside life sciences, earth sciences and geography."
        ],
        "stages": [
            ("Paper I", "Teaching and research aptitude: reasoning, comprehension, quantitative methods and higher-education awareness."),
            ("Paper II", "Environmental Science subject paper, typically 100 questions."),
            ("No interview", "The score decides eligibility; there is no interview stage."),
            ("JRF cut-off", "A separate cut-off determines JRF eligibility in addition to Assistant Professor eligibility."),
        ],
        "syllabus_intro": (
            "The subject syllabus is published in the bulletin. Core areas examined are stable across cycles."
        ),
        "syllabus": [
            "Ecology, biodiversity and conservation biology.",
            "Environmental chemistry, pollution and waste management.",
            "Climate change, environmental law and impact assessment.",
            "Remote sensing, GIS and statistical methods in environmental science.",
        ],
        "pay_note": (
            "Qualifying does not by itself pay anything: it makes you eligible for a fellowship when a "
            "university or project appoints you. The stipend then follows UGC norms and the appointment order."
        ),
        "watch": [
            "NTA announcements for the UGC-NET cycle",
            "The information bulletin, which carries eligibility and syllabus",
            "University advertisement pages for JRF and Assistant Professor posts",
            "The registry's JRF/SRF category",
        ],
        "match": match_any(r"ugc[- ]net", r"assistant professor"),
        "related_exam": "csir-jrf",
        "related_role": "junior-research-fellow",
        "faqs": [
            ("Is UGC-NET the same as CSIR-UGC NET?",
             "They are separate examinations with separate subject lists and bulletins. Both are conducted by NTA, and both can qualify you for research fellowships in different subject areas."),
            ("Does UGC-NET guarantee a job?",
             "No. It is an eligibility qualification. You still apply for individual JRF, PhD or Assistant Professor positions."),
            ("Can I appear before my master's result?",
             "Usually yes, if you are in the final year or awaiting results, subject to the conditions in that cycle's bulletin."),
        ],
    },
    {
        "slug": "wii-pg-diploma",
        "answer": "The WII PG Diploma in Wildlife Management is a one-year postgraduate diploma admitted through an entrance test and interview. A bachelor's in science or forestry is required.",
        "name": "WII PG Diploma in Wildlife Management",
        "short": "WII diploma",
        "h1": "WII PG Diploma in Wildlife Management: Admission & Eligibility",
        "title": "WII PG Diploma in Wildlife Management 2026: Admission & Eligibility",
        "desc": (
            "Wildlife Institute of India postgraduate diploma: eligibility, entrance test and interview, "
            "what the course covers, and how it feeds into WII project and research posts."
        ),
        "kicker": "Postgraduate admission",
        "sub": (
            "The Wildlife Institute of India's postgraduate diploma is one of the standard routes into "
            "wildlife research and field conservation work in India."
        ),
        "facts": [
            ("Institution", "Wildlife Institute of India, Dehradun"),
            ("Programme", "Postgraduate Diploma in Wildlife Management"),
            ("Official portal", "wii.gov.in"),
            ("Admission route", "Entrance test followed by interview"),
            ("Cycle", "Annual, announced on the institute website"),
            ("Outcome", "Field and research roles in wildlife biology and protected-area management"),
        ],
        "eligibility_intro": (
            "The prospectus for the current admission year states the exact criteria. These are the "
            "recurring requirements."
        ),
        "eligibility": [
            "<strong>Degree:</strong> a bachelor's degree in science, forestry, veterinary science, agriculture or a related field.",
            "<strong>Entrance test:</strong> a written paper on wildlife biology, ecology and general science.",
            "<strong>Interview:</strong> shortlisted candidates attend an interview, often with a statement of interest.",
            "<strong>Field fitness:</strong> the course includes field modules, so medical fitness is checked.",
        ],
        "stages": [
            ("Application", "Online form and fee within the window announced by the institute."),
            ("Written entrance test", "Subject and aptitude paper."),
            ("Interview", "Panel interview for shortlisted candidates."),
            ("Offer and registration", "Document verification and fee payment."),
        ],
        "syllabus_intro": (
            "The entrance test draws on the subjects the course itself covers."
        ),
        "syllabus": [
            "Wildlife biology, ecology and conservation principles.",
            "Field methods: transects, camera traps, occupancy and population estimation.",
            "Statistics and basic GIS for ecological data.",
            "Indian wildlife law and protected-area management.",
        ],
        "pay_note": (
            "This is a course, not a salaried post. Fees, scholarships and any stipend are stated in the "
            "admission prospectus for the current year."
        ),
        "watch": [
            "wii.gov.in admissions and notice board",
            "The institute's prospectus PDF for the current academic year",
            "The registry's wildlife and forestry category for WII project posts",
        ],
        "match": match_org(r"wildlife institute"),
        "related_exam": "forest-range-officer",
        "related_role": "wildlife-conservation",
        "faqs": [
            ("Is the diploma equivalent to a master's degree?",
             "No. It is a postgraduate diploma. It is well regarded in the wildlife sector but does not replace an MSc or MTech for posts that require one."),
            ("Does WII recruit diploma holders?",
             "WII advertises project and research posts from time to time, and diploma holders apply alongside other candidates. Selection is per advertisement."),
            ("Is the entrance test hard?",
             "It is competitive. The paper rewards solid ecology and field-methods knowledge more than rote current affairs."),
        ],
    },
    {
        "slug": "forest-survey-of-india",
        "answer": "FSI recruits technical and project staff for forest cover assessment and remote-sensing work. Qualifications range from diploma to master's depending on the post.",
        "name": "Forest Survey of India (FSI)",
        "short": "FSI",
        "h1": "Forest Survey of India Recruitment: Posts, Eligibility & Selection",
        "title": "Forest Survey of India (FSI) Recruitment 2026: Posts & Eligibility",
        "desc": (
            "FSI recruitment for technical, mapping and project posts: what the institute does, "
            "eligibility by post type, selection stages and where vacancies are published."
        ),
        "kicker": "National technical institute",
        "sub": (
            "FSI produces India's forest cover assessment. Its recruitment is technical: mapping, "
            "remote sensing, inventory and project support."
        ),
        "facts": [
            ("Institution", "Forest Survey of India, Dehradun"),
            ("Official portal", "fsi.nic.in/recruitment/"),
            ("Typical posts", "Technical assistant, project staff, mapping and GIS support"),
            ("Application mode", "Online or prescribed form, as notified"),
            ("Cycle", "Notification-driven, not annual"),
            ("Core work", "Forest cover assessment, inventory, remote-sensing interpretation"),
        ],
        "eligibility_intro": (
            "FSI advertises post by post. These are the qualification patterns that recur."
        ),
        "eligibility": [
            "<strong>Technical posts:</strong> a degree or diploma in forestry, remote sensing, GIS or a related science, depending on the post.",
            "<strong>Project staff:</strong> master's in forestry, environmental science or geoinformatics, often with GIS experience.",
            "<strong>Support posts:</strong> school-level qualifications with computer or drafting skills.",
            "<strong>Experience:</strong> desirable experience is listed separately from the essential qualification; do not assume it is optional.",
        ],
        "stages": [
            ("Shortlisting", "Applications screened against the essential criteria."),
            ("Written or skill test", "Technical paper or a practical GIS/mapping test, depending on the post."),
            ("Interview", "Subject interview for shortlisted candidates."),
            ("Document verification", "Certificates and experience letters."),
        ],
        "syllabus_intro": (
            "The test follows the post: technical posts test forestry and remote sensing, support posts test general aptitude."
        ),
        "syllabus": [
            "Forest inventory and forest cover assessment methods.",
            "Remote sensing, image interpretation and GIS operations.",
            "General aptitude and reasoning for support posts.",
            "Basic statistics for inventory and sampling posts.",
        ],
        "pay_note": (
            "Pay follows the pay level printed in the FSI advertisement for that post. No figure is "
            "asserted here because the posts range from support staff to technical specialists."
        ),
        "watch": [
            "fsi.nic.in recruitment section",
            "MoEFCC recruitment page for deputation posts",
            "Employment News for advertised vacancies",
        ],
        "match": match_org(r"forest survey"),
        "related_exam": "indian-forest-service",
        "related_role": "gis-analyst",
        "faqs": [
            ("Does FSI recruit every year?",
             "No. FSI recruitment is notification-driven and depends on sanctioned posts, so there is no guaranteed annual cycle."),
            ("Is GIS experience necessary?",
             "For mapping and remote-sensing posts, yes. For support and administrative posts, the advertisement sets different criteria."),
            ("Are FSI posts central government jobs?",
             "FSI is an attached office of MoEFCC, and its posts follow central government pay and service rules unless the advertisement says otherwise."),
        ],
    },
    {
        "slug": "cpcb-scientist-engineer",
        "answer": "CPCB recruits scientists and engineers for pollution monitoring and standards work. A master's in environmental science or an engineering degree is typically required.",
        "name": "CPCB Scientist & Engineer",
        "short": "CPCB",
        "h1": "CPCB Scientist & Engineer Recruitment: Eligibility & Selection",
        "title": "CPCB Recruitment 2026: Scientist, Engineer Eligibility & Exam",
        "desc": (
            "Central Pollution Control Board recruitment for scientists and engineers: qualification "
            "requirements, selection stages, where notices appear, and live pollution-control openings."
        ),
        "kicker": "National regulator",
        "sub": (
            "The Central Pollution Control Board sets national monitoring standards and runs programmes "
            "on air, water and waste. Its technical posts are recruited directly or on deputation."
        ),
        "facts": [
            ("Organisation", "Central Pollution Control Board"),
            ("Official portal", "cpcb.nic.in"),
            ("Typical posts", "Scientist B, Assistant Environmental Engineer, technical staff"),
            ("Application mode", "Online or prescribed form, as notified"),
            ("Cycle", "Notification-driven"),
            ("Work areas", "Monitoring, standards, consent management, laboratory analysis"),
        ],
        "eligibility_intro": (
            "CPCB advertises each post with its own essential qualification. These are the common patterns."
        ),
        "eligibility": [
            "<strong>Scientist:</strong> a master's or equivalent in environmental science, chemistry, biology or a related discipline, with the experience stated for the grade.",
            "<strong>Engineer:</strong> a bachelor's degree in environmental, civil or chemical engineering.",
            "<strong>Deputation posts:</strong> serving government officers meeting the parent-department criteria.",
            "<strong>Age:</strong> stated per post in the advertisement, with the usual category relaxations.",
        ],
        "stages": [
            ("Shortlisting", "Applications checked against essential qualifications and experience."),
            ("Written examination", "Technical paper where the advertisement prescribes one."),
            ("Interview", "Subject and regulatory interview."),
            ("Document verification", "Certificates, experience and category proof."),
        ],
        "syllabus_intro": (
            "Where a written test is held, it follows the technical scope of the post."
        ),
        "syllabus": [
            "Air, water, noise and waste pollution: sources, standards and control technologies.",
            "Environmental monitoring, sampling and laboratory methods.",
            "Environmental law and regulatory procedure in India.",
            "Environmental engineering fundamentals for engineer posts.",
        ],
        "pay_note": (
            "CPCB posts follow central government pay levels, stated in the advertisement for each post. "
            "No single figure covers scientists, engineers and support staff."
        ),
        "watch": [
            "cpcb.nic.in recruitment and notices section",
            "MoEFCC recruitment page",
            "Employment News for central government vacancies",
        ],
        "match": match_org(r"central pollution control"),
        "related_exam": "state-pollution-control-board",
        "related_role": "environmental-engineer",
        "faqs": [
            ("Is CPCB recruitment through UPSC?",
             "Some central scientific posts are filled through UPSC or deputation, but CPCB also advertises directly. Check the specific advertisement."),
            ("Do I need a GATE score?",
             "Not usually. CPCB advertises its own selection process; GATE is not a standing requirement in its notices."),
            ("Are state pollution control board jobs similar?",
             "The technical work is similar, but state boards recruit under state rules with their own tests and pay scales."),
        ],
    },
    {
        "slug": "state-pollution-control-board",
        "answer": "State Pollution Control Boards recruit scientists, engineers and lab staff under state rules. An engineering or science degree is required; selection is state-specific.",
        "name": "State Pollution Control Board",
        "short": "SPCB",
        "h1": "State Pollution Control Board Recruitment: Scientist & Engineer Posts",
        "title": "State Pollution Control Board Recruitment 2026: Eligibility & Posts",
        "desc": (
            "How state pollution control boards recruit scientists, environmental engineers and lab "
            "staff, with eligibility patterns, selection stages and live regulator openings."
        ),
        "kicker": "State regulator",
        "sub": (
            "State Pollution Control Boards issue consents, monitor industry and run regional "
            "laboratories. Each board recruits under its own state rules."
        ),
        "facts": [
            ("Organisations", "State Pollution Control Boards (one per state)"),
            ("Example portal", "mppcb.mp.gov.in"),
            ("Typical posts", "Scientist, Environmental Engineer, Junior Engineer, Lab Analyst"),
            ("Application mode", "State portal or prescribed form"),
            ("Cycle", "State-wise, notification-driven"),
            ("Work areas", "Consent management, inspection, monitoring, laboratory analysis"),
        ],
        "eligibility_intro": (
            "State rules differ, so treat these as the common pattern rather than a national standard."
        ),
        "eligibility": [
            "<strong>Engineering posts:</strong> a bachelor's degree in environmental, civil or chemical engineering, sometimes with a specified percentage.",
            "<strong>Science posts:</strong> a master's in environmental science, chemistry or a biological science.",
            "<strong>Laboratory posts:</strong> a science degree with analytical-chemistry experience.",
            "<strong>Age and domicile:</strong> set by the state; some boards prefer or require state domicile.",
        ],
        "stages": [
            ("Written test", "Technical and general paper, where the state conducts one."),
            ("Interview", "Subject interview for shortlisted candidates."),
            ("Document verification", "Degree, experience and category certificates."),
            ("Medical", "Fitness for field inspection work."),
        ],
        "syllabus_intro": (
            "The state board publishes the syllabus with its advertisement. Core areas repeat across states."
        ),
        "syllabus": [
            "Water and wastewater treatment, air pollution control and solid waste management.",
            "Environmental monitoring and laboratory analysis.",
            "Environmental law, consent procedure and EIA notification.",
            "Basic environmental engineering design for engineer posts.",
        ],
        "pay_note": (
            "Pay follows the state pay matrix for the post and is printed in the advertisement. It differs "
            "by state and by post, so no single figure is given here."
        ),
        "watch": [
            "The state board's recruitment page (for example mppcb.mp.gov.in)",
            "State public service commission notifications",
            "State gazette and employment newspaper",
            "CPCB's list of state boards for the correct portal",
        ],
        "match": match_org(r"state pollution control", r"\bspcb\b", r"pollution control board"),
        "related_exam": "cpcb-scientist-engineer",
        "related_role": "environmental-engineer",
        "faqs": [
            ("Which state boards recruit most often?",
             "Recruitment depends on sanctioned posts and state budgets; there is no reliable ranking. Track the board for the state you want to work in."),
            ("Can I apply to more than one state board?",
             "Yes. Each board runs its own process, and applications are independent."),
            ("Is an environmental engineering degree required?",
             "For engineer posts, usually yes. Science graduates apply to scientist and laboratory posts instead."),
        ],
    },
]


def exam_live_jobs(exam: Dict[str, Any], pool: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    matcher = exam["match"]
    live = [job for job in pool if matcher(job)]
    live.sort(key=lambda job: str(job.get("valid_through") or "9999"))
    return live


def portal_label(exam: Dict[str, Any]) -> str:
    for label, value in exam["facts"]:
        if label.lower().startswith("official portal"):
            return value.split(" \u00b7 ")[0]
    return "Official portal"


def exam_facts_table(facts: List[Tuple[str, str]]) -> str:
    rows = "\n".join(
        f'            <tr><th scope="row">{esc(label)}</th><td>{esc(value)}</td></tr>'
        for label, value in facts
    )
    return f"""        <div class="table-wrap">
          <table class="data-table">
            <tbody>
{rows}
            </tbody>
          </table>
        </div>"""


def stages_table(stages: List[Tuple[str, str]]) -> str:
    rows = "\n".join(
        f'            <tr><td><strong>{esc(name)}</strong></td><td>{esc(detail)}</td></tr>'
        for name, detail in stages
    )
    return f"""        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>Stage</th><th>What happens</th></tr></thead>
            <tbody>
{rows}
            </tbody>
          </table>
        </div>"""


def build_exam_page(exam: Dict[str, Any]) -> None:
    live = exam_live_jobs(exam, INDIA)
    related_exam = next((e for e in EXAMS if e["slug"] == exam.get("related_exam")), None)
    related_role = next((r for r in ROLES if r["slug"] == exam.get("related_role")), None)

    related_links = []
    if related_role:
        related_links.append(
            f'<li><a href="/roles/{related_role["slug"]}">{esc(related_role["name"])} salary and career profile</a></li>'
        )
    if related_exam:
        related_links.append(
            f'<li><a href="/exams/{related_exam["slug"]}">{esc(related_exam["name"])} guide</a></li>'
        )
    related_links.append('<li><a href="/government-environment-jobs">Government recruitment tracker</a></li>')
    related_links.append('<li><a href="/green-careers">Green career pathways</a></li>')

    body = "\n".join(
        [
            hero(
                exam["kicker"],
                exam["h1"],
                exam["sub"],
                [
                    ("Live openings", str(len(live))),
                    ("Official portal", portal_label(exam)),
                    ("Updated", TODAY.strftime("%d %b %Y")),
                ],
            ),
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>In short</h2>
        <p><strong>{esc(exam["answer"])}</strong></p>
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>At a glance</h2>
        <p>Who runs the recruitment, where it is published and how applications are made.</p>
{exam_facts_table(exam["facts"])}
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Eligibility</h2>
        <p>{esc(exam["eligibility_intro"])}</p>
{bullet_list(exam["eligibility"])}
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Selection stages</h2>
        <p>The sequence below is the standard route; a state or institute may drop or merge a stage.</p>
{stages_table(exam["stages"])}
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>What to study</h2>
        <p>{esc(exam["syllabus_intro"])}</p>
{bullet_list(exam["syllabus"])}
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Pay</h2>
        <p>{esc(exam["pay_note"])}</p>
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Where the notification appears</h2>
        <p>No cycle date is asserted on this page. These are the sources that publish it first.</p>
{bullet_list(exam["watch"])}
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Live openings in the registry ({len(live)})</h2>
        <p>Vacancies currently tracked for this recruiting body or post, sorted by closing date.</p>
{cards_block(live[:9], "No live opening from this body is in the registry today. New vacancies are added as they are published; the tracker lists every open post.")}
        <p style="margin-top:16px;"><a href="/government-environment-jobs">See all public-sector openings &rarr;</a></p>
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Related pages</h2>
        <ul class="check-list">
          {''.join(related_links)}
        </ul>
      </div>
    </section>""",
            beh.bsp.faq_section_html(exam["faqs"]),
        ]
    )
    jsonld = "\n".join(
        [
            beh.bsp.organization_jsonld(),
            beh.bsp.website_jsonld(),
            beh.breadcrumb(exam["name"] + " recruitment guide", f"{SITE}/exams/{exam['slug']}"),
            beh.faq_jsonld(exam["faqs"]),
        ]
    )
    write_sub(
        EXAMS_DIR,
        exam["slug"],
        shell(
            title=exam["title"],
            description=exam["desc"],
            canonical=f"{SITE}/exams/{exam['slug']}",
            body=body,
            jsonld=jsonld,
        ),
    )


def build_exam_index() -> None:
    cards_html = "\n".join(
        f"""        <article class="hub-card">
          <h3 class="hub-card-title"><a href="/exams/{exam['slug']}">{esc(exam["name"])}</a></h3>
          <p class="hub-card-sum">{esc(exam["desc"])}</p>
          <p class="hub-card-foot"><span>{len(exam_live_jobs(exam, INDIA))} live opening(s)</span>
            <a href="/exams/{exam['slug']}">Read the guide &rarr;</a></p>
        </article>"""
        for exam in EXAMS
    )
    body = "\n".join(
        [
            hero(
                "Exam & eligibility guides",
                "Environmental, Forestry & Wildlife Recruitment Exams in India",
                "Evergreen guides to the exams and recruitment routes behind green public-sector jobs. Each guide links to the official portal and to the vacancies currently tracked.",
                [
                    ("Guides", str(len(EXAMS))),
                    ("Live openings", str(sum(len(exam_live_jobs(e, INDIA)) for e in EXAMS))),
                    ("Updated", TODAY.strftime("%d %b %Y")),
                ],
            ),
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Choose a recruitment route</h2>
        <p>Guides cover the process, not a guessed date. Where a cycle has not been notified, the page says so and points at the portal.</p>
        <div class="hub-list">
{cards_html}
        </div>
      </div>
    </section>""",
            section(
                "How to use these guides",
                "Read the process first, then watch the portal.",
                """        <ul class="check-list">
          <li><strong>Confirm the current cycle.</strong> Every guide names the body that publishes the notification. That notice overrides anything on this site.</li>
          <li><strong>Prepare before the notice.</strong> Written tests and physical standards take months; the eligibility rules take an afternoon to read.</li>
          <li><strong>Track live vacancies.</strong> Each guide lists the openings currently in the registry for that body or post.</li>
          <li><strong>Check the pay basis, not a number.</strong> Government pay follows a matrix, research posts follow funding norms, and both are printed in the advertisement.</li>
        </ul>""",
            ),
            beh.bsp.faq_section_html(
                [
                    ("Do these pages carry the current notification date?",
                     "No. Dates move every cycle and a stale date is worse than none. Each guide links to the official portal where the live notification is published."),
                    ("Are the guides only for government jobs?",
                     "They cover public recruitment plus the national eligibility tests (CSIR-UGC NET, UGC-NET, ICAR) that research and fellowship posts depend on."),
                    ("How often are the guides updated?",
                     "The guides are rebuilt with the site, and the live-opening counts and links refresh from the registry on every build."),
                ]
            ),
        ]
    )
    write_sub(
        EXAMS_DIR,
        "index",
        shell(
            title="Environmental & Forestry Recruitment Exams in India 2026",
            description=(
                "Guides to Indian Forest Service, forest guard, range officer, CSIR JRF, ICAR, UGC-NET, "
                "WII, FSI and pollution board recruitment, with official portals and live vacancies."
            ),
            canonical=f"{SITE}/exams",
            body=body,
            jsonld="\n".join(
                [
                    beh.bsp.organization_jsonld(),
                    beh.bsp.website_jsonld(),
                    beh.breadcrumb("Environmental & Forestry Recruitment Exams", f"{SITE}/exams"),
                ]
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Role salary profiles
# ---------------------------------------------------------------------------
ROLES: List[Dict[str, Any]] = [
    {
        "slug": "esg-analyst",
        "answer": "An ESG analyst collects and reports environmental, social and governance data under frameworks like BRSR and GRI. Entry usually needs a master's or strong internship; pay is rarely published in Indian notices.",
        "name": "ESG Analyst",
        "h1": "ESG Analyst Salary in India: Pay, Skills & Entry Route",
        "title": "ESG Analyst Salary in India 2026: Pay, Skills & How to Enter",
        "desc": (
            "What an ESG analyst does, what the registry shows about advertised pay, the skills "
            "employers ask for, and how to move from analyst to sustainability manager."
        ),
        "kicker": "Corporate & consulting",
        "what": (
            "ESG analysts collect and structure environmental, social and governance data for disclosure, "
            "ratings and assurance. The work is part reporting, part data quality control and part "
            "explaining numbers to people who do not work in sustainability."
        ),
        "entry": [
            "A master's in environmental science, economics, business or sustainability helps, but several listings accept a bachelor's with relevant internship experience.",
            "Learn the reporting frameworks actually named in Indian notices: BRSR, GRI, and increasingly CSRD for global teams.",
            "Build one artefact you can show: a mock BRSR section, a carbon inventory, or a data dashboard.",
            "Expect a screening test or case exercise on data interpretation before the interview.",
        ],
        "match": lambda job: bool(
            re.search(r"\besg\b", title_of(job))
            or (
                "esg" in job_text(job, "category")
                and re.search(r"analyst|associate|executive|consultant", title_of(job))
            )
        ),
        "ladder": "Analyst &rarr; Senior Analyst &rarr; Manager / Lead &rarr; Head of Sustainability",
        "exam": "csir-jrf",
        "hub": ("/esg-carbon-sustainability-jobs", "ESG, carbon and sustainability jobs"),
        "faqs": [
            ("Why do so few ESG listings publish pay?",
             "Corporate and consulting roles in India often negotiate pay privately, and the notice states only the role. The table above shows every listing that did publish a figure, plus the count that did not."),
            ("Is ESG analyst a good first job?",
             "It is one of the few green roles that hires at entry level in volume. The trade-off is that much of the first year is data collection and documentation rather than strategy."),
            ("Do I need a CA or CFA?",
             "No. Assurance and valuation teams value them, but most analyst postings ask for sustainability, environment or economics backgrounds."),
        ],
    },
    {
        "slug": "sustainability-manager",
        "answer": "A sustainability manager owns a company's ESG programme, targets and disclosure cycles. Most postings need 3-6 years of experience; pay varies widely by firm and city.",
        "name": "Sustainability Manager",
        "h1": "Sustainability Manager Salary in India: Pay & Progression",
        "title": "Sustainability Manager Salary in India 2026: Pay & Progression",
        "desc": (
            "Sustainability manager roles in India: what the job owns, the experience employers ask "
            "for, advertised pay in the registry and the route from analyst to head of sustainability."
        ),
        "kicker": "Corporate leadership",
        "what": (
            "Sustainability managers own a company's environment and ESG programme: targets, disclosure "
            "cycles, supplier engagement and the internal argument for capital. The role is managerial "
            "before it is technical."
        ),
        "entry": [
            "Most postings ask for three to six years in ESG reporting, carbon accounting, EHS or consulting.",
            "Programme ownership matters more than subject depth: budgets, timelines and cross-functional teams.",
            "Fluency in BRSR and assurance readiness is the most common technical requirement in Indian listings.",
            "People move in from consulting, EHS, quality and finance rather than from a single degree path.",
        ],
        "match": lambda job: bool(
            re.search(r"sustainab", title_of(job))
            and re.search(r"manager|lead|head|director", title_of(job))
        ),
        "ladder": "Analyst &rarr; Manager &rarr; Senior Manager &rarr; Head of Sustainability / ESG",
        "exam": "cpcb-scientist-engineer",
        "hub": ("/esg-carbon-sustainability-jobs", "ESG, carbon and sustainability jobs"),
        "faqs": [
            ("How much experience do these roles need?",
             "The listings in the registry cluster at mid-senior level, typically three to six years. Genuine entry-level manager roles are rare."),
            ("Does a sustainability manager need an engineering degree?",
             "Not necessarily. The notices accept environment, business and economics backgrounds, but technical fluency in carbon and reporting is expected."),
            ("Is the title standardised?",
             "No. The same job appears as ESG manager, sustainability lead, CSR manager and head of ESG depending on the company."),
        ],
    },
    {
        "slug": "carbon-analyst",
        "answer": "A carbon analyst builds greenhouse-gas inventories and models reduction pathways using the GHG Protocol. Entry needs quantitative skills and sector knowledge.",
        "name": "Carbon & Decarbonisation Analyst",
        "h1": "Carbon Analyst Salary in India: Pay, Skills & Entry",
        "title": "Carbon Analyst Salary in India 2026: Pay, Skills & Entry",
        "desc": (
            "Carbon accounting and decarbonisation analyst roles in India: what the work involves, "
            "skills employers list, advertised pay in the registry and how the role progresses."
        ),
        "kicker": "Carbon markets",
        "what": (
            "Carbon analysts build greenhouse-gas inventories, model reduction pathways and support "
            "climate targets. The work sits between engineering, finance and reporting."
        ),
        "entry": [
            "Learn the GHG Protocol scopes properly; most interview questions start there.",
            "Sector knowledge matters: cement, steel, power and logistics have different abatement options.",
            "Spreadsheet and data modelling skills are assumed; Python or Power BI is increasingly listed.",
            "A master's in environmental engineering, energy or economics is common but not universal.",
        ],
        "match": lambda job: bool(re.search(r"carbon|decarbon|climate risk|\bghg\b", title_of(job))),
        "ladder": "Analyst &rarr; Senior Analyst &rarr; Carbon / Climate Manager &rarr; Decarbonisation Lead",
        "exam": "ugc-net-environmental-science",
        "hub": ("/esg-carbon-sustainability-jobs", "ESG, carbon and sustainability jobs"),
        "faqs": [
            ("Is carbon accounting the same as carbon trading?",
             "No. Accounting measures and reports emissions. Trading buys and sells credits or allowances. Some roles cover both, most do not."),
            ("Which certification helps?",
             "Employers name frameworks (GHG Protocol, SBTi, ISO 14064) more often than certificates. Learn the framework and show a worked inventory."),
            ("Is the role quantitative?",
             "Yes. Expect emission-factor calculations, unit conversions and scenario modelling in the first interview."),
        ],
    },
    {
        "slug": "climate-policy-analyst",
        "answer": "A climate policy analyst researches and writes on mitigation, adaptation and finance for think tanks and multilaterals. A master's in policy, economics or environment is the usual entry credential.",
        "name": "Climate Policy & Research Analyst",
        "h1": "Climate Policy Analyst Salary in India: Pay & Career Path",
        "title": "Climate Policy Analyst Salary in India 2026: Pay & Career Path",
        "desc": (
            "Climate policy and research analyst roles in Indian think tanks and multilaterals: what "
            "the work involves, entry routes, advertised pay and progression."
        ),
        "kicker": "Policy & research",
        "what": (
            "Policy analysts turn research into briefs, submissions and programme design. In climate, "
            "that means adaptation, energy transition, finance and state-level implementation."
        ),
        "entry": [
            "A master's in public policy, economics, environment or development studies is the common entry credential.",
            "Writing samples decide more interviews than grades: one clear two-page brief beats a long dissertation summary.",
            "Quantitative comfort with Excel, Stata or R is listed in most research postings.",
            "Internships at think tanks, multilaterals or state departments are the standard first step.",
        ],
        "match": lambda job: bool(
            re.search(r"climate|policy", title_of(job))
            and re.search(r"analyst|research|associate|fellow|officer", title_of(job))
        ),
        "ladder": "Research Assistant &rarr; Analyst / Associate &rarr; Senior Fellow / Programme Lead",
        "exam": "ugc-net-environmental-science",
        "hub": ("/sustainability-jobs-india", "Sustainability and climate jobs in India"),
        "faqs": [
            ("Do policy roles pay less than corporate ESG roles?",
             "The registry's advertised figures are too sparse to compare reliably. Think tanks often publish bands in the notice; corporates usually do not."),
            ("Is a PhD required?",
             "Not for analyst and associate roles. Senior fellow and research lead positions increasingly list one."),
            ("What writing do employers ask for?",
             "A policy brief, a research paper or an op-ed. They usually ask for a sample with the application."),
        ],
    },
    {
        "slug": "gis-analyst",
        "answer": "A GIS analyst turns spatial data into maps and models using QGIS, ArcGIS and Google Earth Engine. Entry accepts science or engineering graduates with demonstrated GIS skills.",
        "name": "GIS & Remote Sensing Analyst",
        "h1": "GIS Analyst Salary in India: Pay, Skills & Entry Route",
        "title": "GIS Analyst Salary in India 2026: Pay, Skills & Entry Route",
        "desc": (
            "GIS and remote-sensing analyst roles in environment and climate: tools employers list, "
            "advertised pay in the registry, and the route to earth-observation specialist."
        ),
        "kicker": "Geospatial",
        "what": (
            "GIS analysts turn spatial data into maps, layers and models: land cover, forest change, "
            "flood risk and site suitability. Remote-sensing work adds satellite imagery processing."
        ),
        "entry": [
            "QGIS or ArcGIS plus one scripting language (Python or R) is the standard minimum.",
            "Google Earth Engine appears in a growing share of environmental listings.",
            "A portfolio of two or three maps with documented methods is more persuasive than a certificate list.",
            "Degrees range from geography and environmental science to civil engineering and geoinformatics.",
        ],
        "match": lambda job: bool(
            "gis" in job_text(job, "category")
            or re.search(r"\bgis\b|remote sensing|geospatial|earth observation", title_of(job))
        ),
        "ladder": "GIS Executive &rarr; GIS Analyst &rarr; Remote Sensing Specialist &rarr; Earth Observation Lead",
        "exam": "forest-survey-of-india",
        "hub": ("/gis-remote-sensing-climate-jobs", "GIS and remote sensing jobs"),
        "faqs": [
            ("Which software should I learn first?",
             "QGIS, because it is free and used across institutes, then ArcGIS if the employers you target list it. Add Python for automation."),
            ("Is GIS a good entry into environmental work?",
             "Yes. It is one of the thinnest-supply categories in the registry relative to demand, and it accepts science and engineering graduates."),
            ("Do I need a geoinformatics degree?",
             "No. Several listings accept any science or engineering degree with demonstrated GIS skills."),
        ],
    },
    {
        "slug": "junior-research-fellow",
        "answer": "A JRF is a funded research position requiring a master's and a national eligibility test. Stipends follow funding-agency norms, typically 37,000-42,000 per month plus HRA.",
        "name": "Junior Research Fellow (JRF/SRF)",
        "h1": "JRF Salary in India: Stipend, Eligibility & Progression",
        "title": "JRF Salary in India 2026: Stipend, Eligibility & Progression",
        "desc": (
            "Junior and senior research fellow pay in India: advertised stipends in the registry, "
            "eligibility through NET or GATE, and how JRF progresses to SRF and research associate."
        ),
        "kicker": "Research fellowship",
        "what": (
            "A JRF is a funded research position attached to a project or a PhD. The work is fieldwork, "
            "analysis, writing and project reporting, usually under a principal investigator."
        ),
        "entry": [
            "A master's in the project's discipline plus a national eligibility test (CSIR-UGC NET, UGC-NET or GATE) is the standard route.",
            "Some institute advertisements accept a master's without NET when the project funding allows it; the notice says so explicitly.",
            "PhD registration is usually required before upgrading from JRF to SRF.",
            "Field, laboratory or modelling experience in the project's subject is the main differentiator.",
        ],
        "match": lambda job: bool(
            re.search(r"junior research fellow|senior research fellow|\bjrf\b|\bsrf\b", title_of(job))
        ),
        "ladder": "JRF &rarr; SRF &rarr; Research Associate &rarr; Scientist / Faculty",
        "exam": "csir-jrf",
        "hub": ("/jrf-srf-project-associate-jobs", "JRF, SRF and project associate jobs"),
        "faqs": [
            ("Is the JRF stipend fixed?",
             "Fellowship rates follow the funding agency's norms and are printed in the advertisement. The registry reproduces the advertised figure for each post."),
            ("Can I take a JRF without a PhD seat?",
             "Yes for the initial period. Most institutes require registration before the SRF upgrade."),
            ("Is JRF experience counted as work experience?",
             "For academic and research applications, usually yes. For corporate roles, it depends on how the employer reads the fellowship."),
        ],
    },
    {
        "slug": "project-associate",
        "answer": "A project associate delivers a funded research project on contract. A master's in the project's discipline is required; contracts are co-terminous with the project.",
        "name": "Project Associate / Research Associate",
        "h1": "Project Associate Salary in India: Pay, Eligibility & Growth",
        "title": "Project Associate Salary in India 2026: Pay, Eligibility & Growth",
        "desc": (
            "Project and research associate roles in Indian institutes: advertised pay, contract terms, "
            "eligibility and how the post fits into a research career."
        ),
        "kicker": "Contract research",
        "what": (
            "Project associates deliver a funded project: data collection, analysis, field coordination "
            "and reporting. Contracts are co-terminous with the project, typically one to three years."
        ),
        "entry": [
            "A master's in the project's discipline is the usual requirement; some posts accept a bachelor's with experience.",
            "Look for the contract length and extension conditions in the advertisement before applying.",
            "Data skills (Excel, R, Python, GIS) widen the range of projects you can join.",
            "NET or GATE is often desirable rather than essential for associate posts.",
        ],
        "match": lambda job: bool(
            re.search(r"project associate|research associate|project assistant|research assistant", title_of(job))
        ),
        "ladder": "Project Assistant &rarr; Project Associate &rarr; Research Associate &rarr; Project Scientist",
        "exam": "icar-jrf-srf",
        "hub": ("/jrf-srf-project-associate-jobs", "JRF, SRF and project associate jobs"),
        "faqs": [
            ("Are project associate jobs permanent?",
             "Almost never. They are contract appointments tied to a funded project, and the advertisement states the duration."),
            ("Does the contract renew automatically?",
             "No. Extensions depend on funding and performance and are issued as a fresh order."),
            ("Is it worth taking over a JRF?",
             "A JRF carries a fellowship and usually a PhD path. A project associate post can pay more in some institutes but carries less academic structure."),
        ],
    },
    {
        "slug": "wildlife-conservation",
        "answer": "A wildlife biologist surveys species and habitats and advises protected-area managers. A master's in wildlife science or ecology is the common entry point.",
        "name": "Wildlife & Conservation Scientist",
        "h1": "Wildlife Biologist Salary in India: Pay, Skills & Entry",
        "title": "Wildlife Biologist Salary in India 2026: Pay, Skills & Entry",
        "desc": (
            "Wildlife biology and conservation roles in India: advertised pay in the registry, field "
            "and research skills employers list, and the route from field assistant to scientist."
        ),
        "kicker": "Field conservation",
        "what": (
            "Wildlife biologists survey species and habitats, run camera-trap grids, model occupancy and "
            "advise protected-area managers. The job is part field craft and part statistics."
        ),
        "entry": [
            "A master's in wildlife science, zoology, ecology or environmental science is the common entry point.",
            "Field experience is decisive: a season of survey work outweighs a classroom certificate.",
            "Occupancy modelling, distance sampling and R are named in most research listings.",
            "The WII postgraduate diploma is one recognised route into the sector.",
        ],
        "match": lambda job: bool(re.search(r"wildlife|ecolog|conservation", title_of(job))),
        "ladder": "Field Assistant &rarr; Research Fellow &rarr; Wildlife Biologist &rarr; Scientist / Park Manager",
        "exam": "wii-pg-diploma",
        "hub": ("/forestry-wildlife-government-jobs", "Forestry and wildlife jobs"),
        "faqs": [
            ("Do I need to be physically fit?",
             "Field roles require it. Surveys often run for weeks in remote areas, and the interview will probe your field experience."),
            ("Is conservation work well paid?",
             "The registry has too few disclosed figures to generalise. Government and institute posts follow pay norms; NGO roles vary widely."),
            ("Which skills get shortlisted?",
             "Species identification, camera-trap handling, occupancy or abundance modelling, and GIS."),
        ],
    },
    {
        "slug": "environmental-engineer",
        "answer": "An environmental engineer designs and runs treatment systems and compliance processes. A bachelor's in environmental, civil or chemical engineering is standard.",
        "name": "Environmental Engineer / Compliance Officer",
        "h1": "Environmental Engineer Salary in India: Pay & Compliance Roles",
        "title": "Environmental Engineer Salary in India 2026: Pay & Compliance Roles",
        "desc": (
            "Environmental engineering and compliance roles in India: what the job covers, qualifications "
            "employers ask for, advertised pay and the route into pollution control boards."
        ),
        "kicker": "Engineering & compliance",
        "what": (
            "Environmental engineers design and run treatment systems, monitoring programmes and "
            "compliance processes: effluent plants, air-quality control, waste management and consents."
        ),
        "entry": [
            "A bachelor's in environmental, civil or chemical engineering is the standard qualification.",
            "Compliance roles add environmental law and consent procedure to the engineering base.",
            "Plant experience, even as an intern, is valued more than a second certificate.",
            "Pollution control board posts are a parallel route with their own exams.",
        ],
        "match": lambda job: bool(
            re.search(r"environment(al)? engineer|environment engineer|pollution|compliance", title_of(job))
        ),
        "ladder": "Graduate Engineer Trainee &rarr; Environmental Engineer &rarr; Senior Engineer / Manager EHS",
        "exam": "state-pollution-control-board",
        "hub": ("/esg-carbon-sustainability-jobs", "ESG, carbon and sustainability jobs"),
        "faqs": [
            ("Is environmental engineering the same as EHS?",
             "They overlap. EHS covers worker safety and occupational health as well as environment; environmental engineering focuses on pollution control and process design."),
            ("Do I need a master's?",
             "Not for most plant and compliance roles. Design and research posts often prefer one."),
            ("Are board jobs better paid?",
             "They follow the state pay matrix, which is transparent but usually lower than private-sector packages at senior levels."),
        ],
    },
    {
        "slug": "forest-guard",
        "answer": "A forest guard is an entry-level state post for forest protection and patrol. A school-leaving certificate and physical standards are required; pay follows the state pay matrix.",
        "name": "Forest Guard & Forest Ranger",
        "h1": "Forest Guard Salary in India: State Pay, Eligibility & Exam",
        "title": "Forest Guard Salary in India 2026: State Pay, Eligibility & Exam",
        "desc": (
            "Forest guard and ranger pay in India: why it depends on the state pay matrix, what the "
            "recruitment involves, and how the post progresses to range officer."
        ),
        "kicker": "State forest service",
        "what": (
            "Forest guards patrol beats, control fire and grazing, run nurseries and support plantation "
            "targets. Rangers supervise a range and its staff. Both are state posts."
        ),
        "entry": [
            "A school-leaving certificate is the usual minimum for forest guard; ranger posts ask for a degree.",
            "The written test is only one stage: physical standards eliminate more candidates than the paper.",
            "State domicile and language requirements apply in several states.",
            "Promotion from guard to ranger is possible through departmental exams, but it takes years.",
        ],
        "match": lambda job: bool(re.search(r"forest guard|\bforester\b|\branger\b", title_of(job))),
        "ladder": "Forest Guard &rarr; Forester / Ranger &rarr; Range Officer &rarr; State Forest Service",
        "exam": "forest-guard",
        "hub": ("/forestry-wildlife-government-jobs", "Forestry and wildlife jobs"),
        "faqs": [
            ("Why is there no salary figure on this page?",
             "Forest guard pay is set by the state pay matrix, so a single national number would be misleading. The state notification carries the current figure."),
            ("Is forest guard a permanent government job?",
             "Yes, in most states it is a regular state government post with pension or NPS benefits as applicable."),
            ("Can women apply?",
             "Yes. Most states recruit women, with separate physical standards and sometimes a reservation in the cadre."),
        ],
    },
    {
        "slug": "renewable-energy-engineer",
        "answer": "A renewable energy engineer designs, installs and maintains solar, wind and green hydrogen systems. A bachelor's in electrical or mechanical engineering is the standard entry; site experience is valued over certificates.",
        "name": "Renewable Energy Engineer",
        "h1": "Renewable Energy Engineer Salary in India: Pay, Skills & Entry",
        "title": "Renewable Energy Engineer Salary in India 2026: Pay, Skills & Entry",
        "desc": "Renewable energy engineering roles in India: solar, wind and green hydrogen. What the work involves, skills employers list, and how to enter.",
        "kicker": "Clean energy",
        "what": "Renewable energy engineers design, install and maintain solar, wind and green hydrogen systems. The sector is India's largest green employer and is growing fast.",
        "entry": [
            "A bachelor's in electrical, mechanical or energy engineering is the standard entry qualification.",
            "Solar PV design, wind resource assessment and grid integration are the most listed technical skills.",
            "Site experience, even as an intern, is valued more than a second certificate.",
            "State renewable energy agencies and private developers both hire; the pay and contract terms differ.",
        ],
        "match": lambda job: bool(re.search(r"renewable|solar|wind|green hydrogen|clean energy|energy engineer", title_of(job))),
        "ladder": "Graduate Engineer Trainee -> Renewable Energy Engineer -> Senior Engineer -> Project Manager -> Head of Projects",
        "exam": None,
        "hub": ("/esg-carbon-sustainability-jobs", "ESG, carbon and sustainability jobs"),
        "faqs": [
            ("Is renewable energy a good career in India?", "Yes. India has one of the world's largest renewable targets, and the sector hires engineers, project managers and analysts at scale."),
            ("Do I need a master's?", "Not for most plant and design roles. Research and R&D posts often prefer one."),
            ("Are government jobs available?", "Yes. State renewable energy agencies and public sector units recruit engineers regularly."),
        ],
    },
    {
        "slug": "sustainability-consulting",
        "answer": "A sustainability consultant advises companies on ESG strategy, reporting and decarbonisation. Entry usually needs a master's in sustainability or business; framework knowledge (BRSR, GRI, TCFD) is listed in most postings.",
        "name": "Sustainability Consultant",
        "h1": "Sustainability Consultant Salary in India: Pay & Career Path",
        "title": "Sustainability Consultant Salary in India 2026: Pay & Career Path",
        "desc": "Sustainability consulting roles in India: what consultants do, skills employers list, advertised pay, and progression to partner.",
        "kicker": "Consulting",
        "what": "Sustainability consultants advise companies on ESG strategy, reporting, carbon accounting and decarbonisation. The work is a mix of analysis, client management and delivery.",
        "entry": [
            "A master's in sustainability, environment, business or economics is common but not universal.",
            "Big Four and specialist firms hire analysts with strong data and writing skills.",
            "Framework knowledge (BRSR, GRI, TCFD) is listed in most postings.",
            "Client-facing skills matter as much as technical depth.",
        ],
        "match": lambda job: bool(re.search(r"consultant", title_of(job)) and re.search(r"sustainab|esg|carbon|climate|environment", title_of(job))),
        "ladder": "Analyst -> Consultant -> Senior Consultant -> Manager -> Partner",
        "exam": None,
        "hub": ("/esg-carbon-sustainability-jobs", "ESG, carbon and sustainability jobs"),
        "faqs": [
            ("Do consultants earn more than in-house ESG roles?", "Usually yes at junior levels, but the gap narrows at senior levels."),
            ("Is travel required?", "Often yes. Consulting roles involve client sites and field visits."),
            ("How do I enter consulting?", "Internships at consulting firms and strong case-interview preparation are the standard route."),
        ],
    },
    {
        "slug": "carbon-market-analyst",
        "answer": "A carbon market analyst works on carbon credit generation, trading and compliance. Understanding of carbon standards (Verra, Gold Standard) and MRV is essential; finance and environment backgrounds are both common.",
        "name": "Carbon Market Analyst",
        "h1": "Carbon Market Analyst Salary in India: Pay, Skills & Entry",
        "title": "Carbon Market Analyst Salary in India 2026: Pay, Skills & Entry",
        "desc": "Carbon market analyst roles in India: voluntary and compliance markets, MRV, trading and policy. Skills, pay and career path.",
        "kicker": "Carbon markets",
        "what": "Carbon market analysts work on carbon credit generation, trading and compliance. India's Carbon Credit Trading Scheme is creating new demand for this role.",
        "entry": [
            "A background in economics, finance, environment or engineering is common.",
            "Understanding of carbon standards (Verra, Gold Standard) and MRV is essential.",
            "Quantitative skills and market awareness are listed in most postings.",
            "Entry-level roles exist in project developers and verification bodies.",
        ],
        "match": lambda job: bool(re.search(r"carbon", title_of(job))),
        "ladder": "Analyst -> Senior Analyst -> Carbon Market Manager -> Head of Carbon",
        "exam": None,
        "hub": ("/esg-carbon-sustainability-jobs", "ESG, carbon and sustainability jobs"),
        "faqs": [
            ("Is carbon trading legal in India?", "India is developing a Carbon Credit Trading Scheme under the Energy Conservation Act amendment. The framework is being notified."),
            ("Do I need a finance degree?", "Not necessarily. Environmental science and engineering backgrounds are common, with finance learned on the job."),
            ("Which certifications help?", "Carbon standards (Verra, Gold Standard) and GHG Protocol knowledge are valued more than generic certificates."),
        ],
    },
    {
        "slug": "climate-risk-analyst",
        "answer": "A climate risk analyst assesses how climate change affects financial portfolios in banks and insurers. TCFD and NGFS scenarios are the standard frameworks; quantitative skills are essential.",
        "name": "Climate Risk Analyst",
        "h1": "Climate Risk Analyst Salary in India: Pay, Skills & Entry",
        "title": "Climate Risk Analyst Salary in India 2026: Pay, Skills & Entry",
        "desc": "Climate risk analyst roles in Indian banks and insurers: TCFD, stress testing, physical and transition risk. Skills and career path.",
        "kicker": "Financial services",
        "what": "Climate risk analysts assess how climate change affects financial portfolios. They work in banks, insurers and asset managers on physical and transition risk.",
        "entry": [
            "A master's in finance, economics, climate science or environmental engineering is common.",
            "TCFD and NGFS scenarios are the standard frameworks.",
            "Quantitative skills (modelling, data analysis) are essential.",
            "Banks and large insurers are the main employers in India.",
        ],
        "match": lambda job: bool(re.search(r"climate risk|risk analyst|tcfd", title_of(job))),
        "ladder": "Analyst -> Senior Analyst -> Climate Risk Manager -> Chief Risk Officer",
        "exam": None,
        "hub": ("/esg-carbon-sustainability-jobs", "ESG, carbon and sustainability jobs"),
        "faqs": [
            ("Is this a finance or science role?", "Both. It sits at the intersection of climate science and financial analysis."),
            ("Which banks hire climate risk analysts in India?", "Large private and public sector banks, plus insurers and asset managers."),
            ("Is TCFD mandatory in India?", "Not yet mandatory, but RBI has issued climate risk guidance for banks."),
        ],
    },
    {
        "slug": "waste-circular-economy",
        "answer": "A waste and circular economy specialist works on waste reduction, recycling and EPR compliance. An environmental engineering or chemistry degree is common; field experience at waste facilities is valued.",
        "name": "Waste Management & Circular Economy Specialist",
        "h1": "Waste Management Specialist Salary in India: Pay & Career",
        "title": "Waste Management & Circular Economy Salary in India 2026",
        "desc": "Waste management and circular economy roles in India: EPR compliance, recycling, waste-to-energy. Skills, pay and career path.",
        "kicker": "Waste & circularity",
        "what": "Waste management and circular economy specialists work on waste reduction, recycling, EPR compliance and waste-to-energy. India's EPR rules are driving hiring.",
        "entry": [
            "A degree in environmental engineering, chemistry or waste management is common.",
            "Knowledge of EPR rules, waste classification and treatment technologies is listed in most postings.",
            "Field experience at waste processing facilities is valued.",
            "NGOs, consultancies and waste management companies are the main employers.",
        ],
        "match": lambda job: bool(re.search(r"waste|circul|recycl|epr", title_of(job))),
        "ladder": "Waste Management Executive -> Specialist -> Manager -> Head of Sustainability",
        "exam": "state-pollution-control-board",
        "hub": ("/esg-carbon-sustainability-jobs", "ESG, carbon and sustainability jobs"),
        "faqs": [
            ("What is EPR?", "Extended Producer Responsibility makes producers responsible for end-of-life management of their products."),
            ("Are waste jobs well paid?", "Entry-level roles are modestly paid; senior roles in waste-to-energy and consulting pay well."),
            ("Is this a government or private sector role?", "Both. State pollution boards and private waste companies hire."),
        ],
    },
    {
        "slug": "water-wash-specialist",
        "answer": "A water and WASH specialist works on water supply, sanitation and resource management. A civil or environmental engineering degree is standard; Jal Jeevan Mission is driving demand.",
        "name": "Water & WASH Specialist",
        "h1": "Water & WASH Specialist Salary in India: Pay & Career",
        "title": "Water & WASH Specialist Salary in India 2026: Pay & Career",
        "desc": "Water resources and WASH roles in India: Jal Jeevan Mission, water treatment, sanitation. Skills, pay and career path.",
        "kicker": "Water & sanitation",
        "what": "Water and WASH specialists work on water supply, sanitation, treatment and resource management. Jal Jeevan Mission and urban water projects drive demand.",
        "entry": [
            "A degree in civil engineering, environmental engineering or water resources is standard.",
            "Knowledge of water treatment, hydrology and sanitation systems is listed in most postings.",
            "Field experience with water projects is valued.",
            "Government agencies, NGOs and consultancies are the main employers.",
        ],
        "match": lambda job: bool(re.search(r"water|wash|hydro|sanitation", title_of(job))),
        "ladder": "Water Engineer -> Specialist -> Manager -> Head of Water Programmes",
        "exam": "state-pollution-control-board",
        "hub": ("/esg-carbon-sustainability-jobs", "ESG, carbon and sustainability jobs"),
        "faqs": [
            ("What is WASH?", "Water, Sanitation and Hygiene — a sector covering safe water supply, sanitation and hygiene promotion."),
            ("Is Jal Jeevan Mission hiring?", "Yes, through state implementing agencies and partner organisations."),
            ("Do I need a civil engineering degree?", "For engineering posts, yes. Science graduates apply to monitoring and programme roles."),
        ],
    },
    {
        "slug": "biodiversity-analyst",
        "answer": "A biodiversity and natural capital analyst assesses ecosystem services and nature-related risks. A master's in ecology or environmental science is common; TNFD is creating new demand.",
        "name": "Biodiversity & Natural Capital Analyst",
        "h1": "Biodiversity Analyst Salary in India: Pay, Skills & Entry",
        "title": "Biodiversity & Natural Capital Analyst Salary in India 2026",
        "desc": "Biodiversity and natural capital analyst roles in India: TNFD, nature-based solutions, ecosystem services. Skills and career path.",
        "kicker": "Nature & biodiversity",
        "what": "Biodiversity and natural capital analysts assess ecosystem services and nature-related risks for companies and investors. TNFD is creating new demand.",
        "entry": [
            "A master's in ecology, biodiversity, environmental science or economics is common.",
            "TNFD and nature-based solutions (NbS) frameworks are the emerging standards.",
            "Field survey skills and species identification are valued for conservation roles.",
            "Think tanks, NGOs and consultancies are the main employers.",
        ],
        "match": lambda job: bool(re.search(r"biodivers|ecolog|conservation|natural capital|nature", title_of(job))),
        "ladder": "Research Assistant -> Biodiversity Analyst -> Senior Analyst -> Nature Lead",
        "exam": "wii-pg-diploma",
        "hub": ("/forestry-wildlife-government-jobs", "Forestry and wildlife jobs"),
        "faqs": [
            ("What is TNFD?", "Taskforce on Nature-related Financial Disclosures — a framework for reporting nature-related risks."),
            ("Is this a new field?", "Yes. Nature-related disclosure is emerging, similar to where climate disclosure was 5 years ago."),
            ("Do I need field experience?", "For conservation roles, yes. For corporate natural capital roles, data and finance skills matter more."),
        ],
    },
    {
        "slug": "sustainability-reporting",
        "answer": "A sustainability reporting specialist prepares BRSR, GRI and other disclosure reports. BRSR and GRI framework knowledge is the most listed requirement; CA/CMA backgrounds are also hired.",
        "name": "Sustainability Reporting Specialist",
        "h1": "Sustainability Reporting Specialist Salary in India: Pay & Career",
        "title": "Sustainability Reporting Specialist Salary in India 2026",
        "desc": "Sustainability reporting specialist roles in India: BRSR, GRI, CSRD. Skills, pay and how to enter.",
        "kicker": "Reporting & disclosure",
        "what": "Sustainability reporting specialists prepare BRSR, GRI and other disclosure reports for companies. The role is part data collection, part writing and part assurance coordination.",
        "entry": [
            "A master's in sustainability, environment or business is common; CA/CMA backgrounds are also hired.",
            "BRSR and GRI framework knowledge is the most listed requirement.",
            "Data management and Excel skills are essential.",
            "Consulting firms and large listed companies are the main employers.",
        ],
        "match": lambda job: bool(re.search(r"reporting|brsr|disclosure|sustainability report", title_of(job))),
        "ladder": "Reporting Analyst -> Reporting Specialist -> Reporting Manager -> Head of Reporting",
        "exam": None,
        "hub": ("/esg-carbon-sustainability-jobs", "ESG, carbon and sustainability jobs"),
        "faqs": [
            ("Is BRSR mandatory?", "Yes for the top 1000 listed companies by market capitalisation, phased in from FY2022-23."),
            ("Do I need a CA?", "Not necessarily. Many postings accept sustainability or environment backgrounds."),
            ("What is CSRD?", "Corporate Sustainability Reporting Directive — the EU's reporting standard, relevant for Indian companies with EU operations."),
        ],
    },
    {
        "slug": "green-building",
        "answer": "A green building specialist works on LEED, GRIHA and IGBC certification and energy efficiency. An architecture or civil engineering degree is standard; LEED or GRIHA accreditation is listed in most postings.",
        "name": "Green Building & LEED Specialist",
        "h1": "Green Building Specialist Salary in India: Pay & Career",
        "title": "Green Building & LEED Specialist Salary in India 2026",
        "desc": "Green building and LEED specialist roles in India: certification, energy efficiency, sustainable construction. Skills and career path.",
        "kicker": "Built environment",
        "what": "Green building specialists work on LEED, GRIHA and IGBC certification, energy efficiency and sustainable construction. Real estate and consulting firms hire.",
        "entry": [
            "A degree in architecture, civil engineering or environmental engineering is standard.",
            "LEED or GRIHA accreditation is listed in most postings.",
            "Energy modelling and building simulation skills are valued.",
            "Consulting firms and real estate developers are the main employers.",
        ],
        "match": lambda job: bool(re.search(r"green building|leed|griha|igbc|built environment|building energy", title_of(job))),
        "ladder": "Green Building Analyst -> Specialist -> Manager -> Head of Sustainability",
        "exam": None,
        "hub": ("/esg-carbon-sustainability-jobs", "ESG, carbon and sustainability jobs"),
        "faqs": [
            ("What is LEED?", "Leadership in Energy and Environmental Design — a global green building certification by USGBC."),
            ("What is GRIHA?", "Green Rating for Integrated Habitat Assessment — India's national green building rating system."),
            ("Is green building a growing field?", "Yes. India is one of the top countries for LEED-certified space, and IGBC membership is growing."),
        ],
    },
    {
        "slug": "csr-manager",
        "answer": "A CSR manager oversees a company's social responsibility spend under Section 135 of the Companies Act. A master's in social work or business is common; programme management experience is listed in most postings.",
        "name": "CSR Manager",
        "h1": "CSR Manager Salary in India: Pay & Career Path",
        "title": "CSR Manager Salary in India 2026: Pay & Career Path",
        "desc": "CSR manager roles in India: corporate social responsibility spending, community programmes, NGO partnerships. Skills and career path.",
        "kicker": "Corporate responsibility",
        "what": "CSR managers oversee a company's social responsibility spend under Section 135 of the Companies Act. The role covers programme design, NGO partnerships and impact reporting.",
        "entry": [
            "A master's in social work, development studies or business is common.",
            "Programme management and NGO partnership experience are listed in most postings.",
            "Impact measurement and reporting skills are increasingly required.",
            "Large listed companies and their foundations are the main employers.",
        ],
        "match": lambda job: bool(re.search(r"\bcsr\b|corporate social", title_of(job))),
        "ladder": "CSR Executive -> CSR Manager -> Head of CSR / Sustainability",
        "exam": None,
        "hub": ("/esg-carbon-sustainability-jobs", "ESG, carbon and sustainability jobs"),
        "faqs": [
            ("Is CSR the same as ESG?", "No. CSR is a spending obligation; ESG is a performance framework. They overlap in practice."),
            ("Is CSR mandatory in India?", "Yes. Companies meeting profit/turnover/net-worth thresholds must spend 2% of average net profit on CSR activities."),
            ("Does CSR pay well?", "It varies. Foundation and large company roles pay reasonably; smaller company roles are modest."),
        ],
    },
]


def role_records(role: Dict[str, Any]) -> List[Dict[str, Any]]:
    matcher = role["match"]
    return [job for job in POOL if matcher(job)]


def build_role_page(role: Dict[str, Any]) -> None:
    records = role_records(role)
    paid = [job for job in records if discloses_pay(job)]
    skills = top_skills(records, 10)
    cities = top_cities(records, 6)
    exam = next((e for e in EXAMS if e["slug"] == role.get("exam")), None)

    skill_html = (
        "        <p class=\"skill-row\">"
        + " ".join(f'<span class="badge badge-type">{esc(skill)}</span>' for skill in skills)
        + "</p>"
        if skills
        else "        <p class=\"muted\">No structured skill list is attached to these listings.</p>"
    )
    city_html = (
        "<ul class=\"check-list\">"
        + "".join(
            f"<li><strong>{esc(city)}</strong> &mdash; {count} listing{'s' if count != 1 else ''}</li>"
            for city, count in cities
        )
        + "</ul>"
        if cities
        else "<p class=\"muted\">Location is not disclosed in these listings.</p>"
    )

    live = sorted(records, key=lambda j: str(j.get("valid_through") or "9999"))[:9]

    pay_section = f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Pay as advertised ({len(paid)} of {len(records)})</h2>
        <p>Every figure below is reproduced verbatim from the employer's notice. {len(records) - len(paid)} listing{'s' if len(records) - len(paid) != 1 else ''} in this role do not publish an amount, so no market band is inferred.</p>
{pay_table(records, "None of the current listings in this role publishes a pay figure. That is common in Indian ESG and research hiring; the notice for each post is the only reliable source.")}
      </div>
    </section>"""

    benchmark_section = """    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>How to benchmark when nothing is published</h2>
        <p>Most Indian notices leave pay out. These questions get you a comparable answer without a guessed band.</p>
        <ul class="check-list">
          <li><strong>Ask for the fixed and variable split.</strong> A headline CTC that is 20% variable is not the same as a fixed package.</li>
          <li><strong>Ask what the band is for the grade.</strong> Companies that will not quote a number will usually confirm a band once you are shortlisted.</li>
          <li><strong>Compare the whole offer.</strong> Provident fund, gratuity, insurance, travel and field allowance change the effective value materially in this sector.</li>
          <li><strong>Check the contract type.</strong> Fellowship, project contract and permanent posts are taxed and renewed differently; the notice states which one applies.</li>
        </ul>
      </div>
    </section>"""

    body = "\n".join(
        [
            hero(
                role["kicker"],
                role["h1"],
                role["what"],
                [
                    ("Listings analysed", str(len(records))),
                    ("Publish pay", f"{len(paid)}/{len(records)}" if records else "0"),
                    ("Updated", TODAY.strftime("%d %b %Y")),
                ],
            ),
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>In short</h2>
        <p><strong>{esc(role["answer"])}</strong></p>
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>How people enter</h2>
        <p>Drawn from the qualification and experience requirements in the current listings.</p>
{bullet_list(role["entry"])}
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Skills the notices ask for</h2>
        <p>Most frequent skills recorded across the {len(records)} active listings in this role.</p>
{skill_html}
      </div>
    </section>""",
            pay_section,
            benchmark_section,
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Where the roles are</h2>
        <p>Location recorded in the current listings. Remote and multi-location posts are grouped as published.</p>
{city_html}
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Live openings ({len(records)})</h2>
        <p>Sorted by closing date. Each links to the full dossier and the official application page.</p>
{cards_block(live, "No live listing matches this role today. New roles are added daily; browse the full registry in the meantime.")}
      </div>
    </section>""",
            section(
                "Progression",
                "The ladder most people follow, not a guarantee.",
                f"""        <p>{role["ladder"]}</p>
        <p>Movement between rungs depends on the employer. Government posts follow a promotion matrix; corporate and NGO roles depend on scope and budget.</p>""",
            ),
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Related pages</h2>
        <ul class="check-list">
          <li><a href="{role["hub"][0]}">{esc(role["hub"][1])}</a></li>
          {f'<li><a href="/exams/{exam["slug"]}">{esc(exam["name"])} recruitment guide</a></li>' if exam else ''}
          <li><a href="/salary-guide">Full salary guide by role, city and experience</a></li>
          <li><a href="/green-careers">Green career pathways</a></li>
        </ul>
      </div>
    </section>""",
            beh.bsp.faq_section_html(role["faqs"]),
        ]
    )
    jsonld = "\n".join(
        [
            beh.bsp.organization_jsonld(),
            beh.bsp.website_jsonld(),
            beh.breadcrumb(role["name"] + " salary profile", f"{SITE}/roles/{role['slug']}"),
            beh.faq_jsonld(role["faqs"]),
        ]
    )
    write_sub(
        ROLES_DIR,
        role["slug"],
        shell(
            title=role["title"],
            description=role["desc"],
            canonical=f"{SITE}/roles/{role['slug']}",
            body=body,
            jsonld=jsonld,
        ),
    )


def role_cards_html() -> str:
    return "\n".join(
        f"""        <article class="hub-card">
          <h3 class="hub-card-title"><a href="/roles/{role['slug']}">{esc(role["name"])}</a></h3>
          <p class="hub-card-sum">{esc(role["desc"])}</p>
          <p class="hub-card-foot"><span>{len(role_records(role))} live listing(s) &middot; {sum(1 for j in role_records(role) if discloses_pay(j))} with pay</span>
            <a href="/roles/{role['slug']}">See pay &rarr;</a></p>
        </article>"""
        for role in ROLES
    )


def exam_cards_html() -> str:
    return "\n".join(
        f"""        <article class="hub-card">
          <h3 class="hub-card-title"><a href="/exams/{exam['slug']}">{esc(exam["name"])}</a></h3>
          <p class="hub-card-sum">{esc(exam["desc"])}</p>
          <p class="hub-card-foot"><span>{len(exam_live_jobs(exam, INDIA))} live opening(s)</span>
            <a href="/exams/{exam['slug']}">Read the guide &rarr;</a></p>
        </article>"""
        for exam in EXAMS
    )


# ---------------------------------------------------------------------------
# Cross-links
# ---------------------------------------------------------------------------
def inject_cross_links() -> None:
    tracker = PUBLIC / "government-environment-jobs.html"
    if tracker.exists():
        block = f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Exam &amp; eligibility guides ({len(EXAMS)})</h2>
        <p>How each route recruits, what it asks for, and where the notification is published.</p>
        <div class="hub-list">
{exam_cards_html()}
        </div>
        <p style="margin-top:16px;"><a class="btn btn-primary" href="/exams">Open all exam guides &rarr;</a></p>
      </div>
    </section>"""
        tracker.write_text(inject(tracker.read_text(encoding="utf-8"), "<!-- EXAM_GUIDES_BLOCK -->", block), encoding="utf-8")

    careers = PUBLIC / "green-careers.html"
    if careers.exists():
        block = f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Role salary profiles ({len(ROLES)})</h2>
        <p>What each role pays where a notice publishes a figure, and what the work actually involves.</p>
        <div class="hub-list">
{role_cards_html()}
        </div>
      </div>
    </section>"""
        careers.write_text(inject(careers.read_text(encoding="utf-8"), "<!-- ROLE_PROFILES_BLOCK -->", block), encoding="utf-8")

    salary = PUBLIC / "salary-guide.html"
    if salary.exists():
        text = salary.read_text(encoding="utf-8")
        block = f"""    <section id="role-profiles" style="margin-top:28px;">
      <h2>Role profiles</h2>
      <p>Pay, skills and entry routes for the roles that appear most often in the registry. Each profile reproduces advertised figures and states how many listings disclose one.</p>
      <ul>
{chr(10).join(f'        <li><a href="/roles/{role["slug"]}">{esc(role["name"])} &mdash; salary and career profile</a></li>' for role in ROLES)}
      </ul>
    </section>"""
        if "<!-- ROLE_PROFILES_START -->" in text:
            text = re.sub(
                r"<!-- ROLE_PROFILES_START -->.*?<!-- ROLE_PROFILES_END -->",
                "<!-- ROLE_PROFILES_START -->\n" + block + "\n<!-- ROLE_PROFILES_END -->",
                text,
                flags=re.S,
            )
        else:
            text = text.replace(
                "</main>",
                "<!-- ROLE_PROFILES_START -->\n" + block + "\n<!-- ROLE_PROFILES_END -->\n  </main>",
                1,
            )
        salary.write_text(text, encoding="utf-8")


def main() -> None:
    for exam in EXAMS:
        build_exam_page(exam)
    build_exam_index()

    for role in ROLES:
        build_role_page(role)

    inject_cross_links()

    for exam in EXAMS:
        set_url(f"/exams/{exam['slug']}", "monthly", "0.8")
    set_url("/exams", "weekly", "0.9")
    for role in ROLES:
        set_url(f"/roles/{role['slug']}", "weekly", "0.7")

    print(f"Wrote {len(EXAMS)} exam guides + index and {len(ROLES)} role profiles")


if __name__ == "__main__":
    main()
