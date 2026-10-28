/* ==========================================================================
   Urban Forest Park — Institutional Cookie & Data Governance Consent Bar
   --------------------------------------------------------------------------
   Shared across every public page (registry, career-pathway hubs, legal
   documents, utilities). Self-contained: injects its own styles so it can
   never drift from the pages that include it.

   Public API
   ----------
   window.ufpOpenCookieConsent()  -> clears the stored choice and reopens the
                                     consent bar (wired to the global footer
                                     "Cookie Preferences" control).
   window.ufpCookieConsent()      -> returns {"accepted" | "essential" | null}.

   Storage
   -------
   localStorage["ufp_cookie_consent"]     "accepted" | "essential"
   localStorage["ufp_cookie_consent_ts"]  ISO-8601 timestamp of the decision

   The decision is mirrored onto <html data-consent="..."> and a
   "ufp:consent-change" CustomEvent is dispatched so future advertising or
   analytics gating can subscribe without touching this file.
   ========================================================================== */
(function () {
  'use strict';

  var CONSENT_KEY = 'ufp_cookie_consent';
  var CONSENT_TS_KEY = 'ufp_cookie_consent_ts';
  var STYLE_ID = 'ufp-consent-styles';
  var VALID_CHOICES = { accepted: 1, essential: 1 };
  var banner = null;

  /* ---------------------------------------------------------------- */
  /* Storage helpers (private browsing / disabled storage safe)        */
  /* ---------------------------------------------------------------- */
  function storageGet(key) {
    try { return window.localStorage.getItem(key); } catch (e) { return null; }
  }
  function storageSet(key, value) {
    try { window.localStorage.setItem(key, value); } catch (e) { /* ignore */ }
  }
  function storageRemove(key) {
    try { window.localStorage.removeItem(key); } catch (e) { /* ignore */ }
  }

  function currentConsent() {
    var value = storageGet(CONSENT_KEY);
    return VALID_CHOICES[value] ? value : null;
  }

  /* ---------------------------------------------------------------- */
  /* Styles                                                            */
  /* ---------------------------------------------------------------- */
  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = [
      '.ufp-cc{position:fixed;left:0;right:0;bottom:0;z-index:2147483647;',
      'background:var(--card,#ffffff);color:var(--ink,#0f172a);',
      'border-top:1px solid var(--border,#e2e8f0);',
      'box-shadow:0 -14px 40px -22px rgba(15,23,42,.35);',
      'transform:translateY(105%);transition:transform .28s ease;will-change:transform;}',
      '.ufp-cc.is-open{transform:translateY(0);}',
      '.ufp-cc[hidden]{display:none;}',
      '.ufp-cc-inner{max-width:var(--maxw,1240px);margin:0 auto;padding:16px 24px;',
      'display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;}',
      '.ufp-cc-text{margin:0;flex:1 1 420px;max-width:78ch;font-size:12.8px;line-height:1.6;',
      'color:var(--ink-2,#334155);}',
      '.ufp-cc-text strong{color:var(--ink,#0f172a);font-weight:700;}',
      '.ufp-cc-short{display:none;}',
      '.ufp-cc-text a{color:var(--accent,#065f46);font-weight:600;text-decoration:underline;',
      'text-underline-offset:2px;}',
      '.ufp-cc-actions{display:flex;align-items:center;gap:9px;flex-wrap:wrap;}',
      '.ufp-cc-btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;',
      'padding:10px 17px;border-radius:8px;border:1px solid transparent;font:inherit;',
      'font-size:12.4px;font-weight:700;letter-spacing:.01em;cursor:pointer;',
      'text-decoration:none;transition:transform .12s ease,filter .12s ease,',
      'border-color .12s ease,color .12s ease;white-space:nowrap;}',
      '.ufp-cc-btn:hover{transform:translateY(-1px);}',
      '.ufp-cc-primary{background:var(--accent,#065f46);color:var(--accent-ink,#ffffff);}',
      '.ufp-cc-primary:hover{filter:brightness(1.08);}',
      '.ufp-cc-secondary{background:transparent;border-color:var(--border-2,#cbd5e1);',
      'color:var(--ink,#0f172a);}',
      '.ufp-cc-secondary:hover{border-color:var(--accent,#065f46);color:var(--accent,#065f46);}',
      '.ufp-cc-link{background:transparent;color:var(--ink-3,#64748b);padding:10px 8px;',
      'text-decoration:underline;text-underline-offset:3px;}',
      '.ufp-cc-link:hover{color:var(--accent,#065f46);}',
      'html.ufp-consent-open body{padding-bottom:118px;}',
      /* Explicit fallbacks for pages that toggle dark mode without the
         registry variable set (defensive; hub/legal/registry pages all
         define the variables so these rarely apply). */
      '[data-theme="dark"] .ufp-cc{background:#111827;color:#f1f5f9;',
      'border-top-color:#1e293b;box-shadow:0 -14px 40px -20px rgba(0,0,0,.7);}',
      '[data-theme="dark"] .ufp-cc-text{color:#cbd5e1;}',
      '[data-theme="dark"] .ufp-cc-text strong{color:#f1f5f9;}',
      '[data-theme="dark"] .ufp-cc-secondary{border-color:#334155;color:#f1f5f9;}',
      '[data-theme="dark"] .ufp-cc-link{color:#94a3b8;}',
      '[data-theme="dark"] .ufp-cc-primary{background:#34d399;color:#052e1f;}',
      '[data-theme="dark"] .ufp-cc-text a{color:#34d399;}',
      '@media (max-width:768px){',
      '.ufp-cc-inner{padding:10px 12px;gap:8px;flex-direction:column;align-items:stretch;}',
      '.ufp-cc-text{flex:1 1 auto;max-width:none;font-size:11.5px;line-height:1.35;',
      'display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:3;overflow:hidden;}',
      '.ufp-cc-long{display:none;}',
      '.ufp-cc-short{display:inline;}',
      '.ufp-cc-text strong{display:none;}',
      '.ufp-cc-actions{width:100%;gap:6px;flex-wrap:nowrap;}',
      '.ufp-cc-primary,.ufp-cc-secondary{flex:1 1 0;min-width:0;justify-content:center;',
      'padding:6px 10px;font-size:11.5px;}',
      '.ufp-cc-link{display:none;}',
      'html.ufp-consent-open body{padding-bottom:116px;}',
      '}',
      '@media (prefers-reduced-motion:reduce){',
      '.ufp-cc{transition:none;}.ufp-cc-btn:hover{transform:none;}',
      '}'
    ].join('');
    document.head.appendChild(style);
  }

  /* ---------------------------------------------------------------- */
  /* Banner                                                            */
  /* ---------------------------------------------------------------- */
  function buildBanner() {
    var el = document.createElement('div');
    el.className = 'ufp-cc';
    el.id = 'ufp-cookie-consent';
    el.setAttribute('role', 'region');
    el.setAttribute('aria-label', 'Cookie and data governance consent');
    el.innerHTML = [
      '<div class="ufp-cc-inner">',
      '  <p class="ufp-cc-text">',
      '    <strong>Institutional Cookie &amp; Telemetry Notice:</strong> ',
      '    <span class="ufp-cc-long">Urban Forest Park utilizes essential storage for interface preferences (including Night Mode) ',
      '    and analytical / advertising cookies (including Google AdSense &amp; Google Analytics) to ',
      '    sustain open-access platform operations. Review our ',
      '    <a href="/cookies.html">Cookie Policy</a> and ',
      '    <a href="/privacy.html">Privacy Policy</a> for statutory details.</span>',
      '    <span class="ufp-cc-short">We use essential storage and analytics / advertising cookies (including Google AdSense) ',
      '    to sustain open access. See our <a href="/cookies.html">Cookie Policy</a> and ',
      '    <a href="/privacy.html">Privacy Policy</a>.</span>',
      '  </p>',
      '  <div class="ufp-cc-actions">',
      '    <button type="button" class="ufp-cc-btn ufp-cc-primary" data-ufp-cc-choice="accepted">Accept All Cookies</button>',
      '    <button type="button" class="ufp-cc-btn ufp-cc-secondary" data-ufp-cc-choice="essential">Essential Only</button>',
      '    <a class="ufp-cc-btn ufp-cc-link" href="/cookies.html#preferences">Cookie Policy</a>',
      '  </div>',
      '</div>'
    ].join('\n');

    el.addEventListener('click', function (event) {
      var btn = event.target && event.target.closest
        ? event.target.closest('[data-ufp-cc-choice]')
        : null;
      if (!btn) return;
      recordChoice(btn.getAttribute('data-ufp-cc-choice'));
    });

    document.body.appendChild(el);
    return el;
  }

  function showBanner() {
    injectStyles();
    if (!banner) banner = buildBanner();
    banner.hidden = false;
    document.documentElement.classList.add('ufp-consent-open');
    /* allow the browser to paint the hidden state before animating in */
    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(function () {
        banner.classList.add('is-open');
      });
    });
  }

  function hideBanner() {
    if (!banner) return;
    banner.classList.remove('is-open');
    document.documentElement.classList.remove('ufp-consent-open');
    window.setTimeout(function () { banner.hidden = true; }, 300);
  }

  function recordChoice(choice) {
    if (!VALID_CHOICES[choice]) return;
    storageSet(CONSENT_KEY, choice);
    storageSet(CONSENT_TS_KEY, new Date().toISOString());
    document.documentElement.setAttribute('data-consent', choice);
    try {
      document.dispatchEvent(new CustomEvent('ufp:consent-change', {
        detail: { consent: choice, recordedAt: new Date().toISOString() }
      }));
    } catch (e) { /* older browsers: no CustomEvent constructor */ }
    hideBanner();
  }

  /* Clear the stored decision and re-ask — the "Cookie Preferences"
     control in the global footer of every page. */
  function reopen() {
    storageRemove(CONSENT_KEY);
    storageRemove(CONSENT_TS_KEY);
    document.documentElement.removeAttribute('data-consent');
    showBanner();
  }

  window.ufpOpenCookieConsent = reopen;
  window.ufpCookieConsent = currentConsent;

  /* ---------------------------------------------------------------- */
  /* Boot                                                              */
  /* ---------------------------------------------------------------- */
  function init() {
    var existing = currentConsent();
    if (existing) document.documentElement.setAttribute('data-consent', existing);

    /* Footer re-trigger — delegated so it also works for elements added
       after load (e.g. inside rendered dossiers). */
    document.addEventListener('click', function (event) {
      var trigger = event.target && event.target.closest
        ? event.target.closest('[data-ufp-cookie-settings]')
        : null;
      if (!trigger) return;
      event.preventDefault();
      reopen();
    });

    if (!existing) window.setTimeout(showBanner, 350);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
