/* ==========================================================================
   Urban Forest Park - App install & instant job-alert widget (js/pwa.js)
   --------------------------------------------------------------------------
   - "Download / Install App" uses the browser beforeinstallprompt event
     (with an iOS "Share -> Add to Home Screen" hint when no prompt exists).
   - "Enable Instant Job Notifications" requests Notification permission,
     stores ufp_notifications_enabled = "true" and ufp_last_seen_job_id,
     shows a welcome notification and then alerts automatically whenever a
     newer listing appears in jobs.json / global_jobs.json.
   - The x button collapses the panel to the floating "App & Alerts" pill.
   - Registers /sw.js (offline shell + freshness checks + notificationclick).
   ========================================================================== */
(function () {
  'use strict';

  var LS_NOTIFY = 'ufp_notifications_enabled';
  var LS_LAST_SEEN = 'ufp_last_seen_job_id';
  var LS_COLLAPSED = 'ufp_app_widget_collapsed';
  var DATA_URLS = ['jobs.json', 'global_jobs.json'];
  var POLL_MS = 10 * 60 * 1000;

  var initialized = false;
  var deferredPrompt = null;

  function $(id) { return document.getElementById(id); }

  function read(key) {
    try { return window.localStorage.getItem(key); } catch (e) { return null; }
  }
  function store(key, value) {
    try { window.localStorage.setItem(key, value); } catch (e) { /* private mode */ }
  }
  function note(message) {
    var el = $('ufp-app-note');
    if (el) el.textContent = message || '';
  }

  function notificationsEnabled() { return read(LS_NOTIFY) === 'true'; }
  function permissionGranted() {
    return ('Notification' in window) && window.Notification.permission === 'granted';
  }
  function isStandalone() {
    return (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) ||
      window.navigator.standalone === true;
  }
  function isIos() {
    return /iphone|ipad|ipod/i.test(window.navigator.userAgent || '');
  }

  /* ---------------------------------------------------------------------- */
  /* Service worker                                                          */
  /* ---------------------------------------------------------------------- */
  function registerServiceWorker() {
    if (!('serviceWorker' in navigator)) return;
    var https = window.location.protocol === 'https:';
    var local = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    if (!https && !local) return;
    navigator.serviceWorker.register('/sw.js').catch(function (err) {
      if (window.console) console.warn('[pwa] service worker registration failed:', err);
    });
  }

  /* ---------------------------------------------------------------------- */
  /* Newest-job detection (India + Global registries, never mixed)          */
  /* ---------------------------------------------------------------------- */
  function fetchNewestJob() {
    return Promise.all(DATA_URLS.map(function (url) {
      return fetch(url + '?_=' + Date.now(), { cache: 'no-store' })
        .then(function (response) { return response.ok ? response.json() : []; })
        .catch(function () { return []; });
    })).then(function (lists) {
      var best = null;
      lists.forEach(function (list) {
        (Array.isArray(list) ? list : []).forEach(function (job) {
          if (!job || !job.id) return;
          if (!best || String(job.date_added || '') > String(best.date_added || '')) best = job;
        });
      });
      return best;
    });
  }

  function jobLocation(job) {
    if (job.region) return job.city || job.country || job.region;
    if (job.state) return job.city ? job.city + ', ' + job.state : job.state;
    return 'India';
  }

  function showNotification(title, body, url) {
    if (!permissionGranted()) return;
    var options = {
      body: body,
      icon: '/web-app-manifest-192x192.png',
      badge: '/favicon-96x96.png',
      tag: 'ufp-job-alert',
      data: { url: url || '/' }
    };
    if (navigator.serviceWorker && navigator.serviceWorker.getRegistration) {
      navigator.serviceWorker.getRegistration().then(function (registration) {
        if (registration && registration.showNotification) registration.showNotification(title, options);
        else try { new window.Notification(title, options); } catch (e) { /* ignored */ }
      }).catch(function () {
        try { new window.Notification(title, options); } catch (e) { /* ignored */ }
      });
    } else {
      try { new window.Notification(title, options); } catch (e) { /* ignored */ }
    }
  }

  function checkForNewJobs() {
    if (!notificationsEnabled() || !permissionGranted()) return;
    fetchNewestJob().then(function (job) {
      if (!job || !job.id) return;
      var lastSeen = read(LS_LAST_SEEN);
      if (!lastSeen) { store(LS_LAST_SEEN, String(job.id)); return; }
      if (String(job.id) === lastSeen) return;
      store(LS_LAST_SEEN, String(job.id));
      showNotification(
        'New on UrbanForestPark: ' + (job.clean_title || 'New opportunity'),
        (job.organization ? job.organization + ' \u00b7 ' : '') + jobLocation(job) +
          ' \u2014 tap to view and apply',
        '/?job=' + encodeURIComponent(job.id)
      );
    });
  }

  /* ---------------------------------------------------------------------- */
  /* Enable instant notifications                                            */
  /* ---------------------------------------------------------------------- */
  function markNotifyButton() {
    var btn = $('ufp-notify-btn');
    if (!btn) return;
    if (notificationsEnabled() && permissionGranted()) {
      btn.classList.add('is-on');
      btn.textContent = '\ud83d\udd14 Instant Job Alerts Are ON';
    }
  }

  function enableNotifications() {
    if (!('Notification' in window)) {
      note('This browser does not support notifications. You can still install the app and check the registry for new listings.');
      return;
    }
    if (notificationsEnabled() && permissionGranted()) {
      note('Instant job alerts are already enabled on this device. New verified listings are pushed automatically.');
      return;
    }
    if (isIos() && !isStandalone()) {
      note('On iPhone / iPad: tap the Share icon, then "Add to Home Screen", open the installed app and enable alerts there.');
      return;
    }
    window.Notification.requestPermission().then(function (permission) {
      if (permission === 'granted') {
        store(LS_NOTIFY, 'true');
        markNotifyButton();
        fetchNewestJob().then(function (job) {
          if (job && job.id) store(LS_LAST_SEEN, String(job.id));
          showNotification(
            'UrbanForestPark alerts are ON \ud83d\udd14',
            'You will be notified the moment a new JRF, forestry, ESG, grant or global opportunity is verified.',
            '/'
          );
          note('Instant job alerts enabled. New verified listings will reach this device automatically.');
        });
        if (navigator.serviceWorker && navigator.serviceWorker.controller) {
          navigator.serviceWorker.controller.postMessage({ type: 'UFP_CHECK_JOBS' });
        }
      } else {
        store(LS_NOTIFY, 'false');
        note('Notifications are blocked. You can allow them for this site in your browser settings at any time.');
      }
    }).catch(function () {
      note('Could not request notification permission. Please try again from your browser settings.');
    });
  }

  /* ---------------------------------------------------------------------- */
  /* Install / download the app                                              */
  /* ---------------------------------------------------------------------- */
  function installApp() {
    if (isStandalone()) {
      note('The UrbanForestPark app is already installed on this device.');
      return;
    }
    if (deferredPrompt) {
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then(function (choice) {
        note(choice && choice.outcome === 'accepted'
          ? 'Installing the UrbanForestPark app\u2026'
          : 'Installation dismissed \u2014 you can install any time from this panel or your browser menu.');
        deferredPrompt = null;
      }).catch(function () { deferredPrompt = null; });
      return;
    }
    if (isIos()) {
      note('On iPhone / iPad: tap the Share icon, then choose "Add to Home Screen".');
    } else {
      note('Open your browser menu (\u22ee or \u22ef) and choose "Install app" / "Add to Home Screen".');
    }
  }

  /* ---------------------------------------------------------------------- */
  /* Widget show / collapse                                                  */
  /* ---------------------------------------------------------------------- */
  function showWidget(show) {
    var widget = $('ufp-app-widget');
    var pill = $('ufp-app-pill');
    if (!widget || !pill) return;
    widget.hidden = !show;
    pill.hidden = show;
  }

  function init() {
    if (initialized) return;
    initialized = true;
    registerServiceWorker();

    var widget = $('ufp-app-widget');
    var pill = $('ufp-app-pill');
    if (!widget || !pill) return;

    showWidget(read(LS_COLLAPSED) !== '1');

    var closeBtn = $('ufp-app-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', function () {
        showWidget(false);
        store(LS_COLLAPSED, '1');
      });
    }
    pill.addEventListener('click', function () {
      showWidget(true);
      store(LS_COLLAPSED, '0');
      note('');
    });

    var installBtn = $('ufp-install-btn');
    if (installBtn) installBtn.addEventListener('click', installApp);
    var notifyBtn = $('ufp-notify-btn');
    if (notifyBtn) notifyBtn.addEventListener('click', enableNotifications);

    if (notificationsEnabled() && permissionGranted()) markNotifyButton();
    if (isStandalone()) {
      note('App installed \u2014 enable instant alerts below to get new JRF, forestry, ESG and grant listings the moment they are verified.');
    }

    /* Alerts: check shortly after load, on every tab focus, and while open. */
    window.setTimeout(checkForNewJobs, 4000);
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'visible') checkForNewJobs();
    });
    window.addEventListener('focus', checkForNewJobs);
    window.setInterval(checkForNewJobs, POLL_MS);

    if (navigator.serviceWorker) {
      navigator.serviceWorker.addEventListener('message', function (event) {
        var data = event.data || {};
        if (data.type === 'UFP_JOBS_UPDATED') checkForNewJobs();
      });
    }
  }

  window.addEventListener('beforeinstallprompt', function (event) {
    event.preventDefault();
    deferredPrompt = event;
  });

  window.UFPAppWidget = { init: init };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { window.setTimeout(init, 900); });
  } else {
    window.setTimeout(init, 900);
  }
})();
