#!/usr/bin/env python3
"""Build the Career Advice and News hub pages."""
from __future__ import annotations

import build_expansion_hubs as beh
import build_seo_pages as bsp

PUBLIC = beh.PUBLIC
SITE = beh.SITE
TODAY = beh.TODAY
esc = beh.esc


def source_list(items):
    lines = []
    for name, url, note in items:
        lines.append('          <li><a href="%s" target="_blank" rel="noopener noreferrer">%s</a> &mdash; %s</li>' % (url, esc(name), esc(note)))
    return "\n".join(lines)


def build_career_advice():
    faqs = [
        ("Is a science degree required for green jobs?",
         "No. Many ESG, sustainability reporting and climate communications roles accept graduates from commerce, management, law and social sciences, provided they build domain knowledge."),
        ("How long does a career transition take?",
         "Most transitions take six to eighteen months of focused upskilling, portfolio work and targeted applications. Shorter for adjacent roles, longer for technical specialisations."),
        ("Which certifications help most?",
         "GRI, SASB, TCFD, GHG Protocol, LEED, IGBC and ISO 14064 are widely recognised. Choose one that matches the roles you are targeting rather than collecting many."),
        ("Where should I apply first?",
         "Start with the verified registry, then add direct employer portals, university project positions and government notifications. Avoid paid application channels."),
    ]
    related = [
        ("/green-careers", "Green career pathways"),
        ("/guides", "How-to guides"),
        ("/salary-guide", "Salary guide"),
        ("/courses", "Certification courses"),
        ("/compare", "Career comparisons"),
        ("/glossary", "Glossary of green terms"),
        ("/green-internships", "Internships and entry-level roles"),
        ("/fellowship-deadlines", "Fellowship deadlines"),
    ]
    hero_html = beh.hero(
        "Career advice",
        "Career Advice for Climate, Forestry, ESG & Sustainability",
        "Practical, evidence-based guidance for entering and growing in green careers in India - from first internship to senior ESG and forestry leadership roles.",
        [
            ("Focus", "India + Global"),
            ("Topics", "Skills, CV, interviews"),
            ("Updated", TODAY.strftime("%d %b %Y")),
        ],
    )
    sections = []
    sections.append("""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Start with a pathway, not a job title</h2>
        <p>The green sector is wide. Pick one pathway, learn its vocabulary and build proof of work before applying broadly.</p>
        <ul class="check-list">
          <li><a href="/green-careers">Green career pathways</a> &mdash; research, forestry, ESG, GIS, climate policy and internships.</li>
          <li><a href="/guides">How-to guides</a> &mdash; step-by-step entry routes, including JRF applications and BRSR reporting.</li>
          <li><a href="/salary-guide">Salary guide</a> &mdash; realistic pay bands by role and experience.</li>
          <li><a href="/compare">Career comparisons</a> &mdash; JRF vs SRF, ESG vs CSR, GIS vs remote sensing and more.</li>
        </ul>
      </div>
    </section>""")
    sections.append("""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Skills employers actually ask for</h2>
        <ul class="check-list">
          <li><strong>Domain foundations:</strong> ecology, forestry, climate science, environmental law, ESG frameworks and sustainability reporting.</li>
          <li><strong>Data skills:</strong> GIS, remote sensing, R or Python, Excel, dashboards and basic statistics.</li>
          <li><strong>Reporting and compliance:</strong> GRI, SASB, TCFD, BRSR, GHG Protocol and ISO 14064.</li>
          <li><strong>Field and project skills:</strong> sampling, survey design, community engagement and monitoring.</li>
          <li><strong>Communication:</strong> technical writing, policy briefs, presentations and stakeholder management.</li>
        </ul>
      </div>
    </section>""")
    sections.append("""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Resume, CV and interview preparation</h2>
        <p>Use the registry's guides to structure applications and avoid the common errors that screeners reject.</p>
        <ul class="check-list">
          <li><a href="/guides/jrf-cv-format">JRF CV format</a> and <a href="/guides/jrf-interview-prep">JRF interview preparation</a>.</li>
          <li><a href="/guides/esg-interview-questions">ESG interview questions</a> and <a href="/guides/gis-interview-questions">GIS interview questions</a>.</li>
          <li><a href="/guides/esg-analyst-resume-template">ESG analyst resume template</a>.</li>
          <li><a href="/guides/interview-preparation">General interview preparation</a>.</li>
        </ul>
      </div>
    </section>""")
    sections.append("""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Networking and professional visibility</h2>
        <ul class="check-list">
          <li>Join the <a href="https://t.me/urbanforestpark" target="_blank" rel="noopener noreferrer">Urban Forest Park Telegram community</a> for verified openings.</li>
          <li>Participate in the <a href="https://www.linkedin.com/groups/40965341/" target="_blank" rel="noopener noreferrer">LinkedIn group</a> and share short case notes or field observations.</li>
          <li>Attend <a href="/webinars-live-events">webinars and live events</a> and <a href="/conferences-summits-events">conferences and summits</a>.</li>
          <li>Build a small public portfolio: a short analysis, a map, a plantation monitoring note or a BRSR commentary.</li>
        </ul>
      </div>
    </section>""")
    sections.append("""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Certifications and courses</h2>
        <p>Certifications signal commitment, but projects and evidence of work matter more. Browse the <a href="/courses">course directory</a> for GRI, SASB, TCFD, GHG Protocol, LEED, IGBC, ISO 14064 and related programmes.</p>
      </div>
    </section>""")
    sections.append("""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Common mistakes to avoid</h2>
        <ul class="check-list">
          <li>Applying with a generic CV instead of tailoring to the role.</li>
          <li>Ignoring deadlines, eligibility and required documents.</li>
          <li>Paying for placement or application services.</li>
          <li>Listing coursework without evidence of applied work.</li>
          <li>Networking only when you need a job.</li>
        </ul>
      </div>
    </section>""")
    related_html = "".join('<li><a href="%s">%s</a></li>' % (href, esc(label)) for href, label in related)
    sections.append("""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Related pages</h2>
        <ul class="check-list">
          %s
        </ul>
      </div>
    </section>""" % related_html)
    body = "\n".join([hero_html] + sections + [bsp.faq_section_html(faqs)])
    jsonld = "\n".join([
        bsp.organization_jsonld(),
        bsp.website_jsonld(),
        beh.breadcrumb("Career Advice for Climate, Forestry, ESG & Sustainability", SITE + "/career-advice"),
        beh.faq_jsonld(faqs),
    ])
    beh.write_page("career-advice", beh.shell(
        title="Career Advice for Climate, Forestry, ESG & Sustainability | UFP",
        description="Practical career advice for green jobs in India - skills, CVs, interviews, networking, certifications and pathways across forestry, ESG, GIS and climate policy.",
        canonical=SITE + "/career-advice",
        body=body,
        jsonld=jsonld,
    ))
    print("Wrote career-advice")


