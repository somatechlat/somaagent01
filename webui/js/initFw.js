import * as initializer from "./initializer.js";
import * as _modals from "./modals.js";
import * as _components from "./components.js";

// initialize required elements
await initializer.initialize();

// NOTE: Alpine core is already loaded via CDN in index.html.
// Importing it again can overwrite the existing Alpine instance and lose plugins such as `collapse`.
// Therefore we intentionally **do not** re-import the Alpine library here.

// add x-destroy directive to alpine
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
