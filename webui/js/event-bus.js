// Minimal event bus for UI modules
// API: on(event, handler) => unsubscribe fn; emit(event, payload); once(event, handler)
// Namespacing: use dot notation (e.g., 'ui.status.progress'); wildcard subscription not implemented for simplicity.

const handlers = new Map(); // eventName -> Set<fn>

export function on(event, fn) {
  if (!handlers.has(event)) handlers.set(event, new Set());
  handlers.get(event).add(fn);
  return () => off(event, fn);
}

export function off(event, fn) {
  const set = handlers.get(event);
  if (set) {
    set.delete(fn);
    if (set.size === 0) handlers.delete(event);
  }
}

export function once(event, fn) {
  const wrap = (payload) => {
    try { fn(payload); } finally { off(event, wrap); }
  };
  return on(event, wrap);
}

export function emit(event, payload) {
  const set = handlers.get(event);
  if (set) {
    // shallow copy iteration to allow unsubscribe during emit
    [...set].forEach((fn) => {
      try { fn(payload); } catch (e) { console.error('Event bus handler error', event, e); }
    });
  }
}

// Health introspection (optional)
export function listenerCount(event) {
  const set = handlers.get(event);
  return set ? set.size : 0;
}

export function events() {
  return [...handlers.keys()];
}

// Global convenience (optional; non-destructive)
if (!globalThis.eventBus) {
  globalThis.eventBus = { on, off, once, emit, listenerCount, events };
}

export default { on, off, once, emit, listenerCount, events };
