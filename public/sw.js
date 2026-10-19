/* ==========================================================================
   Urban Forest Park - service worker (sw.js)
   --------------------------------------------------------------------------
   1. Offline-first shell: caches the registry shell, styles, scripts and the
      latest jobs.json / global_jobs.json snapshot so the app opens without a
      network connection.
   2. Freshness discipline: data files are served network-first (the reader
      always sees the newest registry run when online; the cached snapshot is
      used when offline).
   3. Instant alerts: pages can send { type: 'UFP_CHECK_JOBS' } and the worker
      fetches stats.json + jobs.json + global_jobs.json, compares the newest
      record and broadcasts { type: 'UFP_JOBS_UPDATED', job } to open windows,
      which trigger registration.showNotification() in the page context.
   ========================================================================== */
'use strict';

/* Bump this cache name whenever the shell CSS/JS changes, so installed
   clients replace the old interface instead of serving it cache-first. */
var CACHE_NAME = 'ufp-shell-v2';
var DATA_FILES = ['/jobs.json', '/global_jobs.json', '/archive.json', '/global_archive.json', '/stats.json', '/daily_digest.json'];
var PRECACHE = [
  '/',
  '/',
  '/manifest.json',
  '/styles/jobs.css',
  '/js/i18n.js',
  '/js/jobs.js',
  '/js/pwa.js',
  '/favicon.svg',
  '/favicon-96x96.png',
  '/web-app-manifest-192x192.png',
  '/web-app-manifest-512x512.png'
];

function precache() {
  return caches.open(CACHE_NAME).then(function (cache) {
    return Promise.all(
      PRECACHE.concat(DATA_FILES).map(function (url) {
        return cache.add(new Request(url, { cache: 'reload' })).catch(function () {
          /* A single missing asset must never block the install. */
        });
      })
    );
  });
}

self.addEventListener('install', function (event) {
  event.waitUntil(precache().then(function () { return self.skipWaiting(); }));
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (key) {
        return key === CACHE_NAME ? null : caches.delete(key);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

function isDataRequest(url) {
  return /\.json$/.test(url.pathname);
}

function isStaticAsset(url) {
  return url.pathname.indexOf('/styles/') === 0 ||
    url.pathname.indexOf('/js/') === 0 ||
    url.pathname.indexOf('/assets/') === 0 ||
    /\.(css|js|png|jpg|jpeg|svg|ico|webp|woff2?)$/.test(url.pathname);
}

self.addEventListener('fetch', function (event) {
  var request = event.request;
  if (request.method !== 'GET') return;
  var url;
  try { url = new URL(request.url); } catch (e) { return; }
  if (url.origin !== self.location.origin) return;

  /* Registry data: network-first, cached snapshot as the offline fallback. */
  if (isDataRequest(url)) {
    event.respondWith(
      fetch(request).then(function (response) {
        if (response && response.ok) {
          var copy = response.clone();
          caches.open(CACHE_NAME).then(function (cache) { cache.put(request, copy); });
        }
        return response;
      }).catch(function () {
        return caches.match(request).then(function (cached) {
          return cached || new Response('[]', { headers: { 'Content-Type': 'application/json' } });
        });
      })
    );
    return;
  }

  /* Navigations: network-first with cached shell fallback. */
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).then(function (response) {
        if (response && response.ok) {
          var copy = response.clone();
          caches.open(CACHE_NAME).then(function (cache) { cache.put(request, copy); });
        }
        return response;
      }).catch(function () {
        return caches.match(request).then(function (cached) {
          return cached || caches.match('/') || caches.match('/');
        });
      })
    );
    return;
  }

  /* Static assets: cache-first with background fill. */
  if (isStaticAsset(url)) {
    event.respondWith(
      caches.match(request).then(function (cached) {
        if (cached) return cached;
        return fetch(request).then(function (response) {
          if (response && response.ok) {
            var copy = response.clone();
            caches.open(CACHE_NAME).then(function (cache) { cache.put(request, copy); });
          }
          return response;
        });
      })
    );
  }
});

/* ------------------------------------------------------------------------ */
/* Instant job alert checks (invoked from the page via postMessage)          */
/* ------------------------------------------------------------------------ */
function newestJob() {
  return Promise.all(DATA_FILES.slice(0, 2).map(function (file) {
    return fetch(file, { cache: 'no-store' })
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

self.addEventListener('message', function (event) {
  var data = event.data || {};
  if (data.type === 'UFP_CHECK_JOBS') {
    event.waitUntil(
      newestJob().then(function (job) {
        if (!job) return;
        return self.clients.matchAll({ type: 'window', includeUncontrolled: true })
          .then(function (clients) {
            clients.forEach(function (client) {
              client.postMessage({ type: 'UFP_JOBS_UPDATED', job: job });
            });
          });
      })
    );
  }
});

self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  var target = (event.notification.data && event.notification.data.url) || '/';
  var absolute;
  try { absolute = new URL(target, self.location.origin).href; }
  catch (e) { absolute = self.location.origin + '/'; }
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (clients) {
      for (var i = 0; i < clients.length; i += 1) {
        if (clients[i].url.indexOf(self.location.origin) === 0 && 'focus' in clients[i]) {
          if ('navigate' in clients[i]) clients[i].navigate(absolute).catch(function () {});
          return clients[i].focus();
        }
      }
      if (self.clients.openWindow) return self.clients.openWindow(absolute);
      return null;
    })
  );
});
