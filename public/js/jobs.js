/* ==========================================================================
   UrbanForestPark — India Green Jobs Board
   js/jobs.js — data loading, filters, ?job= query & hash routing, job
   detail view, dynamic SEO (JobPosting JSON-LD), sharing, partner modal.
   Vanilla JS, no dependencies.
   ========================================================================== */
(function () {
  'use strict';

  /* ------------------------------------------------------------------ */
  /* Config & state                                                      */
  /* ------------------------------------------------------------------ */
  var CONFIG = {
    DATA_URL: 'jobs.json',
    CONTACT_EMAIL: 'arkraj.biswas6@gmail.com',
    ADS_EVERY: 5,            // inject an in-feed ad card after every 5th job
    VALID_DAYS: 90,          // jobPosting validThrough = datePosted + N days
    SITE_URL: 'https://www.urbanforestpark.com/'
  };

  var DEFAULT_TITLE = document.title;
  var DEFAULT_DESC = (document.querySelector('meta[name="description"]') || {}).content || '';

  var state = {
    jobs: [],
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
      pin: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s7-5.6 7-11a7 7 0 10-14 0c0 5.4 7 11 7 11z"/><circle cx="12" cy="10" r="2.6"/></svg>',
      calendar: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M8 3v4M16 3v4M3 10h18"/></svg>',
      arrow: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 5l7 7-7 7"/></svg>',
      back: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5M11 19l-7-7 7-7"/></svg>',
      external: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4h6v6"/><path d="M20 4L10 14"/><path d="M19 13v6a1 1 0 01-1 1H5a1 1 0 01-1-1V6a1 1 0 011-1h6"/></svg>',
      whatsapp: '<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 00-8.6 15.1L2 22l5-1.3A10 10 0 1012 2zm5.5 14.1c-.2.6-1.3 1.2-1.8 1.3-.5.1-1 .1-1.7-.1-1.7-.5-4.7-2.6-6-5.2-.4-.8-.6-1.6-.4-2.3.1-.5.7-1.3 1.1-1.5.3-.2.8-.2 1 0 .2.2 1 1.7 1.1 1.9.1.2.1.4 0 .6-.1.2-.5.7-.6.9-.1.1-.2.3-.1.5.4.8 1.7 2.3 2.8 2.8.2.1.4.1.5-.1.2-.2.7-.7.9-.9.2-.2.4-.2.6-.1.2.1 1.6.9 1.8 1.1.2.2.2.7-.2 1.1z"/></svg>',
      linkedin: '<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M4.98 3.5a2.5 2.5 0 11-.02 5 2.5 2.5 0 01.02-5zM3 9h4v12H3zM9 9h3.8v1.7h.1c.5-1 1.8-2 3.7-2 4 0 4.7 2.6 4.7 6V21h-4v-5.5c0-1.3 0-3-1.9-3s-2.1 1.4-2.1 2.9V21H9z"/></svg>',
      copy: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 012-2h9"/></svg>',
      bulb: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18h6"/><path d="M10 21h4"/><path d="M12 3a6 6 0 00-4 10.5c.7.7 1 1.6 1 2.5h6c0-.9.3-1.8 1-2.5A6 6 0 0012 3z"/></svg>'
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

  function daysSince(dateStr) {
    var d = new Date(dateStr + 'T00:00:00');
    if (isNaN(d.getTime())) return null;
    var today = new Date();
    today.setHours(0, 0, 0, 0);
    return Math.max(0, Math.round((today - d) / 86400000));
  }

  function formatPosted(dateStr) {
    var days = daysSince(dateStr);
    if (days === null) return 'Recently posted';
    if (days === 0) return 'Posted today';
    if (days === 1) return 'Posted yesterday';
    if (days < 7) return 'Posted ' + days + ' days ago';
    var d = new Date(dateStr + 'T00:00:00');
    var opts = { day: 'numeric', month: 'short', year: 'numeric' };
    return 'Posted on ' + d.toLocaleDateString('en-IN', opts);
  }

  function stateLabel(job) {
    if (job.state === 'Multiple States / Remote') return 'Multiple States / Remote';
    return job.city ? job.city + ', ' + job.state : job.state;
  }

  function toast(message) {
    var el = els.toast;
    if (!el) return;
    el.textContent = message;
    el.classList.add('show');
    clearTimeout(toast._t);
    toast._t = setTimeout(function () { el.classList.remove('show'); }, 2200);
  }

  /* ------------------------------------------------------------------ */
  /* Data loading                                                        */
  /* ------------------------------------------------------------------ */
  function loadJobs() {
    els.grid.innerHTML = '<div class="loading-state" role="status">Loading green jobs&hellip;</div>';
    fetch(CONFIG.DATA_URL)
      .then(function (res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .then(function (jobs) {
        jobs.sort(function (a, b) { return (b.date_added || '').localeCompare(a.date_added || ''); });
        state.jobs = jobs;
        state.loaded = true;
        buildStats(jobs);
        populateStateSelect(jobs);
        populateCategoryCounts(jobs);
        injectFeedJsonLd(jobs);
        applyFilters();
        route(true);
      })
      .catch(function (err) {
        els.grid.innerHTML = '<div class="empty-state"><h3>Could not load job listings</h3>' +
          '<p>Please refresh the page. If this persists, check that <code>jobs.json</code> is being served on this domain.</p></div>';
        if (window.console) console.error('[jobs] failed to load listings:', err);
      });
  }

  function buildStats(jobs) {
    var states = {}, orgs = {};
    jobs.forEach(function (j) {
      if (j.state && j.state !== 'Multiple States / Remote') states[j.state] = 1;
      if (j.organization) orgs[j.organization] = 1;
    });
    setText('stat-jobs', String(jobs.length));
    setText('stat-states', String(Object.keys(states).length || 1));
    setText('stat-orgs', String(Object.keys(orgs).length));
  }

  function setText(id, value) {
    var el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function populateStateSelect(jobs) {
    var counts = {};
    jobs.forEach(function (j) {
      if (!j.state) return;
      counts[j.state] = (counts[j.state] || 0) + 1;
    });
    var states = Object.keys(counts).sort();
    var html = '<option value="all">All India (' + jobs.length + ')</option>';
    states.forEach(function (s) {
      html += '<option value="' + escapeHtml(s) + '">' + escapeHtml(s) + ' (' + counts[s] + ')</option>';
    });
    els.stateSelect.innerHTML = html;
  }

  function populateCategoryCounts(jobs) {
    var counts = { all: jobs.length };
    jobs.forEach(function (j) {
      counts[j.category] = (counts[j.category] || 0) + 1;
    });
    document.querySelectorAll('.cat-pill').forEach(function (pill) {
      var cat = pill.getAttribute('data-cat') || 'all';
      var cnt = pill.querySelector('.cnt');
      if (cnt && counts[cat] != null) cnt.textContent = counts[cat];
    });
  }

  /* ------------------------------------------------------------------ */
  /* Filtering & feed rendering                                          */
  /* ------------------------------------------------------------------ */
  function applyFilters() {
    var q = state.query.trim().toLowerCase();
    state.filtered = state.jobs.filter(function (job) {
      if (state.state !== 'all' && job.state !== state.state) return false;
      if (state.category !== 'all' && job.category !== state.category) return false;
      if (state.experience !== 'all' && job.experience_level !== state.experience) return false;
      if (q) {
        var haystack = [
          job.clean_title, job.organization, job.city, job.state,
          job.category, (job.must_have_skills || []).join(' ')
        ].join(' ').toLowerCase();
        if (haystack.indexOf(q) === -1) return false;
      }
      return true;
    });
    renderFeed();
  }

  function renderFeed() {
    var jobs = state.filtered;
    var countEl = els.resultsCount;
    if (countEl) {
      countEl.textContent = jobs.length === 1 ? '1 position' : jobs.length + ' positions';
    }

    if (!state.loaded) return;
    if (!state.jobs.length) {
      els.grid.innerHTML = '<div class="empty-state"><h3>No listings yet</h3><p>New green jobs are added regularly. Check back soon.</p></div>';
      return;
    }
    if (!jobs.length) {
      els.grid.innerHTML = '<div class="empty-state"><h3>No roles match these filters</h3>' +
        '<p>Try a different keyword, state or category — or clear all filters.</p>' +
        '<button class="btn btn-moss" type="button" onclick="document.getElementById(\'clear-filters\').click()">Clear all filters</button></div>';
      return;
    }

    var html = '';
    jobs.forEach(function (job, index) {
      html += jobCardHtml(job);
      var position = index + 1;
      if (position % CONFIG.ADS_EVERY === 0 && position < jobs.length) {
        html += adInFeedHtml();
      }
    });
    els.grid.innerHTML = html;
  }

  function jobCardHtml(job) {
    var skills = job.must_have_skills || [];
    var shown = skills.slice(0, 3);
    var extra = skills.length - shown.length;
    var chips = shown.map(function (s) {
      return '<span class="skill-chip">' + escapeHtml(s) + '</span>';
    }).join('');
    if (extra > 0) chips += '<span class="skill-chip more">+' + extra + ' more</span>';

    return '' +
      '<article class="job-card" data-id="' + escapeHtml(job.id) + '" tabindex="0" role="link" ' +
        'aria-label="View details: ' + escapeHtml(job.clean_title) + ' at ' + escapeHtml(job.organization) + '">' +
        '<div class="jc-top">' +
          '<span class="badge ' + catClass(job.category) + '">' + escapeHtml(job.category) + '</span>' +
          '<span class="badge badge-exp">' + escapeHtml(job.experience_level) + '</span>' +
        '</div>' +
        '<h3 class="jc-title">' + escapeHtml(job.clean_title) + '</h3>' +
        '<p class="jc-org">' + escapeHtml(job.organization) + '</p>' +
        '<div class="jc-meta">' +
          '<span>' + iconSvg('pin') + escapeHtml(stateLabel(job)) + '</span>' +
          '<span>' + iconSvg('calendar') + escapeHtml(formatPosted(job.date_added)) + '</span>' +
        '</div>' +
        '<div class="jc-skills">' + chips + '</div>' +
        '<div class="jc-foot">' +
          '<span class="jc-date">' + escapeHtml(job.date_added) + '</span>' +
          '<span class="jc-view">View details ' + iconSvg('arrow') + '</span>' +
        '</div>' +
      '</article>';
  }

  function adInFeedHtml() {
    return '' +
      '<div class="ad-container ad-infeed" aria-label="Sponsored placement">' +
        '<span class="ad-label">Sponsored &middot; Environmental Partner Space</span>' +
        '<div class="ad-slot">' +
          '<span>Your organisation here — reach India&rsquo;s environmental workforce.</span>' +
          '<a class="ad-cta" href="mailto:' + encodeURIComponent(CONFIG.CONTACT_EMAIL) +
            '?subject=' + encodeURIComponent('Advertising / Partnership on UrbanForestPark Jobs Board') + '">Sponsor this space &rarr;</a>' +
        '</div>' +
      '</div>';
  }

  /* ------------------------------------------------------------------ */
  /* Routing (hash based: #/job/<id>)                                    */
  /* ------------------------------------------------------------------ */
  /*
   * Job URLs come in two flavours, both shareable and crawlable:
   *   1. https://www.urbanforestpark.com/?job=<id>   (preferred; set via history.pushState)
   *   2. https://www.urbanforestpark.com/#/job/<id>  (legacy hash fallback, still parsed)
   * The query parameter form gives Googlebot and AdSense crawlers a distinct URL
   * per listing (fragments are ignored by crawlers).
   */
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

  /* Replace the URL without adding a history entry (used to clean bad deep links). */
  function setUrlQuietly(path) {
    if (window.history && window.history.replaceState) {
      try { window.history.replaceState({}, '', path); } catch (e) { /* ignore */ }
    }
  }

  /* Return to the feed view and drop ?job=… / #/job/… from the URL. */
  function goHome() {
    var path = window.location.pathname;
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
      var job = state.jobs.filter(function (j) { return j.id === id; })[0];
      if (job) {
        state.detailId = id;
        renderDetail(job);
        document.body.classList.add('view-detail');
        if (!initial) window.scrollTo({ top: 0, behavior: 'smooth' });
        updateSeoForJob(job);
        return;
      }
      /* Unknown job id — clean the URL and fall back to the feed */
      if (state.loaded) {
        toast('That job listing was not found.');
        setUrlQuietly(window.location.pathname);
      }
    }
    state.detailId = null;
    document.body.classList.remove('view-detail');
    restoreHomeSeo();
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
  /* Job detail view                                                     */
  /* ------------------------------------------------------------------ */
  function renderDetail(job) {
    var skills = (job.must_have_skills || []).map(function (s) {
      return '<span class="skill-chip">' + escapeHtml(s) + '</span>';
    }).join('');

    var responsibilities = (job.key_responsibilities || []).map(function (r) {
      return '<li>' + escapeHtml(r) + '</li>';
    }).join('');

    var shareUrl = shareableUrl(job.id);
    var waHref = 'https://wa.me/?text=' + encodeURIComponent(job.clean_title + ' at ' + job.organization + ' — ' + shareUrl);
    var liHref = 'https://www.linkedin.com/sharing/share-offsite/?url=' + encodeURIComponent(shareUrl);

    els.detail.innerHTML = '' +
      '<div class="detail-topbar">' +
        '<a class="back-link" href="#" data-action="back">' + iconSvg('back') + ' All green jobs</a>' +
        '<div class="share-row">' +
          '<a class="share-btn share-whatsapp" href="' + waHref + '" target="_blank" rel="noopener noreferrer">' + iconSvg('whatsapp') + 'Share on WhatsApp</a>' +
          '<a class="share-btn share-linkedin" href="' + liHref + '" target="_blank" rel="noopener noreferrer">' + iconSvg('linkedin') + 'Share on LinkedIn</a>' +
          '<button class="share-btn share-copy" type="button" data-action="copy" title="Copies the direct ?job= link for this listing">' + iconSvg('copy') + 'Copy Direct Job Link</button>' +
        '</div>' +
      '</div>' +

      '<div class="detail-card">' +
        '<div class="detail-kicker">' +
          '<span class="badge ' + catClass(job.category) + '">' + escapeHtml(job.category) + '</span>' +
          '<span class="badge badge-exp">' + escapeHtml(job.experience_level) + '</span>' +
          '<span class="badge badge-state">' + iconSvg('pin') + escapeHtml(stateLabel(job)) + '</span>' +
        '</div>' +

        '<h1>' + escapeHtml(job.clean_title) + '</h1>' +
        '<p class="detail-org">' + escapeHtml(job.organization) + '</p>' +
        '<div class="detail-meta">' +
          '<span>' + iconSvg('calendar') + escapeHtml(formatPosted(job.date_added)) + '</span>' +
          '<span>Ref: ' + escapeHtml(String(job.id).slice(0, 18)) + '</span>' +
        '</div>' +

        '<div class="detail-section">' +
          '<h2>Role Summary</h2>' +
          '<p>' + escapeHtml(job.role_summary) + '</p>' +
        '</div>' +

        '<div class="detail-section">' +
          '<h2>Key Responsibilities</h2>' +
          '<ul class="resp-list">' + responsibilities + '</ul>' +
        '</div>' +

        '<div class="detail-section">' +
          '<h2>Must-Have Skills</h2>' +
          '<div class="skills-wrap">' + skills + '</div>' +
        '</div>' +

        adDetailHtml() +

        '<div class="tip-callout">' +
          '<span class="tip-title">' + iconSvg('bulb') + 'Editor&rsquo;s Application Tip</span>' +
          '<p>' + escapeHtml(job.application_tip) + '</p>' +
        '</div>' +

        adDetailHtml() +

        '<div class="apply-block">' +
          '<a class="btn-apply" href="' + escapeHtml(job.apply_url) + '" target="_blank" rel="noopener noreferrer nofollow">' +
            'Apply on Official Portal ' + iconSvg('external') +
          '</a>' +
          '<p class="apply-note">Opens the official application portal in a new tab. ' +
            'Always verify eligibility and deadlines on the employer&rsquo;s page.</p>' +
        '</div>' +

        '<div class="detail-foot">' +
          '<a class="back-link" href="#" data-action="back">' + iconSvg('back') + ' Back to all green jobs</a>' +
          '<div class="share-row">' +
            '<a class="share-btn share-whatsapp" href="' + waHref + '" target="_blank" rel="noopener noreferrer">WhatsApp</a>' +
            '<a class="share-btn share-linkedin" href="' + liHref + '" target="_blank" rel="noopener noreferrer">LinkedIn</a>' +
          '</div>' +
        '</div>' +
      '</div>';
  }

  function adDetailHtml() {
    return '' +
      '<div class="ad-container" style="margin:24px 0;" aria-label="Sponsored placement">' +
        '<span class="ad-label">Sponsored &middot; Environmental Partner Space</span>' +
        '<div class="ad-slot">' +
          '<span>Reach thousands of climate, forestry and ESG professionals every month.</span>' +
          '<a class="ad-cta" href="mailto:' + encodeURIComponent(CONFIG.CONTACT_EMAIL) +
            '?subject=' + encodeURIComponent('Advertising / Partnership on UrbanForestPark Jobs Board') + '">Partner with UrbanForestPark &rarr;</a>' +
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
      navigator.clipboard.writeText(url).then(function () { toast('Job link copied'); },
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
    try { document.execCommand('copy'); toast('Job link copied'); }
    catch (e) { toast('Copy failed — please copy from the address bar'); }
    document.body.removeChild(ta);
  }

  /* ------------------------------------------------------------------ */
  /* Dynamic SEO: title, meta, JobPosting JSON-LD                        */
  /* ------------------------------------------------------------------ */
  function updateSeoForJob(job) {
    document.title = job.clean_title + ' — ' + job.organization + ' | UrbanForestPark Green Jobs';

    var desc = (job.role_summary || '').slice(0, 158);
    var meta = document.querySelector('meta[name="description"]');
    if (meta) meta.setAttribute('content', desc);

    /* Canonical points at the ?job= URL so crawlers index the listing, not the feed */
    var canonical = document.querySelector('link[rel="canonical"]');
    if (canonical) canonical.setAttribute('href', shareableUrl(job.id));

    var ogTitle = document.querySelector('meta[property="og:title"]');
    var ogDesc = document.querySelector('meta[property="og:description"]');
    var ogUrl = document.querySelector('meta[property="og:url"]');
    if (ogTitle) ogTitle.setAttribute('content', document.title);
    if (ogDesc) ogDesc.setAttribute('content', desc);
    if (ogUrl) ogUrl.setAttribute('content', shareableUrl(job.id));

    injectJsonLd(jobPostingSchema(job));
  }

  function restoreHomeSeo() {
    document.title = DEFAULT_TITLE;
    var meta = document.querySelector('meta[name="description"]');
    if (meta && DEFAULT_DESC) meta.setAttribute('content', DEFAULT_DESC);
    var canonical = document.querySelector('link[rel="canonical"]');
    if (canonical) canonical.setAttribute('href', CONFIG.SITE_URL);
    var ogTitle = document.querySelector('meta[property="og:title"]');
    var ogDesc = document.querySelector('meta[property="og:description"]');
    var ogUrl = document.querySelector('meta[property="og:url"]');
    if (ogTitle) ogTitle.setAttribute('content', DEFAULT_TITLE);
    if (ogDesc) ogDesc.setAttribute('content', DEFAULT_DESC);
    if (ogUrl) ogUrl.setAttribute('content', CONFIG.SITE_URL);

    var existing = document.getElementById('job-posting-jsonld');
    if (existing) existing.parentNode.removeChild(existing);
  }

  function jobPostingSchema(job) {
    var posted = new Date(job.date_added + 'T00:00:00');
    var valid = new Date(posted.getTime() + CONFIG.VALID_DAYS * 86400000);

    var descriptionHtml = '' +
      '<p>' + escapeHtml(job.role_summary) + '</p>' +
      '<h3>Key Responsibilities</h3><ul>' +
      (job.key_responsibilities || []).map(function (r) { return '<li>' + escapeHtml(r) + '</li>'; }).join('') +
      '</ul><h3>Must-Have Skills</h3><ul>' +
      (job.must_have_skills || []).map(function (s) { return '<li>' + escapeHtml(s) + '</li>'; }).join('') +
      '</ul>';

    var schema = {
      '@context': 'https://schema.org',
      '@type': 'JobPosting',
      title: job.clean_title,
      description: descriptionHtml,
      identifier: {
        '@type': 'PropertyValue',
        name: 'UrbanForestPark',
        value: job.id
      },
      datePosted: job.date_added,
      validThrough: valid.toISOString().slice(0, 10),
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

  function injectJsonLd(schema) {
    var existing = document.getElementById('job-posting-jsonld');
    if (existing) existing.parentNode.removeChild(existing);
    var script = document.createElement('script');
    script.type = 'application/ld+json';
    script.id = 'job-posting-jsonld';
    script.textContent = JSON.stringify(schema);
    document.head.appendChild(script);
  }

  function injectFeedJsonLd(jobs) {
    if (document.getElementById('feed-jobs-jsonld')) return;
    var schema = {
      '@context': 'https://schema.org',
      '@type': 'ItemList',
      name: 'Green jobs in India — Climate, Forestry, ESG & GIS',
      numberOfItems: jobs.length,
      itemListElement: jobs.slice(0, 20).map(function (job, i) {
        return {
          '@type': 'ListItem',
          position: i + 1,
          name: job.clean_title + ' — ' + job.organization,
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
  /* Partner / post-a-job modal                                          */
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

    var subject = 'Post a green job on UrbanForestPark: ' + (role || org);
    var body = [
      'Organisation: ' + org,
      'Role title: ' + role,
      'Contact email: ' + email,
      '',
      'Details:',
      message,
      '',
      '— Sent from the UrbanForestPark jobs board'
    ].join('\n');

    window.location.href = 'mailto:' + CONFIG.CONTACT_EMAIL +
      '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
    closeModal();
  }

  /* ------------------------------------------------------------------ */
  /* Event wiring                                                        */
  /* ------------------------------------------------------------------ */
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
        pillRow.querySelectorAll('.cat-pill').forEach(function (p) { p.classList.remove('active'); });
        pill.classList.add('active');
        state.category = pill.getAttribute('data-cat') || 'all';
        applyFilters();
      });
    }

    var clearBtn = document.getElementById('clear-filters');
    if (clearBtn) {
      clearBtn.addEventListener('click', function () {
        state.query = ''; state.state = 'all'; state.category = 'all'; state.experience = 'all';
        if (searchInput) searchInput.value = '';
        if (els.stateSelect) els.stateSelect.value = 'all';
        if (expSelect) expSelect.value = 'all';
        if (pillRow) {
          pillRow.querySelectorAll('.cat-pill').forEach(function (p) { p.classList.remove('active'); });
          var all = pillRow.querySelector('[data-cat="all"]');
          if (all) all.classList.add('active');
        }
        applyFilters();
      });
    }

    /* Card clicks → detail view (delegated) */
    if (els.grid) {
      els.grid.addEventListener('click', function (e) {
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
        if (!action) return;
        var name = action.getAttribute('data-action');
        if (name === 'back') {
          e.preventDefault();
          goHome();
        } else if (name === 'copy') {
          copyShareLink(e);
        }
      });
    }

    window.addEventListener('hashchange', function () { route(false); });
    /* Browser back/forward between feed and ?job= detail views */
    window.addEventListener('popstate', function () { route(false); });

    /* Browse by State nav link: leave detail view first if open */
    var browseLink = document.getElementById('nav-browse');
    if (browseLink) {
      browseLink.addEventListener('click', function (e) {
        e.preventDefault();
        if (state.detailId) {
          goHome();
          setTimeout(function () {
            var target = document.getElementById('filter-bar');
            if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }, 60);
        } else {
          var target = document.getElementById('filter-bar');
          if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
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

    /* Modal */
    var openers = document.querySelectorAll('[data-open-modal]');
    openers.forEach(function (btn) {
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
      modal: document.getElementById('post-job-modal'),
      toast: document.getElementById('toast')
    };
    bindEvents();
    loadJobs();
  });
})();
