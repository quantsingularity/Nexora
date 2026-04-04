# syntax=docker/dockerfile:1
# ─────────────────────────────────────────────────────────────
# Stage 1 – builder: build the React/Vite static assets
# ─────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG REACT_APP_API_URL=/api
ARG REACT_APP_ENV=production
ENV REACT_APP_API_URL=$REACT_APP_API_URL \
    REACT_APP_ENV=$REACT_APP_ENV

RUN npm run build

# ─────────────────────────────────────────────────────────────
# Stage 2 – runner: serve static files via nginx
# ─────────────────────────────────────────────────────────────
FROM nginx:1.27-alpine AS runner

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

COPY --from=builder /app/build /usr/share/nginx/html

# Nginx config injected at container start so env vars can override API URL
COPY docker-entrypoint.sh /docker-entrypoint.d/40-nexora-env.sh
RUN chmod +x /docker-entrypoint.d/40-nexora-env.sh

COPY nginx.conf /etc/nginx/conf.d/nexora.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost/health || exit 1
