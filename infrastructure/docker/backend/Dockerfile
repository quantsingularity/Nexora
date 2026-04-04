# syntax=docker/dockerfile:1
# ─────────────────────────────────────────────────────────────
# Stage 1 – deps: install production node_modules only
# ─────────────────────────────────────────────────────────────
FROM node:20-alpine AS deps

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# ─────────────────────────────────────────────────────────────
# Stage 2 – builder: transpile (TypeScript / Babel / etc.)
# ─────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build --if-present

# ─────────────────────────────────────────────────────────────
# Stage 3 – runner: lean production image
# ─────────────────────────────────────────────────────────────
FROM node:20-alpine AS runner

RUN apk add --no-cache dumb-init

# Non-root user
RUN addgroup -S nexora && adduser -S nexora -G nexora

WORKDIR /app

COPY --from=deps    --chown=nexora:nexora /app/node_modules ./node_modules
COPY --from=builder --chown=nexora:nexora /app/dist        ./dist
COPY --from=builder --chown=nexora:nexora /app/package*.json ./

USER nexora

EXPOSE 3000

ENV NODE_ENV=production \
    PORT=3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/health', r => process.exit(r.statusCode===200?0:1)).on('error',()=>process.exit(1))"

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["node", "dist/index.js"]
