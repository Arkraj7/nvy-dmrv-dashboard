/* ==========================================================================
   Urban Forest Park — consent-gated Google tags
   --------------------------------------------------------------------------
   Nothing is requested from Google until the visitor chooses "Accept All
   Cookies" in the shared consent bar (see /js/consent.js).

   * Consent Mode v2 defaults are set to denied before any tag can load.
   * GA4 is injected only after acceptance.
   * AdSense is injected only after acceptance, and only on pages that opt in
     with ``window.ufpAdsClient`` (currently the homepage).
   * The loader listens for ``ufp:consent-change`` so an in-page decision takes
     effect immediately without a reload.

   Storage key: localStorage["ufp_cookie_consent"] = "accepted" | "essential".
   ========================================================================== */
(function () {
  'use strict';

  var CONSENT_KEY = 'ufp_cookie_consent';
  var GA_ID = 'G-4E7BLPFWP7';
  var loaded = { ga: false, ads: false };

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };

  function consentPayload(value) {
    return {
      ad_storage: value,
      ad_user_data: value,
      ad_personalization: value,
      analytics_storage: value
    };
  }

  /* Must run before gtag.js is requested. */
  window.gtag('consent', 'default', {
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    analytics_storage: 'denied',
    functionality_storage: 'granted',
    security_storage: 'granted',
    wait_for_update: 500
  });

  function readConsent() {
    try { return window.localStorage.getItem(CONSENT_KEY); } catch (e) { return null; }
  }

  function injectScript(src, attributes) {
    var script = document.createElement('script');
    script.async = true;
    script.src = src;
    if (attributes) {
      Object.keys(attributes).forEach(function (name) {
        script.setAttribute(name, attributes[name]);
      });
    }
    document.head.appendChild(script);
    return script;
  }

  function loadAnalytics() {
    if (loaded.ga) return;
    loaded.ga = true;
    injectScript('https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(GA_ID));
    window.gtag('js', new Date());
    window.gtag('config', GA_ID);
  }

  function loadAdvertising() {
    if (loaded.ads || !window.ufpAdsClient) return;
    loaded.ads = true;
    injectScript(
      'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=' +
        encodeURIComponent(window.ufpAdsClient),
      { crossorigin: 'anonymous' }
    );
  }

  function grant() {
    window.gtag('consent', 'update', consentPayload('granted'));
    loadAnalytics();
    loadAdvertising();
  }

  function deny() {
    window.gtag('consent', 'update', consentPayload('denied'));
  }

  function apply(choice) {
    if (choice === 'accepted') {
      grant();
    } else {
      deny();
    }
  }

  apply(readConsent());

  document.addEventListener('ufp:consent-change', function (event) {
    apply(event && event.detail ? event.detail.consent : readConsent());
  });
})();
