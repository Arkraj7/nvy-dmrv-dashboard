/* ==========================================================================
   Urban Forest Park — bilingual interface engine (EN | हिंदी)
   --------------------------------------------------------------------------
   Loaded before js/jobs.js (defer order). Responsibilities:

     1. Dictionary of formal English + formal Hindi strings for the core
        registry interface: hero, navigation, telemetry ribbon, filters,
        career tracks, sector tabs, archive notice, community strip,
        Email alert box, executive FAQ and every dynamic label that
        jobs.js renders (counts, cards, dossier sections, apply buttons).

     2. data-i18n attribute translator for static markup:
          data-i18n             -> textContent
          data-i18n-html        -> innerHTML (trusted static strings only)
          data-i18n-placeholder -> placeholder attribute
          data-i18n-aria        -> aria-label attribute
          data-i18n-title       -> title attribute

     3. Persistence in localStorage ('ufp_lang'), <html lang="en-IN"> /
        <html lang="hi-IN"> synchronisation, and a 'ufp:langchange' event
        that js/jobs.js consumes to re-render the feed and open dossier
        with the bilingual job fields (title_hi / summary_hi).

   Public API (window.UFPI18N):
     t(key)            -> current-language string (undefined when absent)
     lang              -> 'en' | 'hi'
     isHindi()         -> boolean
     setLang('en'|'hi', opts) -> switches language (opts.silent skips event)
     apply(root)       -> re-applies data-i18n attributes under root
     heroHtml()        -> hero <h1> markup for the active language
   ========================================================================== */
