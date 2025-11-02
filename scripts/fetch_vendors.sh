#!/usr/bin/env bash
set -euo pipefail

# Lightweight vendor fetcher used during image builds to populate webui/vendor
# This script downloads a minimal set of frontend vendor assets into
# webui/vendor so the image serves them locally and avoids CDN-only fallbacks.

ROOT_DIR="/git/agent-zero"
VENDOR_DIR="$ROOT_DIR/webui/vendor"
mkdir -p "$VENDOR_DIR/flatpickr"
mkdir -p "$VENDOR_DIR/ace"
mkdir -p "$VENDOR_DIR/katex"
mkdir -p "$VENDOR_DIR/qrcode"

echo "Fetching flatpickr..."
curl -fsSL -o "$VENDOR_DIR/flatpickr/flatpickr.min.css" "https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css"
curl -fsSL -o "$VENDOR_DIR/flatpickr/flatpickr.min.js" "https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.js"

echo "Fetching ace editor..."
# Use a CDN-hosted stable ACE version
curl -fsSL -o "$VENDOR_DIR/ace/ace.min.js" "https://cdnjs.cloudflare.com/ajax/libs/ace/1.9.6/ace.min.js"

echo "Fetching KaTeX..."
curl -fsSL -o "$VENDOR_DIR/katex/katex.min.css" "https://cdn.jsdelivr.net/npm/katex/dist/katex.min.css"
curl -fsSL -o "$VENDOR_DIR/katex/katex.min.js" "https://cdn.jsdelivr.net/npm/katex/dist/katex.min.js"

echo "Fetching QRCode library..."
curl -fsSL -o "$VENDOR_DIR/qrcode/qrcode.min.js" "https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js" || true

# Make files world-readable
chmod -R a+r "$VENDOR_DIR"

echo "Vendor assets fetched to $VENDOR_DIR"
