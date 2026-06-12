# ═══════════════════════════════════════════════════════════════════════════════
# 🐳 WEBUI DOCKERFILE — Lit 3.x + Vite + nginx
# ═══════════════════════════════════════════════════════════════════════════════
# Multi-stage build:
#   Stage 1: Build the Vite app with Node
#   Stage 2: Serve static dist/ with nginx:alpine
# ═══════════════════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────────────────
# STAGE 1: Build
# ───────────────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# ───────────────────────────────────────────────────────────────────────────────
# STAGE 2: Serve
# ───────────────────────────────────────────────────────────────────────────────
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config (proxies /api/ and /ws/ to backend)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
