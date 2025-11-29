# Canonical Web UI i18n Roadmap for SomaAgent01

## Overview
This document defines the **canonical roadmap** for turning the entire Web UI of the **SomaAgent01** project into a fully internationalised (i18n) product.  It follows the Vibe coding standards, provides a clean architecture, and is ready for production deployment.

---

## 1️⃣ Scope – What must be translated

| UI Area | Example English strings (extracted) | Why it needs i18n |
|--------|--------------------------------------|-------------------|
| **Header / Sidebar** | “Reset Chat”, “New Chat”, “Load Chats”, “Save Chat”, “Restart”, “Settings”, “Notifications”, “Memory”, “Language”, “English”, “Spanish” | Core actions – users must understand them in any locale. |
| **Agent Config panel** (the block you quoted) | “Agent parameters.”, “Default agent profile”, “Subdirectory of /knowledge folder”, “'default' subfolder is always imported and contains framework knowledge.” | Configuration text appears in the Settings modal – must be localisable. |
| **Settings modal** | “Save”, “Cancel”, tab titles (Agent, Model, Scheduler, System), section titles, field labels, placeholders, tooltips. |
| **Toast / Notification messages** | “Error loading”, “No data”, “Clear All”, “Create”, “Mark Read”. |
| **Tooltips / ARIA labels** | “Refresh”, “Toggle Sidebar”, “Open Modal”, etc. |
| **HTML meta data** | `<title>Agent Zero</title>`, `alt` attributes, `aria‑label`s. |
| **Help / Docs links** | “How to use”, “Documentation”, etc. |
| **Static page text** (index.html, help pages) | Any hard‑coded headings or paragraphs. |

> **Result:** Every user‑facing string will be replaced by a lookup key (e.g. `i18n.t('settings.save')`).

---

## 2️⃣ File‑system layout (the “perfect pattern”)

```
webui/
│
├─ i18n/
│   ├─ en.json          ← English dictionary (source of truth)
│   ├─ es.json          ← Spanish dictionary (initial translation)
│   └─ …                ← Future language files
│
├─ js/
│   ├─ i18n.js          ← Loader + `t(key)` helper
│   ├─ initFw.js        ← Early bootstrap that loads the default language
│   └─ *.js             ← UI modules (settings.js, notificationsStore.js, …) – now call `i18n.t(...)`
│
├─ components/…         ← Alpine stores / components (use `i18n.t`)
│
└─ index.html           ← `base href="/static/"` + placeholder for language selector
```
* **Static mount** – FastAPI already serves `webui/` under `/static/`.  
* **Loader** – `i18n.js` fetches `/static/i18n/<lang>.json` once at start and caches the dictionary.  
* **Fallback** – If a key is missing, the loader returns the English value and logs a warning.  
* **Hot‑swap** – Selecting a new language calls `i18n.load('es')` (or any locale) and forces Alpine to re‑evaluate all stores, updating the UI instantly without a page reload.

---

## 3️⃣ Step‑by‑step implementation

| # | Action | Files / Artefacts | What to do |
|---|--------|-------------------|------------|
| **1** | **Create the English dictionary** | `webui/i18n/en.json` | Populate with every literal that currently appears in the UI. Use hierarchical keys (`settings.save`, `agentConfig.profile.label`, `tooltip.refresh`). |
| **2** | **Create the Spanish dictionary** | `webui/i18n/es.json` | Copy the keys from `en.json` and provide Spanish translations. |
| **3** | **Improve the loader** | `webui/js/i18n.js` | Ensure it fetches from `/static/i18n/<lang>.json` and falls back to English when a key is missing. |
| **4** | **Bootstrap the default language** | `webui/js/initFw.js` | Add `await i18n.load('en');` before any UI module is imported. |
| **5** | **Replace hard‑coded strings** | All `.js` files, `index.html`, component templates | Search for literal strings and replace them with `i18n.t('key')`. Example: `const title = "Agent Config"` → `const title = i18n.t('agentConfig.title')`. |
| **6** | **Add any missing keys** | `en.json` | Whenever a literal is found that has no key, add it to the JSON with a clear hierarchical name. |
| **7** | **Language selector component** | New file `webui/components/language-selector.js` (or inline in HTML) | Simple `select>` bound to an Alpine store. On change: `await i18n.load(lang); Alpine.store('root').refresh();` |
| **8** | **Wire selector to a global Alpine store** | `webui/js/initFw.js` → `Alpine.store('i18nStore')` | Store holds the current `lang` and a `setLang()` method that calls the loader and refreshes UI. |
| **9** | **Update tooltips / ARIA labels** | HTML & component templates | Replace `title="Refresh"` / `aria-label="Close"` with `x-bind:title="i18n.t('tooltip.refresh')"` etc. |
| **10** | **Unit tests for i18n** | `tests/unit/test_i18n.py` | Verify that loading Spanish returns the correct strings and that missing keys fall back to English. |
| **11** | **Run full test suite** | `pytest -q` + Playwright UI tests | Ensure no 404s for `/static/i18n/*.json` and that UI behaves correctly after a language change. |
| **12** | **Documentation** | `docs/development-manual/i18n.md` | Explain the key‑naming convention, how to add a new language, and how the loader works. |

