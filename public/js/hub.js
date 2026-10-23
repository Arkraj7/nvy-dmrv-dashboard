/* ============================================================
   Urban Forest Park - career pathway hub page behaviour.
   Minimal by design: the pages are pre-rendered, so this file
   only powers the theme toggle and the mobile navigation.
   ============================================================ */
(function () {
  'use strict';

  var root = document.documentElement;

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    var meta = document.getElementById('meta-theme-color');
    if (meta) meta.setAttribute('content', theme === 'dark' ? '#0B0F17' : '#F8FAFC');
    var label = document.getElementById('theme-label');
    if (label) label.textContent = theme === 'dark' ? 'Light' : 'Night';
    var btn = document.getElementById('theme-toggle');
    if (btn) {
      btn.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
      btn.setAttribute('aria-label', theme === 'dark' ? 'Switch to light mode' : 'Switch to night mode');
    }
  }

  var current = root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  applyTheme(current);

  var toggle = document.getElementById('theme-toggle');
  if (toggle) {
    toggle.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      try { localStorage.setItem('ufp_theme', next); } catch (e) { /* private mode */ }
      applyTheme(next);
    });
  }

  /* Mobile navigation */
  var navToggle = document.getElementById('nav-toggle');
  var siteNav = document.getElementById('site-nav');
  if (navToggle && siteNav) {
    navToggle.addEventListener('click', function () {
      var open = siteNav.classList.toggle('open');
      navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  /* Registry freshness badge: pre-rendered at build time, refreshed from
     stats.json so the date and both registry counts stay data-derived. */
  function formatBadgeDate(value) {
    var raw = String(value || '').slice(0, 10);
    if (!raw) return '';
    var d = new Date(raw + 'T12:00:00+05:30');
    if (isNaN(d.getTime())) return '';
    return d.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      timeZone: 'Asia/Kolkata'
    });
  }

  function hydrateRegistryBadge() {
    var pill = document.getElementById('registry-refresh-pill');
    if (!pill) return;
    fetch('/stats.json', { cache: 'no-store' })
      .then(function (res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .then(function (stats) {
        if (!stats || typeof stats !== 'object') return;
        var india = typeof stats.active_open_jobs === 'number'
          ? stats.active_open_jobs
          : parseInt(pill.getAttribute('data-india-count') || '0', 10);
        var global = typeof stats.active_global_jobs === 'number'
          ? stats.active_global_jobs
          : parseInt(pill.getAttribute('data-global-count') || '0', 10);
        var dateValue = stats.last_pipeline_run_date_ist ||
          (stats.last_updated_ist ? String(stats.last_updated_ist).slice(0, 10) : '') ||
          pill.getAttribute('data-refresh-date') || '';
        var dateText = formatBadgeDate(dateValue);
        var textEl = document.getElementById('registry-refresh-text');
        if (textEl && dateText) {
          textEl.textContent = 'Registry verified & refreshed: ';
          var strong = document.createElement('strong');
          strong.textContent = dateText + ' IST';
          textEl.appendChild(strong);
        }
        var summary = pill.querySelector('.registry-stats-summary');
        if (summary) {
          summary.textContent = india + ' Active India \u00b7 ' + global +
            (global === 1 ? ' Global Opportunity' : ' Global Opportunities');
        }
        if (dateValue) pill.setAttribute('data-refresh-date', dateValue);
        pill.setAttribute('data-india-count', String(india));
        pill.setAttribute('data-global-count', String(global));
      })
      .catch(function (err) {
        if (window.console) console.warn('[registry] stats refresh unavailable:', err);
      });
  }

  hydrateRegistryBadge();
})();
