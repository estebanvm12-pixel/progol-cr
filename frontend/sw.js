/**
 * ProGol CR — Service Worker v2.0
 * Estrategia: Network-first para datos, Cache-first para assets estáticos
 */

const CACHE_VERSION = 'progolcr-v2';
const STATIC_CACHE  = `${CACHE_VERSION}-static`;
const DATA_CACHE    = `${CACHE_VERSION}-data`;

// Assets que siempre se cachean (shell de la app)
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/styles.css',
  '/app.js',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/offline.html',
];

// ── Install: pre-cachear shell ────────────────────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then(cache => {
      return cache.addAll(STATIC_ASSETS).catch(err => {
        console.warn('[SW] Pre-cache parcial:', err);
      });
    })
  );
  self.skipWaiting();
});

// ── Activate: limpiar caches viejos ──────────────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(k => k.startsWith('progolcr-') && k !== STATIC_CACHE && k !== DATA_CACHE)
          .map(k => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

// ── Fetch: estrategia mixta ───────────────────────────────────────────────────
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // WebSocket: no interceptar
  if (url.protocol === 'ws:' || url.protocol === 'wss:') return;

  // POST / APIs: siempre network, nunca cache
  if (request.method !== 'GET') return;

  // Assets estáticos: cache-first
  if (isStaticAsset(url.pathname)) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // Páginas HTML: network-first con fallback offline
  if (request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(networkFirstWithOfflineFallback(request));
    return;
  }

  // Por defecto: network-first
  event.respondWith(networkFirst(request));
});

function isStaticAsset(pathname) {
  return /\.(css|js|png|jpg|svg|ico|woff2?|ttf)$/.test(pathname)
    || pathname.startsWith('/icons/');
}

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return new Response('Asset no disponible offline', { status: 503 });
  }
}

async function networkFirst(request) {
  try {
    const response = await fetch(request, { timeout: 8000 });
    if (response.ok) {
      const cache = await caches.open(DATA_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    return cached || new Response('{}', { headers: { 'Content-Type': 'application/json' } });
  }
}

async function networkFirstWithOfflineFallback(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    if (cached) return cached;
    const offlinePage = await caches.match('/offline.html');
    return offlinePage || new Response(
      `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>ProGol CR</title>
       <meta name="viewport" content="width=device-width,initial-scale=1">
       <style>body{font-family:system-ui;background:#0f172a;color:#e2e8f0;display:flex;
       align-items:center;justify-content:center;height:100vh;text-align:center;margin:0}
       .logo{font-size:40px;margin-bottom:16px}.title{font-size:24px;font-weight:700;
       color:#f5c842}.sub{color:#94a3b8;margin-top:8px;font-size:14px}
       .btn{margin-top:20px;padding:12px 24px;background:#f5c842;color:#0f172a;
       border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:14px}</style>
       </head><body><div><div class="logo">⚽</div>
       <div class="title">ProGol CR</div>
       <div class="sub">Sin conexión · Los pronósticos se cargarán cuando vuelvas online</div>
       <button class="btn" onclick="location.reload()">Reintentar</button>
       </div></body></html>`,
      { headers: { 'Content-Type': 'text/html' } }
    );
  }
}

// ── Push Notifications ────────────────────────────────────────────────────────
self.addEventListener('push', event => {
  if (!event.data) return;

  let payload;
  try { payload = event.data.json(); }
  catch { payload = { title: 'ProGol CR', body: event.data.text() }; }

  const options = {
    body:    payload.body    || '¡Nuevo pick disponible!',
    icon:    payload.icon    || '/icons/icon-192.png',
    badge:   payload.badge   || '/icons/icon-96.png',
    image:   payload.image,
    tag:     payload.tag     || 'progolcr-pick',
    renotify: true,
    vibrate: [200, 100, 200],
    data:    payload.data    || { url: '/' },
    actions: payload.actions || [
      { action: 'view',    title: '📊 Ver análisis' },
      { action: 'dismiss', title: 'Cerrar' },
    ],
  };

  event.waitUntil(
    self.registration.showNotification(payload.title || 'ProGol CR', options)
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  if (event.action === 'dismiss') return;

  const targetUrl = event.notification.data?.url || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
      for (const client of clientList) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.navigate(targetUrl);
          return client.focus();
        }
      }
      return clients.openWindow(targetUrl);
    })
  );
});

// ── Background Sync (picks del día al volver online) ─────────────────────────
self.addEventListener('sync', event => {
  if (event.tag === 'sync-picks') {
    event.waitUntil(syncPicksInBackground());
  }
});

async function syncPicksInBackground() {
  try {
    const response = await fetch('/api/picks/today');
    if (response.ok) {
      const data = await response.json();
      const cache = await caches.open(DATA_CACHE);
      await cache.put('/api/picks/today', new Response(JSON.stringify(data)));
    }
  } catch (err) {
    console.warn('[SW] Background sync failed:', err);
  }
}