def build_news():
    faqs = [
        ("How often is this page updated?",
         "The page is refreshed with each site build. For daily verified vacancies, use the career registry and RSS feeds."),
        ("Are these links official sources?",
         "We prioritise ministry, regulator, multilateral and research-institution sources, alongside established climate and environment publications."),
        ("Does Urban Forest Park publish original journalism?",
         "No. We are a career and research registry; this page points to reporting and primary sources for context."),
    ]
    india_sources = [
        ("Ministry of Environment, Forest and Climate Change", "https://moef.gov.in", "Policy, programmes and notifications."),
        ("Press Information Bureau", "https://pib.gov.in", "Government announcements and releases."),
        ("Forest Survey of India", "https://fsi.nic.in", "Forest cover and assessment updates."),
        ("NITI Aayog", "https://www.niti.gov.in", "Strategy and sustainability initiatives."),
        ("Down To Earth", "https://www.downtoearth.org.in", "Environment and development reporting."),
        ("Mongabay India", "https://india.mongabay.com", "Conservation and biodiversity reporting."),
    ]
    global_sources = [
        ("UNEP", "https://www.unep.org", "Global environment programme updates."),
        ("IPCC", "https://www.ipcc.ch", "Climate science assessments."),
        ("World Bank", "https://www.worldbank.org", "Climate and development finance."),
        ("UNFCCC", "https://unfccc.int", "Climate negotiations and NDCs."),
        ("Carbon Brief", "https://www.carbonbrief.org", "Climate science and policy analysis."),
        ("IUCN", "https://www.iucn.org", "Conservation and nature-based solutions."),
    ]
    esg_sources = [
        ("SEBI", "https://www.sebi.gov.in", "BRSR and ESG disclosure regulation in India."),
        ("RBI", "https://www.rbi.org.in", "Green finance and climate risk guidance."),
        ("GRI", "https://www.globalreporting.org", "Sustainability reporting standards."),
        ("TCFD", "https://www.fsb-tcfd.org", "Climate-related financial disclosures."),
        ("SASB", "https://sasb.org", "Industry-specific sustainability standards."),
    ]
    forest_sources = [
        ("FAO Forestry", "https://www.fao.org/forestry", "Global forest resources and policy."),
        ("Global Forest Watch", "https://www.globalforestwatch.org", "Forest monitoring and alerts."),
        ("ICFRE", "https://icfre.gov.in", "Forestry research and education in India."),
        ("WII", "https://wii.gov.in", "Wildlife research and training."),
    ]
    research_sources = [
        ("CSIR", "https://www.csir.res.in", "Scientific research and vacancies."),
        ("ICAR", "https://icar.org.in", "Agricultural and environmental research."),
        ("Nature Climate Change", "https://www.nature.com/nclimate", "Peer-reviewed climate research."),
        ("Science", "https://www.science.org", "Scientific developments."),
    ]
    hero_html = beh.hero(
        "News & developments",
        "Climate, Forestry & ESG News — Global and India",
        "A curated orientation to current developments in climate, forestry, ESG and sustainability, with links to the primary sources and publications we track.",
        [
            ("Scope", "India + Global"),
            ("Themes", "Policy, markets, forests"),
            ("Updated", TODAY.strftime("%d %b %Y")),
        ],
    )
    sections = []
    sections.append("""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>How to use this page</h2>
        <p>This is not a live wire service. It is a stable orientation page that points to the institutions, regulators and publications where new developments appear first. For verified vacancies, use the <a href="/">career registry</a> and <a href="/feeds">RSS feeds</a>.</p>
      </div>
    </section>""")
    sections.append("""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>India: climate, forestry and ESG developments</h2>
        <p>Track notifications, programmes and reporting from Indian institutions.</p>
        <ul class="check-list">
%s
        </ul>
      </div>
    </section>""" % source_list(india_sources))
    sections.append("""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Global developments</h2>
        <p>Multilateral assessments, negotiations and finance that shape national policy.</p>
        <ul class="check-list">
%s
        </ul>
      </div>
    </section>""" % source_list(global_sources))
    sections.append("""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>ESG and sustainable finance</h2>
        <p>Disclosure standards, green finance and corporate sustainability reporting.</p>
        <ul class="check-list">
%s
        </ul>
      </div>
    </section>""" % source_list(esg_sources))
    sections.append("""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Forests, biodiversity and dMRV</h2>
        <p>Forest monitoring, conservation and measurement, reporting and verification.</p>
        <ul class="check-list">
%s
        </ul>
        <p style="margin-top:12px;"><a href="/dashboard">Open the Nagar Van dMRV Dashboard &rarr;</a></p>
      </div>
    </section>""" % source_list(forest_sources))
    sections.append("""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Research and innovation</h2>
        <p>Scientific advances and research institutions behind green careers.</p>
        <ul class="check-list">
%s
        </ul>
      </div>
    </section>""" % source_list(research_sources))
    sections.append("""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Related pages</h2>
        <ul class="check-list">
          <li><a href="/career-advice">Career advice</a></li>
          <li><a href="/green-careers">Green career pathways</a></li>
          <li><a href="/guides">How-to guides</a></li>
          <li><a href="/glossary">Glossary</a></li>
          <li><a href="/courses">Certification courses</a></li>
        </ul>
      </div>
    </section>""")
    body = "\n".join([hero_html] + sections + [bsp.faq_section_html(faqs)])
    jsonld = "\n".join([
        bsp.organization_jsonld(),
        bsp.website_jsonld(),
        beh.breadcrumb("Climate, Forestry & ESG News — Global and India", SITE + "/news"),
        beh.faq_jsonld(faqs),
    ])
    beh.write_page("news", beh.shell(
        title="Climate, Forestry & ESG News — Global and India Developments | UFP",
        description="Curated orientation to current developments in climate, forestry, ESG and sustainability, with links to primary sources and publications we track.",
        canonical=SITE + "/news",
        body=body,
        jsonld=jsonld,
    ))
    print("Wrote news")


def main():
    build_career_advice()
    build_news()
    # update sitemap
    sitemap = beh.SITEMAP
    text = sitemap.read_text(encoding="utf-8")
    added = 0
    for path in ("/career-advice", "/news"):
        loc = SITE + path
        if "<loc>%s</loc>" % loc in text:
            continue
        entry = "  <url><loc>%s</loc><lastmod>%s</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>" % (loc, TODAY.isoformat())
        text = text.replace("</urlset>", entry + "\n</urlset>")
        added += 1
    if added:
        sitemap.write_text(text, encoding="utf-8")
    print("sitemap +%d" % added)


if __name__ == "__main__":
    main()
