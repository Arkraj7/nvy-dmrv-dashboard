/* Urban Forest Park — floating "Back to top" control.
 *
 * Self-contained: this script injects the button and its own styles, so the
 * registry, the generated SEO hubs, the legal pages and the dashboard tools
 * all get the same institutional control from a single deferred <script>.
 *
 * Behaviour
 *   - appears once the reader scrolls past the hero (SHOW_AFTER px)
 *   - smooth-scrolls to the top (instant jump when the user prefers reduced
 *     motion)
 *   - follows night mode on every surface: html[data-theme="dark"] (registry,
 *     hubs, legal pages) and html.dark (dashboard tools)
 *   - never overlaps the cookie notice or the PWA app/alerts widget: the
 *     layout() pass measures both and lifts the button above or beside them
 *   - speaks the interface language (EN / Hindi) for its aria-label + title
 */
(function () {
  'use strict';

  if (window.__ufpBackToTop) { return; }
  window.__ufpBackToTop = true;

  var SHOW_AFTER = 440;   /* px of scroll before the control appears     */
  var SIZE = 46;          /* button diameter (also referenced by layout) */
  var GAP = 22;           /* resting distance from the viewport corner   */

  var STYLE_ID = 'ufp-btt-styles';
  var btn = null;
  var ticking = false;

  var CSS = [
    '.ufp-btt{position:fixed;right:22px;bottom:22px;z-index:620;width:46px;height:46px;',
    'display:inline-flex;align-items:center;justify-content:center;padding:0;margin:0;',
    'border:1px solid var(--border-2,#cbd8d0);border-radius:999px;',
    'background:var(--card,#ffffff);color:var(--ink-2,#2f4239);cursor:pointer;',
    'box-shadow:0 16px 34px -16px rgba(3,52,36,.42),0 2px 6px rgba(3,52,36,.08);',
    'opacity:0;visibility:hidden;transform:translateY(10px);',
    'transition:opacity .22s ease,transform .22s ease,visibility .22s ease,',
    'border-color .15s ease,color .15s ease,background .15s ease;}',
    '.ufp-btt.is-visible{opacity:1;visibility:visible;transform:none;}',
    '.ufp-btt:hover,.ufp-btt:focus{border-color:#0f8a5f;color:#0f8a5f;}',
    '.ufp-btt:focus-visible{outline:2px solid #0f8a5f;outline-offset:3px;}',
    '.ufp-btt svg{width:19px;height:19px;}',
    'html[data-theme="dark"] .ufp-btt,html.dark .ufp-btt{background:#101a16;color:#d7e6de;',
    'border-color:rgba(255,255,255,.18);box-shadow:0 18px 36px -18px rgba(0,0,0,.78);}',
    'html[data-theme="dark"] .ufp-btt:hover,html[data-theme="dark"] .ufp-btt:focus,',
    'html.dark .ufp-btt:hover,html.dark .ufp-btt:focus{border-color:#34d399;color:#34d399;}',
    '@media (max-width:640px){.ufp-btt{width:43px;height:43px;right:16px;}}',
    '@media print{.ufp-btt{display:none !important;}}',
    '@media (prefers-reduced-motion:reduce){.ufp-btt{transition:none;}}'
  ].join('');

  function reducedMotion() {
    try {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    } catch (err) {
      return false;
    }
  }

  function isHindi() {
    var root = document.documentElement;
    var lang = (root.getAttribute('data-lang') || root.lang || '').toLowerCase();
    return lang.indexOf('hi') === 0;
  }

  function applyLabel() {
    if (!btn) { return; }
    var text = isHindi() ? '\u090a\u092a\u0930 \u091c\u093e\u090f\u0901' : 'Back to top';
    btn.setAttribute('aria-label', text);
    btn.setAttribute('title', text);
  }

  /* Visible rect of a fixed/absolute element, or null when it is hidden. */
  function visibleRect(el) {
    if (!el) { return null; }
    if (el.hasAttribute && el.hasAttribute('hidden')) { return null; }
    var cs = window.getComputedStyle(el);
    if (!cs || cs.display === 'none' || cs.visibility === 'hidden') { return null; }
    var r = el.getBoundingClientRect();
    return (r.width > 0 && r.height > 0) ? r : null;
  }

  /* Keep the control clear of the cookie notice and the app/alerts widget. */
  function layout() {
    if (!btn) { return; }
    var bottom = GAP;
    var right = GAP;

    var bar = visibleRect(document.getElementById('ufp-cookie-consent'));
    if (bar) {
      bottom = Math.max(bottom, window.innerHeight - bar.top + 10);
    }

    var app = visibleRect(document.getElementById('ufp-app-widget')) ||
              visibleRect(document.getElementById('ufp-app-pill'));
    if (app) {
      var appBottom = window.innerHeight - app.bottom;      /* px above the viewport base */
      var appFromRight = window.innerWidth - app.left;      /* horizontal footprint       */
      if (bottom + SIZE + 8 > appBottom) {
        var leftRoom = app.left - SIZE - 14;
        if (leftRoom >= 12) {
          right = appFromRight + 14;                        /* tuck beside the widget column */
        } else {
          bottom = appBottom + app.height + 12;             /* stack above it (narrow screens) */
        }
      }
    }

    btn.style.bottom = Math.round(bottom) + 'px';
    btn.style.right = Math.round(right) + 'px';
  }

  function onScroll() {
    if (!btn || ticking) { return; }
    ticking = true;
    window.requestAnimationFrame(function () {
      ticking = false;
      var y = window.pageYOffset || document.documentElement.scrollTop || 0;
      var show = y > SHOW_AFTER;
      if (show) { layout(); }
      btn.classList.toggle('is-visible', show);
    });
  }

  function toTop() {
    var behavior = reducedMotion() ? 'auto' : 'smooth';
    try {
      window.scrollTo({ top: 0, left: 0, behavior: behavior });
    } catch (err) {
      window.scrollTo(0, 0);
    }
  }

  function build() {
    if (btn || !document.body) { return; }

    if (!document.getElementById(STYLE_ID)) {
      var style = document.createElement('style');
      style.id = STYLE_ID;
      style.appendChild(document.createTextNode(CSS));
      (document.head || document.documentElement).appendChild(style);
    }

    btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'ufp-btt';
    btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"' +
      ' stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"' +
      ' aria-hidden="true"><path d="M12 19V5"/><path d="M5 12l7-7 7 7"/></svg>';
    btn.addEventListener('click', toTop);
    document.body.appendChild(btn);

    applyLabel();
    document.addEventListener('ufp:langchange', applyLabel);
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', function () {
      if (btn.classList.contains('is-visible')) { layout(); }
    });
    window.addEventListener('orientationchange', function () {
      if (btn.classList.contains('is-visible')) { layout(); }
    });
    onScroll();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }
})();
