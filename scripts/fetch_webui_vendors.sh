#!/usr/bin/env bash
set -euo pipefail

# Downloads vendor assets used by the web UI into agent-zero/webui/vendor
# Files are saved with the exact paths/names expected by the frontend.

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WEBUI_DIR="$ROOT_DIR/webui"

echo "Web UI dir: $WEBUI_DIR"

mkdir -p "$WEBUI_DIR/vendor/marked"
mkdir -p "$WEBUI_DIR/vendor/alpine"
mkdir -p "$WEBUI_DIR/vendor/flatpickr"
mkdir -p "$WEBUI_DIR/vendor/ace-min"
mkdir -p "$WEBUI_DIR/vendor/katex"
mkdir -p "$WEBUI_DIR/vendor/google"

download() {
  local url="$1"
  local out="$2"
  echo "Downloading $url -> $out"
  curl -sSL --fail "$url" -o "$out"
}

# marked ESM (used by messages.js)
download "https://cdn.jsdelivr.net/npm/marked@5/lib/marked.esm.js" "$WEBUI_DIR/vendor/marked/marked.esm.js"

# Alpine (ESM-friendly module) and the collapse plugin -> saved with expected names
download "https://cdn.jsdelivr.net/npm/alpinejs@3/dist/module.esm.js" "$WEBUI_DIR/vendor/alpine/alpine.min.js"
download "https://cdn.jsdelivr.net/npm/@alpinejs/collapse@3/dist/cdn.min.js" "$WEBUI_DIR/vendor/alpine/alpine.collapse.min.js"

# flatpickr JS + CSS
download "https://cdn.jsdelivr.net/npm/flatpickr@4.6.13/dist/flatpickr.min.js" "$WEBUI_DIR/vendor/flatpickr/flatpickr.min.js"
download "https://cdn.jsdelivr.net/npm/flatpickr@4.6.13/dist/flatpickr.min.css" "$WEBUI_DIR/vendor/flatpickr/flatpickr.min.css"

# Ace editor (ace.js). Ace doesn't ship a dedicated CSS; create a minimal fallback CSS file
download "https://cdnjs.cloudflare.com/ajax/libs/ace/1.4.14/ace.js" "$WEBUI_DIR/vendor/ace-min/ace.js"
cat > "$WEBUI_DIR/vendor/ace-min/ace.min.css" <<'EOF'
/* Minimal ACE CSS fallback used by the UI when a dedicated CSS isn't provided */
.ace_editor { font-family: monospace; }
EOF

# KaTeX JS + CSS + auto-render
download "https://cdn.jsdelivr.net/npm/katex@0.16.4/dist/katex.min.js" "$WEBUI_DIR/vendor/katex/katex.min.js"
download "https://cdn.jsdelivr.net/npm/katex@0.16.4/dist/katex.min.css" "$WEBUI_DIR/vendor/katex/katex.min.css"
download "https://cdn.jsdelivr.net/npm/katex@0.16.4/dist/contrib/auto-render.min.js" "$WEBUI_DIR/vendor/katex/katex.auto-render.min.js"

# QR code
download "https://cdn.jsdelivr.net/npm/qrcode@1.5.1/build/qrcode.min.js" "$WEBUI_DIR/vendor/qrcode.min.js"

# Google Material icons CSS (local file that references Google Fonts)
cat > "$WEBUI_DIR/vendor/google/google-icons.css" <<'EOF'
/* Loads Material Symbols Outlined from Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,0..1');
.material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; font-family: 'Material Symbols Outlined'; }
EOF

echo "All vendor files downloaded into $WEBUI_DIR/vendor"
