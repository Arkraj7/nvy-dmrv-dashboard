/* ==========================================================================
   Urban Forest Park — National Climate, Forestry, ESG & Geospatial
   Career Registry (India)
   js/jobs.js — registry data loading (jobs.json + archive.json + stats.json),
   weekly telemetry, active/archived views, ?job= ?view= ?state= ?category=
   routing, position dossiers, schema.org lifecycle (JobPosting for active
   mandates, WebPage + BreadcrumbList for archived ones), sharing, and the
   institutional partnership modal. Vanilla JS, no dependencies.
   ========================================================================== */
(function () {
  'use strict';

  /* ------------------------------------------------------------------ */
  /* Config & state                                                      */
  /* ------------------------------------------------------------------ */
  var CONFIG = {
    DATA_URL: 'jobs.json',
    ARCHIVE_URL: 'archive.json',
    STATS_URL: 'stats.json',
    CONTACT_EMAIL: 'arkraj.biswas6@gmail.com',
    ADS_EVERY: 5,              // inject an in-feed ad card after every 5th card
    VALID_DAYS: 30,            // fallback jobPosting validThrough = datePosted + N days
    ARCHIVE_RECENT_DAYS: 7,    // "Closed in the last 7 days" archive window
    SITE_URL: 'https://www.urbanforestpark.com/',
    SITE_NAME: 'Urban Forest Park'
  };

  var CATEGORY_SLUGS = {
    'Climate & Sustainability': 'climate-sustainability',
    'Forestry & Afforestation': 'forestry-afforestation',
    'ESG & Carbon Markets': 'esg-carbon-markets',
    'GIS, Remote Sensing & UHI': 'gis-remote-sensing-uhi',
    'Environmental Policy & Fellowships': 'environmental-policy-fellowships'
  };

  var DEFAULT_TITLE = document.title;
  var DEFAULT_DESC = (document.querySelector('meta[name="description"]') || {}).content || '';
  var DEFAULT_HERO_HTML = '';

  var state = {
    jobs: [],                 // active listings (jobs.json)
    archive: [],              // past listings (archive.json)
    stats: null,              // weekly telemetry (stats.json)
    view: 'active',           // 'active' | 'archive'
    archiveRecent: false,     // archive: only records closed in the last 7 days
    filtered: [],
    query: '',
    state: 'all',
    category: 'all',
    experience: 'all',
    detailId: null,
    loaded: false
  };

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
      archive: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="4" rx="1"/><path d="M5 8v11a1 1 0 001 1h12a1 1 0 001-1V8"/><path d="M10 12h4"/></svg>'
    };
    return icons[name] || '';
  }

  var CATEGORY_CLASS = {
    'Climate & Sustainability': 'cat-climate',
    'Forestry & Afforestation': 'cat-forestry',
    'ESG & Carbon Markets': 'cat-esg',
    'GIS, Remote Sensing & UHI': 'cat-gis',
    'Environmental Policy & Fellowships': 'cat-policy'
  };

  function catClass(category) { return CATEGORY_CLASS[category] || 'cat-policy'; }

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
    if (job.state === 'Multiple States / Remote') return 'Multiple States / Remote';
    return job.city ? job.city + ', ' + job.state : (job.state || 'India');
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

  function loadAll() {
    els.grid.innerHTML = '<div class="loading-state" role="status">Loading registry mandates&hellip;</div>';
    Promise.all([
      fetchJson(CONFIG.DATA_URL, true),
      fetchJson(CONFIG.ARCHIVE_URL, false),
      fetchJson(CONFIG.STATS_URL, false)
    ]).then(function (results) {
      state.jobs = sortByDateDesc(Array.isArray(results[0]) ? results[0] : [], 'date_added');
      state.archive = sortByDateDesc(Array.isArray(results[1]) ? results[1] : [], 'date_archived');
      state.stats = (results[2] && typeof results[2] === 'object') ? results[2] : null;
      state.loaded = true;

      DEFAULT_HERO_HTML = els.heroHeading ? els.heroHeading.innerHTML : '';

      initFromUrl();
      renderTelemetry();
      updateTabCounts();
      syncViewChrome();
      populateStateSelect();
      refreshCategoryPills();
      injectFeedJsonLd(state.jobs);
      renderSeoDirectory();
      applyFilters();
      route(true);
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
    for (key in CATEGORY_CLASS) {
      if (key.toLowerCase() === raw.toLowerCase()) return key;
    }
    return null;
  }

  function initFromUrl() {
    var params;
    try { params = new URLSearchParams(window.location.search || ''); }
    catch (e) { params = null; }
    if (!params) return;

    if ((params.get('view') || '') === 'archive') state.view = 'archive';
    var stateParam = params.get('state');
    if (stateParam && stateParam !== 'all') state.state = stateParam;
    var cat = resolveCategoryParam(params.get('category'));
    if (cat) state.category = cat;
    state.detailId = null;
  }

  /* Query string reflecting the current registry view (no ?job=). */
  function queryForState() {
    var parts = [];
    if (state.view === 'archive') parts.push('view=archive');
    if (state.state !== 'all') parts.push('state=' + encodeURIComponent(state.state));
    if (state.category !== 'all') {
      parts.push('category=' + encodeURIComponent(CATEGORY_SLUGS[state.category] || state.category));
    }
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
    return state.view === 'archive' ? state.archive : state.jobs;
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
    if (changed || opts.force) applyFilters();
    if (!opts.keepUrl) syncUrl(opts.push !== false);
  }

  function updateTabCounts() {
    setText('tab-active-count', String(state.jobs.length));
    setText('tab-archive-count', String(state.archive.length));
  }

  function findJob(id) {
    var i;
    for (i = 0; i < state.jobs.length; i += 1) {
      if (state.jobs[i].id === id) return { job: state.jobs[i], archived: false };
    }
    for (i = 0; i < state.archive.length; i += 1) {
      if (state.archive[i].id === id) return { job: state.archive[i], archived: true };
    }
    return null;
  }

  /* ------------------------------------------------------------------ */
  /* Weekly telemetry ribbon                                             */
  /* ------------------------------------------------------------------ */
  function statsWindow() {
    var weekAgo = isoDaysAgo(CONFIG.ARCHIVE_RECENT_DAYS);
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
    setText('tel-updated', statsData.last_updated ? formatLongDate(String(statsData.last_updated).slice(0, 10)) : 'local sync');
  }

  /* ------------------------------------------------------------------ */
  /* Filters & feed rendering                                            */
  /* ------------------------------------------------------------------ */
  function populateStateSelect() {
    if (!els.stateSelect) return;
    var source = getViewData();
    var counts = {};
    source.forEach(function (j) {
      if (!j.state) return;
      counts[j.state] = (counts[j.state] || 0) + 1;
    });
    var states = Object.keys(counts).sort();
    var html = '<option value="all">All India (' + source.length + ')</option>';
    states.forEach(function (s) {
      html += '<option value="' + escapeHtml(s) + '">' + escapeHtml(s) + ' (' + counts[s] + ')</option>';
    });
    els.stateSelect.innerHTML = html;
    els.stateSelect.value = counts[state.state] ? state.state : 'all';
    if (els.stateSelect.value === 'all') state.state = 'all';
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

  function archiveCutoff() {
    return isoDaysAgo(CONFIG.ARCHIVE_RECENT_DAYS);
  }

  function applyFilters() {
    var q = state.query.trim().toLowerCase();
    var source = getViewData();
    var isArchive = state.view === 'archive';
    var cutoff = archiveCutoff();

    state.filtered = source.filter(function (job) {
      if (state.state !== 'all' && job.state !== state.state) return false;
      if (state.category !== 'all' && job.category !== state.category) return false;
      if (!isArchive && state.experience !== 'all' && job.experience_level !== state.experience) return false;
      if (isArchive && state.archiveRecent && String(job.date_archived || '') < cutoff) return false;
      if (q) {
        var haystack = [
          job.clean_title, job.organization, job.city, job.state,
          job.category, job.experience_level, (job.must_have_skills || []).join(' ')
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
        countEl.textContent = 'Loading\u2026';
      } else if (isArchive) {
        countEl.textContent = jobs.length === 1 ? '1 historical record' : jobs.length + ' historical records';
      } else {
        countEl.textContent = jobs.length === 1 ? '1 active position' : jobs.length + ' active positions';
      }
    }

    if (!state.loaded) return;

    var source = getViewData();
    if (!source.length) {
      els.grid.innerHTML = isArchive
        ? '<div class="empty-state"><h3>The historical archive is being catalogued</h3><p>Past mandates appear here once their application windows close.</p></div>'
        : '<div class="empty-state"><h3>No listings yet</h3><p>New green-sector mandates are published regularly. Check back soon.</p></div>';
      els.grid.setAttribute('aria-busy', 'false');
      return;
    }

    if (!jobs.length) {
      els.grid.innerHTML = emptyFilterHtml();
      els.grid.setAttribute('aria-busy', 'false');
      return;
    }

    var html = '';
    jobs.forEach(function (job, index) {
      html += jobCardHtml(job, isArchive);
      var position = index + 1;
      if (position % CONFIG.ADS_EVERY === 0 && position < jobs.length) {
        html += adInFeedHtml();
      }
    });
    els.grid.innerHTML = html;
    els.grid.setAttribute('aria-busy', 'false');
  }

  function emptyFilterHtml() {
    var isArchive = state.view === 'archive';
    var html = '<div class="empty-state">';
    html += '<h3>No ' + (isArchive ? 'archived records' : 'active mandates') + ' match these filters</h3>';
    html += '<p>Try a different keyword, region or sector \u2014 or reset the filters.</p>';

    /* Active view with zero matches in a sector that has historical records:
       route the visitor to the archive instead of a dead end. */
    if (!isArchive && state.category !== 'all') {
      var archivedCount = state.archive.filter(function (j) { return j.category === state.category; }).length;
      if (archivedCount > 0) {
        html += '<p>No active mandates are open in this sector at present \u2014 ' + archivedCount +
          ' historical record' + (archivedCount === 1 ? ' exists' : 's exist') + ' in the archive.</p>';
        html += '<button class="btn btn-outline" type="button" data-switch-archive>View Historical Archive ' + iconSvg('arrow') + '</button>';
      }
    }
    html += '<button class="btn btn-ghost" type="button" data-clear-filters>Reset Filters</button>';
    html += '</div>';
    return html;
  }

  function jobCardHtml(job, isArchived) {
    var skills = job.must_have_skills || [];
    var shown = skills.slice(0, 3);
    var extra = skills.length - shown.length;
    var chips = shown.map(function (s) {
      return '<span class="skill-chip">' + escapeHtml(s) + '</span>';
    }).join('');
    if (extra > 0) chips += '<span class="skill-chip more">+' + extra + ' more</span>';

    var statusBadge = isArchived
      ? '<span class="badge badge-archived">' + iconSvg('archive') + 'Archived</span>'
      : '';

    var dateMeta = isArchived
      ? iconSvg('clock') + escapeHtml(formatClosed(job.date_archived))
      : iconSvg('calendar') + escapeHtml(formatPosted(job.date_added));

    var footDate = isArchived
      ? 'Closed ' + escapeHtml(job.date_archived || '')
      : escapeHtml(job.date_added || '');

    var ctaLabel = isArchived ? 'Open Archived Record' : 'View Position Dossier';

    return '' +
      '<article class="job-card' + (isArchived ? ' is-archived' : '') + '" data-id="' + escapeHtml(job.id) + '" tabindex="0" role="link" ' +
        'aria-label="' + (isArchived ? 'Open archived record: ' : 'View position dossier: ') +
        escapeHtml(job.clean_title) + ' at ' + escapeHtml(job.organization) + '">' +
        '<div class="jc-top">' +
          '<span class="badge ' + catClass(job.category) + '">' + escapeHtml(job.category) + '</span>' +
          '<span class="badge badge-exp">' + escapeHtml(job.experience_level || '') + '</span>' +
          statusBadge +
        '</div>' +
        '<h3 class="jc-title">' + escapeHtml(job.clean_title) + '</h3>' +
        '<p class="jc-org">' + escapeHtml(job.organization) + '</p>' +
        '<div class="jc-meta">' +
          '<span>' + iconSvg('pin') + escapeHtml(stateLabel(job)) + '</span>' +
          '<span>' + dateMeta + '</span>' +
        '</div>' +
        '<div class="jc-skills">' + chips + '</div>' +
        '<div class="jc-foot">' +
          '<span class="jc-date">' + footDate + '</span>' +
          '<span class="jc-view">' + ctaLabel + ' ' + iconSvg('arrow') + '</span>' +
        '</div>' +
      '</article>';
  }

  function adInFeedHtml() {
    return '' +
      '<div class="ad-container ad-infeed" aria-label="Sponsored placement">' +
        '<span class="ad-label">Sponsored &middot; Institutional Partner Space</span>' +
        '<div class="ad-slot">' +
          '<span>Place your organisation here &mdash; reach India&rsquo;s environmental workforce.</span>' +
          '<a class="ad-cta" href="mailto:' + encodeURIComponent(CONFIG.CONTACT_EMAIL) +
            '?subject=' + encodeURIComponent('Advertising / Partnership on UrbanForestPark Jobs Board') + '">Sponsor this space &rarr;</a>' +
        '</div>' +
      '</div>';
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
    } catch (e) { /* URLSearchParams unavailable: fall through to the hash form */ }

    var hash = window.location.hash || '';
    var match = hash.match(/^#\/job\/([A-Za-z0-9._-]+)/);
    return match ? decodeURIComponent(match[1]) : null;
  }

  function setUrlQuietly(path) {
    if (window.history && window.history.replaceState) {
      try { window.history.replaceState({}, '', path); } catch (e) { /* ignore */ }
    }
  }

  function goHome() {
    var path = window.location.pathname + queryForState();
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
    var id = getJobIdFromUrl();
    if (id) {
      var found = findJob(id);
      if (found) {
        state.detailId = id;
        /* Keep the active/archived switcher aligned with the record type. */
        var wantedView = found.archived ? 'archive' : 'active';
        if (state.view !== wantedView) {
          state.view = wantedView;
          syncViewChrome();
          updateTabCounts();
          populateStateSelect();
          refreshCategoryPills();
        }
        renderDetail(found.job, found.archived);
        document.body.classList.add('view-detail');
        if (!initial) window.scrollTo({ top: 0, behavior: 'smooth' });
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
    updateViewSeo();
  }

  function openJob(id) {
    if (state.detailId === id) return;
    var url = '?job=' + encodeURIComponent(id);
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
  function renderDetail(job, isArchived) {
    var skills = (job.must_have_skills || []).map(function (s) {
      return '<span class="skill-chip">' + escapeHtml(s) + '</span>';
    }).join('');

    var responsibilities = (job.key_responsibilities || []).map(function (r) {
      return '<li>' + escapeHtml(r) + '</li>';
    }).join('');

    var shareUrl = shareableUrl(job.id);
    var waHref = 'https://wa.me/?text=' + encodeURIComponent(job.clean_title + ' at ' + job.organization + ' \u2014 ' + shareUrl);
    var liHref = 'https://www.linkedin.com/sharing/share-offsite/?url=' + encodeURIComponent(shareUrl);
    var backLabel = isArchived ? 'Historical Archive' : 'Active Opportunities';

    var banner = '';
    if (isArchived) {
      banner = '' +
        '<div class="archive-banner" role="note">' +
          '<span class="archive-flag">Archived</span>' +
          '<p><strong>Archived Mandate:</strong> the application window for this position closed on ' +
            escapeHtml(formatLongDate(job.date_archived || job.valid_through || job.date_added)) +
            '. This record is maintained in the Urban Forest Park Career Registry for compensation, ' +
            'skill, and institutional reference.</p>' +
        '</div>';
    }

    var archiveBadge = isArchived ? '<span class="badge badge-archived">' + iconSvg('archive') + 'Archived Record</span>' : '';

    var dateLine = isArchived
      ? '<span>' + iconSvg('clock') + escapeHtml(formatClosed(job.date_archived)) + '</span>'
      : '<span>' + iconSvg('calendar') + escapeHtml(formatPosted(job.date_added)) + '</span>';

    var applyBlock;
    if (isArchived) {
      applyBlock = '' +
        '<div class="apply-block">' +
          '<a class="btn-apply btn-apply-closed" href="' + escapeHtml(job.apply_url) + '" target="_blank" rel="nofollow noopener">' +
            'Application Window Closed (View Organization Portal ' + iconSvg('external') + ')' +
          '</a>' +
          '<p class="apply-note">This mandate is archived \u2014 the deadline has passed. The link opens the ' +
            'organisation&rsquo;s portal for institutional reference only.</p>' +
        '</div>';
    } else {
      applyBlock = '' +
        '<div class="apply-block">' +
          '<a class="btn-apply" href="' + escapeHtml(job.apply_url) + '" target="_blank" rel="noopener noreferrer nofollow">' +
            'Open Official Application Portal ' + iconSvg('external') +
          '</a>' +
          '<p class="apply-note">Opens the official application portal in a new tab. Always verify eligibility ' +
            'and deadlines on the employer&rsquo;s page.</p>' +
        '</div>';
    }

    var suggestions = isArchived ? suggestionsHtml(job) : '';

    els.detail.innerHTML = '' +
      '<div class="detail-topbar">' +
        '<a class="back-link" href="#" data-action="back">' + iconSvg('back') + ' ' + backLabel + '</a>' +
        '<div class="share-row">' +
          '<a class="share-btn share-whatsapp" href="' + waHref + '" target="_blank" rel="noopener noreferrer">' + iconSvg('whatsapp') + 'Share on WhatsApp</a>' +
          '<a class="share-btn share-linkedin" href="' + liHref + '" target="_blank" rel="noopener noreferrer">' + iconSvg('linkedin') + 'Share on LinkedIn</a>' +
          '<button class="share-btn share-copy" type="button" data-action="copy" title="Copies the direct ?job= link for this record">' + iconSvg('copy') + 'Copy Direct Link</button>' +
        '</div>' +
      '</div>' +

      banner +

      '<div class="detail-card">' +
        '<div class="detail-kicker">' +
          '<span class="badge ' + catClass(job.category) + '">' + escapeHtml(job.category) + '</span>' +
          '<span class="badge badge-exp">' + escapeHtml(job.experience_level || '') + '</span>' +
          '<span class="badge badge-state">' + iconSvg('pin') + escapeHtml(stateLabel(job)) + '</span>' +
          archiveBadge +
        '</div>' +

        '<h1>' + escapeHtml(job.clean_title) + '</h1>' +
        '<p class="detail-org">' + escapeHtml(job.organization) + '</p>' +
        '<div class="detail-meta">' +
          dateLine +
          '<span>Ref: ' + escapeHtml(String(job.id).slice(0, 24)) + '</span>' +
          (isArchived ? '<span>Archived ' + escapeHtml(job.date_archived || '') + '</span>' : '<span>Valid through ' + escapeHtml(job.valid_through || '') + '</span>') +
        '</div>' +

        '<div class="detail-section">' +
          '<h2>Mandate Summary</h2>' +
          '<p>' + escapeHtml(job.role_summary) + '</p>' +
        '</div>' +

        '<div class="detail-section">' +
          '<h2>Core Responsibilities</h2>' +
          '<ul class="resp-list">' + responsibilities + '</ul>' +
        '</div>' +

        '<div class="detail-section">' +
          '<h2>Required Competencies</h2>' +
          '<div class="skills-wrap">' + skills + '</div>' +
        '</div>' +

        adDetailHtml() +

        '<div class="tip-callout">' +
          '<span class="tip-title">' + iconSvg('bulb') + ' Candidate Advisory</span>' +
          '<p>' + escapeHtml(job.application_tip) + '</p>' +
        '</div>' +

        adDetailHtml() +

        applyBlock +

        '<div class="detail-foot">' +
          '<a class="back-link" href="#" data-action="back">' + iconSvg('back') + ' Back to ' + backLabel + '</a>' +
          '<div class="share-row">' +
            '<a class="share-btn share-whatsapp" href="' + waHref + '" target="_blank" rel="noopener noreferrer">WhatsApp</a>' +
            '<a class="share-btn share-linkedin" href="' + liHref + '" target="_blank" rel="noopener noreferrer">LinkedIn</a>' +
          '</div>' +
        '</div>' +
      '</div>' +

      suggestions;
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
          'aria-label="View active position: ' + escapeHtml(j.clean_title) + ' at ' + escapeHtml(j.organization) + '">' +
          '<span class="sc-title">' + escapeHtml(j.clean_title) + '</span>' +
          '<span class="sc-org">' + escapeHtml(j.organization) + ' &middot; ' + escapeHtml(stateLabel(j)) + '</span>' +
          '<span class="sc-meta"><span>' + escapeHtml(j.category) + '</span><span>Listed ' + escapeHtml(j.date_added || '') + '</span></span>' +
        '</article>';
    }).join('');

    return '' +
      '<div class="suggest-block">' +
        '<h3>Currently Active Positions in This Sector</h3>' +
        '<div class="suggest-grid">' + cards + '</div>' +
      '</div>';
  }

  function adDetailHtml() {
    return '' +
      '<div class="ad-container" style="margin:24px 0;padding:0;" aria-label="Sponsored placement">' +
        '<span class="ad-label">Sponsored &middot; Institutional Partner Space</span>' +
        '<div class="ad-slot">' +
          '<span>Reach thousands of climate, forestry and ESG professionals every month.</span>' +
          '<a class="ad-cta" href="mailto:' + encodeURIComponent(CONFIG.CONTACT_EMAIL) +
            '?subject=' + encodeURIComponent('Advertising / Partnership on UrbanForestPark Jobs Board') + '">Partner with Urban Forest Park &rarr;</a>' +
        '</div>' +
      '</div>';
  }

  function shareableUrl(id) {
    return CONFIG.SITE_URL + '?job=' + encodeURIComponent(id);
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

  function fallbackCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); toast('Direct link copied'); }
    catch (e) { toast('Copy failed \u2014 please copy from the address bar'); }
    document.body.removeChild(ta);
  }

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
    var hasState = state.state !== 'all';
    var hasCat = state.category !== 'all';
    var isArchive = state.view === 'archive';

    var title = DEFAULT_TITLE;
    var desc = DEFAULT_DESC;
    var url = CONFIG.SITE_URL;
    var heroHtml = DEFAULT_HERO_HTML;
    var heroText = null;
    var feedEyebrow = 'Active Sector Mandates';
    var feedTitle = 'Active Opportunities';

    if (isArchive) {
      feedEyebrow = 'Historical Mandate Archive';
      feedTitle = 'Archived / Past Positions';
      title = 'Historical Mandate Archive \u2014 Past Climate, Forestry, ESG & GIS Positions | Urban Forest Park';
      desc = 'Archived climate, forestry, ESG, carbon-market and geospatial mandates' +
        (hasState ? ' in ' + state.state : '') +
        (hasCat ? ' (\u2018' + state.category + '\u2019 sector)' : '') +
        ', preserved in the Urban Forest Park career registry for institutional reference.';
      if (hasCat || hasState) {
        feedTitle = 'Archived / Past Positions';
        heroText = 'Historical Mandate Archive \u2014 ' + (hasCat ? state.category : '') +
          (hasCat && hasState ? ' \u00b7 ' : '') + (hasState ? state.state : '');
      }
      url = CONFIG.SITE_URL + queryForState();
    } else if (hasCat || hasState) {
      var scope = hasState ? state.state : 'India';
      title = (hasCat ? state.category : 'Climate, Forestry, ESG & GIS') + ' Jobs in ' + scope + ' | Urban Forest Park';
      desc = 'Active ' + (hasCat ? state.category.toLowerCase() + ' ' : '') + 'positions' +
        (hasState ? ' across ' + state.state : ' across India') +
        ' \u2014 verified listings with direct links to official application portals, maintained by the Urban Forest Park registry.';
      heroText = hasCat
        ? state.category + ' Jobs \u2014 ' + (hasState ? state.state : 'All India')
        : 'Climate, Forestry, ESG & Geospatial Jobs \u2014 ' + state.state;
      feedTitle = hasCat ? state.category : 'Active Opportunities';
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
      injectJsonLd(breadcrumbSchema(job), 'job-breadcrumb-jsonld');
      removeJsonLd('job-posting-jsonld');
    } else {
      title = job.clean_title + ' \u2014 ' + job.organization + ' | Urban Forest Park Registry';
      injectJsonLd(jobPostingSchema(job), 'job-posting-jsonld');
      removeJsonLd('job-webpage-jsonld');
      removeJsonLd('job-breadcrumb-jsonld');
    }

    applyMetaBlock(title, desc, url);
    setText('feed-eyebrow', isArchived ? 'Historical Mandate Archive' : 'Active Sector Mandates');
    setText('feed-title', isArchived ? 'Archived / Past Positions' : 'Active Opportunities');
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
      employmentType: 'FULL_TIME',
      hiringOrganization: {
        '@type': 'Organization',
        name: job.organization,
        sameAs: CONFIG.SITE_URL
      },
      jobLocation: {
        '@type': 'Place',
        address: {
          '@type': 'PostalAddress',
          addressLocality: job.city || '',
          addressRegion: job.state || '',
          addressCountry: 'IN'
        }
      },
      directApply: false,
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
      name: job.clean_title + ' \u2014 ' + job.organization + ' (Archived Mandate)',
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

  function breadcrumbSchema(job) {
    return {
      '@context': 'https://schema.org',
      '@type': 'BreadcrumbList',
      itemListElement: [
        { '@type': 'ListItem', position: 1, name: 'Career Registry', item: CONFIG.SITE_URL },
        { '@type': 'ListItem', position: 2, name: 'Historical Archive', item: CONFIG.SITE_URL + '?view=archive' },
        { '@type': 'ListItem', position: 3, name: job.clean_title }
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
    var schema = {
      '@context': 'https://schema.org',
      '@type': 'ItemList',
      name: 'Active green-sector mandates in India \u2014 Climate, Forestry, ESG & GIS',
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
    if (label) label.textContent = theme === 'dark' ? 'Light' : 'Night';
    var btn = els.themeToggle;
    if (btn) {
      btn.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
      btn.setAttribute('aria-label', theme === 'dark' ? 'Switch to light mode' : 'Switch to night mode');
    }
    if (announce) toast(theme === 'dark' ? 'Night mode enabled' : 'Light mode enabled');
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
      'Mandate details:',
      message,
      '',
      '\u2014 Sent from the Urban Forest Park career registry'
    ].join('\n');

    window.location.href = 'mailto:' + CONFIG.CONTACT_EMAIL +
      '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
    closeModal();
  }

  /* ------------------------------------------------------------------ */
  /* Event wiring                                                        */
  /* ------------------------------------------------------------------ */
  function resetFilters() {
    state.query = ''; state.state = 'all'; state.category = 'all'; state.experience = 'all';
    state.archiveRecent = false;
    var searchInput = document.getElementById('jobs-search');
    var expSelect = document.getElementById('experience-filter');
    if (searchInput) searchInput.value = '';
    if (expSelect) expSelect.value = 'all';
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
    var searchInput = document.getElementById('jobs-search');
    if (searchInput) {
      searchInput.addEventListener('input', debounce(function (e) {
        state.query = e.target.value || '';
        applyFilters();
      }, 160));
    }

    if (els.stateSelect) {
      els.stateSelect.addEventListener('change', function (e) {
        state.state = e.target.value;
        applyFilters();
        syncUrl(false);
      });
    }

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
        state.detailId = null;
        document.body.classList.remove('view-detail');
        setView('active');
      });
    }
    if (els.navArchive) {
      els.navArchive.addEventListener('click', function (e) {
        if (state.view === 'archive' && !state.detailId) return;
        e.preventDefault();
        state.detailId = null;
        document.body.classList.remove('view-detail');
        setView('archive');
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
        var card = e.target.closest('.job-card');
        if (card) openJob(card.getAttribute('data-id'));
      });
      els.grid.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter' && e.key !== ' ') return;
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
      if (e.key !== 'Escape') return;
      if (els.modal && !els.modal.classList.contains('hidden')) { closeModal(); return; }
      if (state.detailId) goHome();
    });
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
      seoStates: document.getElementById('seo-states'),
      seoCategories: document.getElementById('seo-categories'),
      themeToggle: document.getElementById('theme-toggle'),
      navRegistry: document.getElementById('nav-registry'),
      navArchive: document.getElementById('nav-archive'),
      modal: document.getElementById('post-job-modal'),
      toast: document.getElementById('toast')
    };
    bindEvents();
    initTheme();
    loadAll();
  });
})();
