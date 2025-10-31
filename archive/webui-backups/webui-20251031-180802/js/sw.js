// Minimal service worker for offline-friendly UX without aggressive caching.
// This is intentionally lightweight: it just installs/activates cleanly and
// claims clients so updates apply promptly.

self.addEventListener('install', (event) => {
	// Skip waiting so new SW takes control ASAP on next navigation
	self.skipWaiting();
});

self.addEventListener('activate', (event) => {
	// Take control of uncontrolled clients immediately
	event.waitUntil(self.clients.claim());
});

// Pass-through fetch handler: allows future enhancement while avoiding 404s
self.addEventListener('fetch', (event) => {
	// Network-first, no caching here to prevent stale UIs during rapid dev
	event.respondWith(fetch(event.request).catch(() => fetch(event.request)));
});

