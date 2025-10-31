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
}

// Load alpine collapse plugin (local-first, CDN fallback) BEFORE starting Alpine to avoid x-collapse warnings
async function loadAlpineCollapsePlugin() {
  function inject(src) {
    return new Promise((resolve) => {
      const s = document.createElement('script');
      s.src = src;
      s.defer = true;
      s.onload = () => resolve(true);
      s.onerror = () => resolve(false);
      document.head.appendChild(s);
    });
  }
  const okLocal = await inject('/vendor/alpine/alpine.collapse.min.js');
  if (!okLocal) {
    await inject('https://cdn.jsdelivr.net/npm/@alpinejs/collapse@3.14.3/dist/cdn.min.js');
  }
}

await loadAlpineCollapsePlugin();

// Start Alpine after plugins are present
if (window.Alpine && window.Alpine.start) {
  try { window.Alpine.start(); } catch (e) { /* ignore */ }
}

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
