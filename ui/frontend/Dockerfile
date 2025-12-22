# Eye of God Frontend Dockerfile
# Per Eye of God UIX Design Section 1.1
#
# VIBE COMPLIANT:
# - Production-grade multi-stage build
# - nginx for static serving
# - Non-root user

# =============================================================================
# Stage 1: Build Frontend
# =============================================================================
FROM node:20-alpine as builder

WORKDIR /build

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy source
COPY . .

# Build production bundle
RUN npm run build

# =============================================================================
# Stage 2: Production nginx
# =============================================================================
FROM nginx:alpine as production

# Security: Remove unnecessary configs
RUN rm -rf /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder
COPY --from=builder /build/dist /usr/share/nginx/html

# Non-root user
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --spider -q http://localhost:80/health || exit 1

# Run nginx
CMD ["nginx", "-g", "daemon off;"]
