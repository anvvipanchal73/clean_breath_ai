// CleanBreath AI Service Worker – Phase 0 skeleton
// Provides: offline shell caching, last-known AQI cache, push notification handler.
// Full implementation in Phase 1 (cache-busting strategy, background sync).

const CACHE_VERSION = "v1";
const SHELL_CACHE = `cb-shell-${CACHE_VERSION}`;
const DATA_CACHE = `cb-data-${CACHE_VERSION}`;

// App shell assets to cache on install
const SHELL_ASSETS = ["/", "/offline", "/manifest.webmanifest"];

// API patterns to cache with network-first strategy
const API_CACHE_PATTERNS = [/\/api\/v1\/air/, /\/api\/v1\/plan/];

// ---------------------------------------------------------------------------
// Install – pre-cache app shell
// ---------------------------------------------------------------------------
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) => cache.addAll(SHELL_ASSETS))
  );
  self.skipWaiting();
});

// ---------------------------------------------------------------------------
// Activate – clean up old caches
// ---------------------------------------------------------------------------
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== SHELL_CACHE && k !== DATA_CACHE)
          .map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

// ---------------------------------------------------------------------------
// Fetch – network-first for API, cache-first for shell
// ---------------------------------------------------------------------------
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests and cross-origin requests
  if (request.method !== "GET" || url.origin !== self.location.origin) return;

  const isApiRequest = API_CACHE_PATTERNS.some((p) => p.test(url.pathname));

  if (isApiRequest) {
    // Network-first with stale-while-revalidate fallback for air quality data
    event.respondWith(
      caches.open(DATA_CACHE).then(async (cache) => {
        try {
          const networkResponse = await fetch(request);
          if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
          }
          return networkResponse;
        } catch {
          const cached = await cache.match(request);
          return (
            cached ||
            new Response(
              JSON.stringify({ error: "offline", is_stale: true }),
              {
                status: 503,
                headers: { "Content-Type": "application/json" },
              }
            )
          );
        }
      })
    );
  } else {
    // Cache-first for shell
    event.respondWith(
      caches.match(request).then((cached) => cached || fetch(request))
    );
  }
});

// ---------------------------------------------------------------------------
// Push notifications
// ---------------------------------------------------------------------------
self.addEventListener("push", (event) => {
  if (!event.data) return;
  let data;
  try {
    data = event.data.json();
  } catch {
    data = { title: "Air Quality Alert", body: event.data.text() };
  }

  event.waitUntil(
    self.registration.showNotification(data.title || "CleanBreath AI Alert", {
      body: data.body || "Check your current air quality.",
      icon: "/icons/icon-192.png",
      badge: "/icons/icon-192.png",
      tag: "aqi-alert",
      renotify: true,
      requireInteraction: false,
      data: { url: data.url || "/" },
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const targetUrl = event.notification.data?.url || "/";
  event.waitUntil(
    self.clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then((clients) => {
        const existing = clients.find((c) => c.url === targetUrl && "focus" in c);
        return existing ? existing.focus() : self.clients.openWindow(targetUrl);
      })
  );
});
