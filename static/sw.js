const CACHE_NAME = 'food-health-app-v1';

// Only static shell assets & offline fallback page are cached
const STATIC_ASSETS = [
    '/static/css/style.css',
    '/static/js/pwa_register.js',
    '/static/manifest.json',
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png',
    '/offline/'
];

// Install Event: Cache essential static shell assets & offline page
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[PWA SW] Pre-caching static app shell & offline fallback');
            return cache.addAll(STATIC_ASSETS);
        }).then(() => self.skipWaiting())
    );
});

// Activate Event: Cleanup old cache versions
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cache) => {
                    if (cache !== CACHE_NAME) {
                        console.log('[PWA SW] Removing legacy cache:', cache);
                        return caches.delete(cache);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch Event: Network-first for dynamic content/APIs; static fallback for offline
self.addEventListener('fetch', (event) => {
    const request = event.request;
    const url = new URL(request.url);

    // CRITICAL PRIVACY & SECURITY RULE:
    // Do NOT cache API requests, sensitive endpoints, or non-GET requests
    if (
        request.method !== 'GET' ||
        url.pathname.startsWith('/health-analysis/') ||
        url.pathname.startsWith('/products/lookup/') ||
        url.pathname.startsWith('/accounts/') ||
        url.pathname.startsWith('/admin/')
    ) {
        // Network-only execution for private API and auth routes
        return;
    }

    // For HTML navigation requests (page visits):
    // Try Network first. If offline/network error occurs, serve /offline/ fallback.
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request).catch(() => {
                return caches.match('/offline/').then((cachedOffline) => {
                    if (cachedOffline) {
                        return cachedOffline;
                    }
                    return new Response(
                        '<!DOCTYPE html><html><body><h1>You\'re offline</h1><p>An internet connection is required to scan new products and use AI health analysis.</p></body></html>',
                        { headers: { 'Content-Type': 'text/html' } }
                    );
                });
            })
        );
        return;
    }

    // For static assets (CSS, JS, Manifest, Icons): Stale-while-revalidate / Cache-first
    event.respondWith(
        caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
                return cachedResponse;
            }
            return fetch(request).then((networkResponse) => {
                // Cache valid static asset responses
                if (networkResponse && networkResponse.status === 200 && networkResponse.type === 'basic') {
                    const responseToCache = networkResponse.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, responseToCache);
                    });
                }
                return networkResponse;
            });
        })
    );
});
