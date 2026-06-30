const CACHE_NAME = 'nagar-van-dmrv-v2';
const STATIC_CACHE = 'nagar-van-static-v2';

const STATIC_ASSETS = [
  '/assets/images/tree-svgrepo-com.svg',
  '/assets/css/night-mode.css'
];

self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(STATIC_CACHE).then(cache => cache.addAll(STATIC_ASSETS))
  );
});

self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(names => Promise.all(
      names.filter(n => n !== CACHE_NAME && n !== STATIC_CACHE).map(n => caches.delete(n))
    )).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // Only handle same-origin requests
  if (url.origin !== self.location.origin) return;

  const path = url.pathname;

  // Static assets from assets/ folder - cache-first
  if (path.startsWith('/assets/')) {
    event.respondWith(
      caches.match(event.request).then(cached => cached || fetchAndCache(event.request, STATIC_CACHE))
    );
    return;
  }

  // HTML pages and navigation - network-first
  if (path.endsWith('.html') || event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          const cloned = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, cloned));
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // Everything else - network-first
  event.respondWith(
    fetch(event.request)
      .then(response => {
        const cloned = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, cloned));
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});

function fetchAndCache(request, cacheName) {
  return fetch(request).then(response => {
    const cloned = response.clone();
    caches.open(cacheName).then(cache => cache.put(request, cloned));
    return response;
  });
}
