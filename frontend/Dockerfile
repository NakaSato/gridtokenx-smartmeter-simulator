# syntax=docker/dockerfile:1
FROM oven/bun:1 AS base
WORKDIR /app

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app
COPY package.json bun.lock* ./
RUN --mount=type=cache,target=/root/.bun/install/cache \
    bun install --frozen-lockfile

# Build the application
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Next bakes rewrite destinations into routes-manifest at build time, so the
# backend URL must be present here (not just at runtime).
ARG SIMULATOR_URL=http://smartmeter-simulator:8082
ENV SIMULATOR_URL=$SIMULATOR_URL
RUN bun run build

# Production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME="0.0.0.0"

RUN <<EOT
    groupadd --system --gid 1001 nodejs || true
    useradd --system --uid 1001 --gid nodejs nextjs || true
EOT

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]