---

## 4️⃣ Sample English → Spanish dictionary (partial)

```json
{
  "resetChat": "Reset Chat",
  "newChat": "New Chat",
  "loadChats": "Load Chats",
  "saveChat": "Save Chat",
  "restart": "Restart",
  "settings": "Settings",
  "notifications": "Notifications",
  "memory": "Memory",
  "language": "Language",
  "english": "English",
  "spanish": "Spanish",

  "agentConfig": {
    "title": "Agent Config",
    "description": "Agent parameters.",
    "profileLabel": "Default agent profile",
    "knowledgeLabel": "Knowledge subdirectory",
    "knowledgeNote": "'default' subfolder is always imported and contains framework knowledge."
  },

  "settings": {
    "title": "Settings",
    "save": "Save",
    "cancel": "Cancel",
    "tabs": {
      "agent": "Agent",
      "model": "Model",
      "scheduler": "Scheduler",
      "system": "System"
    }
  },

  "tooltip": {
    "refresh": "Refresh",
    "toggleSidebar": "Toggle Sidebar",
    "openModal": "Open Modal"
  },

  "toast": {
    "errorLoading": "Error loading",
    "noData": "No data",
    "clearAll": "Clear All",
    "create": "Create",
    "markRead": "Mark Read"
  }
}
```
*The Spanish file (`es.json`) contains the same keys with the corresponding Spanish values (e.g., `"resetChat": "Reiniciar chat"`).*

---

## 5️⃣ Automated extraction of missing strings

A tiny utility (`tools/extract_ui_strings.py`) can be run once to pull every literal from the `webui/` folder and generate a skeleton `en.json`. After the first run you simply tidy up the keys (group them logically) and add the Spanish values.

```python
# tools/extract_ui_strings.py
import pathlib, re, json
ROOT = pathlib.Path(__file__).parent.parent / "webui"
PATTERNS = [
    ("js",   r'"([^\\"]{2,})"'),      # double‑quoted strings in JS
    ("html", r'>\s*([^<]{2,})\s*<')   # text between HTML tags
]

def collect():
    strings = set()
    for f in ROOT.rglob("*.*"):
        txt = f.read_text(encoding="utf-8")
        for ext, pat in PATTERNS:
            if f.suffix.lstrip('.') == ext:
                for m in re.finditer(pat, txt):
                    s = m.group(1).strip()
                    if s and not s.isnumeric():
                        strings.add(s)
    return sorted(strings)

if __name__ == "__main__":
    out = {"en": {}}
    for s in collect():
        key = "ui." + re.sub(r'\s+', '_', s.lower())
        out["en"][key] = s
    pathlib.Path("webui/i18n/en.json").write_text(
        json.dumps(out["en"], indent=2, ensure_ascii=False)
    )
    print(f"Extracted {len(out['en'])} strings → en.json")
```
Run it with `python tools/extract_ui_strings.py`; then edit the generated keys to the hierarchical form shown above and add the Spanish values.

---

## 6️⃣ Testing & Validation checklist

| ✅ | Validation |
|---|------------|
| 1 | Every UI string appears as a key in `en.json`. |
| 2 | Each key also exists in `es.json` (or falls back to English). |
| 3 | Switching language via the selector updates the UI instantly, no page reload. |
| 4 | No console warnings about missing translations. |
| 5 | Playwright UI tests still pass (they use element IDs, not text). |
| 6 | All `aria‑label` and tooltip attributes now use `i18n.t`. |
| 7 | Documentation is up‑to‑date and describes how to add new languages. |

---

## 7️⃣ Next concrete step

**Choose where the language selector should live**:
* **Option A – Header bar** (top‑right, next to the user avatar).  
* **Option B – Settings modal** (its own tab).

Once you decide, I will:
1. Add the selector component file.
2. Wire it to the global `i18nStore`.
3. Run the extraction script, merge the generated keys into `en.json`, and add the missing Spanish translations.
4. Run the full test suite to confirm everything works.

*Let me know the preferred placement, and we’ll finish the integration in a single commit.* 🚀
