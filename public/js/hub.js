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
    if (meta) meta.setAttribute('content', theme === 'dark' ? '#0D131A' : '#F3F7F4');
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
})();