(function () {
  'use strict';

  var STORE_KEY = 'ufp_lang';
  var HTML_LANG = { en: 'en-IN', hi: 'hi-IN' };

  /* ------------------------------------------------------------------
     Dictionary. Keys are shared between the static markup (data-i18n)
     and the dynamic renderers in jobs.js (UFPI18N.t(key)).
     Acronyms and technical terms (JRF, SRF, GIS, ESG, PhD, dMRV, BRSR)
     deliberately stay in Latin script inside the Hindi strings, per the
     registry's bilingual editorial standard.
     ------------------------------------------------------------------ */
  var DICT = {
    en: {
      'skip.link': 'Skip to registry listings',

      'brand.sub': 'Green Jobs & Research Registry',
      'nav.registry': 'Career Registry',
      'nav.archive': 'Historical Archive',
      'nav.browse': 'Browse by State',
      'nav.dashboard': 'dMRV Dashboard',
      'nav.livebadge': 'Live Tool',
      'nav.publish': 'Publish a Vacancy',
      'lang.aria': 'Interface language: English',
      'theme.aria': 'Switch to night mode',
      'theme.aria.light': 'Switch to light mode',
      'detail.archive.badge': 'Archived Record',
      'detail.foot.back': 'Back to ',
      'mini.email.aria': 'Email address',
      'theme.night': 'Night',
      'theme.light': 'Light',

      'tel.aria': 'Weekly hiring telemetry',
      'tel.eyebrow': 'Weekly Hiring Telemetry',
      'tel.updated': 'Registry updated',
      'tel.local': 'local sync',
      'tel.active.label': 'Active Open Positions',
      'tel.active.note': 'Live registry-wide count',
      'tel.new.label': 'New Roles Added (Last 7 Days)',
      'tel.new.note': 'Weekly inflow of jobs',
      'tel.passed.label': 'Positions Closed / Passed (Last 7 Days)',
      'tel.passed.note': 'Weekly outflow to the archive',
      'tel.archive.label': 'Cumulative Career Archive',
      'tel.archive.note': 'Total historical roles tracked',

      'hero.kicker': 'Verified Environmental, Forestry, JRF, GIS & ESG Jobs - India',
      'hero.title_html': 'Environmental, Forestry, JRF, GIS &amp; ESG Jobs in India <span class="accent">(2026)</span>',
      'hero.sub_html': 'Verified Government Forestry, JRF/SRF Environmental Science, CAMPA, Wildlife, GIS/Remote Sensing, Corporate ESG &amp; PhD Fellowships across India &amp; Globally. <strong>Every listing links straight to the official application page</strong> - free, no fees. Closed roles stay in the Historical Archive for stipend, skills and institutional reference.',
      'hero.cta.browse': 'Browse Active Jobs & Fellowships',
      'hero.cta.archive': 'Historical Job Archive',

      'community.title': 'Join India\u2019s Green & Academic Job Alert Network',
      'community.sub': 'Daily JRF, forestry, GIS, ESG and climate jobs - verified and broadcast every morning at 7 AM IST.',
      'community.wa': 'Join WhatsApp Job Group',
      'community.tg': 'Join Telegram Channel',

      'tabs.aria': 'Registry view',
      'tabs.active': 'Active Opportunities',
      'tabs.archive': 'Archived / Past Positions',

      'filters.search.label': 'Search the registry',
      'filters.search.placeholder': 'Search title, organisation or competency\u2026',
      'filters.search.aria': 'Search registry by position title, organisation or competency',
      'filters.state.label': 'State / Region',
      'filters.state.aria': 'Filter jobs by Indian state or region',
      'filters.state.all': 'All India',
      'filters.state.alln': 'All India ({n})',
      'filters.exp.label': 'Experience Tier',
      'filters.exp.aria': 'Filter jobs by experience tier',
      'filters.exp.all': 'All Levels',
      'filters.exp.entry': 'Entry Level / Fellowship',
      'filters.exp.1-3': '1-3 Years',
      'filters.exp.mid': 'Mid-Senior (3-6 Years)',
      'filters.exp.senior': 'Senior',
      'filters.window.label': 'Application Window',
      'filters.window.all': 'All Past Records',
      'filters.window.recent': 'Closed in Last 7 Days',
      'filters.reset': 'Reset Filters',
      'tracks.aria': 'Filter jobs by career track',
      'tracks.label': 'Career Track',
      'tracks.all': 'All Environmental Jobs',
      'tracks.research': 'JRF / SRF & Project Associates',
      'tracks.phd': 'PhD & Postdoctoral Fellowships',
      'tracks.contractual': 'Young Professional & Govt Contractual',
      'tracks.corporate': 'Corporate ESG & Sustainability',
      'tracks.thinktank': 'Think-Tanks, NGOs & Policy',
      'pills.aria': 'Filter jobs by sector',
      'pills.all': 'All Environmental Jobs',
      'pills.academic': 'JRF, SRF, Project Associate & PhD',
      'pills.research': 'Research Associate & Project Staff',
      'pills.forestry': 'Govt Forestry, CAMPA, Wildlife & SPCB',
      'pills.gis': 'GIS, Remote Sensing & Earth Observation',
      'pills.esg': 'ESG, Carbon & Sustainability',
      'pills.policy': 'Climate Policy, Think-Tanks & NGOs',
      'pills.grants': 'Grants & Research Funding',
      'pills.scholarships': 'Scholarships & Doctoral Support',
      'pills.fellowships': 'Fellowships & Leadership Programs',
      'pills.internships': 'Internships & Student Traineeships',
      'pills.competitions': 'Competitions, Hackathons & Awards',

      /* Jurisdiction switcher (India jobs | Global opportunities) */
      'js.aria': 'Jurisdiction switcher — India jobs or Global opportunities',
      'js.india.title': 'India Jobs',
      'js.india.sub': 'Jobs, JRF, Fellowships & Grants',
      'js.india.short': 'India',
      'js.global.title': 'Global Opportunities',
      'js.global.sub': 'International Jobs, Grants & Scholarships',
      'js.global.short': 'Global',
      'registry.switch.india': 'Showing India jobs (JRF, fellowships & grants)',
      'registry.switch.global': 'Showing Global Opportunities (international jobs, grants & scholarships)',
      'hero.cta.globals': '🌍 Global Opportunities Hub',
      'hero.global.kicker': 'Global Opportunities Registry (International)',
      'hero.global.title_html': 'Worldwide <span class="accent">Climate &amp; Sustainability</span> Opportunities',
      'hero.global.sub': 'International jobs, grants, scholarships, fellowships, internships and competitions across climate, forestry, energy, water, biodiversity and ESG — verified, with direct links to the official portal.',

      /* Opportunity type filter (jobs + grants + scholarships + ...) */
      'filters.kind.label': 'Opportunity Type',
      'filters.kind.aria': 'Filter by opportunity type — job, fellowship, scholarship, grant, internship or competition',
      'filters.kind.all': 'All Types (Jobs, Grants, Fellowships…)',
      'filters.kind.job': 'Job / Career',
      'filters.kind.fellowship': 'Fellowship',
      'filters.kind.scholarship': 'Scholarship',
      'filters.kind.grant': 'Grant / Funding',
      'filters.kind.internship': 'Internship',
      'filters.kind.competition': 'Competition / Award',
      'filters.gregion.label': 'Global Region',
      'filters.gregion.all': 'All Global ({n})',

      /* Opportunity kind badges, deadlines & region rows */
      'card.deadline': 'Apply: {d}',
      'detail.kind': 'Opportunity Type',
      'detail.deadline': 'Deadline / Window',
      'detail.region': 'Region',

      /* PWA install + instant alert widget */
      'widget.title': 'Get the UrbanForestPark App & Instant Job Alerts',
      'widget.sub': 'JRF, Forestry, ESG and Grant alerts — straight to your phone the moment they are verified.',
      'widget.install': '📲 Download / Install App',
      'widget.notify': '🔔 Enable Instant Job Notifications',
      'widget.pill': 'App & Alerts',

      'mini.aria': 'Subscribe to free job and fellowship email alerts',
      'mini.title': 'Free Job & Fellowship Email Alerts',
      'mini.sub': 'New verified jobs and fellowships - issued every 72 hours.',
      'mini.join': 'Join',
      'mini.placeholder': 'you@organisation.in',

      'feed.eyebrow': 'Active Environmental Jobs',
      'feed.title': 'Active Jobs & Fellowships',
      'feed.eyebrow.archive': 'Historical Job Archive',
      'feed.title.archive': 'Archived / Past Positions',
      'feed.eyebrow.global': 'Global Opportunities Registry',
      'feed.title.global': 'International Opportunities',
      'feed.order': 'Ordered by publication date',
      'feed.loading': 'Loading\u2026',
      'feed.active.one': '1 active position',
      'feed.active.many': '{n} active positions',
      'feed.archive.one': '1 historical record',
      'feed.archive.many': '{n} historical records',
      'feed.loadingstate': 'Loading registry jobs\u2026',

      'empty.nomatch.active': 'No active jobs match these filters',
      'empty.nomatch.archive': 'No archived records match these filters',
      'empty.hint': 'Try a different keyword, region or sector — or reset the filters.',
      'empty.archive.note': 'No active jobs are open in this sector at present - {n} historical record(s) exist in the archive.',
      'empty.switcharchive': 'View Historical Archive',
      'empty.reset': 'Reset Filters',
      'empty.nolist.active.title': 'No listings yet',
      'empty.nolist.active.sub': 'New environmental jobs are published regularly. Check back soon.',
      'empty.nolist.archive.title': 'The historical archive is being catalogued',
      'empty.nolist.archive.sub': 'Past jobs appear here once their application windows close.',
      'empty.error.title': 'Could not load registry data',
      'empty.error.sub': 'Please refresh the page. If this persists, check that jobs.json is being served on this domain.',

      'card.cta.active': 'View Job & Apply',
      'card.cta.archive': 'Open Archived Record',
      'card.archived': 'Archived',
      'card.more': '+{n} more',
      'card.aria.view': 'View job and apply: ',
      'card.aria.archive': 'Open archived record: ',
      'card.closed': 'Closed ',

      'detail.back.active': 'Active Opportunities',
      'detail.back.archive': 'Historical Archive',
      'detail.share.wa': 'Share on WhatsApp',
      'detail.share.li': 'Share on LinkedIn',
      'detail.share.copy': 'Copy Direct Link',
      'detail.banner.archived': 'Archived Job:',
      'detail.banner.body': 'the application window for this position closed on {date}. This record is maintained in the Urban Forest Park Career Registry for compensation, skill, and institutional reference.',
      'detail.summary.h2': 'Job Summary',
      'detail.summaryhi.h2': 'हिंदी सारांश',
      'detail.elig.h2': 'Position & Eligibility',
      'detail.pt': 'Position Type',
      'detail.engagement': 'Engagement',
      'detail.qualification': 'Qualification',
      'detail.comp': 'Compensation / Fellowship',
      'detail.resp.h2': 'Core Responsibilities',
      'detail.skills.h2': 'Required Competencies',
      'detail.tip': 'Candidate Advisory',
      'detail.ref': 'Ref: ',
      'detail.valid': 'Valid through ',
      'detail.archived.on': 'Archived ',
      'detail.suggest.h3': 'Currently Active Positions in This Sector',
      'detail.suggest.aria': 'View active position: ',

      'verify.kicker': 'Application record',
      'verify.source': 'Source: ',
      'verify.apply.on': 'Apply on ',
      'verify.apply.archive': 'View Original Application Portal',
      'verify.website': 'Visit Official Website',
      'verify.website.sub': 'official portal',
      'verify.website.empty': 'Official Website',
      'verify.website.empty.sub': 'Not listed — use the source portal',
      'verify.note.active': 'Both links open in a new tab. Always verify eligibility, fellowship norms and deadlines on the employer\u2019s page before applying.',
      'verify.note.archive': 'This job is archived — the application window has closed. Both links open the original portal for institutional reference only.',

      'cc.title': 'Get Daily JRF, Forestry, GIS & ESG Job Alerts',
      'cc.sub': 'Join India\u2019s green & academic job-alert network - verified jobs delivered every morning at 7 AM IST.',
      'cc.join.wa': 'Join WhatsApp Job Group \u2197',
      'cc.join.tg': 'Join Telegram Job Channel \u2197',
      'cc.share.wa': 'Share Formatted Alert to WhatsApp',
      'cc.share.tg': 'Share to Telegram',

      'dispatch.eyebrow': 'Free Email Job Alerts',
      'dispatch.title': 'Environmental, Forestry, JRF & ESG Job Alerts',
      'dispatch.sub': 'A free email alert - issued every 72 hours - carrying the period\u2019s verified jobs: Govt forestry, CAMPA, FSI and SPCB roles, JRF / SRF and PhD fellowships, GIS and remote sensing positions, and corporate ESG jobs across India.',
      'dispatch.point1': 'Drawn exclusively from the same verified registry published on this page.',
      'dispatch.point2': 'Direct application links and free access — no fees at any stage.',
      'dispatch.point3': 'One-click opt-out; unsubscribe requests honoured within 7 working days.',
      'dispatch.ledger_html': 'Also available: the instant <a href="https://t.me/urbanforestpark" target="_blank" rel="noopener">Telegram channel</a> and the <a href="https://chat.whatsapp.com/JJ0ItiNOfvEDCDIENscenw" target="_blank" rel="noopener">WhatsApp job group</a>.',
      'dispatch.form.title': 'Subscribe to Free Job & Fellowship Email Alerts',
      'dispatch.email.label': 'Email Address',
      'dispatch.freq.legend': 'Frequency',
      'dispatch.freq.group': 'Email alert frequency',
      'dispatch.freq.3day': 'Every 3 Days (Recommended)',
      'dispatch.freq.weekly': 'Weekly Digest',
      'dispatch.sector.label': 'Sector Preference',
      'dispatch.sector.all': 'All Environmental Jobs',
      'dispatch.sector.academic': 'JRF / PhD / Academic',
      'dispatch.sector.forestry': 'Forestry & GIS',
      'dispatch.sector.esg': 'Corporate ESG',
      'dispatch.submit': 'Subscribe to Free Job & Fellowship Email Alerts',
      'dispatch.micro_html': 'Issued every 72 hours. Zero spam. Governed by our <a href="/privacy.html">institutional Privacy Policy</a> and our <a href="/terms.html">Terms of Use</a>.',
      'dispatch.invalid': 'Enter a valid email address to subscribe.',
      'dispatch.registering': 'Registering subscription\u2026',
      'dispatch.mini.ok': 'Subscribed — next email alert within 72 hours.',
      'dd.title': 'Subscription recorded',
      'dd.address': 'Address',
      'dd.frequency': 'Frequency',
      'dd.sector': 'Sector',
      'dd.freq.weekly': 'Weekly digest',
      'dd.freq.3day': 'Every 3 days',
      'dd.manage': 'Manage or withdraw this subscription',
      'dd.update': 'Update preferences',
      'dd.note.local': 'Saved on this device. To join the current email alert list immediately, write to urbanforestpark@gmail.com.',
      'sector.all': 'All jobs',
      'sector.academic': 'JRF / PhD / Academic',
      'sector.forestry-gis': 'Forestry & GIS',
      'sector.corporate-esg': 'Corporate ESG',
      'toast.dark': 'Night mode enabled',
      'toast.light': 'Light mode enabled',
      'toast.subscribed': 'Email alerts subscribed - next briefing within 72 hours.',
      'toast.saved': 'Email alert preference saved on this device.',

      'faq.eyebrow': 'Platform Governance & Methodology',
      'faq.title': 'Frequently Asked Questions',
      'faq.sub': 'A formal reference for candidates, institutions, researchers and partners on how this registry is governed, verified and maintained. Corresponding structured data is published as FAQPage schema in this page\u2019s metadata.',
      'faq.q1': 'What is the core mission of the Urban Forest Park Career Registry, and what gap does it resolve?',
      'faq.a1': 'India\u2019s environmental, forestry, geospatial and academic recruitment landscape is fragmented across hundreds of unindexed institutional notices - recruitment PDFs and advertisements issued by ICFRE institutes, the Wildlife Institute of India, IIFM, IIRS, ICAR bodies and Indian universities, alongside opportunities published separately by development think-tanks such as CEEW, WRI India, TERI and ATREE, and by corporate ESG portals. Urban Forest Park resolves this information asymmetry by aggregating, verifying and structuring these jobs and fellowships into a single searchable national registry, with every entry linked to a direct application source.',
      'faq.q2': 'How are job listings, JRF/SRF fellowships, and institutional links verified on this platform?',
      'faq.a2': 'Every listing passes through an automated verification pipeline before publication. Candidates are surfaced from employer portals, job platforms, verified feeds and institutional notices; each record then undergoes domain verification, redirect unwrapping (so links resolve to the publisher rather than a news wrapper), duplicate hashing and editorial structuring into a standardised dossier. Each dossier presents both a direct application link and the verified website of the parent organisation, so applicants can confirm every detail at its authoritative source.',
      'faq.q3': 'What happens to expired or closed jobs, and why is a historical archive maintained?',
      'faq.a3': 'Active jobs remain in the registry for a 30-day lifecycle; when an application window closes, the record transitions automatically into the Historical Job Archive (archive.json). The archive is maintained as a public research asset: students, researchers and policy analysts can benchmark historical fellowship stipends, recurring technical requirements (GIS, Google Earth Engine, BRSR reporting, carbon markets) and seasonal hiring velocity across Indian states and union territories.',
      'faq.q4': 'How frequently is the registry updated, and how do the Email, WhatsApp, and Telegram job alerts work?',
      'faq.a4': 'The registry is harvested by an automated pipeline every day at 07:00 AM IST. Verified jobs are published immediately and broadcast through instant Telegram and WhatsApp alert channels; a free email briefing of new jobs and fellowships is issued every 72 hours, summarising each period\u2019s verified positions, registry telemetry and geographical coverage.',
      'faq.q5': 'What is the relationship between the Career Registry and the Nagar Van Yojana dMRV Dashboard & Green Calculator?',
      'faq.a5_html': 'Urban Forest Park originated as a digital Monitoring, Reporting and Verification (dMRV) and Urban Heat Island (UHI) analytics initiative for urban forestry in India. Alongside the national career registry, the platform continues to operate and maintain its open-access public research utilities — the <a href="/dashboard.html">Nagar Van dMRV Dashboard</a> and the <a href="/green-calculator.html">Green Calculator</a> — freely available to institutions, researchers and citizens.',
      'faq.q6': 'Is there any fee for candidates or institutions to access listings or subscribe to email alerts?',
      'faq.a6': 'None. The registry and every alert channel - the website, the 72-hour email briefing, the Telegram channel and the WhatsApp group - are 100% open-access for candidates, researchers, academic scholars and institutional partners. Urban Forest Park does not charge candidates any fee at any stage and does not act as a recruitment intermediary; all applications are submitted directly to the employer\u2019s official portal.',
      'faq.note_html': 'Further statutory detail is published in the <a href="/privacy.html">Privacy Policy</a>, <a href="/terms.html">Terms of Use</a> and <a href="/cookies.html">Cookie Policy</a>. Institutional enquiries: <a href="mailto:urbanforestpark@gmail.com">urbanforestpark@gmail.com</a>.'
    },

    hi: {
      'skip.link': 'सूचीबद्ध भर्तियों पर जाएँ',

      'brand.sub': 'हरित करियर रजिस्ट्री',
      'nav.registry': 'करियर रजिस्ट्री',
      'nav.archive': 'ऐतिहासिक संग्रह',
      'nav.browse': 'राज्य अनुसार देखें',
      'nav.dashboard': 'dMRV डैशबोर्ड',
      'nav.livebadge': 'लाइव टूल',
      'nav.publish': 'रिक्ति प्रकाशित करें',
      'lang.aria': 'इंटरफ़ेस भाषा: हिंदी',
      'theme.aria': 'रात्रि मोड पर स्विच करें',
      'theme.aria.light': 'दिवस मोड पर स्विच करें',
      'detail.archive.badge': 'संग्रहित रिकॉर्ड',
      'detail.foot.back': 'वापस: ',
      'mini.email.aria': 'ई-मेल पता',
      'theme.night': 'रात्रि',
      'theme.light': 'दिवस',

      'tel.aria': 'साप्ताहिक भर्ती टेलीमेट्री',
      'tel.eyebrow': 'साप्ताहिक भर्ती टेलीमेट्री',
      'tel.updated': 'रजिस्ट्री अद्यतन',
      'tel.local': 'स्थानीय सिंक',
      'tel.active.label': 'सक्रिय खुले पद',
      'tel.active.note': 'रजिस्ट्री-व्यापी सक्रिय गणना',
      'tel.new.label': 'नए जोड़े गए पद (पिछले 7 दिन)',
      'tel.new.note': 'अधिदेशों का साप्ताहिक अंतर्वाह',
      'tel.passed.label': 'बंद / समाप्त पद (पिछले 7 दिन)',
      'tel.passed.note': 'संग्रह की ओर साप्ताहिक बहिर्वाह',
      'tel.archive.label': 'संचयी करियर संग्रह',
      'tel.archive.note': 'कुल ऐतिहासिक पद दर्ज',

      'hero.kicker': 'राष्ट्रीय पर्यावरणीय अधिदेश रजिस्ट्री — भारत',
      'hero.title_html': 'भारत में पर्यावरण, वानिकी, JRF, GIS एवं ESG नौकरियाँ <span class="accent">(2026)</span>',
      'hero.sub_html': 'भारत एवं वैश्विक स्तर पर सत्यापित सरकारी वानिकी, JRF/SRF पर्यावरण विज्ञान, CAMPA, वन्यजीव, GIS/रिमोट सेंसिंग, कॉर्पोरेट ESG एवं PhD फेलोशिप। <strong>प्रत्येक सूची सीधे आधिकारिक आवेदन पोर्टल से जुड़ी है</strong> — निःशुल्क, कोई शुल्क नहीं। बंद नौकरियाँ वेतन, कौशल एवं संस्थागत संदर्भ हेतु ऐतिहासिक संग्रह में सुरक्षित रहती हैं।',
      'hero.cta.browse': 'सक्रिय अधिदेश देखें',
      'hero.cta.archive': 'ऐतिहासिक अधिदेश संग्रह',

      'community.title': 'भारत के ग्रीन एवं शैक्षणिक जॉब अलर्ट नेटवर्क से जुड़ें',
      'community.sub': 'प्रतिदिन JRF, वानिकी, GIS, ESG एवं जलवायु अधिदेश — प्रत्येक सुबह 7 बजे IST पर सत्यापित एवं प्रसारित।',
      'community.wa': 'WhatsApp जॉब ग्रुप जॉइन करें',
      'community.tg': 'Telegram चैनल जॉइन करें',

      'tabs.aria': 'रजिस्ट्री दृश्य',
      'tabs.active': 'सक्रिय अवसर',
      'tabs.archive': 'संग्रहित / पूर्व पद',

      'filters.search.label': 'रजिस्ट्री में खोजें',
      'filters.search.placeholder': 'पद, संस्था या दक्षता खोजें\u2026',
      'filters.search.aria': 'पद शीर्षक, संस्था या दक्षता से रजिस्ट्री खोजें',
      'filters.state.label': 'राज्य / क्षेत्र',
      'filters.state.aria': 'भारतीय राज्य या क्षेत्र अनुसार अधिदेश फ़िल्टर करें',
      'filters.state.all': 'सम्पूर्ण भारत',
      'filters.state.alln': 'सम्पूर्ण भारत ({n})',
      'filters.exp.label': 'अनुभव स्तर',
      'filters.exp.aria': 'अनुभव स्तर अनुसार अधिदेश फ़िल्टर करें',
      'filters.exp.all': 'सभी स्तर',
      'filters.exp.entry': 'प्रारंभिक स्तर / फेलोशिप',
      'filters.exp.1-3': '1-3 वर्ष',
      'filters.exp.mid': 'मध्य-वरिष्ठ (3-6 वर्ष)',
      'filters.exp.senior': 'वरिष्ठ',
      'filters.window.label': 'आवेदन अवधि',
      'filters.window.all': 'सभी पूर्व रिकॉर्ड',
      'filters.window.recent': 'पिछले 7 दिनों में बंद',
      'filters.reset': 'फ़िल्टर रीसेट करें',
      'tracks.aria': 'करियर ट्रैक अनुसार अधिदेश फ़िल्टर करें',
      'tracks.label': 'करियर ट्रैक',
      'tracks.all': 'सभी पर्यावरणीय नौकरियाँ',
      'tracks.research': 'JRF / SRF एवं प्रोजेक्ट एसोसिएट',
      'tracks.phd': 'PhD एवं पोस्टडॉक्टोरल फेलोशिप',
      'tracks.contractual': 'यंग प्रोफेशनल एवं सरकारी संविदा',
      'tracks.corporate': 'कॉर्पोरेट ESG एवं सस्टेनेबिलिटी',
      'tracks.thinktank': 'थिंक-टैंक, NGO एवं नीति',
      'pills.aria': 'सेक्टर अनुसार अधिदेश फ़िल्टर करें',
      'pills.all': 'सभी पर्यावरणीय नौकरियाँ',
      'pills.academic': 'शैक्षणिक, JRF, SRF एवं PhD',
      'pills.research': 'रिसर्च एसोसिएट एवं प्रोजेक्ट स्टाफ',
      'pills.forestry': 'वानिकी, वन्यजीव एवं वृक्षारोपण',
      'pills.gis': 'GIS, रिमोट सेंसिंग एवं पृथ्वी अवलोकन',
      'pills.esg': 'ESG, कार्बन बाज़ार एवं कॉर्पोरेट सस्टेनेबिलिटी',
      'pills.policy': 'जलवायु नीति, थिंक-टैंक एवं फेलोशिप',
      'pills.grants': 'ग्रांट एवं शोध वित्तपोषण',
      'pills.scholarships': 'स्कॉलरशिप एवं डॉक्टोरल सहयोग',
      'pills.fellowships': 'फेलोशिप एवं नेतृत्व कार्यक्रम',
      'pills.internships': 'इंटर्नशिप एवं छात्र प्रशिक्षुता',
      'pills.competitions': 'प्रतियोगिताएँ, हैकाथॉन एवं पुरस्कार',

      /* क्षेत्राधिकार स्विच (भारत अधिदेश | वैश्विक अवसर) */
      'js.aria': 'क्षेत्राधिकार स्विच — भारत अधिदेश अथवा वैश्विक अवसर',
      'js.india.title': 'भारत अधिदेश',
      'js.india.sub': 'नौकरियाँ, JRF, फेलोशिप एवं ग्रांट',
      'js.india.short': 'भारत',
      'js.global.title': 'वैश्विक अवसर',
      'js.global.sub': 'अंतर्राष्ट्रीय नौकरियाँ, ग्रांट एवं स्कॉलरशिप',
      'js.global.short': 'वैश्विक',
      'registry.switch.india': 'भारत अधिदेश दिखाए जा रहे हैं (नौकरियाँ, JRF, फेलोशिप एवं ग्रांट)',
      'registry.switch.global': 'वैश्विक अवसर दिखाए जा रहे हैं (अंतर्राष्ट्रीय नौकरियाँ, ग्रांट एवं स्कॉलरशिप)',
      'hero.cta.globals': '🌍 वैश्विक अवसर हब',
      'hero.global.kicker': 'वैश्विक अवसर रजिस्ट्री (अंतर्राष्ट्रीय)',
      'hero.global.title_html': 'विश्वभर के <span class="accent">जलवायु एवं सस्टेनेबिलिटी</span> अवसर',
      'hero.global.sub': 'जलवायु, वानिकी, ऊर्जा, जल, जैवविविधता एवं ESG के क्षेत्र में अंतर्राष्ट्रीय नौकरियाँ, ग्रांट, स्कॉलरशिप, फेलोशिप, इंटर्नशिप एवं प्रतियोगिताएँ — सत्यापित, आधिकारिक पोर्टल के सीधे लिंक सहित।',

      /* अवसर प्रकार फ़िल्टर */
      'filters.kind.label': 'अवसर प्रकार',
      'filters.kind.aria': 'अवसर प्रकार अनुसार फ़िल्टर करें — नौकरी, फेलोशिप, स्कॉलरशिप, ग्रांट, इंटर्नशिप या प्रतियोगिता',
      'filters.kind.all': 'सभी प्रकार (नौकरियाँ, ग्रांट, फेलोशिप…)',
      'filters.kind.job': 'नौकरी / करियर',
      'filters.kind.fellowship': 'फेलोशिप',
      'filters.kind.scholarship': 'स्कॉलरशिप',
      'filters.kind.grant': 'ग्रांट / वित्तपोषण',
      'filters.kind.internship': 'इंटर्नशिप',
      'filters.kind.competition': 'प्रतियोगिता / पुरस्कार',
      'filters.gregion.label': 'वैश्विक क्षेत्र',
      'filters.gregion.all': 'सम्पूर्ण वैश्विक ({n})',

      /* अवसर प्रकार बैज, अंतिम तिथि एवं क्षेत्र */
      'card.deadline': 'आवेदन: {d}',
      'detail.kind': 'अवसर प्रकार',
      'detail.deadline': 'अंतिम तिथि / अवधि',
      'detail.region': 'क्षेत्र',

      /* PWA ऐप एवं तत्काल अलर्ट विजेट */
      'widget.title': 'UrbanForestPark ऐप एवं तत्काल जॉब अलर्ट प्राप्त करें',
      'widget.sub': 'JRF, वानिकी, ESG एवं ग्रांट अलर्ट — सत्यापन होते ही सीधे आपके फ़ोन पर।',
      'widget.install': '📲 ऐप डाउनलोड / इंस्टॉल करें',
      'widget.notify': '🔔 तत्काल जॉब सूचनाएँ सक्षम करें',
      'widget.pill': 'ऐप एवं अलर्ट',

      'mini.aria': '72-घंटे मैंडेट डिस्पैच की सदस्यता लें',
      'mini.title': '72-घंटे मैंडेट डिस्पैच',
      'mini.sub': 'नए सत्यापित अधिदेशों की ईमेल ब्रीफिंग — प्रत्येक 72 घंटे में प्रकाशित।',
      'mini.join': 'जुड़ें',
      'mini.placeholder': 'you@organisation.in',

      'feed.eyebrow': 'सक्रिय सेक्टर अधिदेश',
      'feed.title': 'सक्रिय अवसर',
      'feed.eyebrow.archive': 'ऐतिहासिक अधिदेश संग्रह',
      'feed.title.archive': 'संग्रहित / पूर्व पद',
      'feed.eyebrow.global': 'ग्लोबल अवसर रजिस्ट्री',
      'feed.title.global': 'अंतरराष्ट्रीय अवसर',
      'feed.order': 'प्रकाशन तिथि अनुसार क्रमित',
      'feed.loading': 'लोड हो रहा है\u2026',
      'feed.active.one': '1 सक्रिय पद',
      'feed.active.many': '{n} सक्रिय पद',
      'feed.archive.one': '1 ऐतिहासिक रिकॉर्ड',
      'feed.archive.many': '{n} ऐतिहासिक रिकॉर्ड',
      'feed.loadingstate': 'रजिस्ट्री लोड हो रही है\u2026',

      'empty.nomatch.active': 'इन फ़िल्टरों से कोई सक्रिय अधिदेश मेल नहीं खाता',
      'empty.nomatch.archive': 'इन फ़िल्टरों से कोई संग्रहित रिकॉर्ड मेल नहीं खाता',
      'empty.hint': 'कोई अन्य कीवर्ड, क्षेत्र या सेक्टर आज़माएँ — अथवा फ़िल्टर रीसेट करें।',
      'empty.archive.note': 'इस सेक्टर में इस समय कोई सक्रिय अधिदेश नहीं है — संग्रह में {n} ऐतिहासिक रिकॉर्ड उपलब्ध हैं।',
      'empty.switcharchive': 'ऐतिहासिक संग्रह देखें',
      'empty.reset': 'फ़िल्टर रीसेट करें',
      'empty.nolist.active.title': 'अभी कोई सूची नहीं',
      'empty.nolist.active.sub': 'नए ग्रीन-सेक्टर अधिदेश नियमित रूप से प्रकाशित होते हैं। शीघ्र पुनः देखें।',
      'empty.nolist.archive.title': 'ऐतिहासिक संग्रह संकलित किया जा रहा है',
      'empty.nolist.archive.sub': 'आवेदन अवधि समाप्त होने पर पूर्व अधिदेश यहाँ दिखाई देते हैं।',
      'empty.error.title': 'रजिस्ट्री डेटा लोड नहीं हो सका',
      'empty.error.sub': 'कृपया पृष्ठ पुनः लोड करें। समस्या बनी रहे तो जाँचें कि इस डोमेन पर jobs.json उपलब्ध है।',

      'card.cta.active': 'पद विवरण देखें',
      'card.cta.archive': 'संग्रहित रिकॉर्ड खोलें',
      'card.archived': 'संग्रहित',
      'card.more': '+{n} अधिक',
      'card.aria.view': 'पद विवरण देखें: ',
      'card.aria.archive': 'संग्रहित रिकॉर्ड खोलें: ',
      'card.closed': 'बंद ',

      'detail.back.active': 'सक्रिय अवसर',
      'detail.back.archive': 'ऐतिहासिक संग्रह',
      'detail.share.wa': 'WhatsApp पर साझा करें',
      'detail.share.li': 'LinkedIn पर साझा करें',
      'detail.share.copy': 'सीधा लिंक कॉपी करें',
      'detail.banner.archived': 'संग्रहित अधिदेश:',
      'detail.banner.body': 'इस पद की आवेदन अवधि {date} को बंद हो चुकी है। यह रिकॉर्ड अनुशंसा, कौशल एवं संस्थागत संदर्भ हेतु अर्बन फॉरेस्ट पार्क करियर रजिस्ट्री में संरक्षित है।',
      'detail.summary.h2': 'अधिदेश सारांश',
      'detail.summaryhi.h2': 'हिंदी सारांश',
      'detail.elig.h2': 'पद एवं पात्रता',
      'detail.pt': 'पद प्रकार',
      'detail.engagement': 'कार्य प्रकार',
      'detail.qualification': 'अर्हता',
      'detail.comp': 'वेतन / फेलोशिप',
      'detail.resp.h2': 'मुख्य उत्तरदायित्व',
      'detail.skills.h2': 'आवश्यक दक्षताएँ',
      'detail.tip': 'उम्मीदवार परामर्श',
      'detail.ref': 'संदर्भ: ',
      'detail.valid': 'मान्य अवधि: ',
      'detail.archived.on': 'संग्रहित: ',
      'detail.suggest.h3': 'इस सेक्टर में वर्तमान सक्रिय पद',
      'detail.suggest.aria': 'सक्रिय पद देखें: ',

      'verify.kicker': 'आवेदन रिकॉर्ड',
      'verify.source': 'स्रोत: ',
      'verify.apply.on': 'आवेदन करें: ',
      'verify.apply.archive': 'मूल आवेदन पोर्टल देखें',
      'verify.website': 'आधिकारिक वेबसाइट देखें',
      'verify.website.sub': 'आधिकारिक पोर्टल',
      'verify.website.empty': 'आधिकारिक वेबसाइट',
      'verify.website.empty.sub': 'सूचीबद्ध नहीं — स्रोत पोर्टल का उपयोग करें',
      'verify.note.active': 'दोनों लिंक नए टैब में खुलते हैं। आवेदन से पूर्व नियोक्ता के पृष्ठ पर पात्रता, फेलोशिप मानदंड एवं अंतिम तिथि अवश्य सत्यापित करें।',
      'verify.note.archive': 'यह अधिदेश संग्रहित है — आवेदन अवधि समाप्त हो चुकी है। दोनों लिंक केवल संस्थागत संदर्भ हेतु मूल पोर्टल खोलते हैं।',

      'cc.title': 'प्रतिदिन JRF, वानिकी, GIS एवं ESG नौकरी अलर्ट पाएँ',
      'cc.sub': 'भारत के ग्रीन एवं शैक्षणिक जॉब अलर्ट नेटवर्क से जुड़ें — प्रत्येक सुबह 7 बजे IST पर सत्यापित अधिदेश।',
      'cc.join.wa': 'WhatsApp जॉब ग्रुप जॉइन करें \u2197',
      'cc.join.tg': 'Telegram जॉब चैनल जॉइन करें \u2197',
      'cc.share.wa': 'स्वरूपित अलर्ट WhatsApp पर साझा करें',
      'cc.share.tg': 'Telegram पर साझा करें',

      'dispatch.eyebrow': 'निःशुल्क ईमेल जॉब अलर्ट',
      'dispatch.title': 'पर्यावरण, वानिकी, JRF एवं ESG जॉब अलर्ट',
      'dispatch.sub': 'निःशुल्क ईमेल अलर्ट — प्रत्येक 72 घंटे में — जिसमें अवधि की सत्यापित नौकरियाँ एवं फेलोशिप सम्मिलित होते हैं: JRF / SRF एवं डॉक्टोरल फेलोशिप, वानिकी, वन्यजीव एवं GIS पद, तथा भारत भर के कॉर्पोरेट ESG पद।',
      'dispatch.point1': 'केवल इसी पृष्ठ पर प्रकाशित सत्यापित रजिस्ट्री से संकलित।',
      'dispatch.point2': 'प्रत्यक्ष आवेदन लिंक एवं आधिकारिक संस्थागत स्रोत — कोई बिचौलिया नहीं।',
      'dispatch.point3': 'एक-क्लिक ऑप्ट-आउट; अनसब्सक्राइब अनुरोध 7 कार्य-दिवसों में स्वीकार किए जाते हैं।',
      'dispatch.ledger_html': 'साथ ही उपलब्ध: तत्काल <a href="https://t.me/urbanforestpark" target="_blank" rel="noopener">Telegram चैनल</a> एवं <a href="https://chat.whatsapp.com/JJ0ItiNOfvEDCDIENscenw" target="_blank" rel="noopener">WhatsApp जॉब ग्रुप</a>।',
      'dispatch.form.title': 'निःशुल्क जॉब एवं फेलोशिप ईमेल अलर्ट सब्सक्राइब करें',
      'dispatch.email.label': 'आधिकारिक ई-मेल पता',
      'dispatch.freq.legend': 'आवृत्ति',
      'dispatch.freq.group': 'ईमेल अलर्ट आवृत्ति',
      'dispatch.freq.3day': 'प्रत्येक 3 दिन (अनुशंसित)',
      'dispatch.freq.weekly': 'साप्ताहिक डाइजेस्ट',
      'dispatch.sector.label': 'सेक्टर प्राथमिकता',
      'dispatch.sector.all': 'सभी पर्यावरणीय नौकरियाँ',
      'dispatch.sector.academic': 'JRF / PhD / शैक्षणिक',
      'dispatch.sector.forestry': 'वानिकी एवं GIS',
      'dispatch.sector.esg': 'कॉर्पोरेट ESG',
      'dispatch.submit': 'निःशुल्क जॉब एवं फेलोशिप ईमेल अलर्ट सब्सक्राइब करें',
      'dispatch.micro_html': 'प्रत्येक 72 घंटे में प्रकाशित। शून्य स्पैम। हमारी <a href="/privacy.html">संस्थागत गोपनीयता नीति</a> एवं <a href="/terms.html">उपयोग की शर्तों</a> के अधीन।',
      'dispatch.invalid': 'सब्सक्राइब करने हेतु मान्य आधिकारिक ई-मेल पता दर्ज करें।',
      'dispatch.registering': 'सदस्यता दर्ज हो रही है\u2026',
      'dispatch.mini.ok': 'सब्सक्राइब हुआ — अगला ईमेल अलर्ट 72 घंटों में।',
      'dd.title': 'सदस्यता दर्ज हुई',
      'dd.address': 'ई-मेल पता',
      'dd.frequency': 'आवृत्ति',
      'dd.sector': 'सेक्टर',
      'dd.freq.weekly': 'साप्ताहिक डाइजेस्ट',
      'dd.freq.3day': 'प्रत्येक 3 दिन',
      'dd.manage': 'सदस्यता प्रबंधित या वापस लें',
      'dd.update': 'प्राथमिकताएँ बदलें',
      'dd.note.local': 'इस डिवाइस पर सहेजा गया। वर्तमान डिस्पैच सूची में तत्काल जुड़ने हेतु urbanforestpark@gmail.com पर लिखें।',
      'sector.all': 'सभी अधिदेश',
      'sector.academic': 'JRF / PhD / शैक्षणिक',
      'sector.forestry-gis': 'वानिकी एवं GIS',
      'sector.corporate-esg': 'कॉर्पोरेट ESG',
      'toast.dark': 'रात्रि मोड सक्रिय',
      'toast.light': 'दिवस मोड सक्रिय',
      'toast.subscribed': 'डिस्पैच सब्सक्राइब हुआ — अगली ब्रीफिंग 72 घंटों में।',
      'toast.saved': 'डिस्पैच प्राथमिकता इस डिवाइस पर सहेजी गई।',

      'faq.eyebrow': 'प्लेटफ़ॉर्म शासन एवं कार्यप्रणाली',
      'faq.title': 'अक्सर पूछे जाने वाले प्रश्न',
      'faq.sub': 'उम्मीदवारों, संस्थानों, शोधकर्ताओं एवं भागीदारों हेतु औपचारिक संदर्भ कि यह रजिस्ट्री किस प्रकार संचालित, सत्यापित एवं अनुरक्षित की जाती है। संबंधित संरचित डेटा इस पृष्ठ के मेटाडेटा में FAQPage स्कीमा के रूप में प्रकाशित है।',
      'faq.q1': 'अर्बन फॉरेस्ट पार्क करियर रजिस्ट्री का मुख्य उद्देश्य क्या है, और यह कौन-सी सूचना-असमानता दूर करती है?',
      'faq.a1': 'भारत का पर्यावरण, वानिकी, भू-स्थानिक एवं शैक्षणिक भर्ती परिदृश्य सैकड़ों अनुक्रमित-रहित संस्थागत विज्ञापनों में बिखरा हुआ है — ICFRE संस्थानों, भारतीय वन्यजीव संस्थान, IIFM, IIRS, ICAR निकायों एवं भारतीय विश्वविद्यालयों की भर्ती सूचनाएँ, तथा CEEW, WRI India, TERI एवं ATREE जैसे विकास थिंक-टैंकों और कॉर्पोरेट ESG पोर्टलों की अलग-अलग प्रकाशित रिक्तियाँ। अर्बन फॉरेस्ट पार्क इन अधिदेशों को एकल, खोज-योग्य राष्ट्रीय रजिस्ट्री में संकलित, सत्यापित एवं संरचित करके इस सूचना-असमानता को दूर करता है, जहाँ प्रत्येक प्रविष्टि अपने आधिकारिक आवेदन स्रोत से जुड़ी होती है।',
      'faq.q2': 'इस प्लेटफ़ॉर्म पर नौकरी सूचियों, JRF/SRF फेलोशिप एवं संस्थागत लिंक का सत्यापन कैसे होता है?',
      'faq.a2': 'प्रत्येक सूची प्रकाशन से पूर्व स्वचालित सत्यापन प्रक्रिया से गुज़रती है। रिक्तियाँ आधिकारिक पोर्टलों, सत्यापित फ़ीड एवं संस्थागत सूचनाओं से संकलित की जाती हैं; तत्पश्चात प्रत्येक रिकॉर्ड का डोमेन सत्यापन, रीडायरेक्ट अनरैपिंग (जिससे लिंक समाचार-आवरण के बजाय प्रकाशक तक पहुँचें), डुप्लीकेट हैशिंग एवं मानकीकृत डोज़ियर संरचना से गुज़रना होता है। प्रत्येक डोज़ियर प्रत्यक्ष आवेदन पोर्टल लिंक एवं संबंधित संस्था की सत्यापित आधिकारिक वेबसाइट — दोनों प्रस्तुत करता है, जिससे आवेदक प्रत्येक विवरण अपने आधिकारिक स्रोत पर सत्यापित कर सकें।',
      'faq.q3': 'समाप्त या बंद अधिदेशों का क्या होता है, और ऐतिहासिक संग्रह क्यों बनाए रखा जाता है?',
      'faq.a3': 'सक्रिय अधिदेश रजिस्ट्री में 30-दिवसीय जीवनचक्र तक रहते हैं; आवेदन अवधि बंद होने पर रिकॉर्ड स्वतः ऐतिहासिक अधिदेश संग्रह (archive.json) में स्थानांतरित हो जाता है। यह संग्रह एक सार्वजनिक शोध-संपदा के रूप में अनुरक्षित है: विद्यार्थी, शोधकर्ता एवं नीति-विश्लेषक ऐतिहासिक फेलोशिप राशि, आवर्ती तकनीकी आवश्यकताओं (GIS, Google Earth Engine, BRSR रिपोर्टिंग, कार्बन बाज़ार) तथा भारतीय राज्यों एवं केंद्रशासित प्रदेशों में मौसमी भर्ती गति का तुलनात्मक विश्लेषण कर सकते हैं।',
      'faq.q4': 'रजिस्ट्री कितनी बार अद्यतन होती है — स्वचालित ईमेल, WhatsApp एवं Telegram प्रसारण कैसे कार्य करते हैं?',
      'faq.a4': 'रजिस्ट्री प्रतिदिन प्रातः 07:00 बजे IST पर स्वचालित पाइपलाइन द्वारा संकलित की जाती है। सत्यापित अधिदेश तत्काल रजिस्ट्री में प्रकाशित होते हैं और तत्काल Telegram एवं WhatsApp अलर्ट चैनलों पर प्रसारित होते हैं; एक संकलित ईमेल ब्रीफिंग — मैंडेट डिस्पैच — प्रत्येक 72 घंटे में जारी होती है, जिसमें प्रत्येक अवधि के नए सत्यापित पद, रजिस्ट्री टेलीमेट्री एवं भौगोलिक कवरेज का सारांश होता है।',
      'faq.q5': 'करियर रजिस्ट्री तथा नगर वन योजना dMRV डैशबोर्ड एवं ग्रीन कैलकुलेटर का संबंध क्या है?',
      'faq.a5_html': 'अर्बन फॉरेस्ट पार्क की शुरुआत भारत में शहरी वानिकी हेतु डिजिटल मॉनिटरिंग, रिपोर्टिंग एवं वेरिफिकेशन (dMRV) तथा अर्बन हीट आइलैंड (UHI) विश्लेषण पहल के रूप में हुई थी। राष्ट्रीय करियर रजिस्ट्री के साथ-साथ यह प्लेटफ़ॉर्म अपनी खुली-पहुँच सार्वजनिक शोध उपयोगिताएँ — <a href="/dashboard.html">नगर वन dMRV डैशबोर्ड</a> एवं <a href="/green-calculator.html">ग्रीन कैलकुलेटर</a> — संस्थानों, शोधकर्ताओं एवं नागरिकों के लिए निःशुल्क संचालित एवं अनुरक्षित रखता है।',
      'faq.q6': 'उम्मीदवारों या संस्थानों के लिए सूचियाँ देखने अथवा डिस्पैच की सदस्यता में कोई शुल्क है?',
      'faq.a6': 'नहीं। रजिस्ट्री एवं प्रत्येक डिस्पैच माध्यम — वेबसाइट, 72-घंटे ईमेल डिस्पैच, Telegram चैनल एवं WhatsApp ग्रुप — उम्मीदवारों, शोधकर्ताओं, शैक्षणिक विद्वानों एवं संस्थागत भागीदारों हेतु 100% खुली-पहुँच है। अर्बन फॉरेस्ट पार्क किसी भी चरण पर उम्मीदवारों से कोई शुल्क नहीं लेता और भर्ती मध्यस्थ के रूप में कार्य नहीं करता; सभी आवेदन सीधे नियोक्ता के आधिकारिक पोर्टल पर जमा होते हैं।',
      'faq.note_html': 'विस्तृत सांविधिक जानकारी <a href="/privacy.html">गोपनीयता नीति</a>, <a href="/terms.html">उपयोग की शर्तें</a> तथा <a href="/cookies.html">कुकी नीति</a> में प्रकाशित है। संस्थागत पूछताछ: <a href="mailto:urbanforestpark@gmail.com">urbanforestpark@gmail.com</a>।'
    }
  };

  /* ------------------------------------------------------------------
     State + helpers
     ------------------------------------------------------------------ */
  var current = 'en';

  function storedLang() {
    try {
      var raw = window.localStorage.getItem(STORE_KEY);
      return raw === 'hi' || raw === 'en' ? raw : '';
    } catch (e) { return ''; }
  }

  function t(key, vars) {
    var table = DICT[current] || DICT.en;
    var value = table[key];
    if (value === undefined) value = (DICT.en[key] !== undefined ? DICT.en[key] : undefined);
    if (value === undefined) return undefined;
    if (vars) {
      Object.keys(vars).forEach(function (name) {
        value = value.split('{' + name + '}').join(String(vars[name]));
      });
    }
    return value;
  }

  function applyTranslations(root) {
    var scope = root || document;
    Array.prototype.forEach.call(scope.querySelectorAll('[data-i18n]'), function (el) {
      var value = t(el.getAttribute('data-i18n'));
      if (value !== undefined) el.textContent = value;
    });
    Array.prototype.forEach.call(scope.querySelectorAll('[data-i18n-html]'), function (el) {
      var value = t(el.getAttribute('data-i18n-html'));
      if (value !== undefined) el.innerHTML = value;
    });
    Array.prototype.forEach.call(scope.querySelectorAll('[data-i18n-placeholder]'), function (el) {
      var value = t(el.getAttribute('data-i18n-placeholder'));
      if (value !== undefined) el.setAttribute('placeholder', value);
    });
    Array.prototype.forEach.call(scope.querySelectorAll('[data-i18n-aria]'), function (el) {
      var value = t(el.getAttribute('data-i18n-aria'));
      if (value !== undefined) el.setAttribute('aria-label', value);
    });
    Array.prototype.forEach.call(scope.querySelectorAll('[data-i18n-title]'), function (el) {
      var value = t(el.getAttribute('data-i18n-title'));
      if (value !== undefined) el.setAttribute('title', value);
    });
  }

  function syncToggle() {
    var buttons = document.querySelectorAll('[data-ufp-lang-option]');
    Array.prototype.forEach.call(buttons, function (btn) {
      var isActive = btn.getAttribute('data-ufp-lang-option') === current;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });
    var group = document.getElementById('lang-toggle');
    if (group) group.setAttribute('aria-label', t('lang.aria') || 'Interface language');
  }

  function setLang(lang, opts) {
    opts = opts || {};
    var next = lang === 'hi' ? 'hi' : 'en';
    var changed = next !== current;
    current = next;
    try { window.localStorage.setItem(STORE_KEY, next); } catch (e) { /* private mode */ }
    document.documentElement.setAttribute('lang', HTML_LANG[next]);
    document.documentElement.setAttribute('data-lang', next);
    applyTranslations(document);
    syncToggle();
    if (changed && !opts.silent) {
      document.dispatchEvent(new CustomEvent('ufp:langchange', { detail: { lang: next } }));
    }
  }

  function heroHtml() {
    return t('hero.title_html');
  }

  /* ------------------------------------------------------------------
     Boot
     ------------------------------------------------------------------ */
  current = storedLang() || 'en';
  document.documentElement.setAttribute('lang', HTML_LANG[current]);
  document.documentElement.setAttribute('data-lang', current);

  function initToggle() {
    var group = document.getElementById('lang-toggle');
    if (!group) return;
    group.addEventListener('click', function (event) {
      var btn = event.target.closest('[data-ufp-lang-option]');
      if (!btn) return;
      setLang(btn.getAttribute('data-ufp-lang-option'));
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initToggle();
    applyTranslations(document);
    syncToggle();
  });

  window.UFPI18N = {
    get lang() { return current; },
    isHindi: function () { return current === 'hi'; },
    t: t,
    setLang: setLang,
    apply: applyTranslations,
    heroHtml: heroHtml
  };
})();
