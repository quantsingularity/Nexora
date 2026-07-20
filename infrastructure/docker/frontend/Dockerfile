# syntax=docker/dockerfile:1
# ─────────────────────────────────────────────────────────────
# Stage 1 – builder: build the React (Parcel) static assets
# Build context is web-frontend/ (see ../../docker-compose.yml)
# ─────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# web-frontend/src/services/api.js reads REACT_APP_API_BASE_URL at build
# time (Parcel inlines process.env.* references into the bundle, so this
# must be set here; it cannot be overridden at container start).
# Defaults to a relative path so the gateway nginx (see ../nginx/nginx.conf)
# can proxy /api/* to the backend without rebuilding per environment.
ARG REACT_APP_API_BASE_URL=/api
ENV REACT_APP_API_BASE_URL=$REACT_APP_API_BASE_URL

RUN npm run build

# ─────────────────────────────────────────────────────────────
# Stage 2 – runner: serve static files via nginx
# Parcel's default output directory is `dist/` (see web-frontend's
# "build" script: `parcel build src/index.html`), NOT `build/`.
# ─────────────────────────────────────────────────────────────
FROM nginx:1.27-alpine AS runner

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/nexora.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost/health || exit 1
