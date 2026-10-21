/* ==========================================================================
   Urban Forest Park — National Climate, Forestry, ESG & Geospatial
   Career Registry (India)
   js/jobs.js — registry data loading (jobs.json + archive.json + stats.json),
   weekly telemetry, active/archived views, ?job= ?view= ?state= ?category=
   routing, position dossiers, schema.org lifecycle (JobPosting for active
   jobs, WebPage + BreadcrumbList for archived ones), sharing, and the
   institutional partnership modal. Vanilla JS, no dependencies.
   ========================================================================== */
(function () {
  'use strict';

  /* The registry restores the feed's scroll offset itself, so the browser's
     automatic restoration must not compete with the dossier navigation. */
  if ('scrollRestoration' in window.history) {
    window.history.scrollRestoration = 'manual';
  }

  /* Session keys for exact feed-position memory (Phase 2). */
  var SCROLL_KEY = 'ufp_saved_scroll_y';
  var SCROLL_JOB_KEY = 'ufp_last_clicked_job_id';
  var RETURN_FLAG = 'ufp_returning_from_job';

  /* ------------------------------------------------------------------ */
  /* Config & state                                                      */
  /* ------------------------------------------------------------------ */
  var CONFIG = {
    DATA_URL: '/jobs.json',
    ARCHIVE_URL: '/archive.json',
    STATS_URL: '/stats.json',
    /* Strictly separated Global opportunities registry: these two files
       never contain India records and are never mixed into jobs.json. */
    GLOBAL_DATA_URL: '/global_jobs.json',
    GLOBAL_ARCHIVE_URL: '/global_archive.json',
    CONTACT_EMAIL: 'urbanforestpark@gmail.com',
    VALID_DAYS: 30,            // fallback jobPosting validThrough = datePosted + N days
    ARCHIVE_RECENT_DAYS: 7,    // "Closed in the last 7 days" archive window
    SITE_URL: 'https://www.urbanforestpark.com/',
    SITE_NAME: 'Urban Forest Park'
  };

  /* WhatsApp / Telegram job-alert network. The owner can point these at the
     real invite links in one line by editing the two <meta> tags in
     index.html (<meta name="ufp-whatsapp-group"> / ufp-telegram-channel). */
  var COMMUNITY_CHANNELS = (function () {
    function metaValue(name, fallback) {
      var el = document.querySelector('meta[name="' + name + '"]');
      var content = el && el.getAttribute('content');
      return (content && content.trim()) || fallback;
    }
    return {
      whatsapp_group_url: metaValue('ufp-whatsapp-group', 'https://chat.whatsapp.com/JJ0ItiNOfvEDCDIENscenw'),
      telegram_channel_url: metaValue('ufp-telegram-channel', 'https://t.me/urbanforestpark')
    };
  })();

  function isPlaceholderChannel(url, kind) {
    if (!url) return true;
    if (kind === 'whatsapp') {
      return /0029VaGreenJobsIndia|your[-_]|placeholder|example/i.test(url);
    }
    return false;
  }

  function communityGuardAttr(kind) {
    var url = kind === 'whatsapp'
      ? COMMUNITY_CHANNELS.whatsapp_group_url
      : COMMUNITY_CHANNELS.telegram_channel_url;
    return isPlaceholderChannel(url, kind) ? ' data-community-guard="' + kind + '"' : '';
  }

  var CATEGORY_SLUGS = {
    'Academic, JRF, SRF & PhD Positions': 'academic-jrf-srf-phd',
    'Research Associate & Project Staff (Contractual)': 'research-associate-project-staff',
    'Forestry, Wildlife & Afforestation': 'forestry-wildlife-afforestation',
    'GIS, Remote Sensing & Earth Observation': 'gis-remote-sensing-earth-observation',
    'ESG, Carbon Markets & Corporate Sustainability': 'esg-carbon-sustainability',
    'Climate Policy, Think-Tanks & Fellowships': 'climate-policy-think-tanks-fellowships'
  };

  /* Pre-upgrade category slugs and display names keep resolving as aliases so
     old bookmarks, sitemap-era links and search-engine results never dead-end. */
  var LEGACY_CATEGORY_SLUGS = {
    'climate-sustainability': 'ESG, Carbon Markets & Corporate Sustainability',
    'esg-carbon-markets': 'ESG, Carbon Markets & Corporate Sustainability',
    'forestry-afforestation': 'Forestry, Wildlife & Afforestation',
    'gis-remote-sensing-uhi': 'GIS, Remote Sensing & Earth Observation',
    'environmental-policy-fellowships': 'Climate Policy, Think-Tanks & Fellowships'
  };

  var CATEGORY_LEGACY_NAMES = {
    'Climate & Sustainability': 'ESG, Carbon Markets & Corporate Sustainability',
    'ESG & Carbon Markets': 'ESG, Carbon Markets & Corporate Sustainability',
    'Forestry & Afforestation': 'Forestry, Wildlife & Afforestation',
    'GIS, Remote Sensing & UHI': 'GIS, Remote Sensing & Earth Observation',
    'Environmental Policy & Fellowships': 'Climate Policy, Think-Tanks & Fellowships'
  };

  /* Career tracks: the quick-filter strip over position_type + category.
     Order matters - trackOf() returns exactly one track per record. */
  var TRACK_META = [
    { id: 'all', label: 'All Environmental Jobs' },
    { id: 'research', label: 'JRF / SRF & Project Associates' },
    { id: 'phd', label: 'PhD & Postdoctoral Fellowships' },
    { id: 'contractual', label: 'Young Professional & Govt Contractual' },
    { id: 'corporate', label: 'Corporate ESG & Sustainability' },
    { id: 'thinktank', label: 'Think-Tanks, NGOs & Policy' }
  ];

  var DEFAULT_TITLE = document.title;
  var DEFAULT_DESC = (document.querySelector('meta[name="description"]') || {}).content || '';
  var DEFAULT_HERO_HTML = '';
  var DEFAULT_HERO_SUB_HTML = '';

  /* ------------------------------------------------------------------ */
  /* Bilingual interface helpers (js/i18n.js is loaded before this file) */
  /* ------------------------------------------------------------------ */
  function t(key, fallback, vars) {
    var i18n = window.UFPI18N;
    var value = i18n ? i18n.t(key, vars) : undefined;
    return value !== undefined && value !== null && value !== '' ? value : fallback;
  }

  function isHindi() {
    return !!(window.UFPI18N && window.UFPI18N.isHindi());
  }

  /* Hindi title when the interface is in Hindi and the record carries the
     bilingual field; otherwise the canonical English title. Acronyms
     (JRF, SRF, GIS, ESG, PhD) remain in Latin script inside title_hi. */
  function displayTitle(job) {
    if (isHindi() && job.title_hi) return job.title_hi;
    return job.clean_title;
  }

  function heroDefaultHtml() {
    var i18n = window.UFPI18N;
    var html = i18n && i18n.heroHtml ? i18n.heroHtml() : '';
    return html || DEFAULT_HERO_HTML;
  }

  var state = {
    jobs: [],                 // active listings (jobs.json, India)
    archive: [],              // past listings (archive.json, India)
    globalJobs: [],           // active global opportunities (global_jobs.json)
    globalArchive: [],        // archived global opportunities (global_archive.json)
    stats: null,              // weekly telemetry (stats.json)
    view: 'active',           // 'active' | 'archive'
    registry: 'india',        // 'india' | 'global' (never mixed)
    region: 'all',            // global-region filter (global registry only)
    archiveRecent: false,     // archive: only records closed in the last 7 days
    filtered: [],
    query: '',
    state: 'all',
    category: 'all',
    track: 'all',
    kind: 'all',              // opportunity kind filter (jobs + grants + ...)
    experience: 'all',
    quick: 'all',
    savedOnly: false,
    detailId: null,
    loaded: false
  };

  var SAVED_KEY = 'ufp_saved_jobs';
  var QUICK_FILTERS = {
    academic: function (job) {
      return /(jrf|junior research fellow|srf|senior research fellow|project associate|research associate|project assistant|research fellow|young professional|field assistant|phd|doctoral|postdoc|fellowship)/i
        .test(jobText(job));
    },
    net: function (job) {
      return /(net\s*\/?\s*gate|net qualified|net exempted|gate qualified|m\.?sc|master of science)/i
        .test(jobText(job) + ' ' + String((job.academic_meta || {}).net_gate || ''));
    },
    govt: function (job) {
      return /(icfre|wildlife institute|\bwii\b|icar|iit|iisc|iiser|csir|isro|iirs|nrsc|moefcc|forest survey|\bfsi\b|campa|\bcpcb\b|\bspcb\b|dpcc|mpcb|kspcb|gpcb|uppcb|tnpcb|ntca|nba\b|czma|ncscm|iifm|university|institute|government|govt\.?|autonomous|forest department)/i
        .test(String(job.organization || '') + ' ' + jobText(job));
    },
    corporate: function (job) {
      return /(esg|carbon|sustainability|brsr|dmrv|net zero|climate risk|ehs|csr|clean energy|renewable)/i
        .test(jobText(job) + ' ' + String(job.category || ''));
    },
    gis: function (job) {
      return /(gis|remote sensing|earth observation|lidar|qgis|arcgis|google earth engine|geospatial|satellite)/i
        .test(jobText(job) + ' ' + String(job.category || '') + ' ' + (job.must_have_skills || []).join(' '));
    },
    wildlife: function (job) {
      return /(wildlife|conservation|biodiversity|ecology|tiger|elephant|mangrove|marine|sanctuary|national park|ntca|wii|wcs|wwf|ncf|atree)/i
        .test(jobText(job) + ' ' + String(job.category || '') + ' ' + String(job.organization || ''));
    },
    phd: function (job) {
      return /(phd|doctoral|postdoc|fellowship|scholarship|grant|research funding|stipend)/i
        .test(jobText(job) + ' ' + String(job.category || '') + ' ' + String(job.opportunity_kind || ''));
    }
  };

  /* Canonical static detail page for every registry record. The physical file
     is /jobs/<id>.html; Cloudflare serves it at the extensionless URL and the
     static page declares that URL as its canonical. */
  function jobPath(id) {
    return '/jobs/' + encodeURIComponent(String(id || '')).replace(/%2F/gi, '');
  }

  function jobText(job) {
    return [
      job.clean_title, job.organization, job.position_type, job.category,
      job.role_summary, job.qualification_summary, job.compensation_or_fellowship
    ].join(' ');
  }

  function savedList() {
    try {
      var parsed = JSON.parse(window.localStorage.getItem(SAVED_KEY) || '[]');
      return Array.isArray(parsed) ? parsed.map(String) : [];
    } catch (e) { return []; }
  }

  function savedSet() {
    var set = {};
    savedList().forEach(function (id) { set[id] = true; });
    return set;
  }

  function storeSaved(ids) {
    try { window.localStorage.setItem(SAVED_KEY, JSON.stringify(ids)); } catch (e) { /* private mode */ }
    updateSavedUi();
  }

  function isSaved(id) { return savedSet()[String(id)] === true; }

  function toggleSaved(id) {
    id = String(id);
    var ids = savedList();
    var index = ids.indexOf(id);
    if (index >= 0) ids.splice(index, 1);
    else ids.unshift(id);
    storeSaved(ids);
    toast(index >= 0 ? 'Removed from saved jobs' : 'Saved — find it under ★ Saved');
    if (state.savedOnly) applyFilters();
    return index < 0;
  }

  function savedJobs() {
    var map = {};
    state.jobs.concat(state.globalJobs, state.archive, state.globalArchive).forEach(function (job) {
      map[String(job.id)] = job;
    });
    return savedList().map(function (id) { return map[id]; }).filter(Boolean);
  }

  function updateSavedUi() {
    var ids = savedList();
    var count = ids.length;
    ['saved-count', 'saved-filter-count'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.textContent = String(count);
    });
    var btn = document.getElementById('saved-header-btn');
    if (btn) btn.setAttribute('aria-label', 'Open saved jobs (' + count + ')');
    var filterBtn = document.getElementById('saved-filter-btn');
    if (filterBtn) {
      filterBtn.classList.toggle('active', state.savedOnly);
      filterBtn.setAttribute('aria-pressed', state.savedOnly ? 'true' : 'false');
    }
    Array.prototype.forEach.call(document.querySelectorAll('[data-save-id]'), function (item) {
      var on = ids.indexOf(String(item.getAttribute('data-save-id'))) >= 0;
      item.setAttribute('aria-pressed', on ? 'true' : 'false');
      item.classList.toggle('is-saved', on);
      var label = item.querySelector('.save-label');
      if (label) label.textContent = on ? 'Saved' : 'Save';
    });
    renderSavedDrawer();
  }

  function renderSavedDrawer() {
    var listEl = document.getElementById('saved-drawer-list');
    if (!listEl) return;
    var jobs = savedJobs();
    if (!jobs.length) {
      listEl.innerHTML = '<p class="saved-empty">No saved jobs yet. Tap <strong>★ Save</strong> on any card to build your shortlist.</p>';
      return;
    }
    listEl.innerHTML = jobs.map(function (job) {
      return '<div class="saved-item">' +
        '<button class="saved-item-open" type="button" data-saved-open="' + escapeHtml(job.id) + '">' +
          '<span class="saved-item-title">' + escapeHtml(displayTitle(job)) + '</span>' +
          '<span class="saved-item-org">' + escapeHtml(job.organization) + ' · ' + escapeHtml(stateLabel(job)) + '</span>' +
        '</button>' +
        '<button class="saved-item-remove" type="button" data-saved-remove="' + escapeHtml(job.id) + '" aria-label="Remove saved job">×</button>' +
      '</div>';
    }).join('');
  }

  function openSavedDrawer() {
    var drawer = document.getElementById('saved-drawer');
    var backdrop = document.getElementById('saved-backdrop');
    if (!drawer) return;
    renderSavedDrawer();
    drawer.classList.add('open');
    drawer.setAttribute('aria-hidden', 'false');
    if (backdrop) { backdrop.hidden = false; backdrop.classList.add('open'); }
    document.body.classList.add('saved-open');
    var header = document.getElementById('saved-header-btn');
    if (header) header.setAttribute('aria-expanded', 'true');
    var close = drawer.querySelector('.saved-close');
    if (close) close.focus();
  }

  function closeSavedDrawer() {
    var drawer = document.getElementById('saved-drawer');
    var backdrop = document.getElementById('saved-backdrop');
    if (!drawer) return;
    drawer.classList.remove('open');
    drawer.setAttribute('aria-hidden', 'true');
    if (backdrop) { backdrop.classList.remove('open'); backdrop.hidden = true; }
    document.body.classList.remove('saved-open');
    var header = document.getElementById('saved-header-btn');
    if (header) header.setAttribute('aria-expanded', 'false');
  }

  function shareTextFor(job) {
    var location = stateLabel(job) || job.city || job.region || 'India';
    var detail = job.compensation_or_fellowship || job.qualification_summary || 'As per institute norms';
    return '📌 ' + displayTitle(job) + ' — ' + job.organization + '\n' +
      '📍 ' + location + '\n' +
      '🎓 ' + detail + '\n' +
      '🔗 Apply: ' + shareableUrl(job.id);
  }

  function findAnyJob(id) {
    var pools = [state.jobs, state.globalJobs, state.archive, state.globalArchive];
    for (var i = 0; i < pools.length; i++) {
      for (var j = 0; j < pools[i].length; j++) {
        if (String(pools[i][j].id) === String(id)) return pools[i][j];
      }
    }
    return null;
  }

  function shareJob(id, mode, event) {
    if (event) event.preventDefault();
    var job = findAnyJob(id);
    if (!job) return;
    var text = shareTextFor(job);
    if (mode === 'native' && navigator.share) {
      navigator.share({ title: displayTitle(job) + ' — ' + job.organization, text: text, url: shareableUrl(job.id) })
        .catch(function () { copyTextToClipboard(text, 'Share card copied'); });
      return;
    }
    copyTextToClipboard(text, '4-line share card copied');
  }

  var els = {};

  /* ------------------------------------------------------------------ */
  /* Small utilities                                                     */
  /* ------------------------------------------------------------------ */
  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function debounce(fn, wait) {
    var t = null;
    return function () {
      var args = arguments, ctx = this;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(ctx, args); }, wait);
    };
  }

  function iconSvg(name) {
    var icons = {
      pin: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21s7-5.6 7-11a7 7 0 10-14 0c0 5.4 7 11 7 11z"/><circle cx="12" cy="10" r="2.6"/></svg>',
      calendar: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M8 3v4M16 3v4M3 10h18"/></svg>',
      clock: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/></svg>',
      arrow: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 5l7 7-7 7"/></svg>',
      back: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 12H5M11 19l-7-7 7-7"/></svg>',
      external: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 4h6v6"/><path d="M20 4L10 14"/><path d="M19 13v6a1 1 0 01-1 1H5a1 1 0 01-1-1V6a1 1 0 011-1h6"/></svg>',
      whatsapp: '<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 00-8.6 15.1L2 22l5-1.3A10 10 0 1012 2zm5.5 14.1c-.2.6-1.3 1.2-1.8 1.3-.5.1-1 .1-1.7-.1-1.7-.5-4.7-2.6-6-5.2-.4-.8-.6-1.6-.4-2.3.1-.5.7-1.3 1.1-1.5.3-.2.8-.2 1 0 .2.2 1 1.7 1.1 1.9.1.2.1.4 0 .6-.1.2-.5.7-.6.9-.1.1-.2.3-.1.5.4.8 1.7 2.3 2.8 2.8.2.1.4.1.5-.1.2-.2.7-.7.9-.9.2-.2.4-.2.6-.1.2.1 1.6.9 1.8 1.1.2.2.2.7-.2 1.1z"/></svg>',
      linkedin: '<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M4.98 3.5a2.5 2.5 0 11-.02 5 2.5 2.5 0 01.02-5zM3 9h4v12H3zM9 9h3.8v1.7h.1c.5-1 1.8-2 3.7-2 4 0 4.7 2.6 4.7 6V21h-4v-5.5c0-1.3 0-3-1.9-3s-2.1 1.4-2.1 2.9V21H9z"/></svg>',
      copy: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 012-2h9"/></svg>',
      bulb: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 18h6"/><path d="M10 21h4"/><path d="M12 3a6 6 0 00-4 10.5c.7.7 1 1.6 1 2.5h6c0-.9.3-1.8 1-2.5A6 6 0 0012 3z"/></svg>',
      archive: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="4" rx="1"/><path d="M5 8v11a1 1 0 001 1h12a1 1 0 001-1V8"/><path d="M10 12h4"/></svg>',
      cap: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 9.5L12 5 2 9.5l10 4.5 10-4.5z"/><path d="M6 11.6V16c0 1.5 2.7 2.8 6 2.8s6-1.3 6-2.8v-4.4"/><path d="M22 9.5v4.6"/></svg>',
      rupee: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 3h12M6 8h12"/><path d="M6 13h4a5 5 0 000-10H6"/><path d="M6 13l8.5 8"/></svg>',
      telegram: '<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M21.9 3.6c.3-1.2-.4-1.7-1.2-1.4L2.6 9.1c-1.2.5-1.2 1.2-.2 1.5l4.7 1.5 1.8 5.5c.2.6.4.8 1 .3l2.6-2.2 4.7 3.5c.9.5 1.5.2 1.7-.8l3-16.3zM9.4 12.5l8.4-5.3c.4-.2.7-.1.4.2l-7.2 6.5-.3 3-1.3-4.4z"/></svg>',
      bell: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 8a6 6 0 10-12 0c0 7-3 8-3 8h18s-3-1-3-8"/><path d="M13.7 21a2 2 0 01-3.4 0"/></svg>'
    };
    return icons[name] || '';
  }

  var CATEGORY_CLASS = {
    'Academic, JRF, SRF & PhD Positions': 'cat-academic',
    'Research Associate & Project Staff (Contractual)': 'cat-research',
    'Forestry, Wildlife & Afforestation': 'cat-forestry',
    'GIS, Remote Sensing & Earth Observation': 'cat-gis',
    'ESG, Carbon Markets & Corporate Sustainability': 'cat-esg',
    'Climate Policy, Think-Tanks & Fellowships': 'cat-policy',
    'Grants & Research Funding': 'cat-grants',
    'Scholarships & Doctoral Support': 'cat-scholarship',
    'Fellowships & Leadership Programs': 'cat-fellowship',
    'Internships & Student Traineeships': 'cat-internship',
    'Competitions, Hackathons & Awards': 'cat-competition'
  };

  /* Opportunity kinds (badges + the Opportunity Type filter). */
  var OPPORTUNITY_KINDS = [
    'Job / Career',
    'Fellowship',
    'Scholarship',
    'Grant / Funding',
    'Internship',
    'Competition / Award'
  ];

  /* Region vocabulary of the Global registry (replaces the India state
     filter when the jurisdiction switcher is on "Global"). */
  var GLOBAL_REGIONS = [
    'Global / Remote',
    'Europe',
    'North America',
    'Asia-Pacific',
    'Africa & Middle East',
    'Latin America',
    'UN / Multilateral'
  ];

  function catClass(category) { return CATEGORY_CLASS[category] || 'cat-policy'; }

  /* ------------------------------------------------------------------ */
  /* Topic figures (right-side square visual), readable links & sharing  */
  /* ------------------------------------------------------------------ */
  var TOPIC_META = {
    'Academic, JRF, SRF & PhD Positions': { key: 'academic', label: 'JRF / PHD', emblem: 'cap' },
    'Research Associate & Project Staff (Contractual)': { key: 'research', label: 'RESEARCH', emblem: 'beaker' },
    'Forestry, Wildlife & Afforestation': { key: 'forestry', label: 'FORESTRY', emblem: 'canopy' },
    'GIS, Remote Sensing & Earth Observation': { key: 'gis', label: 'GIS & EO', emblem: 'satellite' },
    'ESG, Carbon Markets & Corporate Sustainability': { key: 'esg', label: 'ESG & CARBON', emblem: 'leaf' },
    'Climate Policy, Think-Tanks & Fellowships': { key: 'policy', label: 'CLIMATE', emblem: 'globe' },
    'Grants & Research Funding': { key: 'grants', label: 'GRANTS', emblem: 'beaker' },
    'Scholarships & Doctoral Support': { key: 'scholarship', label: 'SCHOLARSHIP', emblem: 'cap' },
    'Fellowships & Leadership Programs': { key: 'fellowship', label: 'FELLOWSHIP', emblem: 'globe' },
    'Internships & Student Traineeships': { key: 'internship', label: 'INTERNSHIP', emblem: 'sprout' },
    'Competitions, Hackathons & Awards': { key: 'competition', label: 'AWARDS', emblem: 'trophy' }
  };

  function topicMetaFor(job) {
    if (TOPIC_META[job.category]) return TOPIC_META[job.category];
    var pt = positionTypeOf(job);
    if (pt === 'JRF / SRF' || pt === 'PhD / Doctoral Fellowship' || pt === 'Faculty / Academic') {
      return TOPIC_META['Academic, JRF, SRF & PhD Positions'];
    }
    if (pt === 'Project Associate / Research Associate') {
      return TOPIC_META['Research Associate & Project Staff (Contractual)'];
    }
    return { key: 'policy', label: 'CLIMATE', emblem: 'globe' };
  }

  /* High-contrast topic emblems shown when no institution logo is available. */
  var EMBLEM_SVGS = {
    cap: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3.5 1.8 8.6 12 13.7l10.2-5.1L12 3.5z"/><path d="M6 11v4.2c0 1.8 2.7 3.3 6 3.3s6-1.5 6-3.3V11"/><path d="M22.2 8.6v4.9"/></svg>',
    beaker: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 3h6"/><path d="M10 3v6.3L4.9 17.2A2 2 0 0 0 6.6 20h10.8a2 2 0 0 0 1.7-2.8L14 9.3V3"/><path d="M7.6 14.6h8.8"/></svg>',
    canopy: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3 6.8 10h10.4L12 3z"/><path d="M12 8 4.8 16h14.4L12 8z"/><path d="M12 16v5"/></svg>',
    satellite: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="13" r="6.4"/><path d="M5.6 13h12.8"/><path d="M12 6.6c-2.1 2.3-3.1 4.4-3.1 6.4s1 4.1 3.1 6.4c2.1-2.3 3.1-4.4 3.1-6.4s-1-4.1-3.1-6.4z"/><ellipse cx="12" cy="11.4" rx="10.3" ry="4.6" transform="rotate(-18 12 11.4)"/><circle cx="21.5" cy="5.4" r="1.3" fill="currentColor" stroke="none"/></svg>',
    leaf: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4.8 19.2C4.8 10 10.8 4.8 20 4.8c0 9.2-5.2 15.2-14.4 15.2z"/><path d="M4.8 19.2c2-2.6 4.9-4.8 8.7-6.4"/></svg>',
    sprout: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21v-7.5"/><path d="M12 13.5c0-4.2 3.2-7.4 8.4-7.4 0 5.2-3.2 7.4-8.4 7.4z"/><path d="M12 13.5c0-3.1-2.5-5.9-6.8-5.9 0 3.9 2.5 5.9 6.8 5.9z"/></svg>',
    trophy: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 3.6h8v3.1a4 4 0 11-8 0V3.6z"/><path d="M8 5.2H5.4a2.6 2.6 0 002.8 3.6"/><path d="M16 5.2h2.6a2.6 2.6 0 01-2.8 3.6"/><path d="M12 10.7v4.2"/><path d="M9.6 20.4h4.8l-.5-5.5h-3.8l-.5 5.5z"/></svg>',
    globe: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="8.6"/><path d="M3.4 12h17.2"/><path d="M12 3.4c-2.7 2.5-3.9 5.4-3.9 8.6s1.2 6.1 3.9 8.6c2.7-2.5 3.9-5.4 3.9-8.6s-1.2-6.1-3.9-8.6z"/></svg>'
  };

  function emblemSvg(name) { return EMBLEM_SVGS[name] || EMBLEM_SVGS.globe; }

  function orgMonogram(organization) {
    var words = String(organization || '')
      .replace(/[^A-Za-z0-9 ]/g, ' ')
      .split(/\s+/)
      .filter(function (w) {
        return w && !/^(the|of|and|for|at|in|india|limited|pvt|ltd|private)$/i.test(w);
      });
    if (!words.length) return 'UFP';
    if (words.length === 1) return words[0].slice(0, 3).toUpperCase();
    return (words[0][0] + words[1][0]).toUpperCase();
  }

  function orgDomainOf(job) {
    if (job.org_domain) return String(job.org_domain).replace(/^www\./i, '');
    var match = String(job.org_website || '').match(/^https?:\/\/(?:www\.)?([^\/?#]+)/i);
    return match ? match[1].toLowerCase() : '';
  }

  function applyHostOf(job) {
    var match = String(job.apply_url || '').match(/^https?:\/\/(?:www\.)?([^\/?#]+)/i);
    return match ? match[1].toLowerCase() : '';
  }

  function sourcePortalOf(job) {
    if (job.source_portal) return job.source_portal;
    var host = applyHostOf(job);
    if (/linkedin\./.test(host)) return 'LinkedIn';
    if (/indeed\./.test(host)) return 'Indeed';
    if (/naukri\./.test(host)) return 'Naukri';
    if (/freejobalert\./.test(host)) return 'FreeJobAlert';
    if (/foundit\./.test(host)) return 'Foundit';
    if (/shine\./.test(host)) return 'Shine';
    if (/timesjobs\./.test(host)) return 'TimesJobs';
    if (/internshala\./.test(host)) return 'Internshala';
    if (/apna\./.test(host)) return 'Apna';
    if (/news\.google\./.test(host)) return 'News Announcement';
    if (/reliefweb\./.test(host)) return 'ReliefWeb';
    if (/\.(gov\.in|nic\.in|ac\.in|res\.in|edu\.in)$/.test(host)) return 'Institute Portal';
    return host || 'Direct source';
  }

  /* Editable platform list mirrored from public/link_policy.json for labels. */
  var PLATFORM_HOSTS = [
    [/linkedin\./, 'LinkedIn'],
    [/indeed\./, 'Indeed'],
    [/naukri\./, 'Naukri'],
    [/freejobalert\./, 'FreeJobAlert'],
    [/foundit\./, 'Foundit'],
    [/shine\./, 'Shine'],
    [/timesjobs\./, 'TimesJobs'],
    [/internshala\./, 'Internshala'],
    [/apna\./, 'Apna']
  ];

  function applyPlatformOf(job) {
    var host = applyHostOf(job);
    for (var i = 0; i < PLATFORM_HOSTS.length; i++) {
      if (PLATFORM_HOSTS[i][0].test(host)) return PLATFORM_HOSTS[i][1];
    }
    return '';
  }

  /* Square institution-logo / topic-emblem figure used on cards & dossiers.
     Tries the organisation's favicon first and swaps to the topic emblem
     (via the delegated .fig-logo error handler) when no logo loads. */
  function logoFigureHtml(job, variant) {
    var topic = topicMetaFor(job);
    var domain = orgDomainOf(job);
    var fallback = domain ? '' : ' fig-fallback';
    var media = '';
    if (domain) {
      media += '<img class="fig-logo" src="https://www.google.com/s2/favicons?domain=' +
        encodeURIComponent(domain) + '&sz=128" alt="" loading="lazy" decoding="async" ' +
        'referrerpolicy="no-referrer" width="64" height="64">';
    }
    media += '<span class="fig-emblem" aria-hidden="true">' + emblemSvg(topic.emblem) +
      '<span class="fig-monogram">' + escapeHtml(orgMonogram(job.organization)) + '</span></span>';
    var strip = '<figcaption class="fig-strip"><span class="fig-topic">' +
      escapeHtml(topic.label) + '</span>' +
      (domain ? '<span class="fig-domain">' + escapeHtml(domain) + '</span>' : '') +
      '</figcaption>';
    var aria = topic.label + ' \u00b7 ' + (job.organization || '') + (domain ? ' (' + domain + ')' : '');
    return '<figure class="job-figure job-figure--' + variant + ' fig-' + topic.key + fallback +
      '" data-cat="' + topic.key + '" role="img" aria-label="' + escapeHtml(aria) + '">' +
      '<span class="fig-media">' + media + '</span>' + strip + '</figure>';
  }

  /* Turn any raw URL inside body copy into a readable pill link. */
  function formatReadableText(text) {
    var src = String(text == null ? '' : text);
    var re = /https?:\/\/[^\s<>"')\]]+/g;
    var out = '';
    var last = 0;
    var match;
    while ((match = re.exec(src)) !== null) {
      var url = match[0].replace(/[.,;:]+$/, '');
      out += escapeHtml(src.slice(last, match.index));
      var host = url.replace(/^https?:\/\//i, '').replace(/^www\./i, '').split(/[\/?#]/)[0];
      out += '<a class="inline-doc-link" href="' + escapeHtml(url) +
        '" target="_blank" rel="noopener noreferrer nofollow">Direct link (' +
        escapeHtml(host) + ') \u2197</a>';
      last = match.index + match[0].length;
    }
    out += escapeHtml(src.slice(last));
    return out;
  }

  /* Rich, forward-ready WhatsApp alert for one job. */
  function whatsappAlertText(job) {
    var location = job.state === 'Multiple States / Remote'
      ? 'Multiple States / Remote (India)'
      : (job.city ? job.city + ', ' + job.state : (job.state || 'India'));
    var lines = [
      '\ud83c\udf31 *NEW GREEN / RESEARCH JOB ALERT*',
      '',
      '\ud83d\udccc *Role:* ' + (job.clean_title || ''),
      '\ud83c\udfdb\ufe0f *Organization:* ' + (job.organization || ''),
      '\ud83d\udccd *Location:* ' + location,
      '\ud83c\udf93 *Eligibility:* ' + (job.qualification_summary || 'As per institute norms'),
      '\ud83d\udcb0 *Fellowship/Pay:* ' + (job.compensation_or_fellowship || 'As per institute norms')
    ];
    if (job.valid_through) lines.push('\u23f3 *Apply before:* ' + job.valid_through);
    lines.push('');
    lines.push('\ud83d\udd17 *Full Details & Apply:* ' + shareableUrl(job.id));
    return lines.join('\n');
  }

  function whatsappShareHref(job) {
    return 'https://api.whatsapp.com/send?text=' + encodeURIComponent(whatsappAlertText(job));
  }

  function telegramShareHref(job) {
    var text = job.clean_title + ' at ' + job.organization + ' \u2014 India green & research jobs registry';
    return 'https://t.me/share/url?url=' + encodeURIComponent(shareableUrl(job.id)) +
      '&text=' + encodeURIComponent(text);
  }

  /* "Get Daily Alerts" callout embedded in every dossier. */
  function communityCalloutHtml(job) {
    return '' +
      '<div class="community-callout">' +
        '<div class="cc-copy">' +
          '<strong class="cc-title">' + iconSvg('bell') + ' ' + t('cc.title', 'Get Daily JRF, Forestry, GIS &amp; ESG Job Alerts') + '</strong>' +
          '<span class="cc-sub">' + t('cc.sub', 'Join India\u2019s green & academic job-alert network \u2014 verified jobs delivered every morning at 7 AM IST.') + '</span>' +
        '</div>' +
        '<div class="cc-actions">' +
          '<a class="cc-btn cc-wa" href="' + escapeHtml(COMMUNITY_CHANNELS.whatsapp_group_url) +
            '" target="_blank" rel="noopener"' + communityGuardAttr('whatsapp') + '>' +
            iconSvg('whatsapp') + t('cc.join.wa', 'Join WhatsApp Job Group \u2197') + '</a>' +
          '<a class="cc-btn cc-tg" href="' + escapeHtml(COMMUNITY_CHANNELS.telegram_channel_url) +
            '" target="_blank" rel="noopener"' + communityGuardAttr('telegram') + '>' +
            iconSvg('telegram') + t('cc.join.tg', 'Join Telegram Job Channel \u2197') + '</a>' +
          '<a class="cc-btn cc-share" href="' + escapeHtml(whatsappShareHref(job)) +
            '" target="_blank" rel="noopener noreferrer">' +
            iconSvg('whatsapp') + t('cc.share.wa', 'Share Formatted Alert to WhatsApp') + '</a>' +
          '<a class="cc-btn cc-share-tg" href="' + escapeHtml(telegramShareHref(job)) +
            '" target="_blank" rel="noopener noreferrer">' +
            iconSvg('telegram') + t('cc.share.tg', 'Share to Telegram') + '</a>' +
        '</div>' +
      '</div>';
  }

  /* Direct application card: Apply / Apply on <platform> + hostname. */
  function verifyCardHtml(job, isArchived) {
    var portal = sourcePortalOf(job);
    var orgDomain = orgDomainOf(job);
    var applyHost = applyHostOf(job);
    var platform = applyPlatformOf(job);
    var verifiedDate = verifiedDateOf(job);

    if (isArchived) {
      /* Archived records keep their data but render no outbound link; the
         original application host is shown as plain text. */
      return '' +
        '<div class="verify-card is-archived">' +
          '<div class="verify-head">' +
            '<span class="verify-kicker">' + t('verify.kicker', 'Application record') + '</span>' +
            '<span class="verify-source">' + t('verify.source', 'Source: ') + '<strong>' + escapeHtml(portal) + '</strong></span>' +
          '</div>' +
          '<p class="apply-note">' + t('verify.note.archive', 'This listing is archived \u2014 the application window has closed. No outbound application link is shown. The original application host was ') +
            '<strong>' + escapeHtml(applyHost || 'not recorded') + '</strong>.</p>' +
        '</div>';
    }

    var secondary = '';
    if (job.org_website) {
      secondary = '<a class="verify-btn verify-btn-org" href="' + escapeHtml(job.org_website) +
        '" target="_blank" rel="noopener noreferrer">' +
        '<span class="vb-label">' + t('verify.website', 'Organisation website') + ' ' + iconSvg('external') + '</span>' +
        '<span class="vb-sub">' + escapeHtml(orgDomain || t('verify.website.sub', 'employer domain')) + '</span></a>';
    }

    var applyLabel = platform
      ? t('verify.apply.platform', 'Apply on ' + platform)
      : t('verify.apply', 'Apply');

    return '' +
      '<div class="verify-card">' +
        '<div class="verify-head">' +
          '<span class="verify-kicker">' + t('verify.kicker.active', 'Direct application link') + '</span>' +
          '<span class="verify-source">' + t('verify.source', 'Source: ') + '<strong>' + escapeHtml(portal) + '</strong></span>' +
        '</div>' +
        '<div class="verify-actions">' +
          '<a class="verify-btn verify-btn-apply" href="' + escapeHtml(job.apply_url) +
            '" target="_blank" rel="noopener noreferrer">' +
            '<span class="vb-label">' + escapeHtml(applyLabel) + ' ' + iconSvg('external') + '</span>' +
            '<span class="vb-sub">' + escapeHtml(applyHost || 'direct link') + '</span></a>' +
          secondary +
        '</div>' +
        '<p class="verify-trust">' + t('verify.trust', 'Link checked on') + ' ' +
          escapeHtml(verifiedDate) + '</p>' +
        '<p class="apply-note">' + t('verify.note.active', 'The application link opens in a new tab. Always verify eligibility, fellowship norms and deadlines before applying. ') +
          '<a class="verify-report" href="' + reportBrokenLinkHref(job) + '">' +
          t('verify.report', 'Report a broken link') + '</a></p>' +
      '</div>';
  }

  /* Position-type inference mirrors scripts/fetch_and_humanize.py so even a
     pre-migration record still lands in an accurate career track. */
  var POSITION_TYPE_PATTERNS = [
    [/\b(jrf|junior research fellow|srf|senior research fellow)\b/i, 'JRF / SRF'],
    [/\b(ph\.?\s?d|doctoral|doctorate|post-?doctoral|postdoc)\b/i, 'PhD / Doctoral Fellowship'],
    [/\b(project associate|research associate|project assistant|research assistant|project scientist|research scientist)\b/i, 'Project Associate / Research Associate'],
    [/\b(young professional|consultant|advisor|adviser)\b/i, 'Young Professional / Consultant (Contractual)'],
    [/\b(professor|faculty|lecturer|dean)\b/i, 'Faculty / Academic'],
    [/\b(fellow|fellowship|intern|internship|trainee)\b/i, 'Fellowship / Internship']
  ];

  var POSITION_TYPE_BY_CATEGORY = {
    'Academic, JRF, SRF & PhD Positions': 'JRF / SRF',
    'Research Associate & Project Staff (Contractual)': 'Project Associate / Research Associate',
    'Grants & Research Funding': 'Young Professional / Consultant (Contractual)',
    'Scholarships & Doctoral Support': 'PhD / Doctoral Fellowship',
    'Fellowships & Leadership Programs': 'Fellowship / Internship',
    'Internships & Student Traineeships': 'Fellowship / Internship',
    'Competitions, Hackathons & Awards': 'Fellowship / Internship'
  };

  var ACADEMIC_POSITION_TYPES = [
    'JRF / SRF',
    'PhD / Doctoral Fellowship',
    'Project Associate / Research Associate',
    'Young Professional / Consultant (Contractual)',
    'Faculty / Academic',
    'Fellowship / Internship'
  ];

  function positionTypeOf(job) {
    if (job.position_type) return job.position_type;
    var text = String(job.clean_title || '') + ' ' + String(job.category || '');
    var i;
    for (i = 0; i < POSITION_TYPE_PATTERNS.length; i += 1) {
      if (POSITION_TYPE_PATTERNS[i][0].test(text)) return POSITION_TYPE_PATTERNS[i][1];
    }
    return POSITION_TYPE_BY_CATEGORY[job.category] || 'Full-Time Corporate / NGO';
  }

  /* Exactly one career track per record (drives the quick-filter strip). */
  function trackOf(job) {
    var pt = positionTypeOf(job);
    if (pt === 'JRF / SRF' || pt === 'Project Associate / Research Associate' || pt === 'Faculty / Academic') return 'research';
    if (pt === 'PhD / Doctoral Fellowship') return 'phd';
    if (pt === 'Young Professional / Consultant (Contractual)') return 'contractual';
    if (job.category === 'Grants & Research Funding' || job.category === 'Fellowships & Leadership Programs') return 'thinktank';
    if (job.category === 'Scholarships & Doctoral Support') return 'phd';
    if (job.category === 'Internships & Student Traineeships') return 'contractual';
    if (job.category === 'Climate Policy, Think-Tanks & Fellowships' || pt === 'Fellowship / Internship') return 'thinktank';
    return 'corporate';
  }

  /* schema.org employmentType derived from the position type. */
  function employmentTypeFor(job) {
    var pt = positionTypeOf(job);
    if (pt === 'JRF / SRF' || pt === 'Project Associate / Research Associate' ||
        pt === 'Young Professional / Consultant (Contractual)') return 'CONTRACTOR';
    if (pt === 'Fellowship / Internship') return 'INTERN';
    return 'FULL_TIME';
  }

  function pad2(n) { return (n < 10 ? '0' : '') + n; }
  function localIso(d) { return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate()); }
  function isoDaysAgo(days) {
    var d = new Date();
    d.setHours(0, 0, 0, 0);
    d.setDate(d.getDate() - days);
    return localIso(d);
  }

  function daysSince(dateStr) {
    var d = new Date(dateStr + 'T00:00:00');
    if (isNaN(d.getTime())) return null;
    var today = new Date();
    today.setHours(0, 0, 0, 0);
    return Math.max(0, Math.round((today - d) / 86400000));
  }

  function formatLongDate(dateStr) {
    var d = new Date(dateStr + 'T00:00:00');
    if (isNaN(d.getTime())) return dateStr || '';
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  }

  function formatPosted(dateStr) {
    var days = daysSince(dateStr);
    if (days === null) return 'Recently listed';
    if (days === 0) return 'Listed today';
    if (days === 1) return 'Listed yesterday';
    if (days < 7) return 'Listed ' + days + ' days ago';
    return 'Listed on ' + formatLongDate(dateStr);
  }

  function formatClosed(dateStr) {
    var days = daysSince(dateStr);
    if (days === null) return 'Closed';
    if (days === 0) return 'Closed today';
    if (days === 1) return 'Closed yesterday';
    if (days < 7) return 'Closed ' + days + ' days ago';
    return 'Closed on ' + formatLongDate(dateStr);
  }

  function stateLabel(job) {
    if (job.region) {
      var base = job.city || job.country || job.region;
      return (job.region && base !== job.region) ? base + ' \u00b7 ' + job.region : base;
    }
    if (job.state === 'Multiple States / Remote') return 'Multiple States / Remote';
    return job.city ? job.city + ', ' + job.state : (job.state || 'India');
  }

  /* Opportunity-kind helpers (badges + filter). */
  function opportunityKindOf(job) {
    var kind = String(job.opportunity_kind || '').trim();
    if (kind && OPPORTUNITY_KINDS.indexOf(kind) !== -1) return kind;
    return 'Job / Career';
  }

  function deadlineOf(job) {
    return String(job.deadline_or_window || '').trim();
  }

  function toast(message) {
    var el = els.toast;
    if (!el) return;
    el.textContent = message;
    el.classList.add('show');
    clearTimeout(toast._t);
    toast._t = setTimeout(function () { el.classList.remove('show'); }, 2400);
  }

  function setText(id, value) {
    var el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  /* ------------------------------------------------------------------ */
  /* Data loading                                                        */
  /* ------------------------------------------------------------------ */
  function fetchJson(url, required) {
    return fetch(url, { cache: 'no-cache' })
      .then(function (res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .catch(function (err) {
        if (required) throw err;
        if (window.console) console.warn('[registry] optional dataset unavailable:', url, err);
        return null;
      });
  }

  function sortByDateDesc(list, field) {
    list.sort(function (a, b) {
      return String(b[field] || '').localeCompare(String(a[field] || '')) ||
        String(b.id || '').localeCompare(String(a.id || ''));
    });
    return list;
  }

  /* Quarantined records stay in the data files for review but never reach
     the public UI, dossier routing, JSON-LD, hubs or the sitemap. */
  function publicOnly(list) {
    return (Array.isArray(list) ? list : []).filter(function (job) {
      return job && job.status !== 'quarantined';
    });
  }

  /* Placement rule: posting -> Jobs; careers_portal -> Careers portals;
     award_portal -> Fellowships & programmes; unknown -> hidden. */
  function entrySectionOf(job) {
    var type = job.entry_type || (job.quarantine && job.quarantine.entry_type) || 'posting';
    if (type === 'careers_portal') return 'careers';
    if (type === 'award_portal') return 'programmes';
    if (type === 'posting') return 'jobs';
    return 'hidden';
  }

  function verifiedDateOf(job) {
    var verification = job.verification || {};
    var stamp = String(verification.verified_at || '').slice(0, 10);
    return stamp || String(job.date_added || '').slice(0, 10);
  }

  function reportBrokenLinkHref(job) {
    var subject = 'Broken link: ' + (job.clean_title || job.id || 'registry record');
    var body = 'Dossier: ' + shareableUrl(job.id) +
      '\nApply host: ' + (applyHostOf(job) || 'unknown') +
      '\nWhat happened: ';
    return 'mailto:urbanforestpark@gmail.com?subject=' +
      encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
  }

  function skeletonHtml() {
    var card = '<div class="job-card skeleton-card" aria-hidden="true">' +
      '<div class="sk-line sk-badge"></div>' +
      '<div class="sk-line sk-title"></div>' +
      '<div class="sk-line sk-sub"></div>' +
      '<div class="sk-line sk-meta"></div>' +
      '<div class="sk-line sk-meta short"></div>' +
      '<div class="sk-line sk-bar"></div>' +
    '</div>';
    return '<div class="skeleton-grid" role="status" aria-label="Loading registry jobs">' + card.repeat(6) + '</div>';
  }

  function loadAll() {
    els.grid.innerHTML = skeletonHtml();
    Promise.all([
      fetchJson(CONFIG.DATA_URL, true),
      fetchJson(CONFIG.ARCHIVE_URL, false),
      fetchJson(CONFIG.STATS_URL, false),
      fetchJson(CONFIG.GLOBAL_DATA_URL, false),
      fetchJson(CONFIG.GLOBAL_ARCHIVE_URL, false)
    ]).then(function (results) {
      state.jobs = sortByDateDesc(publicOnly(results[0]), 'date_added');
      state.archive = sortByDateDesc(publicOnly(results[1]), 'date_archived');
      state.stats = (results[2] && typeof results[2] === 'object') ? results[2] : null;
      state.globalJobs = sortByDateDesc(publicOnly(results[3]), 'date_added');
      state.globalArchive = sortByDateDesc(publicOnly(results[4]), 'date_archived');
      state.loaded = true;

      DEFAULT_HERO_HTML = els.heroHeading ? els.heroHeading.innerHTML : '';
      DEFAULT_HERO_SUB_HTML = els.heroSub ? els.heroSub.innerHTML : '';

      initFromUrl();
      syncRegistryChrome();
      renderTelemetry();
      updateTabCounts();
      syncViewChrome();
      syncKindSelect();
      populateStateSelect();
      refreshCategoryPills();
      refreshTrackButtons();
      refreshQuickButtons();
      updateSavedUi();
      injectFeedJsonLd(state.jobs);
      renderSeoDirectory();
      applyFilters();
      route(true);
      restoreFeedScrollOnLoad();
    }).catch(function (err) {
      els.grid.innerHTML = '<div class="empty-state"><h3>Could not load registry data</h3>' +
        '<p>Please refresh the page. If this persists, check that <code>jobs.json</code> is being served on this domain.</p></div>';
      if (window.console) console.error('[registry] failed to load listings:', err);
    });
  }

  /* ------------------------------------------------------------------ */
  /* URL parsing & state synchronisation                                 */
  /* ------------------------------------------------------------------ */
  function resolveCategoryParam(value) {
    if (!value) return null;
    var raw = String(value).trim();
    var key;
    for (key in CATEGORY_SLUGS) {
      if (CATEGORY_SLUGS[key] === raw) return key;
    }
    if (LEGACY_CATEGORY_SLUGS[raw]) return LEGACY_CATEGORY_SLUGS[raw];
    for (key in CATEGORY_CLASS) {
      if (key.toLowerCase() === raw.toLowerCase()) return key;
    }
    for (key in CATEGORY_LEGACY_NAMES) {
      if (key.toLowerCase() === raw.toLowerCase()) return CATEGORY_LEGACY_NAMES[key];
    }
    return null;
  }

  function initFromUrl() {
    var params;
    try { params = new URLSearchParams(window.location.search || ''); }
    catch (e) { params = null; }
    if (!params) return;

    /* ?lang=hi / ?lang=en deep links (used by the Hindi SEO hub cards). */
    var langParam = params.get('lang');
    if ((langParam === 'hi' || langParam === 'en') && window.UFPI18N && window.UFPI18N.lang !== langParam) {
      window.UFPI18N.setLang(langParam, { silent: true });
    }

    if ((params.get('view') || '') === 'archive') state.view = 'archive';
    var stateParam = params.get('state');
    if (stateParam && stateParam !== 'all') {
      state.state = stateParam;
      state.registry = 'india';
    }
    var cat = resolveCategoryParam(params.get('category'));
    if (cat) state.category = cat;

    /* Jurisdiction routing: ?region=global switches to the strictly
       separated Global registry; ?gregion=<Europe|...> pre-selects a
       global region and implies the global registry. */
    var regionParam = (params.get('region') || '').toLowerCase();
    if (regionParam === 'global') state.registry = 'global';
    var globalRegionParam = params.get('gregion');
    if (globalRegionParam) {
      state.region = globalRegionParam;
      state.registry = 'global';
    }
    var kindParam = params.get('kind');
    if (kindParam) state.kind = kindParam;

    /* Career-track deep links (used by the pathway hub pages). */
    var track = params.get('track');
    if (track) {
      var known = false;
      TRACK_META.forEach(function (t) { if (t.id === track) known = true; });
      if (known) state.track = track;
    }

    /* ?q= entry point for the WebSite SearchAction sitelinks searchbox. */
    var q = params.get('q');
    if (q) {
      state.query = q;
      var searchInput = document.getElementById('jobs-search');
      if (searchInput) searchInput.value = q;
      var heroInput = document.getElementById('hero-search-input');
      if (heroInput) heroInput.value = q;
    }

    state.detailId = null;
  }

  /* Query string reflecting the current registry view (no ?job=). */
  function queryForState() {
    var parts = [];
    if (state.view === 'archive') parts.push('view=archive');
    if (state.registry === 'global') {
      parts.push('region=global');
      if (state.region !== 'all') parts.push('gregion=' + encodeURIComponent(state.region));
    } else if (state.state !== 'all') {
      parts.push('state=' + encodeURIComponent(state.state));
    }
    if (state.category !== 'all') {
      parts.push('category=' + encodeURIComponent(CATEGORY_SLUGS[state.category] || state.category));
    }
    if (state.track !== 'all') parts.push('track=' + encodeURIComponent(state.track));
    if (state.kind !== 'all') parts.push('kind=' + encodeURIComponent(state.kind));
    return parts.length ? '?' + parts.join('&') : '';
  }

  function syncUrl(push) {
    if (state.detailId) return;
    var path = window.location.pathname + queryForState();
    if (window.history && window.history.pushState) {
      try {
        if (push) window.history.pushState({}, '', path);
        else window.history.replaceState({}, '', path);
      } catch (e) { /* ignore */ }
    }
  }

  function getViewData() {
    var isGlobal = state.registry === 'global';
    if (state.view === 'archive') return isGlobal ? state.globalArchive : state.archive;
    return isGlobal ? state.globalJobs : state.jobs;
  }

  /* Jurisdiction switcher: 'india' | 'global'. The two registries are
     strictly separated; switching never mixes their records. */
  function setRegistry(registry, opts) {
    opts = opts || {};
    registry = registry === 'global' ? 'global' : 'india';
    var changed = state.registry !== registry;
    state.registry = registry;
    syncRegistryChrome();
    updateTabCounts();
    renderTelemetry();
    populateStateSelect();
    refreshCategoryPills();
    refreshTrackButtons();
    if (changed || opts.force) applyFilters();
    if (!opts.keepUrl) syncUrl(opts.push !== false);
    if (changed && !opts.silent) {
      toast(registry === 'global'
        ? t('registry.switch.global', 'Showing Global Opportunities (international jobs, grants & scholarships)')
        : t('registry.switch.india', 'Showing India jobs (JRF, fellowships & grants)'));
    }
  }

  function syncRegistryChrome() {
    var isGlobal = state.registry === 'global';
    document.body.classList.toggle('registry-global', isGlobal);
    Array.prototype.forEach.call(
      document.querySelectorAll('[data-jurisdiction]'),
      function (btn) {
        var active = (btn.getAttribute('data-jurisdiction') === 'global') === isGlobal;
        btn.classList.toggle('active', active);
        btn.setAttribute('aria-pressed', active ? 'true' : 'false');
      }
    );
    /* Hero copy follows the jurisdiction (India registry vs Global hub). */
    if (els.heroHeading && DEFAULT_HERO_HTML) {
      els.heroHeading.innerHTML = isGlobal
        ? t('hero.global.title_html', 'Worldwide <span class="accent">Climate &amp; Sustainability</span> Opportunities')
        : DEFAULT_HERO_HTML;
    }
    if (els.heroSub && DEFAULT_HERO_SUB_HTML) {
      els.heroSub.innerHTML = isGlobal
        ? t('hero.global.sub', 'International jobs, grants, scholarships, fellowships, internships and competitions across climate, forestry, energy, water, biodiversity and ESG — verified, with direct application links.')
        : DEFAULT_HERO_SUB_HTML;
    }
    if (els.heroKicker) {
      els.heroKicker.textContent = isGlobal
        ? t('hero.global.kicker', 'Global Opportunities Registry (International)')
        : t('hero.kicker', els.heroKicker.getAttribute('data-default-kicker') || '');
    }
  }

  function syncViewChrome() {
    var isArchive = state.view === 'archive';
    document.body.classList.toggle('view-archive', isArchive);

    if (els.tabActive) {
      els.tabActive.classList.toggle('active', !isArchive);
      els.tabActive.setAttribute('aria-selected', isArchive ? 'false' : 'true');
    }
    if (els.tabArchive) {
      els.tabArchive.classList.toggle('active', isArchive);
      els.tabArchive.setAttribute('aria-selected', isArchive ? 'true' : 'false');
    }
    if (els.experienceField) els.experienceField.classList.toggle('hidden', isArchive);
    if (els.archiveRangeField) els.archiveRangeField.classList.toggle('hidden', !isArchive);
    if (els.navRegistry) els.navRegistry.classList.toggle('active', !isArchive);
    if (els.navArchive) els.navArchive.classList.toggle('active', isArchive);
  }

  function setView(view, opts) {
    opts = opts || {};
    var changed = state.view !== view;
    state.view = view;
    syncViewChrome();
    updateTabCounts();
    populateStateSelect();
    refreshCategoryPills();
    refreshTrackButtons();
    if (changed || opts.force) applyFilters();
    if (!opts.keepUrl) syncUrl(opts.push !== false);
  }

  function updateTabCounts() {
    var isGlobal = state.registry === 'global';
    setText('tab-active-count', String(isGlobal ? state.globalJobs.length : state.jobs.length));
    setText('tab-archive-count', String(isGlobal ? state.globalArchive.length : state.archive.length));
  }

  function findJob(id) {
    var i, isGlobal;
    for (i = 0; i < state.jobs.length; i += 1) {
      if (state.jobs[i].id === id) return { job: state.jobs[i], archived: false, registry: 'india' };
    }
    for (i = 0; i < state.archive.length; i += 1) {
      if (state.archive[i].id === id) return { job: state.archive[i], archived: true, registry: 'india' };
    }
    for (i = 0; i < state.globalJobs.length; i += 1) {
      if (state.globalJobs[i].id === id) return { job: state.globalJobs[i], archived: false, registry: 'global' };
    }
    for (i = 0; i < state.globalArchive.length; i += 1) {
      if (state.globalArchive[i].id === id) return { job: state.globalArchive[i], archived: true, registry: 'global' };
    }
    return null;
  }

  /* ------------------------------------------------------------------ */
  /* Weekly telemetry ribbon                                             */
  /* ------------------------------------------------------------------ */
  function statsWindow() {
    var weekAgo = isoDaysAgo(CONFIG.ARCHIVE_RECENT_DAYS);
    if (state.registry === 'global') {
      return {
        active_open_jobs: state.globalJobs.length,
        opened_this_week: state.globalJobs.filter(function (j) {
          return String(j.date_added || '') >= weekAgo;
        }).length,
        passed_this_week: state.globalArchive.filter(function (j) {
          return String(j.date_archived || '') >= weekAgo;
        }).length,
        total_archived_jobs: state.globalArchive.length,
        total_historical_indexed: state.globalJobs.length + state.globalArchive.length,
        last_updated: null
      };
    }
    var computed = {
      active_open_jobs: state.jobs.length,
      opened_this_week: state.jobs.filter(function (j) {
        return String(j.date_added || '') >= weekAgo;
      }).length,
      passed_this_week: state.archive.filter(function (j) {
        return String(j.date_archived || '') >= weekAgo;
      }).length,
      total_archived_jobs: state.archive.length,
      total_historical_indexed: state.jobs.length + state.archive.length,
      last_updated: null
    };
    var stats = state.stats;
    if (!stats || typeof stats.active_open_jobs !== 'number') return computed;
    return {
      active_open_jobs: stats.active_open_jobs,
      opened_this_week: typeof stats.opened_this_week === 'number' ? stats.opened_this_week : computed.opened_this_week,
      passed_this_week: typeof stats.passed_this_week === 'number' ? stats.passed_this_week : computed.passed_this_week,
      total_archived_jobs: typeof stats.total_archived_jobs === 'number' ? stats.total_archived_jobs : computed.total_archived_jobs,
      total_historical_indexed: typeof stats.total_historical_indexed === 'number' ? stats.total_historical_indexed : computed.total_historical_indexed,
      last_updated: stats.last_updated || null
    };
  }

  function renderTelemetry() {
    var statsData = statsWindow();
    setText('tel-active', String(statsData.active_open_jobs));
    setText('tel-new', String(statsData.opened_this_week));
    setText('tel-passed', String(statsData.passed_this_week));
    setText('tel-archive', String(statsData.total_historical_indexed));
    setText('tel-updated', statsData.last_updated ? formatLongDate(String(statsData.last_updated).slice(0, 10)) : t('tel.local', 'local sync'));
  }

  /* ------------------------------------------------------------------ */
  /* Filters & feed rendering                                            */
  /* ------------------------------------------------------------------ */
  function populateStateSelect() {
    if (!els.stateSelect) return;
    var labelEl = document.getElementById('state-filter-label');

    /* Global registry: the state dropdown becomes a Global Region filter. */
    if (state.registry === 'global') {
      if (labelEl) labelEl.textContent = t('filters.gregion.label', 'Global Region');
      var gsource = getViewData();
      var gcounts = {};
      gsource.forEach(function (j) {
        var region = j.region || 'Global / Remote';
        gcounts[region] = (gcounts[region] || 0) + 1;
      });
      var regions = GLOBAL_REGIONS.slice();
      Object.keys(gcounts).forEach(function (r) {
        if (regions.indexOf(r) === -1) regions.push(r);
      });
      var ghtml = '<option value="all">' + t('filters.gregion.all', 'All Global ({n})', { n: gsource.length }) + '</option>';
      regions.forEach(function (r) {
        ghtml += '<option value="' + escapeHtml(r) + '">' + escapeHtml(r) + ' (' + (gcounts[r] || 0) + ')</option>';
      });
      els.stateSelect.innerHTML = ghtml;
      els.stateSelect.value = gcounts[state.region] ? state.region : 'all';
      if (els.stateSelect.value === 'all') state.region = 'all';
      return;
    }

    if (labelEl) labelEl.textContent = t('filters.state.label', 'State / Region');

    var source = getViewData();
    var counts = {};
    source.forEach(function (j) {
      if (!j.state) return;
      counts[j.state] = (counts[j.state] || 0) + 1;
    });
    var states = Object.keys(counts).sort();
    var html = '<option value="all">' + t('filters.state.alln', 'All India ({n})', { n: source.length }) + '</option>';
    states.forEach(function (s) {
      html += '<option value="' + escapeHtml(s) + '">' + escapeHtml(s) + ' (' + counts[s] + ')</option>';
    });
    els.stateSelect.innerHTML = html;
    els.stateSelect.value = counts[state.state] ? state.state : 'all';
    if (els.stateSelect.value === 'all') state.state = 'all';
  }

  /* Opportunity-type dropdown (jobs + grants + scholarships + ...). */
  function syncKindSelect() {
    if (!els.kindSelect) return;
    var value = OPPORTUNITY_KINDS.indexOf(state.kind) !== -1 ? state.kind : 'all';
    els.kindSelect.value = value;
    if (value === 'all') state.kind = 'all';
  }

  function refreshCategoryPills() {
    var source = getViewData();
    var counts = { all: source.length };
    source.forEach(function (j) {
      counts[j.category] = (counts[j.category] || 0) + 1;
    });
    var pillRow = document.getElementById('category-pills');
    if (!pillRow) return;
    Array.prototype.forEach.call(pillRow.querySelectorAll('.cat-pill'), function (pill) {
      var cat = pill.getAttribute('data-cat') || 'all';
      var cnt = pill.querySelector('.cnt');
      if (cnt) cnt.textContent = counts[cat] != null ? counts[cat] : 0;
      pill.classList.toggle('active', cat === state.category);
    });
  }

  function refreshTrackButtons() {
    var source = getViewData();
    var counts = { all: source.length, research: 0, phd: 0, contractual: 0, corporate: 0, thinktank: 0 };
    source.forEach(function (j) { counts[trackOf(j)] += 1; });
    var row = document.getElementById('career-tracks');
    if (!row) return;
    Array.prototype.forEach.call(row.querySelectorAll('.track-btn'), function (btn) {
      var track = btn.getAttribute('data-track') || 'all';
      var cnt = btn.querySelector('.cnt');
      if (cnt) cnt.textContent = counts[track] != null ? counts[track] : 0;
      var active = track === state.track;
      btn.classList.toggle('active', active);
      btn.setAttribute('aria-pressed', active ? 'true' : 'false');
    });
  }

  function refreshQuickButtons() {
    var row = document.getElementById('quick-filters');
    if (!row) return;
    Array.prototype.forEach.call(row.querySelectorAll('[data-quick]'), function (btn) {
      var active = (btn.getAttribute('data-quick') || 'all') === state.quick;
      btn.classList.toggle('active', active);
      btn.setAttribute('aria-pressed', active ? 'true' : 'false');
    });
  }

  function archiveCutoff() {
    return isoDaysAgo(CONFIG.ARCHIVE_RECENT_DAYS);
  }

  function applyFilters() {
    var q = state.query.trim().toLowerCase();
    var source = getViewData();
    var isArchive = state.view === 'archive';
    var cutoff = archiveCutoff();

    state.filtered = source.filter(function (job) {
      if (!isArchive && entrySectionOf(job) === 'hidden') return false;
      if (state.registry === 'global') {
        if (state.region !== 'all' && (job.region || 'Global / Remote') !== state.region) return false;
      } else if (state.state !== 'all' && job.state !== state.state) {
        return false;
      }
      if (state.category !== 'all' && job.category !== state.category) return false;
      if (state.track !== 'all' && trackOf(job) !== state.track) return false;
      if (state.quick !== 'all' && QUICK_FILTERS[state.quick] && !QUICK_FILTERS[state.quick](job)) return false;
      if (state.savedOnly && savedSet()[String(job.id)] !== true) return false;
      if (state.kind !== 'all' && opportunityKindOf(job) !== state.kind) return false;
      if (!isArchive && state.experience !== 'all' && job.experience_level !== state.experience) return false;
      if (isArchive && state.archiveRecent && String(job.date_archived || '') < cutoff) return false;
      if (q) {
        var haystack = [
          job.clean_title, job.organization, job.city, job.state,
          job.region, job.country, job.opportunity_kind, job.deadline_or_window,
          job.category, job.experience_level, job.position_type,
          job.qualification_summary, job.compensation_or_fellowship,
          (job.must_have_skills || []).join(' ')
        ].join(' ').toLowerCase();
        if (haystack.indexOf(q) === -1) return false;
      }
      return true;
    });
    renderFeed();
    updateViewSeo();
  }

  function renderFeed() {
    var jobs = state.filtered;
    var isArchive = state.view === 'archive';
    var countEl = els.resultsCount;
    if (countEl) {
      if (!state.loaded) {
        countEl.textContent = t('feed.loading', 'Loading\u2026');
      } else if (isArchive) {
        countEl.textContent = jobs.length === 1
          ? t('feed.archive.one', '1 historical record')
          : t('feed.archive.many', '{n} historical records', { n: jobs.length });
      } else {
        countEl.textContent = jobs.length === 1
          ? t('feed.active.one', '1 active position')
          : t('feed.active.many', '{n} active positions', { n: jobs.length });
      }
    }

    if (!state.loaded) return;

    var source = getViewData();
    if (!source.length) {
      els.grid.innerHTML = isArchive
        ? '<div class="empty-state"><h3>' + t('empty.nolist.archive.title', 'The historical archive is being catalogued') + '</h3><p>' + t('empty.nolist.archive.sub', 'Past jobs appear here once their application windows close.') + '</p></div>'
        : '<div class="empty-state"><h3>' + t('empty.nolist.active.title', 'No listings yet') + '</h3><p>' + t('empty.nolist.active.sub', 'New environmental jobs are published regularly. Check back soon.') + '</p></div>';
      els.grid.setAttribute('aria-busy', 'false');
      return;
    }

    if (!jobs.length) {
      els.grid.innerHTML = emptyFilterHtml();
      els.grid.setAttribute('aria-busy', 'false');
      return;
    }

    var html = '';
    if (isArchive) {
      jobs.forEach(function (job) {
        html += jobCardHtml(job, true);
      });
    } else {
      /* Two extra registry sections, same card layout and styling. */
      var groups = [
        { key: 'jobs', title: t('section.jobs', 'Jobs'), items: [] },
        { key: 'careers', title: t('section.careers', 'Careers portals'), items: [] },
        { key: 'programmes', title: t('section.programmes', 'Fellowships & programmes'), items: [] }
      ];
      jobs.forEach(function (job) {
        var section = entrySectionOf(job);
        groups.forEach(function (group) {
          if (group.key === section) group.items.push(job);
        });
      });
      groups.forEach(function (group) {
        if (!group.items.length) return;
        html += '<h3 class="feed-group-title">' + escapeHtml(group.title) +
          ' <span class="feed-group-count">' + group.items.length + '</span></h3>';
        group.items.forEach(function (job) {
          html += jobCardHtml(job, false);
        });
      });
    }
    els.grid.innerHTML = html;
    els.grid.setAttribute('aria-busy', 'false');
  }

  function emptyFilterHtml() {
    var isArchive = state.view === 'archive';
    var html = '<div class="empty-state">';
    html += '<h3>' + (isArchive
      ? t('empty.nomatch.archive', 'No archived records match these filters')
      : t('empty.nomatch.active', 'No active jobs match these filters')) + '</h3>';
    html += '<p>' + t('empty.hint', 'Try a different keyword, region or sector \u2014 or reset the filters.') + '</p>';

    /* Active view with zero matches in a sector that has historical records:
       route the visitor to the archive instead of a dead end. */
    if (!isArchive && state.category !== 'all') {
      var archivedCount = state.archive.filter(function (j) { return j.category === state.category; }).length;
      if (archivedCount > 0) {
        html += '<p>' + t('empty.archive.note', 'No active jobs are open in this sector at present \u2014 {n} historical record(s) exist in the archive.', { n: archivedCount }) + '</p>';
        html += '<button class="btn btn-outline" type="button" data-switch-archive>' + t('empty.switcharchive', 'View Historical Archive') + ' ' + iconSvg('arrow') + '</button>';
      }
    }
    html += '<button class="btn btn-ghost" type="button" data-clear-filters>' + t('empty.reset', 'Reset Filters') + '</button>';
    html += '</div>';
    return html;
  }

  /* Qualification + compensation strip shown under a card's meta row. */
  function academicBadgesHtml(job) {
    var meta = job.academic_meta || {};
    var badges = [];
    if (meta.net_gate) badges.push(meta.net_gate);
    if (job.selection_process) badges.push(job.selection_process);
    if (meta.stipend && job.compensation_or_fellowship !== meta.stipend) badges.push(meta.stipend);
    if (!badges.length) return '';
    return '<div class="jc-academic-badges">' + badges.map(function (badge) {
      return '<span class="jc-academic-badge">' + escapeHtml(badge) + '</span>';
    }).join('') + '</div>';
  }

  function jcEligibilityHtml(job) {
    var items = [];
    if (job.qualification_summary) {
      items.push('<span class="jc-elig-item">' + iconSvg('cap') + escapeHtml(job.qualification_summary) + '</span>');
    }
    if (job.compensation_or_fellowship) {
      items.push('<span class="jc-elig-item">' + iconSvg('rupee') + escapeHtml(job.compensation_or_fellowship) + '</span>');
    }
    if (!items.length && !academicBadgesHtml(job)) return '';
    return '<div class="jc-eligibility">' + items.join('') + '</div>' + academicBadgesHtml(job);
  }

  function jobCardHtml(job, isArchived) {
    var skills = job.must_have_skills || [];
    var shown = skills.slice(0, 3);
    var extra = skills.length - shown.length;
    var chips = shown.map(function (s) {
      return '<span class="skill-chip">' + escapeHtml(s) + '</span>';
    }).join('');
    if (extra > 0) chips += '<span class="skill-chip more">' + t('card.more', '+{n} more', { n: extra }) + '</span>';

    var statusBadge = isArchived
      ? '<span class="badge badge-archived">' + iconSvg('archive') + t('card.archived', 'Archived') + '</span>'
      : '';

    var kind = opportunityKindOf(job);
    var kindBadge = (kind !== 'Job / Career')
      ? '<span class="badge badge-kind">' + escapeHtml(kind) + '</span>'
      : '';
    var regionBadge = job.region
      ? '<span class="badge badge-region">' + iconSvg('pin') + escapeHtml(job.region) + '</span>'
      : '';

    var dateMeta = isArchived
      ? iconSvg('clock') + escapeHtml(formatClosed(job.date_archived))
      : iconSvg('calendar') + escapeHtml(formatPosted(job.date_added));

    var deadlineMeta = (!isArchived && deadlineOf(job))
      ? '<span class="jc-deadline">' + iconSvg('clock') + escapeHtml(t('card.deadline', 'Apply: {d}', { d: deadlineOf(job) })) + '</span>'
      : '';

    var footDate = isArchived
      ? t('card.closed', 'Closed ') + escapeHtml(job.date_archived || '')
      : escapeHtml(job.date_added || '');

    var ctaLabel = isArchived
      ? t('card.cta.archive', 'Open Archived Record')
      : t('card.cta.active', 'View Job & Apply');

    var saved = isSaved(job.id);
    var waShareHref = 'https://wa.me/?text=' + encodeURIComponent(shareTextFor(job));
    var detailHref = jobPath(job.id);

    return '' +
      '<article class="job-card' + (isArchived ? ' is-archived' : '') + '" data-id="' + escapeHtml(job.id) + '" data-href="' + escapeHtml(detailHref) + '" tabindex="0" role="group" ' +
        'aria-label="' + (isArchived ? t('card.aria.archive', 'Open archived record: ') : t('card.aria.view', 'View job and apply: ')) +
        escapeHtml(job.clean_title) + ' at ' + escapeHtml(job.organization) + '">' +
        '<div class="jc-top">' +
          '<span class="badge ' + catClass(job.category) + '">' + escapeHtml(job.category) + '</span>' +
          '<span class="badge badge-type">' + escapeHtml(positionTypeOf(job)) + '</span>' +
          kindBadge +
          regionBadge +
          '<span class="badge badge-exp">' + escapeHtml(job.experience_level || '') + '</span>' +
          statusBadge +
        '</div>' +
        '<div class="jc-main">' +
          '<div class="jc-main-text">' +
            '<h3 class="jc-title"><a class="jc-title-link" href="' + escapeHtml(detailHref) + '">' + escapeHtml(displayTitle(job)) + '</a></h3>' +
            (isHindi() && job.title_hi ? '<p class="jc-title-en">' + escapeHtml(job.clean_title) + '</p>' : '') +
            '<p class="jc-org">' + escapeHtml(job.organization) + '</p>' +
            '<div class="jc-meta">' +
              '<span>' + iconSvg('pin') + escapeHtml(stateLabel(job)) + '</span>' +
              '<span>' + dateMeta + '</span>' +
              deadlineMeta +
            '</div>' +
            jcEligibilityHtml(job) +
            '<div class="jc-skills">' + chips + '</div>' +
          '</div>' +
          logoFigureHtml(job, 'card') +
        '</div>' +
        '<div class="jc-actions" aria-label="Save or share this job">' +
          '<button class="jc-action jc-save' + (saved ? ' is-saved' : '') + '" type="button" data-save-id="' + escapeHtml(job.id) + '" aria-pressed="' + (saved ? 'true' : 'false') + '">' +
            '<span aria-hidden="true">★</span> <span class="save-label">' + (saved ? 'Saved' : 'Save') + '</span>' +
          '</button>' +
          '<a class="jc-action jc-wa" href="' + waShareHref + '" target="_blank" rel="noopener noreferrer" aria-label="Share on WhatsApp">' + iconSvg('whatsapp') + ' WhatsApp</a>' +
          '<button class="jc-action" type="button" data-share-id="' + escapeHtml(job.id) + '" aria-label="Share this job">Share ↗</button>' +
        '</div>' +
        '<div class="jc-foot">' +
          '<span class="jc-date">' + footDate + '</span>' +
          '<a class="jc-view" href="' + escapeHtml(detailHref) + '">' + ctaLabel + ' ' + iconSvg('arrow') + '</a>' +
        '</div>' +
      '</article>';
  }

  /* ------------------------------------------------------------------ */
  /* SEO directory (state & sector landing links)                        */
  /* ------------------------------------------------------------------ */
  function renderSeoDirectory() {
    /* Sector links are static in the HTML for crawlability; enrich with counts. */
    try {
      var byCategory = state.stats && state.stats.by_category ? state.stats.by_category : null;
      if (byCategory && els.seoCategories) {
        var slugToCategory = {};
        Object.keys(CATEGORY_SLUGS).forEach(function (name) {
          slugToCategory[CATEGORY_SLUGS[name]] = name;
        });
        Array.prototype.forEach.call(els.seoCategories.querySelectorAll('a'), function (link) {
          if (link.querySelector('.seo-cnt')) return;
          var href = link.getAttribute('href') || '';
          var match = href.match(/category=([^&]+)/);
          var category = match ? slugToCategory[decodeURIComponent(match[1])] : null;
          var entry = category ? byCategory[category] : null;
          if (!entry || typeof entry.active !== 'number') return;
          var cnt = document.createElement('span');
          cnt.className = 'seo-cnt';
          cnt.textContent = entry.active;
          link.appendChild(cnt);
        });
      }
    } catch (e) { /* directory counts are optional */ }

    if (!els.seoStates) return;
    var counts = {};
    if (state.stats && state.stats.by_state && typeof state.stats.by_state === 'object') {
      counts = state.stats.by_state;
    } else {
      state.jobs.forEach(function (j) {
        if (j.state && j.state !== 'Multiple States / Remote') {
          counts[j.state] = (counts[j.state] || 0) + 1;
        }
      });
    }
    var states = Object.keys(counts);
    if (!states.length) {
      els.seoStates.innerHTML = '<li class="seo-loading">No regional records yet.</li>';
      return;
    }
    states.sort(function (a, b) { return (counts[b] - counts[a]) || a.localeCompare(b); });
    els.seoStates.innerHTML = states.map(function (s) {
      return '<li><a href="?state=' + encodeURIComponent(s) + '">' + escapeHtml(s) +
        ' <span class="seo-cnt">' + counts[s] + '</span></a></li>';
    }).join('');
  }

  /* ------------------------------------------------------------------ */
  /* Routing (?job= / ?view= / ?state= / ?category= + #/job/ legacy)     */
  /* ------------------------------------------------------------------ */
  function getJobIdFromUrl() {
    try {
      var params = new URLSearchParams(window.location.search || '');
      var queryId = params.get('job');
      if (queryId) return queryId.trim();
    } catch (e) { /* URLSearchParams unavailable: fall through to the path form */ }

    var pathMatch = (window.location.pathname || '').match(/^\/jobs\/([A-Za-z0-9._-]+)\/?$/);
    if (pathMatch) return decodeURIComponent(pathMatch[1]);

    var hash = window.location.hash || '';
    var match = hash.match(/^#\/job\/([A-Za-z0-9._-]+)/);
    return match ? decodeURIComponent(match[1]) : null;
  }

  function setUrlQuietly(path) {
    if (window.history && window.history.replaceState) {
      try { window.history.replaceState({}, '', path); } catch (e) { /* ignore */ }
    }
  }

  /* -------------------------- Feed scroll memory -------------------------- */
  function sessionGet(key) {
    try { return window.sessionStorage.getItem(key); } catch (e) { return null; }
  }
  function sessionSet(key, value) {
    try { window.sessionStorage.setItem(key, String(value)); } catch (e) { /* private mode */ }
  }
  function sessionRemove(key) {
    try { window.sessionStorage.removeItem(key); } catch (e) { /* ignore */ }
  }

  function scrollToTopInstant() {
    try {
      window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
    } catch (e) {
      window.scrollTo(0, 0);
    }
  }

  function saveFeedScroll(jobId) {
    var y = window.pageYOffset || document.documentElement.scrollTop || window.scrollY || 0;
    sessionSet(SCROLL_KEY, Math.max(0, Math.round(y)));
    sessionSet(SCROLL_JOB_KEY, jobId);
    sessionSet(RETURN_FLAG, '1');
  }

  /* Restore only after the feed has been re-rendered and laid out. The
     double requestAnimationFrame is deliberate: the first frame lets the
     feed become visible, the second measures the final document height. */
  function restoreFeedScroll() {
    var saved = sessionGet(SCROLL_KEY);
    var y = parseInt(saved, 10);
    sessionRemove(RETURN_FLAG);
    if (isNaN(y) || y <= 0) return;
    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(function () {
        try {
          window.scrollTo({ top: y, left: 0, behavior: 'instant' });
        } catch (e) {
          window.scrollTo(0, y);
        }
      });
    });
  }

  /* A full page load back to "/" (for example the header logo) should also
     return the reader to the feed position they left. */
  function restoreFeedScrollOnLoad() {
    if (getJobIdFromUrl()) return;
    if (sessionGet(RETURN_FLAG) !== '1') return;
    restoreFeedScroll();
  }

  function goHome() {
    var path = '/' + queryForState();
    if (window.history && window.history.pushState) {
      try {
        window.history.pushState({}, '', path);
        route(false);
        return;
      } catch (e) { /* fall through to hash routing */ }
    }
    window.location.hash = '';
  }

  function route(initial) {
    var wasDetail = !!state.detailId;
    var id = getJobIdFromUrl();
    if (id) {
      var found = findJob(id);
      if (found) {
        state.detailId = id;
        /* Keep the jurisdiction + view switchers aligned with the record. */
        var wantedView = found.archived ? 'archive' : 'active';
        var wantedRegistry = found.registry || 'india';
        if (state.view !== wantedView || state.registry !== wantedRegistry) {
          state.view = wantedView;
          state.registry = wantedRegistry;
          syncRegistryChrome();
          syncViewChrome();
          updateTabCounts();
          renderTelemetry();
          populateStateSelect();
          refreshCategoryPills();
          refreshTrackButtons();
        }
        renderDetail(found.job, found.archived);
        document.body.classList.add('view-detail');
        /* Upgrade legacy ?job=<id> links to the clean static job URL. */
        if (window.location.pathname.indexOf('/jobs/') !== 0) {
          setUrlQuietly('/' + jobPath(id).replace(/^\//, ''));
        }
        /* The dossier always opens at its own beginning, never at the
           feed offset the reader came from. */
        scrollToTopInstant();
        updateSeoForJob(found.job, found.archived);
        return;
      }
      /* Unknown job id — clean the URL and fall back to the registry */
      if (state.loaded) {
        toast('That registry record was not found.');
        setUrlQuietly(window.location.pathname + queryForState());
      }
    }
    state.detailId = null;
    document.body.classList.remove('view-detail');
    hideMobileActionBar();
    updateViewSeo();
    if (wasDetail) restoreFeedScroll();
  }

  function openJob(id) {
    if (state.detailId === id) return;
    /* Capture the feed offset before the DOM switches to dossier mode.
       Opening a related role from inside a dossier must not overwrite the
       position the reader originally came from. */
    if (!state.detailId) saveFeedScroll(id);
    var url = jobPath(id);
    if (window.history && window.history.pushState) {
      try {
        window.history.pushState({ jobId: id }, '', url);
        route(false);
        return;
      } catch (e) { /* pushState unavailable (e.g. file://): use the hash fallback */ }
    }
    window.location.hash = '#/job/' + encodeURIComponent(id);
  }

  /* ------------------------------------------------------------------ */
  /* Position dossier (detail view)                                      */
  /* ------------------------------------------------------------------ */
  /* Position-type / qualification / compensation block for a dossier. */
  function eligibilitySectionHtml(job) {
    var rows = '' +
      '<div><dt>' + t('detail.pt', 'Position Type') + '</dt><dd>' + escapeHtml(positionTypeOf(job)) + '</dd></div>' +
      '<div><dt>' + t('detail.kind', 'Opportunity Type') + '</dt><dd>' + escapeHtml(opportunityKindOf(job)) + '</dd></div>' +
      '<div><dt>' + t('detail.engagement', 'Engagement') + '</dt><dd>' + escapeHtml(employmentTypeLabel(job)) + '</dd></div>';
    if (deadlineOf(job)) {
      rows += '<div><dt>' + t('detail.deadline', 'Deadline / Window') + '</dt><dd>' + escapeHtml(deadlineOf(job)) + '</dd></div>';
    }
    if (job.region && (job.country || job.city)) {
      rows += '<div><dt>' + t('detail.region', 'Region') + '</dt><dd>' + escapeHtml((job.country ? job.country + ' \u00b7 ' : '') + job.region) + '</dd></div>';
    }
    if (job.qualification_summary) {
      rows += '<div><dt>' + t('detail.qualification', 'Qualification') + '</dt><dd>' + escapeHtml(job.qualification_summary) + '</dd></div>';
    }
    if (job.compensation_or_fellowship) {
      rows += '<div><dt>' + t('detail.comp', 'Compensation / Fellowship') + '</dt><dd>' + escapeHtml(job.compensation_or_fellowship) + '</dd></div>';
    }
    if (job.academic_meta && job.academic_meta.net_gate) {
      rows += '<div><dt>NET / GATE</dt><dd>' + escapeHtml(job.academic_meta.net_gate) + '</dd></div>';
    }
    if (job.selection_process) {
      rows += '<div><dt>Selection Process</dt><dd>' + escapeHtml(job.selection_process) + '</dd></div>';
    }
    return '' +
      '<div class="detail-section">' +
        '<h2>' + t('detail.elig.h2', 'Position &amp; Eligibility') + '</h2>' +
        '<dl class="elig-grid">' + rows + '</dl>' +
      '</div>';
  }

  function employmentTypeLabel(job) {
    var type = employmentTypeFor(job);
    if (type === 'CONTRACTOR') return 'Contractual / Project Engagement';
    if (type === 'INTERN') return 'Fellowship / Internship';
    return 'Full-Time';
  }

  function detailBreadcrumbHtml(job, isArchived) {
    var categorySlug = CATEGORY_SLUGS[job.category] || job.category;
    var middle = isArchived
      ? '<a href="' + CONFIG.SITE_URL + '?view=archive">' + t('detail.crumb.archive', 'Historical Archive') + '</a>'
      : '<a href="' + CONFIG.SITE_URL + '?category=' + encodeURIComponent(categorySlug) + '">' + escapeHtml(job.category) + '</a>';
    return '<nav class="job-crumbs" aria-label="Breadcrumb">' +
      '<a href="' + CONFIG.SITE_URL + '">' + t('detail.crumb.home', 'Career Registry') + '</a>' +
      '<span aria-hidden="true">/</span>' + middle +
      '<span aria-hidden="true">/</span><span aria-current="page">' + escapeHtml(displayTitle(job)) + '</span>' +
    '</nav>';
  }

  function renderDetail(job, isArchived) {
    var skills = (job.must_have_skills || []).map(function (s) {
      return '<span class="skill-chip">' + escapeHtml(s) + '</span>';
    }).join('');

    var responsibilities = (job.key_responsibilities || []).map(function (r) {
      return '<li>' + formatReadableText(r) + '</li>';
    }).join('');

    var shareUrl = shareableUrl(job.id);
    var waHref = 'https://wa.me/?text=' + encodeURIComponent(job.clean_title + ' at ' + job.organization + ' \u2014 ' + shareUrl);
    var liHref = 'https://www.linkedin.com/sharing/share-offsite/?url=' + encodeURIComponent(shareUrl);
    var backLabel = isArchived
      ? t('detail.back.archive', 'Historical Archive')
      : t('detail.back.active', 'Active Opportunities');

    var banner = '';
    if (isArchived) {
      banner = '' +
        '<div class="archive-banner" role="note">' +
          '<span class="archive-flag">' + t('card.archived', 'Archived') + '</span>' +
          '<p><strong>' + t('detail.banner.archived', 'Archived Job:') + '</strong> ' +
            t('detail.banner.body', 'the application window for this position closed on {date}. This record is maintained in the Urban Forest Park Career Registry for compensation, skill, and institutional reference.', { date: formatLongDate(job.date_archived || job.valid_through || job.date_added) }) +
          '</p>' +
        '</div>';
    }

    var archiveBadge = isArchived ? '<span class="badge badge-archived">' + iconSvg('archive') + t('detail.archive.badge', 'Archived Record') + '</span>' : '';

    var dateLine = isArchived
      ? '<span>' + iconSvg('clock') + escapeHtml(formatClosed(job.date_archived)) + '</span>'
      : '<span>' + iconSvg('calendar') + escapeHtml(formatPosted(job.date_added)) + '</span>';

    var applyBlock = verifyCardHtml(job, isArchived);
    var saved = isSaved(job.id);

    var suggestions = isArchived ? suggestionsHtml(job) : '';

    els.detail.innerHTML = '' +
      detailBreadcrumbHtml(job, isArchived) +
      '<div class="detail-topbar">' +
        '<a class="back-link" href="#" data-action="back">' + iconSvg('back') + ' ' + backLabel + '</a>' +
        '<div class="share-row">' +
          '<button class="share-btn share-save' + (saved ? ' is-saved' : '') + '" type="button" data-action="save" data-save-id="' + escapeHtml(job.id) + '" aria-pressed="' + (saved ? 'true' : 'false') + '">' +
            '<span aria-hidden="true">★</span> <span class="save-label">' + (saved ? 'Saved' : 'Save') + '</span>' +
          '</button>' +
          '<a class="share-btn share-whatsapp" href="' + waHref + '" target="_blank" rel="noopener noreferrer">' + iconSvg('whatsapp') + t('detail.share.wa', 'Share on WhatsApp') + '</a>' +
          '<a class="share-btn share-linkedin" href="' + liHref + '" target="_blank" rel="noopener noreferrer">' + iconSvg('linkedin') + t('detail.share.li', 'Share on LinkedIn') + '</a>' +
          '<button class="share-btn share-copy" type="button" data-action="share-card" title="Copies a 4-line share card with the direct job link">' + iconSvg('copy') + t('detail.share.card', 'Share ↗') + '</button>' +
          '<button class="share-btn share-copy" type="button" data-action="copy" title="Copies the direct job link">' + t('detail.share.link', 'Copy Link') + '</button>' +
        '</div>' +
      '</div>' +

      banner +

      '<div class="detail-card">' +
        '<div class="detail-head">' +
          '<div class="detail-head-main">' +
            '<div class="detail-kicker">' +
              '<span class="badge ' + catClass(job.category) + '">' + escapeHtml(job.category) + '</span>' +
              '<span class="badge badge-type">' + escapeHtml(positionTypeOf(job)) + '</span>' +
              (opportunityKindOf(job) !== 'Job / Career' ? '<span class="badge badge-kind">' + escapeHtml(opportunityKindOf(job)) + '</span>' : '') +
              '<span class="badge badge-exp">' + escapeHtml(job.experience_level || '') + '</span>' +
              '<span class="badge badge-state">' + iconSvg('pin') + escapeHtml(stateLabel(job)) + '</span>' +
              archiveBadge +
            '</div>' +

            '<h1>' + escapeHtml(displayTitle(job)) + '</h1>' +
            (isHindi() && job.title_hi ? '<p class="detail-title-en">' + escapeHtml(job.clean_title) + '</p>' : '') +
            '<p class="detail-org">' + escapeHtml(job.organization) + '</p>' +
            '<div class="detail-meta">' +
              dateLine +
              '<span>' + t('detail.ref', 'Ref: ') + escapeHtml(String(job.id).slice(0, 24)) + '</span>' +
              (isArchived ? '<span>' + t('detail.archived.on', 'Archived ') + escapeHtml(job.date_archived || '') + '</span>' : '<span>' + t('detail.valid', 'Valid through ') + escapeHtml(job.valid_through || '') + '</span>') +
            '</div>' +
          '</div>' +
          logoFigureHtml(job, 'detail') +
        '</div>' +

        (isHindi() && job.summary_hi
          ? '<div class="detail-section detail-section-hi">' +
              '<h2>' + t('detail.summaryhi.h2', '\u0939\u093f\u0902\u0926\u0940 \u0938\u093e\u0930\u093e\u0902\u0936') + '</h2>' +
              '<p>' + formatReadableText(job.summary_hi) + '</p>' +
            '</div>'
          : '') +
        '<div class="detail-section">' +
          '<h2>' + t('detail.summary.h2', 'Job Summary') + '</h2>' +
          '<p>' + formatReadableText(job.role_summary) + '</p>' +
        '</div>' +

        communityCalloutHtml(job) +

        eligibilitySectionHtml(job) +

        '<div class="detail-section">' +
          '<h2>' + t('detail.resp.h2', 'Core Responsibilities') + '</h2>' +
          '<ul class="resp-list">' + responsibilities + '</ul>' +
        '</div>' +

        '<div class="detail-section">' +
          '<h2>' + t('detail.skills.h2', 'Required Competencies') + '</h2>' +
          '<div class="skills-wrap">' + skills + '</div>' +
        '</div>' +

        '<div class="tip-callout">' +
          '<span class="tip-title">' + iconSvg('bulb') + ' ' + t('detail.tip', 'Candidate Advisory') + '</span>' +
          '<p>' + formatReadableText(job.application_tip) + '</p>' +
        '</div>' +

        applyBlock +

        '<div class="detail-foot">' +
          '<a class="back-link" href="#" data-action="back">' + iconSvg('back') + ' ' + t('detail.foot.back', 'Back to ') + backLabel + '</a>' +
          '<div class="share-row">' +
            '<a class="share-btn share-whatsapp" href="' + waHref + '" target="_blank" rel="noopener noreferrer">WhatsApp</a>' +
            '<a class="share-btn share-linkedin" href="' + liHref + '" target="_blank" rel="noopener noreferrer">LinkedIn</a>' +
          '</div>' +
        '</div>' +
      '</div>' +

      suggestions;

    updateMobileActionBar(job, isArchived);
  }

  function updateMobileActionBar(job, isArchived) {
    var bar = document.getElementById('mobile-action-bar');
    if (!bar) return;
    bar.hidden = false;
    var saveBtn = bar.querySelector('[data-action="save-current"]');
    if (saveBtn) {
      var on = isSaved(job.id);
      saveBtn.setAttribute('data-save-id', String(job.id));
      saveBtn.classList.toggle('is-saved', on);
      saveBtn.setAttribute('aria-pressed', on ? 'true' : 'false');
      var label = saveBtn.querySelector('.save-label');
      if (label) label.textContent = on ? 'Saved' : 'Save';
    }
    var apply = bar.querySelector('[data-mobile-apply]');
    if (apply) {
      if (!isArchived && job.apply_url) {
        apply.href = job.apply_url;
        apply.hidden = false;
        apply.innerHTML = 'Apply on Portal ' + iconSvg('external');
      } else {
        apply.removeAttribute('href');
        apply.hidden = true;
      }
    }
  }

  function hideMobileActionBar() {
    var bar = document.getElementById('mobile-action-bar');
    if (bar) bar.hidden = true;
  }

  /* Up to 3 currently active mandates in the same sector or state. */
  function suggestionsHtml(job) {
    var matches = state.jobs.filter(function (j) {
      return j.category === job.category || j.state === job.state;
    }).sort(function (a, b) {
      return String(b.date_added || '').localeCompare(String(a.date_added || ''));
    }).slice(0, 3);

    if (!matches.length) return '';

    var cards = matches.map(function (j) {
      return '' +
        '<article class="suggest-card" data-job-id="' + escapeHtml(j.id) + '" tabindex="0" role="link" ' +
          'aria-label="' + t('detail.suggest.aria', 'View active position: ') + escapeHtml(displayTitle(j)) + ' at ' + escapeHtml(j.organization) + '">' +
          '<span class="sc-title">' + escapeHtml(displayTitle(j)) + '</span>' +
          '<span class="sc-org">' + escapeHtml(j.organization) + ' &middot; ' + escapeHtml(stateLabel(j)) + '</span>' +
          '<span class="sc-meta"><span>' + escapeHtml(j.category) + '</span><span>Listed ' + escapeHtml(j.date_added || '') + '</span></span>' +
        '</article>';
    }).join('');

    return '' +
      '<div class="suggest-block">' +
        '<h3>' + t('detail.suggest.h3', 'Currently Active Positions in This Sector') + '</h3>' +
        '<div class="suggest-grid">' + cards + '</div>' +
      '</div>';
  }

  function shareableUrl(id) {
    return CONFIG.SITE_URL.replace(/\/$/, '') + jobPath(id);
  }

  function copyShareLink(event) {
    event.preventDefault();
    var id = state.detailId;
    if (!id) return;
    var url = shareableUrl(id);
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(function () { toast('Direct link copied'); },
        function () { fallbackCopy(url); });
    } else {
      fallbackCopy(url);
    }
  }

  function fallbackCopy(text, message) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); toast(message || 'Direct link copied'); }
    catch (e) { toast('Copy failed \u2014 please copy from the address bar'); }
    document.body.removeChild(ta);
  }

  function copyTextToClipboard(text, okMessage) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(
        function () { toast(okMessage); },
        function () { fallbackCopy(text, okMessage); }
      );
    } else {
      fallbackCopy(text, okMessage);
    }
  }

  /* (Broadcast & LinkedIn roundup copy buttons were moved into the
     discreet internal Syndication Desk drawer — js/syndication-drawer.js.) */

  /* ------------------------------------------------------------------ */
  /* Dynamic SEO: titles, meta, canonical & schema.org lifecycle         */
  /* ------------------------------------------------------------------ */
  function setMeta(selector, attr, value) {
    var el = document.querySelector(selector);
    if (el) el.setAttribute(attr, value);
  }

  function applyMetaBlock(title, desc, url) {
    document.title = title;
    setMeta('meta[name="description"]', 'content', desc);
    setMeta('link[rel="canonical"]', 'href', url);
    setMeta('meta[property="og:title"]', 'content', title);
    setMeta('meta[property="og:description"]', 'content', desc);
    setMeta('meta[property="og:url"]', 'content', url);
    setMeta('meta[name="twitter:title"]', 'content', title);
    setMeta('meta[name="twitter:description"]', 'content', desc);
  }

  /* Registry feed / filtered landing view SEO. */
  function updateViewSeo() {
    if (state.detailId) return;
    var isGlobal = state.registry === 'global';
    var hasState = state.state !== 'all';
    var hasCat = state.category !== 'all';
    var hasRegion = isGlobal && state.region !== 'all';
    var hasKind = state.kind !== 'all';
    var isArchive = state.view === 'archive';

    var hasTrack = state.track !== 'all';
    var trackLabel = '';
    if (hasTrack) {
      TRACK_META.forEach(function (t) { if (t.id === state.track) trackLabel = t.label; });
    }

    var title = DEFAULT_TITLE;
    var desc = DEFAULT_DESC;
    var url = CONFIG.SITE_URL;
    /* The hero heading is jurisdiction-aware: the Global registry keeps its
       own title, so late SEO passes never overwrite it with the India hero. */
    var heroHtml = isGlobal
      ? t('hero.global.title_html', 'Worldwide <span class="accent">Climate &amp; Sustainability</span> Opportunities')
      : heroDefaultHtml();
    var heroText = null;
    var feedEyebrow = t('feed.eyebrow', 'Active Environmental Jobs');
    var feedTitle = t('feed.title', 'Active Jobs & Fellowships');

    if (isGlobal) {
      feedEyebrow = t('feed.eyebrow.global', 'Global Opportunities Registry');
      feedTitle = t('feed.title.global', 'International Opportunities');
      title = 'Global Climate & Sustainability Opportunities \u2014 International Jobs, Grants & Scholarships | Urban Forest Park';
      desc = 'Verified international climate, forestry, ESG, conservation and development opportunities from UN bodies, multilateral funds and global institutions \u2014 each with a direct application link.';
      url = CONFIG.SITE_URL + queryForState();
      if (hasRegion || hasKind) {
        var globalScope = hasKind ? state.kind : 'Global Opportunities';
        heroText = globalScope + ' \u2014 ' + (hasRegion ? state.region : 'Worldwide');
        title = globalScope + (hasRegion ? ' in ' + state.region : ' Worldwide') + ' | Urban Forest Park';
        desc = 'Live ' + globalScope.toLowerCase() + ' opportunities' +
          (hasRegion ? ' across ' + state.region : ' worldwide') +
          ' \u2014 verified international listings with direct application links.';
      }
      if (hasKind) feedTitle = state.kind;
    } else if (isArchive) {
      feedEyebrow = t('feed.eyebrow.archive', 'Historical Job Archive');
      feedTitle = t('feed.title.archive', 'Archived / Past Positions');
      title = 'Historical Job Archive \u2014 Past Climate, Forestry, ESG & GIS Jobs | Urban Forest Park';
      desc = 'Archived climate, forestry, ESG, carbon-market and geospatial jobs' +
        (hasState ? ' in ' + state.state : '') +
        (hasCat ? ' (\u2018' + state.category + '\u2019 sector)' : '') +
        ', preserved in the Urban Forest Park career registry for institutional reference.';
      if (hasCat || hasState) {
        feedTitle = t('feed.title.archive', 'Archived / Past Positions');
        heroText = 'Historical Job Archive \u2014 ' + (hasCat ? state.category : '') +
          (hasCat && hasState ? ' \u00b7 ' : '') + (hasState ? state.state : '');
      }
      url = CONFIG.SITE_URL + queryForState();
    } else if (hasTrack && !hasCat && !hasState) {
      title = trackLabel + ' Jobs in India | Urban Forest Park';
      desc = 'Current ' + trackLabel.toLowerCase() + ' opportunities across India \u2014 verified listings with direct application links, maintained by the Urban Forest Park registry.';
      heroText = trackLabel + ' \u2014 India';
      feedTitle = trackLabel;
      url = CONFIG.SITE_URL + queryForState();
    } else if (hasCat || hasState) {
      var scope = hasState ? state.state : 'India';
      title = (hasCat ? state.category : 'Climate, Forestry, ESG & GIS') + ' Jobs in ' + scope + ' | Urban Forest Park';
      desc = 'Active ' + (hasCat ? state.category.toLowerCase() + ' ' : '') + 'positions' +
        (hasState ? ' across ' + state.state : ' across India') +
        ' \u2014 verified listings with direct application links, maintained by the Urban Forest Park registry.';
      heroText = hasCat
        ? state.category + ' Jobs \u2014 ' + (hasState ? state.state : 'All India')
        : 'Environmental, Forestry, JRF, GIS & ESG Jobs \u2014 ' + state.state;
      feedTitle = hasCat ? state.category : t('feed.title', 'Active Jobs & Fellowships');
      url = CONFIG.SITE_URL + queryForState();
    }

    applyMetaBlock(title, desc, url);

    if (els.heroHeading) {
      if (heroText) els.heroHeading.textContent = heroText;
      else els.heroHeading.innerHTML = heroHtml;
    }
    setText('feed-eyebrow', feedEyebrow);
    setText('feed-title', feedTitle);
  }

  /* Position dossier SEO: JobPosting for active mandates, WebPage +
     BreadcrumbList for archived records (no stale JobPosting schema). */
  function updateSeoForJob(job, isArchived) {
    var desc = (job.role_summary || '').slice(0, 158);
    var url = shareableUrl(job.id);
    var title;

    if (isArchived) {
      title = 'Archived: ' + job.clean_title + ' \u2014 ' + job.organization + ' | Urban Forest Park Archive';
      injectJsonLd(webPageSchema(job), 'job-webpage-jsonld');
      removeJsonLd('job-posting-jsonld');
    } else {
      title = job.clean_title + ' \u2014 ' + job.organization + ' | Urban Forest Park Registry';
      injectJsonLd(jobPostingSchema(job), 'job-posting-jsonld');
      removeJsonLd('job-webpage-jsonld');
    }
    injectJsonLd(breadcrumbSchema(job, isArchived), 'job-breadcrumb-jsonld');

    applyMetaBlock(title, desc, url);
    setText('feed-eyebrow', isArchived ? 'Historical Job Archive' : 'Active Environmental Jobs');
    setText('feed-title', isArchived ? 'Archived / Past Positions' : 'Active Jobs & Fellowships');
  }

  function jobPostingSchema(job) {
    var validThrough = job.valid_through;
    if (!validThrough) {
      var posted = new Date(job.date_added + 'T00:00:00');
      if (!isNaN(posted.getTime())) {
        validThrough = localIso(new Date(posted.getTime() + CONFIG.VALID_DAYS * 86400000));
      }
    }

    var descriptionHtml = '' +
      '<p>' + escapeHtml(job.role_summary) + '</p>' +
      '<h3>Core Responsibilities</h3><ul>' +
      (job.key_responsibilities || []).map(function (r) { return '<li>' + escapeHtml(r) + '</li>'; }).join('') +
      '</ul><h3>Required Competencies</h3><ul>' +
      (job.must_have_skills || []).map(function (s) { return '<li>' + escapeHtml(s) + '</li>'; }).join('') +
      '</ul>';

    var schema = {
      '@context': 'https://schema.org',
      '@type': 'JobPosting',
      title: job.clean_title,
      description: descriptionHtml,
      identifier: {
        '@type': 'PropertyValue',
        name: 'Urban Forest Park Career Registry',
        value: job.id
      },
      datePosted: job.date_added,
      validThrough: validThrough,
      employmentType: employmentTypeFor(job),
      hiringOrganization: {
        '@type': 'Organization',
        name: job.organization,
        sameAs: (function () {
          var orgUrl = job.org_website || job.apply_url || '';
          if (orgUrl && !/^https?:/i.test(orgUrl)) orgUrl = 'https://' + orgUrl;
          return orgUrl || undefined;
        })()
      },
      industry: job.category || 'Environmental Services',
      occupationalCategory: job.category || undefined,
      jobLocation: {
        '@type': 'Place',
        address: {
          '@type': 'PostalAddress',
          addressLocality: job.city || '',
          addressRegion: job.state || '',
          addressCountry: job.country || 'IN'
        }
      },
      directApply: false,
      qualifications: job.qualification_summary || undefined,
      educationRequirements: job.qualification_summary ? {
        '@type': 'EducationalOccupationalCredential',
        credentialCategory: job.qualification_summary
      } : undefined,
      url: shareableUrl(job.id)
    };

    if (job.state === 'Multiple States / Remote') {
      schema.jobLocationType = 'TELECOMMUTE';
      schema.applicantLocationRequirements = { '@type': 'Country', name: 'India' };
    }

    return schema;
  }

  function webPageSchema(job) {
    return {
      '@context': 'https://schema.org',
      '@type': 'WebPage',
      name: job.clean_title + ' \u2014 ' + job.organization + ' (Archived Job)',
      description: (job.role_summary || '').slice(0, 158),
      url: shareableUrl(job.id),
      dateModified: job.date_archived || undefined,
      isPartOf: {
        '@type': 'WebSite',
        name: 'Urban Forest Park \u2014 National Career Registry (India)',
        url: CONFIG.SITE_URL
      },
      about: { '@type': 'Organization', name: job.organization },
      significantLink: CONFIG.SITE_URL + '?view=archive'
    };
  }

  function breadcrumbSchema(job, isArchived) {
    var categorySlug = CATEGORY_SLUGS[job.category] || job.category;
    var middle = isArchived
      ? { name: 'Historical Archive', item: CONFIG.SITE_URL + '?view=archive' }
      : { name: job.category, item: CONFIG.SITE_URL + '?category=' + encodeURIComponent(categorySlug) };
    return {
      '@context': 'https://schema.org',
      '@type': 'BreadcrumbList',
      itemListElement: [
        { '@type': 'ListItem', position: 1, name: 'Career Registry', item: CONFIG.SITE_URL },
        { '@type': 'ListItem', position: 2, name: middle.name, item: middle.item },
        { '@type': 'ListItem', position: 3, name: job.clean_title, item: shareableUrl(job.id) }
      ]
    };
  }

  function injectJsonLd(schema, id) {
    removeJsonLd(id);
    var script = document.createElement('script');
    script.type = 'application/ld+json';
    script.id = id;
    script.textContent = JSON.stringify(schema);
    document.head.appendChild(script);
  }

  function removeJsonLd(id) {
    var existing = document.getElementById(id);
    if (existing && existing.parentNode) existing.parentNode.removeChild(existing);
  }

  function injectFeedJsonLd(jobs) {
    if (document.getElementById('feed-jobs-jsonld')) return;
    jobs = (jobs || []).filter(function (job) {
      return entrySectionOf(job) !== 'hidden';
    });
    var schema = {
      '@context': 'https://schema.org',
      '@type': 'ItemList',
      name: 'Environmental, Forestry, JRF, GIS & ESG Jobs in India (2026)',
      numberOfItems: jobs.length,
      itemListElement: jobs.slice(0, 20).map(function (job, i) {
        return {
          '@type': 'ListItem',
          position: i + 1,
          name: job.clean_title + ' \u2014 ' + job.organization,
          url: shareableUrl(job.id)
        };
      })
    };
    var script = document.createElement('script');
    script.type = 'application/ld+json';
    script.id = 'feed-jobs-jsonld';
    script.textContent = JSON.stringify(schema);
    document.head.appendChild(script);
  }

  /* ------------------------------------------------------------------ */
  /* Night / light mode                                                  */
  /* ------------------------------------------------------------------ */
  function applyTheme(theme, announce) {
    document.documentElement.setAttribute('data-theme', theme);
    var meta = document.getElementById('meta-theme-color');
    if (meta) meta.setAttribute('content', theme === 'dark' ? '#0B0F17' : '#F8FAFC');
    var label = document.getElementById('theme-label');
    if (label) label.textContent = theme === 'dark' ? t('theme.light', 'Light') : t('theme.night', 'Night');
    var btn = els.themeToggle;
    if (btn) {
      btn.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
      btn.setAttribute('aria-label', theme === 'dark' ? t('theme.aria.light', 'Switch to light mode') : t('theme.aria', 'Switch to night mode'));
    }
    if (announce) toast(theme === 'dark' ? t('toast.dark', 'Night mode enabled') : t('toast.light', 'Light mode enabled'));
  }

  function initTheme() {
    var current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    applyTheme(current, false);

    if (els.themeToggle) {
      els.themeToggle.addEventListener('click', function () {
        var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        applyTheme(next, true);
        try { localStorage.setItem('ufp_theme', next); } catch (e) { /* private mode */ }
      });
    }

    /* Follow OS preference changes only while the user has never chosen. */
    if (window.matchMedia) {
      var mq = window.matchMedia('(prefers-color-scheme: dark)');
      var onChange = function (e) {
        var stored = null;
        try { stored = localStorage.getItem('ufp_theme'); } catch (err) { /* ignore */ }
        if (!stored) applyTheme(e.matches ? 'dark' : 'light', false);
      };
      if (mq.addEventListener) mq.addEventListener('change', onChange);
      else if (mq.addListener) mq.addListener(onChange);
    }
  }

  /* ------------------------------------------------------------------ */
  /* Institutional partnership modal                                     */
  /* ------------------------------------------------------------------ */
  function openModal() {
    if (!els.modal) return;
    els.modal.classList.remove('hidden');
    var first = els.modal.querySelector('input, textarea, button');
    if (first) first.focus();
  }

  function closeModal() {
    if (els.modal) els.modal.classList.add('hidden');
  }

  function submitModal(event) {
    event.preventDefault();
    var org = (document.getElementById('pj-org') || {}).value || '';
    var role = (document.getElementById('pj-role') || {}).value || '';
    var email = (document.getElementById('pj-email') || {}).value || '';
    var message = (document.getElementById('pj-message') || {}).value || '';

    var subject = 'Publish a vacancy on Urban Forest Park Registry: ' + (role || org);
    var body = [
      'Organisation: ' + org,
      'Position title: ' + role,
      'Contact email: ' + email,
      '',
      'Job details:',
      message,
      '',
      '\u2014 Sent from the Urban Forest Park career registry'
    ].join('\n');

    window.location.href = 'mailto:' + CONFIG.CONTACT_EMAIL +
      '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
    closeModal();
  }

  /* ------------------------------------------------------------------ */
  /* Instant hero search & recommendations (active + archived)           */
  /* ------------------------------------------------------------------ */
  /* Domain clusters power the "Related & Similar Positions" engine: a
     record's clusters are derived from its own text (title, category,
     position type, skills, qualification), and shared-cluster /
     shared-skill overlap drives the recommendations. */
  var SEARCH_CLUSTER_DEFS = [
    {
      id: 'geospatial',
      label: 'Geospatial, Remote Sensing & Earth Observation',
      terms: ['gis', 'remote sensing', 'earth engine', 'gee', 'satellite', 'spatial', 'lst',
        'urban heat island', 'uhi', 'qgis', 'arcgis', 'drone', 'lidar']
    },
    {
      id: 'forestry',
      label: 'Forestry, Wildlife & Ecology',
      terms: ['forestry', 'wildlife', 'afforestation', 'campa', 'biodiversity', 'ecology',
        'conservation', 'mangrove', 'agroforestry', 'botany', 'zoology', 'wii', 'icfre']
    },
    {
      id: 'academic',
      label: 'Academic & Research Careers',
      terms: ['jrf', 'srf', 'project associate', 'research associate', 'phd', 'postdoc',
        'fellowship', 'net', 'gate', 'stipend', 'young professional', 'faculty']
    },
    {
      id: 'esg',
      label: 'ESG, Carbon & Corporate Sustainability',
      terms: ['esg', 'brsr', 'carbon', 'carbon credits', 'dmrv', 'net zero', 'ghg',
        'sustainability', 'csr', 'ehs', 'climate risk', 'gri']
    },
    {
      id: 'climate',
      label: 'Climate, Water & Policy',
      terms: ['climate policy', 'think tank', 'adaptation', 'mitigation', 'water', 'wash',
        'clean energy', 'renewable', 'solar', 'circular economy', 'agriculture']
    }
  ];

  var heroState = { open: false, items: [], activeIndex: -1 };

  function heroRefs() {
    return {
      root: document.getElementById('hero-search'),
      form: document.getElementById('hero-search-form'),
      input: document.getElementById('hero-search-input'),
      panel: document.getElementById('hero-search-panel')
    };
  }

  function recordKey(rec) {
    return rec.registry + ':' + (rec.archived ? 'a' : 'l') + ':' + rec.job.id;
  }

  /* Every loaded registry, tagged with its jurisdiction and status. */
  function allRecords() {
    var out = [];
    state.jobs.forEach(function (job) { out.push({ job: job, archived: false, registry: 'india' }); });
    state.globalJobs.forEach(function (job) { out.push({ job: job, archived: false, registry: 'global' }); });
    state.archive.forEach(function (job) { out.push({ job: job, archived: true, registry: 'india' }); });
    state.globalArchive.forEach(function (job) { out.push({ job: job, archived: true, registry: 'global' }); });
    return out;
  }

  /* The searchable surface: exactly the fields the registry promises. */
  function searchBlobOf(job) {
    return [
      job.clean_title, job.title_hi, job.organization, job.state, job.city, job.region,
      job.country, job.category, job.position_type, job.opportunity_kind,
      job.qualification_summary, job.experience_level,
      (job.must_have_skills || []).join(' ')
    ].join(' ').toLowerCase();
  }

  function queryTokens(query) {
    return String(query || '').toLowerCase().split(/[^a-z0-9+#.]+/).filter(function (tok) {
      return tok.length >= 2;
    });
  }

  /* AND-scored direct match: every token must land somewhere, with
     title/organisation/skill hits outranking taxonomy and prose hits. */
  function scoreRecord(job, tokens) {
    var blob = searchBlobOf(job);
    var title = String(job.clean_title || '').toLowerCase();
    var org = String(job.organization || '').toLowerCase();
    var skills = (job.must_have_skills || []).join(' ').toLowerCase();
    var taxo = [job.category, job.position_type, job.opportunity_kind].join(' ').toLowerCase();
    var place = [job.state, job.city, job.region, job.country].join(' ').toLowerCase();
    var qual = String(job.qualification_summary || '').toLowerCase();
    var score = 0;
    for (var i = 0; i < tokens.length; i += 1) {
      var tok = tokens[i];
      if (blob.indexOf(tok) === -1) return 0;
      if (title.indexOf(tok) !== -1) score += 6;
      else if (org.indexOf(tok) !== -1) score += 5;
      else if (skills.indexOf(tok) !== -1) score += 4;
      else if (taxo.indexOf(tok) !== -1) score += 3;
      else if (place.indexOf(tok) !== -1) score += 2;
      else if (qual.indexOf(tok) !== -1) score += 1;
      else score += 1;
    }
    return score;
  }

  function recencyOf(rec) {
    return String(rec.job.date_added || rec.job.date_archived || '');
  }

  function directMatches(query, limit) {
    var tokens = queryTokens(query);
    if (!tokens.length) return [];
    var scored = [];
    allRecords().forEach(function (rec) {
      var score = scoreRecord(rec.job, tokens);
      if (score > 0) scored.push({ rec: rec, score: score });
    });
    if (!scored.length && tokens.length > 1) {
      /* Graceful partial fallback: rank on the strongest single token. */
      var single = tokens[0];
      allRecords().forEach(function (rec) {
        if (searchBlobOf(rec.job).indexOf(single) !== -1) scored.push({ rec: rec, score: 1 });
      });
    }
    scored.sort(function (a, b) {
      return b.score - a.score || recencyOf(b.rec).localeCompare(recencyOf(a.rec));
    });
    return scored.slice(0, limit || 6).map(function (entry) { return entry.rec; });
  }

  function clustersOfText(text) {
    var blob = String(text || '').toLowerCase();
    var found = [];
    SEARCH_CLUSTER_DEFS.forEach(function (cluster) {
      for (var i = 0; i < cluster.terms.length; i += 1) {
        if (blob.indexOf(cluster.terms[i]) !== -1) { found.push(cluster.id); break; }
      }
    });
    return found;
  }

  /* 3-5 relatable mandates: shared domain clusters, overlapping skills and
     the same category/type outrank the rest; active beats archived. */
  function relatedRecords(seedBlobs, excludeKeys, limit) {
    var clusterTally = {};
    var tokenTally = {};
    seedBlobs.forEach(function (blob) {
      clustersOfText(blob).forEach(function (id) { clusterTally[id] = (clusterTally[id] || 0) + 1; });
      String(blob || '').split(/[^a-z0-9+#.]+/).forEach(function (tok) {
        if (tok.length >= 4) tokenTally[tok] = (tokenTally[tok] || 0) + 1;
      });
    });
    var candidates = [];
    allRecords().forEach(function (rec) {
      if (excludeKeys[recordKey(rec)]) return;
      var blob = searchBlobOf(rec.job);
      var score = 0;
      clustersOfText(blob).forEach(function (id) { if (clusterTally[id]) score += 3; });
      var tokenScore = 0;
      String(blob || '').split(/[^a-z0-9+#.]+/).forEach(function (tok) {
        if (tok.length >= 4 && tokenTally[tok]) tokenScore += 2;
      });
      score += Math.min(tokenScore, 6);
      if (score > 0) candidates.push({ rec: rec, score: score });
    });
    candidates.sort(function (a, b) {
      if (b.score !== a.score) return b.score - a.score;
      var aArchived = a.rec.archived ? 1 : 0;
      var bArchived = b.rec.archived ? 1 : 0;
      if (aArchived !== bArchived) return aArchived - bArchived;   /* active first */
      return recencyOf(b.rec).localeCompare(recencyOf(a.rec));
    });
    return candidates.slice(0, limit || 5).map(function (entry) { return entry.rec; });
  }

  function latestRecords(limit) {
    var out = [];
    state.jobs.forEach(function (job) { out.push({ job: job, archived: false, registry: 'india' }); });
    state.globalJobs.forEach(function (job) { out.push({ job: job, archived: false, registry: 'global' }); });
    out.sort(function (a, b) { return recencyOf(b).localeCompare(recencyOf(a)); });
    return out.slice(0, limit || 6);
  }

  function heroRowHtml(rec, index) {
    var job = rec.job;
    var badge = rec.archived
      ? '<span class="hs-badge is-archived">' + t('hero.search.archived', 'ARCHIVED') + '</span>'
      : '<span class="hs-badge is-active">' + t('hero.search.active', 'ACTIVE') + '</span>';
    var region = rec.registry === 'global'
      ? '<span class="hs-region">\uD83C\uDF0D GLOBAL</span>'
      : '<span class="hs-region">\uD83C\uDDEE\uD83C\uDDF3 INDIA</span>';
    var taxonomy = String(job.category || '');
    if (job.position_type) taxonomy += ' \u00b7 ' + job.position_type;
    return '' +
      '<div class="hs-row" role="option" id="hs-opt-' + index + '" data-idx="' + index + '" ' +
        'data-job-id="' + escapeHtml(job.id) + '" aria-label="' + escapeHtml(displayTitle(job) + ' at ' + (job.organization || '')) + '">' +
        '<div class="hs-row-top">' +
          '<span class="hs-title">' + escapeHtml(displayTitle(job)) + '</span>' +
          badge +
        '</div>' +
        '<div class="hs-row-meta">' +
          '<span>' + escapeHtml(job.organization || '') + '</span>' +
          '<span>' + iconSvg('pin') + ' ' + escapeHtml(stateLabel(job)) + '</span>' +
          '<span>' + escapeHtml(taxonomy) + '</span>' +
          region +
        '</div>' +
      '</div>';
  }

  function registryMatchCounts(query) {
    var matches = directMatches(query, 400);
    var counts = { activeCurrent: 0, archivedCurrent: 0, activeOther: 0, archivedOther: 0 };
    matches.forEach(function (rec) {
      var sameRegistry = rec.registry === state.registry;
      if (sameRegistry && !rec.archived) counts.activeCurrent += 1;
      else if (sameRegistry && rec.archived) counts.archivedCurrent += 1;
      else if (!rec.archived) counts.activeOther += 1;
      else counts.archivedOther += 1;
    });
    return counts;
  }

  function renderHeroPanel() {
    var refs = heroRefs();
    if (!refs.panel || !refs.input) return;
    if (!state.loaded) {
      refs.panel.innerHTML = '<p class="hs-empty">' + t('hero.search.loading', 'Loading the registry\u2026') + '</p>';
      openHeroPanel();
      return;
    }

    var query = String(refs.input.value || '').trim();
    var isQuery = query.length >= 2;
    var matches = isQuery ? directMatches(query, 6) : latestRecords(6);
    var excluded = {};
    matches.forEach(function (rec) { excluded[recordKey(rec)] = true; });

    var seedBlobs = matches.map(function (rec) { return searchBlobOf(rec.job); });
    if (isQuery) seedBlobs.push(query.toLowerCase());
    var related = relatedRecords(seedBlobs, excluded, 5);

    var items = [];
    var html = '';

    html += '<p class="hs-group">' + (isQuery
      ? t('hero.search.direct', 'Direct Matches') + ' \u2014 ' + t('hero.search.directNote', 'Active &amp; Archived')
      : t('hero.search.latest', 'Latest Verified Jobs')) + '</p>';

    if (matches.length) {
      matches.forEach(function (rec) {
        html += heroRowHtml(rec, items.length);
        items.push(rec);
      });
    } else {
      html += '<p class="hs-empty">' + t('hero.search.none', 'No job matches that phrase. Try a skill, institution, state or category \u2014 related positions are listed below.') + '</p>';
    }

    if ((isQuery || related.length) && related.length) {
      html += '<p class="hs-group">' + t('hero.search.related', 'Related &amp; Similar Positions in This Field') + '</p>';
      related.forEach(function (rec) {
        html += heroRowHtml(rec, items.length);
        items.push(rec);
      });
    }

    if (isQuery) {
      var counts = registryMatchCounts(query);
      if (counts.activeCurrent === 0 && counts.archivedCurrent > 0) {
        html += '<div class="hs-foot">' +
          '<span>' + counts.archivedCurrent + ' archived reference record' + (counts.archivedCurrent === 1 ? '' : 's') + ' match in this registry.</span>' +
          '<button type="button" class="hs-foot-btn" data-hs-show-archive="1">' +
            t('hero.search.showArchive', 'Show archived matches') + ' \u2192</button>' +
        '</div>';
      } else if (counts.activeCurrent === 0 && counts.activeOther > 0) {
        html += '<div class="hs-foot">' +
          '<span>' + counts.activeOther + ' active match' + (counts.activeOther === 1 ? '' : 'es') + ' sit in the other jurisdiction.</span>' +
          '<button type="button" class="hs-foot-btn" data-hs-switch-registry="1">' +
            (state.registry === 'global' ? t('hero.search.switchIndia', 'Open the India registry') : t('hero.search.switchGlobal', 'Open the Global registry')) +
          ' \u2192</button>' +
        '</div>';
      }
    }

    refs.panel.innerHTML = html;
    heroState.items = items;
    heroState.activeIndex = -1;
    openHeroPanel();
  }

  function openHeroPanel() {
    var refs = heroRefs();
    if (!refs.panel || !refs.root) return;
    refs.panel.hidden = false;
    refs.root.classList.add('hs-open');
    if (refs.input) refs.input.setAttribute('aria-expanded', 'true');
    heroState.open = true;
  }

  function closeHeroPanel() {
    var refs = heroRefs();
    if (!refs.panel || !refs.root) return;
    refs.panel.hidden = true;
    refs.root.classList.remove('hs-open');
    if (refs.input) {
      refs.input.setAttribute('aria-expanded', 'false');
      refs.input.removeAttribute('aria-activedescendant');
    }
    heroState.open = false;
    heroState.activeIndex = -1;
  }

  function setHeroActiveIndex(index) {
    var refs = heroRefs();
    var rows = refs.panel ? refs.panel.querySelectorAll('.hs-row') : [];
    heroState.activeIndex = index;
    Array.prototype.forEach.call(rows, function (row, i) {
      row.classList.toggle('hs-active', i === index);
    });
    if (refs.input) {
      if (index >= 0 && rows[index]) {
        refs.input.setAttribute('aria-activedescendant', rows[index].id);
        if (rows[index].scrollIntoView) rows[index].scrollIntoView({ block: 'nearest' });
      } else {
        refs.input.removeAttribute('aria-activedescendant');
      }
    }
  }

  /* Pressing Enter (or the Search button) mirrors the query into the main
     feed filter. Archived-only matches switch the feed to the archive view;
     matches that only exist in the other jurisdiction switch registries. */
  function submitHeroSearch() {
    var refs = heroRefs();
    if (!refs.input || !state.loaded) return;
    var query = String(refs.input.value || '').trim();
    closeHeroPanel();

    state.query = query;
    var mainSearch = document.getElementById('jobs-search');
    if (mainSearch) mainSearch.value = query;

    if (query.length >= 2) {
      var counts = registryMatchCounts(query);
      if (counts.activeCurrent === 0 && counts.archivedCurrent > 0) {
        setView('archive', { keepUrl: true, force: true });
        toast(t('hero.search.toastArchive', 'No active matches \u2014 showing ') + counts.archivedCurrent +
          t('hero.search.toastArchive2', ' archived reference record(s) for \u201C') + query + '\u201D.');
      } else if (counts.activeCurrent === 0 && counts.activeOther > 0) {
        var target = state.registry === 'global' ? 'india' : 'global';
        setRegistry(target, { keepUrl: true, silent: true });
        setView('active', { keepUrl: true, force: true });
        toast(target === 'global'
          ? t('hero.search.toastGlobal', 'Showing matching Global Opportunities.')
          : t('hero.search.toastIndia', 'Showing matching India jobs.'));
      }
    }

    applyFilters();
    syncUrl(true);
    var feed = document.getElementById('filter-bar') || document.getElementById('jobs-feed');
    if (feed && feed.scrollIntoView) {
      feed.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  function openHeroResult(index) {
    var rec = heroState.items[index];
    if (!rec) return;
    closeHeroPanel();
    openJob(rec.job.id);
  }

  function bindHeroSearch() {
    var refs = heroRefs();
    if (!refs.form || !refs.input || !refs.panel) return;

    refs.form.addEventListener('submit', function (e) {
      e.preventDefault();
      submitHeroSearch();
    });

    refs.input.addEventListener('input', debounce(function () {
      renderHeroPanel();
    }, 120));

    refs.input.addEventListener('focus', function () {
      renderHeroPanel();
    });

    refs.input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        if (!heroState.open) { renderHeroPanel(); return; }
        e.preventDefault();
        var count = heroState.items.length;
        if (!count) return;
        var next = heroState.activeIndex + (e.key === 'ArrowDown' ? 1 : -1);
        if (next < 0) next = count - 1;
        if (next >= count) next = 0;
        setHeroActiveIndex(next);
        return;
      }
      if (e.key === 'Enter') {
        if (heroState.activeIndex >= 0) {
          e.preventDefault();
          openHeroResult(heroState.activeIndex);
        }
        return;   /* otherwise the form submit handler takes over */
      }
      if (e.key === 'Escape') {
        closeHeroPanel();
      }
    });

    refs.panel.addEventListener('mousedown', function (e) {
      var archiveBtn = e.target.closest ? e.target.closest('[data-hs-show-archive]') : null;
      if (archiveBtn) {
        e.preventDefault();
        var query = String(refs.input.value || '').trim();
        state.query = query;
        var mainSearch = document.getElementById('jobs-search');
        if (mainSearch) mainSearch.value = query;
        setView('archive', { keepUrl: true, force: true });
        applyFilters();
        syncUrl(true);
        closeHeroPanel();
        return;
      }
      var switchBtn = e.target.closest ? e.target.closest('[data-hs-switch-registry]') : null;
      if (switchBtn) {
        e.preventDefault();
        var q = String(refs.input.value || '').trim();
        state.query = q;
        setRegistry(state.registry === 'global' ? 'india' : 'global', { keepUrl: true, silent: true });
        setView('active', { keepUrl: true, force: true });
        applyFilters();
        syncUrl(true);
        closeHeroPanel();
        return;
      }
      var row = e.target.closest ? e.target.closest('.hs-row') : null;
      if (!row) return;
      e.preventDefault();
      openHeroResult(parseInt(row.getAttribute('data-idx'), 10));
    });

    document.addEventListener('mousedown', function (e) {
      if (!heroState.open) return;
      if (refs.root && refs.root.contains(e.target)) return;
      closeHeroPanel();
    });
  }

  /* ------------------------------------------------------------------ */
  /* Event wiring                                                        */
  /* ------------------------------------------------------------------ */
  function resetFilters() {
    state.query = ''; state.state = 'all'; state.category = 'all'; state.track = 'all'; state.experience = 'all';
    state.kind = 'all';
    state.quick = 'all';
    state.savedOnly = false;
    state.archiveRecent = false;
    var searchInput = document.getElementById('jobs-search');
    var heroInput = document.getElementById('hero-search-input');
    var expSelect = document.getElementById('experience-filter');
    if (searchInput) searchInput.value = '';
    if (heroInput) heroInput.value = '';
    if (expSelect) expSelect.value = 'all';
    syncKindSelect();
    if (els.stateSelect) els.stateSelect.value = 'all';
    var pillRow = document.getElementById('category-pills');
    if (pillRow) {
      Array.prototype.forEach.call(pillRow.querySelectorAll('.cat-pill'), function (p) { p.classList.remove('active'); });
      var all = pillRow.querySelector('[data-cat="all"]');
      if (all) all.classList.add('active');
    }
    syncRangeButtons();
    populateStateSelect();
    refreshCategoryPills();
    refreshTrackButtons();
    refreshQuickButtons();
    updateSavedUi();
    applyFilters();
    syncUrl(false);
  }

  function syncRangeButtons() {
    var wrap = document.getElementById('archive-range-field');
    if (!wrap) return;
    Array.prototype.forEach.call(wrap.querySelectorAll('.range-btn'), function (btn) {
      var isActive = (btn.getAttribute('data-range') === 'recent') === state.archiveRecent;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });
  }

  function bindEvents() {
    bindHeroSearch();

    var searchInput = document.getElementById('jobs-search');
    if (searchInput) {
      searchInput.addEventListener('input', debounce(function (e) {
        state.query = e.target.value || '';
        var heroInput = document.getElementById('hero-search-input');
        if (heroInput) heroInput.value = state.query;
        applyFilters();
      }, 160));
    }

    if (els.stateSelect) {
      els.stateSelect.addEventListener('change', function (e) {
        if (state.registry === 'global') {
          state.region = e.target.value || 'all';
        } else {
          state.state = e.target.value;
        }
        applyFilters();
        syncUrl(false);
      });
    }

    /* Opportunity-type dropdown (jobs + grants + scholarships + ...). */
    if (els.kindSelect) {
      els.kindSelect.addEventListener('change', function (e) {
        state.kind = e.target.value || 'all';
        applyFilters();
        syncUrl(false);
      });
    }

    /* Jurisdiction switcher (header + hero pills). */
    Array.prototype.forEach.call(
      document.querySelectorAll('[data-jurisdiction]'),
      function (btn) {
        btn.addEventListener('click', function () {
          setRegistry(btn.getAttribute('data-jurisdiction'));
        });
      }
    );

    var expSelect = document.getElementById('experience-filter');
    if (expSelect) {
      expSelect.addEventListener('change', function (e) {
        state.experience = e.target.value;
        applyFilters();
      });
    }

    var pillRow = document.getElementById('category-pills');
    if (pillRow) {
      pillRow.addEventListener('click', function (e) {
        var pill = e.target.closest('.cat-pill');
        if (!pill) return;
        state.category = pill.getAttribute('data-cat') || 'all';
        refreshCategoryPills();
        applyFilters();
        syncUrl(false);
      });
    }

    var trackRow = document.getElementById('career-tracks');
    if (trackRow) {
      trackRow.addEventListener('click', function (e) {
        var btn = e.target.closest('.track-btn');
        if (!btn) return;
        state.track = btn.getAttribute('data-track') || 'all';
        refreshTrackButtons();
        applyFilters();
        syncUrl(false);
      });
    }

    var quickRow = document.getElementById('quick-filters');
    if (quickRow) {
      quickRow.addEventListener('click', function (e) {
        var btn = e.target.closest('[data-quick]');
        if (!btn) return;
        var value = btn.getAttribute('data-quick') || 'all';
        state.quick = (state.quick === value) ? 'all' : value;
        refreshQuickButtons();
        applyFilters();
      });
    }

    var savedHeader = document.getElementById('saved-header-btn');
    if (savedHeader) savedHeader.addEventListener('click', openSavedDrawer);
    var savedFilter = document.getElementById('saved-filter-btn');
    if (savedFilter) {
      savedFilter.addEventListener('click', function () {
        state.savedOnly = !state.savedOnly;
        updateSavedUi();
        applyFilters();
        var feed = document.getElementById('jobs-feed');
        if (feed) feed.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    }
    Array.prototype.forEach.call(document.querySelectorAll('[data-saved-filter]'), function (btn) {
      btn.addEventListener('click', function () {
        state.savedOnly = true;
        closeSavedDrawer();
        updateSavedUi();
        applyFilters();
        var feed = document.getElementById('jobs-feed');
        if (feed) feed.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });
    var savedClose = document.getElementById('saved-close');
    if (savedClose) savedClose.addEventListener('click', closeSavedDrawer);
    var savedBackdrop = document.getElementById('saved-backdrop');
    if (savedBackdrop) savedBackdrop.addEventListener('click', closeSavedDrawer);
    var savedCopy = document.getElementById('saved-copy-all');
    if (savedCopy) {
      savedCopy.addEventListener('click', function () {
        var links = savedJobs().map(function (job) { return shareableUrl(job.id); });
        if (!links.length) { toast('No saved jobs to copy yet'); return; }
        copyTextToClipboard(links.join('\n'), links.length + ' saved link(s) copied');
      });
    }
    var savedDrawer = document.getElementById('saved-drawer');
    if (savedDrawer) {
      savedDrawer.addEventListener('click', function (e) {
        var remove = e.target.closest('[data-saved-remove]');
        if (remove) {
          toggleSaved(remove.getAttribute('data-saved-remove'));
          return;
        }
        var open = e.target.closest('[data-saved-open]');
        if (open) {
          closeSavedDrawer();
          openJob(open.getAttribute('data-saved-open'));
        }
      });
    }
    var mobileBar = document.getElementById('mobile-action-bar');
    if (mobileBar) {
      mobileBar.addEventListener('click', function (e) {
        var save = e.target.closest('[data-action="save-current"]');
        if (save) {
          e.preventDefault();
          toggleSaved(save.getAttribute('data-save-id') || state.detailId);
          return;
        }
        var back = e.target.closest('[data-action="back"]');
        if (back) { e.preventDefault(); goHome(); }
      });
    }

    var clearBtn = document.getElementById('clear-filters');
    if (clearBtn) clearBtn.addEventListener('click', resetFilters);

    /* Archive application-window toggle */
    var rangeWrap = document.getElementById('archive-range-field');
    if (rangeWrap) {
      rangeWrap.addEventListener('click', function (e) {
        var btn = e.target.closest('.range-btn');
        if (!btn) return;
        state.archiveRecent = btn.getAttribute('data-range') === 'recent';
        syncRangeButtons();
        applyFilters();
      });
    }

    /* View switcher */
    if (els.tabActive) els.tabActive.addEventListener('click', function () { setView('active'); });
    if (els.tabArchive) els.tabArchive.addEventListener('click', function () { setView('archive'); });

    /* Header nav shortcuts for the two registry views (crawlable hrefs,
       upgraded in-place when JS is available) */
    if (els.navRegistry) {
      els.navRegistry.addEventListener('click', function (e) {
        if (state.view === 'active' && !state.detailId) return;
        e.preventDefault();
        var wasDetail = !!state.detailId;
        state.detailId = null;
        document.body.classList.remove('view-detail');
    hideMobileActionBar();
        setView('active');
        if (wasDetail) restoreFeedScroll();
      });
    }
    if (els.navArchive) {
      els.navArchive.addEventListener('click', function (e) {
        if (state.view === 'archive' && !state.detailId) return;
        e.preventDefault();
        var wasDetail = !!state.detailId;
        state.detailId = null;
        document.body.classList.remove('view-detail');
    hideMobileActionBar();
        setView('archive');
        if (wasDetail) restoreFeedScroll();
      });
    }

    /* Card clicks → dossier view (delegated) */
    if (els.grid) {
      els.grid.addEventListener('click', function (e) {
        if (e.target.closest('[data-switch-archive]')) {
          setView('archive');
          return;
        }
        if (e.target.closest('[data-clear-filters]')) {
          resetFilters();
          return;
        }
        var saveBtn = e.target.closest('[data-save-id]');
        if (saveBtn) {
          e.preventDefault();
          e.stopPropagation();
          toggleSaved(saveBtn.getAttribute('data-save-id'));
          return;
        }
        var shareBtn = e.target.closest('[data-share-id]');
        if (shareBtn) {
          e.preventDefault();
          e.stopPropagation();
          shareJob(shareBtn.getAttribute('data-share-id'), 'native', e);
          return;
        }
        if (e.target.closest('.jc-actions')) return;
        var card = e.target.closest('.job-card');
        if (card) {
          /* Normal left-clicks open the in-page job view; the real href is
             still the crawlable /jobs/<id> static page for new tabs and
             search engines. */
          var cardLink = e.target.closest('a[href]');
          if (cardLink) e.preventDefault();
          openJob(card.getAttribute('data-id'));
        }
      });
      els.grid.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter' && e.key !== ' ') return;
        if (e.target.closest('a, button, [data-save-id], [data-share-id]')) return;
        var card = e.target.closest('.job-card');
        if (card) {
          e.preventDefault();
          openJob(card.getAttribute('data-id'));
        }
      });
    }

    /* Detail view actions (delegated) */
    if (els.detail) {
      els.detail.addEventListener('click', function (e) {
        var action = e.target.closest('[data-action]');
        if (action) {
          var name = action.getAttribute('data-action');
          if (name === 'back') {
            e.preventDefault();
            goHome();
          } else if (name === 'copy') {
            copyShareLink(e);
          } else if (name === 'save') {
            e.preventDefault();
            toggleSaved(action.getAttribute('data-save-id') || state.detailId);
          } else if (name === 'share-card') {
            e.preventDefault();
            shareJob(state.detailId, 'copy');
          }
          return;
        }
        var suggest = e.target.closest('.suggest-card');
        if (suggest) openJob(suggest.getAttribute('data-job-id'));
      });
      els.detail.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter' && e.key !== ' ') return;
        var suggest = e.target.closest('.suggest-card');
        if (suggest) {
          e.preventDefault();
          openJob(suggest.getAttribute('data-job-id'));
        }
      });
    }

    window.addEventListener('hashchange', function () { route(false); });
    /* Browser back/forward between feed and ?job= dossier views */
    window.addEventListener('popstate', function () { route(false); });

    /* Browse by State nav link: leave the dossier first if open */
    var browseLink = document.getElementById('nav-browse');
    if (browseLink) {
      browseLink.addEventListener('click', function () {
        if (state.detailId) {
          goHome();
          setTimeout(function () {
            var target = document.getElementById('filter-bar');
            if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }, 60);
        }
      });
    }

    /* Mobile nav */
    var navToggle = document.getElementById('nav-toggle');
    var siteNav = document.getElementById('site-nav');
    if (navToggle && siteNav) {
      navToggle.addEventListener('click', function () {
        var open = siteNav.classList.toggle('open');
        navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    }

    /* Partnership modal */
    var openers = document.querySelectorAll('[data-open-modal]');
    Array.prototype.forEach.call(openers, function (btn) {
      btn.addEventListener('click', function (e) { e.preventDefault(); openModal(); });
    });
    var closer = document.getElementById('modal-close');
    if (closer) closer.addEventListener('click', closeModal);
    if (els.modal) {
      els.modal.addEventListener('click', function (e) {
        if (e.target === els.modal) closeModal();
      });
      var form = document.getElementById('post-job-form');
      if (form) form.addEventListener('submit', submitModal);
    }

    document.addEventListener('keydown', function (e) {
      var target = e.target || {};
      var typing = /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName || '') || target.isContentEditable;
      if (e.key === '/' && !typing && !e.ctrlKey && !e.metaKey && !e.altKey) {
        e.preventDefault();
        var search = document.getElementById('jobs-search');
        var filter = document.getElementById('filter-bar');
        if (filter) filter.scrollIntoView({ behavior: 'smooth', block: 'center' });
        if (search) {
          search.focus({ preventScroll: true });
          search.select();
        }
        return;
      }
      if (e.key !== 'Escape') return;
      var drawer = document.getElementById('saved-drawer');
      if (drawer && drawer.classList.contains('open')) { closeSavedDrawer(); return; }
      var nav = document.getElementById('site-nav');
      if (nav && nav.classList.contains('open')) {
        nav.classList.remove('open');
        var toggle = document.getElementById('nav-toggle');
        if (toggle) toggle.setAttribute('aria-expanded', 'false');
        return;
      }
      if (els.modal && !els.modal.classList.contains('hidden')) { closeModal(); return; }
      if (state.detailId) goHome();
    });
  }

  /* Community channels & logo-fallback delegation. */
  function bindCommunityEvents() {
    /* Institution logo failed to load -> swap to the topic emblem. */
    document.addEventListener('error', function (event) {
      var img = event.target;
      if (!img || !img.classList || !img.classList.contains('fig-logo')) return;
      var figure = img.closest ? img.closest('.job-figure') : null;
      if (figure) figure.classList.add('fig-fallback');
    }, true);

    /* Owner placeholder guard: instructs where to paste the real invite link. */
    document.addEventListener('click', function (event) {
      var target = event.target && event.target.closest
        ? event.target.closest('[data-community-guard]')
        : null;
      if (!target) return;
      event.preventDefault();
      var kind = target.getAttribute('data-community-guard');
      toast(kind === 'whatsapp'
        ? 'Owner: paste your real WhatsApp invite link into <meta name="ufp-whatsapp-group"> on index.html to activate this button.'
        : 'Owner: paste the channel link into <meta name="ufp-telegram-channel"> on index.html to activate this button.');
    }, false);
  }

  /* ------------------------------------------------------------------ */
  /* Free job & fellowship email alerts — 72-hour briefing subscription              */
  /* ------------------------------------------------------------------ */
  var NEWSLETTER_STORE_KEY = 'ufp_newsletter';

  var SECTOR_LABELS = {
    'all': 'All jobs',
    'academic': 'JRF / PhD / Academic',
    'forestry-gis': 'Forestry & GIS',
    'corporate-esg': 'Corporate ESG'
  };

  function newsletterEndpoint() {
    var meta = document.querySelector('meta[name="ufp-newsletter-endpoint"]');
    var value = meta && meta.content ? meta.content.trim() : '';
    return value || '/api/subscribe';
  }

  function newsletterStored() {
    try {
      var raw = window.localStorage.getItem(NEWSLETTER_STORE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) { return null; }
  }

  function newsletterStore(payload) {
    try {
      window.localStorage.setItem(NEWSLETTER_STORE_KEY, JSON.stringify(payload));
    } catch (e) { /* private mode: the confirmation simply will not persist */ }
  }

  function validEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(value || '').trim());
  }

  function dispatchStatusEl(form) {
    var scope = form.closest('.dispatch-mini') || form.parentNode;
    return scope ? scope.querySelector('.dispatch-status') : null;
  }

  function dispatchSetStatus(form, message, kind) {
    var el = dispatchStatusEl(form);
    if (!el) return;
    el.textContent = message;
    el.classList.remove('is-ok', 'is-note', 'is-error');
    if (kind) el.classList.add(kind);
  }

  function dispatchPayload(form) {
    var emailInput = form.querySelector('input[type="email"]');
    var email = emailInput ? emailInput.value.trim() : '';
    if (!validEmail(email)) return null;
    var frequencyEl = form.querySelector('input[name="frequency"]:checked');
    var sectorEl = form.querySelector('select[name="sector"]');
    var frequency = frequencyEl ? frequencyEl.value : '3-days';
    if (frequency === '3-day') frequency = '3-days';
    return {
      email: email,
      frequency: frequency,
      sector: sectorEl ? sectorEl.value : 'all'
    };
  }

  /* Swap a submitted form for a formal confirmation state. `note` carries
     any transparency note (e.g. a local-only save when the dispatch
     endpoint is not yet reachable). */
  function dispatchDone(form, record, note) {
    var isMini = !!form.closest('.dispatch-mini');

    if (isMini) {
      form.hidden = true;
      dispatchSetStatus(
        form,
        t('dispatch.mini.ok', 'Subscribed \u2014 next email alert within 72 hours.') + (note ? ' ' + note : ''),
        'is-ok'
      );
      return;
    }

    dispatchSetStatus(form, '', null);
    form.hidden = true;

    var done = document.createElement('div');
    done.className = 'dispatch-done';
    var html = '<p class="dd-title">' + t('dd.title', 'Subscription recorded') + '</p>' +
      '<dl class="dd-meta">' +
      '<div><dt>' + t('dd.address', 'Address') + '</dt><dd>' + escapeHtml(record.email) + '</dd></div>' +
      '<div><dt>' + t('dd.frequency', 'Frequency') + '</dt><dd>' + (record.frequency === 'weekly' ? t('dd.freq.weekly', 'Weekly digest') : t('dd.freq.3day', 'Every 3 days')) + '</dd></div>' +
      '<div><dt>' + t('dd.sector', 'Sector') + '</dt><dd>' + escapeHtml(t('sector.' + (record.sector || 'all'), SECTOR_LABELS[record.sector] || 'All jobs')) + '</dd></div>' +
      '</dl>' +
      (note ? '<p class="dd-note">' + escapeHtml(note) + '</p>' : '') +
      '<p class="dd-actions">' +
      '<a href="/unsubscribe?email=' + encodeURIComponent(record.email) + '">' + t('dd.manage', 'Manage or withdraw this subscription') + '</a>' +
      ' <span class="dd-sep">&middot;</span> ' +
      '<button type="button" class="dd-update">' + t('dd.update', 'Update preferences') + '</button>' +
      '</p>';
    done.innerHTML = html;

    var updateBtn = done.querySelector('.dd-update');
    if (updateBtn) {
      updateBtn.addEventListener('click', function () {
        done.parentNode.removeChild(done);
        form.hidden = false;
        var emailInput = form.querySelector('input[type="email"]');
        if (emailInput) emailInput.focus();
      });
    }
    form.parentNode.insertBefore(done, form.nextSibling);
  }

  function submitDispatch(form, event) {
    event.preventDefault();
    var payload = dispatchPayload(form);
    if (!payload) {
      dispatchSetStatus(form, t('dispatch.invalid', 'Enter a valid email address to subscribe.'), 'is-error');
      var badInput = form.querySelector('input[type="email"]');
      if (badInput) badInput.focus();
      return;
    }

    var record = {
      email: payload.email,
      frequency: payload.frequency,
      sector: payload.sector,
      ts: new Date().toISOString(),
      status: 'pending'
    };
    newsletterStore(record);
    dispatchSetStatus(form, t('dispatch.registering', 'Registering subscription\u2026'), 'is-note');

    var submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.disabled = true;

    fetch(newsletterEndpoint(), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (data) {
        return { ok: response.ok && !(data && data.ok === false), persisted: !!(data && data.persisted) };
      });
    }).then(function (result) {
      record.status = result.ok && result.persisted ? 'subscribed' : 'local';
      record.persisted = result.persisted;
      record.pending = !result.persisted;
      record.synced_at = result.persisted ? new Date().toISOString() : record.synced_at;
      newsletterStore(record);
      if (result.ok) {
        dispatchDone(form, record, result.persisted ? '' :
          t('dd.note.local', 'Saved on this device. To join the current email alert list immediately, write to urbanforestpark@gmail.com.'));
        toast(result.persisted
          ? t('toast.subscribed', 'Email alerts subscribed \u2014 next briefing within 72 hours.')
          : t('toast.saved', 'Email alert preference saved on this device.'));
      } else {
        dispatchDone(form, record,
          t('dd.note.local', 'Saved on this device. To join the current email alert list immediately, write to urbanforestpark@gmail.com.'));
        toast(t('toast.saved', 'Email alert preference saved on this device.'));
      }
    }).catch(function () {
      record.status = 'local';
      record.pending = true;
      newsletterStore(record);
      dispatchDone(form, record,
        t('dd.note.local', 'Saved on this device. To join the current email alert list immediately, write to urbanforestpark@gmail.com.'));
      toast(t('toast.saved', 'Email alert preference saved on this device.'));
    }).then(function () {
      if (submitBtn) submitBtn.disabled = false;
    });
  }

  /* A signup made while the endpoint had no server-side store is kept on the
     device. Retry it silently on the next visit so it reaches the shared
     subscriber file as soon as the backend is configured. */
  function syncPendingNewsletter() {
    var stored = newsletterStored();
    if (!stored || !stored.email || stored.status === 'subscribed' || !stored.pending) return;

    fetch(newsletterEndpoint(), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: stored.email,
        frequency: stored.frequency === 'weekly' ? 'weekly' : '3-days',
        sector: stored.sector || 'all'
      })
    }).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (data) {
        return { ok: response.ok && !(data && data.ok === false), persisted: !!(data && data.persisted) };
      });
    }).then(function (result) {
      if (!result.ok || !result.persisted) return;
      stored.status = 'subscribed';
      stored.persisted = true;
      stored.pending = false;
      stored.synced_at = new Date().toISOString();
      newsletterStore(stored);
    }).catch(function () { /* keep the device copy for the next visit */ });
  }

  function initNewsletter() {
    var forms = document.querySelectorAll('form[data-newsletter-form]');
    Array.prototype.forEach.call(forms, function (form) {
      form.addEventListener('submit', function (event) { submitDispatch(form, event); });

      var stored = newsletterStored();
      var emailInput = form.querySelector('input[type="email"]');
      if (stored && stored.email && emailInput) emailInput.value = stored.email;

      /* Returning visitor with a recorded preference: show the confirmation
         state instead of an empty form. */
      if (stored && stored.email && (stored.status === 'subscribed' || stored.status === 'local')) {
        var frequencyInput = form.querySelector('input[name="frequency"][value="' + (stored.frequency || '3-days') + '"]');
        if (frequencyInput) frequencyInput.checked = true;
        var sectorSelect = form.querySelector('select[name="sector"]');
        if (sectorSelect && SECTOR_LABELS[stored.sector]) sectorSelect.value = stored.sector;
        dispatchDone(form, stored, stored.persisted ? '' : '');
      }
    });
    syncPendingNewsletter();
  }

  /* ------------------------------------------------------------------ */
  /* Boot                                                                */
  /* ------------------------------------------------------------------ */
  document.addEventListener('DOMContentLoaded', function () {
    els = {
      grid: document.getElementById('jobs-grid'),
      detail: document.getElementById('job-detail-content'),
      resultsCount: document.getElementById('results-count'),
      stateSelect: document.getElementById('state-filter'),
      experienceField: document.getElementById('experience-field'),
      archiveRangeField: document.getElementById('archive-range-field'),
      tabActive: document.getElementById('tab-active'),
      tabArchive: document.getElementById('tab-archive'),
      heroHeading: document.getElementById('hero-heading'),
      heroSub: document.getElementById('hero-sub'),
      heroKicker: document.getElementById('hero-kicker'),
      kindSelect: document.getElementById('kind-filter'),
      seoStates: document.getElementById('seo-states'),
      seoCategories: document.getElementById('seo-categories'),
      themeToggle: document.getElementById('theme-toggle'),
      navRegistry: document.getElementById('nav-registry'),
      navArchive: document.getElementById('nav-archive'),
      modal: document.getElementById('post-job-modal'),
      toast: document.getElementById('toast')
    };
    bindEvents();
    bindCommunityEvents();
    initNewsletter();
    initTheme();
    if (window.UFPAppWidget && typeof window.UFPAppWidget.init === 'function') {
      window.UFPAppWidget.init();
    }

    /* Language switch: re-render everything that jobs.js owns dynamically.
       (Static markup is re-translated by js/i18n.js via data-i18n.) */
    document.addEventListener('ufp:langchange', function () {
      renderTelemetry();
      syncRegistryChrome();
      populateStateSelect();
      refreshCategoryPills();
      refreshTrackButtons();
      refreshQuickButtons();
      updateSavedUi();
      applyTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light', false);
      updateTabCounts();
      if (state.detailId) {
        var found = findJob(state.detailId);
        if (found) {
          renderDetail(found.job, found.archived);
          updateSeoForJob(found.job, found.archived);
        }
      } else {
        renderFeed();
        updateViewSeo();
      }
    });

    loadAll();
  });
})();
