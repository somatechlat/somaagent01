// Track all created stores
const stores = new Map();

/**
 * Creates a store that can be used to share state between components.
 * Uses initial state object and returns a proxy to it that uses Alpine when initialized
 * @template T
 * @param {string} name
 * @param {T} initialState
 * @returns {T}
 */
export function createStore(name, initialState) {
  const proxy = new Proxy(initialState, {
    set(target, prop, value) {
      const store = globalThis.Alpine?.store(name);
      if (store) store[prop] = value;
      else target[prop] = value;
      return true;
    },
    get(target, prop) {
      const store = globalThis.Alpine?.store(name);
      if (store) return store[prop];
      return target[prop];
    }
  });

  if (globalThis.Alpine) {
    globalThis.Alpine.store(name, initialState);
  } else {
  i18n.t('ui_i18n_t_ui_i18n_t_ui_alpine_init')t('ui_i18n_t_ui_i18n_t_ui_i18n_t_ui_alpine_init')", () => Alpine.store(name, initialState));
  }

  // Si18n.t('ui_i18n_t_ui_alpine_init')set(name, proxyi18n.t('ui_i18n_t_ui_alpine_init')T} */ (proxy); // explicitly cast for linter support
}

// -------------------------------------------------------------------
// Helper: create a store for i18n locale persistence (VIBE compliant).
// -------------------------------------------------------------------
// The UI now includes a li18n.t('ui_i18n_t_ui_i18n_t_ui_en')gles between "i18i18n.t('ui_i18n_t_ui_i18n_t_ui_es')ui_i18n_t_ui_en')" and "i18n.t('ui_i18n_t_ui_i18n_t_ui_i18n_ti18n.t('ui_i18n_t_ui_en')e expose a dedicated Alpinei18n.t('ui_i18n_t_ui_es')18n.t('ui_i18i18n_t_ui_i18n_t_ui_en_ui_i18n_t_ui_i18ni18n_t_ui_i18n_i18n.t('ui_i18n_t_ui_i18nlocale')ad_write_the_current_locale_the_vali18n.t('ui_i18n_t_ui_i18n_t_ui_localei18n.t('ui_under_the_key_i18n_t_ui_i18n_t_ui_i18n_t_ui_locale_to_survive_page_reloads_this_function_should_be_callei18n_t_ui_i18n_t_ui_locale_ootstrap_export_funci18n_t_ui_localstorage_alestore_const_saved_typeof_localstorage_i18n_t_ui_i18n_t_ui_i18n_t_ui_undefined_localstorage_getitem_i18n_t_ui_i18n_t_uii18n_t_ui_i18n_t_ui_undefined_null_const_initial_saved_i18n_t_ui_i18n_t_ui_locale_ui_i18n_t_ui_es_i18n_t_ui_i18n_t_ui_i18n_t_i18n_t_ui_i18n_t_ui_es_n_t_ui_i18n_t_i18n_t_ui_i18n_t_ui_es_defaulti18n_t_ui_i18n_t_ui_en_the_store_shape_matches_ui_expectations_store_i18nlocale_locale_const_store_createstore_i18n_t_ui_i18n_t_ui_i18n_t_ui_i18nloci18n_t_ui_i18n_t_ui_i18nlocale_al_keep')i18n_t_ui_i18nlocale'))"i18n.t('ui_i18n_t_ui_i18n_t_ui_i18nloci18n.t('ui_i18n_t_ui_i18nloci18n.t('ui_localstorage')/ Keep `localStorage` in syni18n.t('ui_i18n_t_ui_i18n_t_i18n_t')'ui_localstorage')typeofi18n.t('ui_proxy_already_forwards_set_operations_to_the_alpine_store_we_add_a_watcher_alpine_does_not_provide_a_native_watcher_for_arbitrary_stores_so_we_use_a_simple_interval_poll_lightweight_acceptable_for_a_small_ui_let_last_store_value_setinterval_if_store_value_last_last_store_value_try_localstorage_setitem_i18n_t')'ui_i18n_t_i18n.t('i18n.t('ui_i18n_t_ui_locale')')')", store.value); } catch (_) {}
      }
    }, 500);
  }
  return store;
}

/**
 * Get an existing store by name
 * @template T
 * @param {string} name
 * @returns {T | undefined}
 */
export function getStore(name) {
  return /** @type {T | undefined} */ (stores.get(name));
}