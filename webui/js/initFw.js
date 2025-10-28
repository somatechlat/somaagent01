import * as initializer from "./initializer.js";
import * as _modals from "./modals.js";
import * as _components from "./components.js";

// initialize required elements
await initializer.initialize();

// import alpine library as a module, then expose as global `Alpine`
let AlpineModule = null;
try {
  AlpineModule = await import("../vendor/alpine/alpine.min.js");
} catch (e) {
  // if module import fails, try loading the script globally as a fallback
  const s = document.createElement('script');
  s.src = '/vendor/alpine/alpine.min.js';
  s.defer = true;
  document.head.appendChild(s);
  // wait a short while for the script to load
  await new Promise((res) => setTimeout(res, 300));
}

const AlpineCandidate = (AlpineModule && (AlpineModule.default || AlpineModule.Alpine)) || window.Alpine;
if (AlpineCandidate) {
  window.Alpine = AlpineCandidate;
  try { if (window.Alpine.start) window.Alpine.start(); } catch (e) { /* ignore */ }
}

// Load alpine collapse plugin (local-first, CDN fallback) after Alpine is present
(() => {
  function loadPlugin(src, cdnSrc) {
    const s = document.createElement('script');
    s.src = src;
    s.defer = true;
    s.onerror = function () {
      if (cdnSrc) {
        const f = document.createElement('script');
        f.src = cdnSrc;
        f.defer = true;
        document.head.appendChild(f);
      }
    };
    document.head.appendChild(s);
  }

  // Prefer local plugin bundle; fallback to official CDN plugin package
  loadPlugin(
    '/vendor/alpine/alpine.collapse.min.js',
    'https://cdn.jsdelivr.net/npm/@alpinejs/collapse@3.14.3/dist/cdn.min.js'
  );
})();

// add x-destroy directive to alpine (safe-guarded)
if (window.Alpine) {
  Alpine.directive(
    "destroy",
    (el, { expression }, { evaluateLater, cleanup }) => {
      const onDestroy = evaluateLater(expression);
      cleanup(() => onDestroy());
    }
  );

  // add x-create directive to alpine
  Alpine.directive("create", (_el, { expression }, { evaluateLater }) => {
    const onCreate = evaluateLater(expression);
    onCreate();
  });
}
