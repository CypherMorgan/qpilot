# syntax=docker/dockerfile:1
#
# CypherPilot Frontend — Multi-stage Docker image
# =============================================
#
# Builder stage: Builds the React + Vite SPA.
# Runtime stage: Serves the built SPA via Nginx.
#
# Usage (development)
#   docker compose up --build
#
# Usage (production build)
#   docker build -t cypherpilot-frontend:latest frontend/
#   docker run --rm -p 3000:80 cypherpilot-frontend:latest

# ═══════════════════════════════════════════════════════════════════════════════
# Stage 1 — Builder
# ═══════════════════════════════════════════════════════════════════════════════
FROM node:20-alpine AS builder

WORKDIR /app

# ── Layer 1: Dependencies ─────────────────────────────────────
# Copy only dependency manifests first for Docker layer caching.
COPY package.json package-lock.json ./
RUN npm ci --frozen-lockfile

# ── Layer 2: Application source ───────────────────────────────
# Copy the rest of the source and build the SPA.
COPY . .
RUN npm run build

# ═══════════════════════════════════════════════════════════════════════════════
# Stage 2 — Runtime (Nginx)
# ═══════════════════════════════════════════════════════════════════════════════
FROM nginx:alpine AS runtime

# ── Copy built assets from builder ────────────────────────────
COPY --from=builder /app/dist /usr/share/nginx/html

# ── Copy custom Nginx config with SPA fallback ────────────────
COPY nginx.conf /etc/nginx/conf.d/default.conf

# ── Security: Drop root privileges ────────────────────────────
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
