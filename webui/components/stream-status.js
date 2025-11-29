// Stream Status Banner: shows SSE connectivity state using event-bus
import * as bus from "/static/js/event-bus.js";

(function () {
  const ID = 'stream-status-banner';
  const mounted = () => document.getElementById(ID) != null;

  function ensureStyles() {
    if (document.getElementById('stream-status-styles')) return;
    const css = `
    .stream-status-banner { position: fixed; bottom: 12px; left: 12px; z-index: 9999; font-size: 12px; }
    .stream-status-banner .bubble { display: inline-flex; gap: 6px; align-items: center; padding: 6px 10px; border-radius: 16px; box-shadow: 0 2px 6px rgba(0,0,0,0.15); background: #111827; color: #e5e7eb; }
    .stream-status-banner.online .bubble { background: #065f46; color: #ecfdf5; }
    .stream-status-banner.reconnecting .bubble { background: #92400e; color: #fff7ed; }
    .stream-status-banner.stale .bubble { background: #1e3a8a; color: #dbeafe; }
    .stream-status-banner.offline .bubble { background: #7f1d1d; color: #fef2f2; }
    .stream-status-banner .dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; opacity: 0.9; }
    .stream-status-banner .msg { opacity: 0.95; }
    `;
    const style = document.createElement('style');
    style.id = 'stream-status-styles';
    style.textContent = css;
    document.head.appendChild(style);
  }

  function mount() {
    if (mounted()) return;
    ensureStyles();
    const el = document.createElement('div');
    el.id = ID;
    el.className = 'stream-status-banner offline';
    el.innerHTML = `<div class="bubble"><span class="dot"></span><span class="msg">Connecting…</span></div>`;
    document.body.appendChild(el);
  }

  function setState(state, text) {
    const el = document.getElementById(ID);
    if (!el) return;
    el.className = `stream-status-banner ${state}`;
    const msg = el.querySelector('.msg');
    if (msg && text) msg.textContent = text;
  }

  function init() {
    mount();
    let hideTimer = null;

    bus.on('stream.online', () => {
      setState('online', 'Live');
      if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; }
      hideTimer = setTimeout(() => {
        const el = document.getElementById(ID);
        if (el) el.style.display = 'none';
      }, 1500);
    });

    bus.on('stream.offline', (p) => {
      const el = document.getElementById(ID);
      if (el) el.style.display = '';
      const reason = (p && (p.reason || p.error)) ? `: ${String(p.reason || p.error)}` : '';
      setState('offline', `Disconnected${reason}`);
    });

    bus.on('stream.reconnecting', (p) => {
      const el = document.getElementById(ID);
      if (el) el.style.display = '';
      const attempt = p && typeof p.attempt === 'number' ? p.attempt : 1;
      const delay = p && typeof p.delay === 'number' ? p.delay : 0;
      setState('reconnecting', `Reconnecting (attempt ${attempt}, ${delay}ms)…`);
    });

    bus.on('stream.stale', (p) => {
      const el = document.getElementById(ID);
      if (el) el.style.display = '';
      const ms = p && p.ms_since_heartbeat ? p.ms_since_heartbeat : '?';
      setState('stale', `Stale (${ms}ms since heartbeat)`);
    });

    bus.on('stream.retry.success', (p) => {
      // transient success indicator if banner currently visible in reconnect state
      const el = document.getElementById(ID);
      if (el && el.style.display !== 'none') {
        setState('online', 'Recovered');
        setTimeout(() => {
          if (el) el.style.display = 'none';
        }, 1200);
      }
    });

    bus.on('stream.retry.giveup', (p) => {
      const el = document.getElementById(ID);
      if (el) el.style.display = '';
      setState('offline', 'Give up (manual reload)');
    });

    // heartbeat keeps online state sticky
    bus.on('stream.heartbeat', () => {
      // Keep banner hidden if stable
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
