# ═══════════════════════════════════════════════════════════════════════════════
#  Frontend SaaS Dockerfile — Next.js 14 Standalone
#  Multi-stage build | node:18-alpine | context = frontend-saas/
#  يتطلب output: 'standalone' في next.config.mjs
# ═══════════════════════════════════════════════════════════════════════════════

# ── Stage 1: تثبيت المتطلبات ─────────────────────────────────────────────────
FROM node:18-alpine AS deps

WORKDIR /app

# نسخ ملفات package فقط (cache layer)
COPY package*.json ./

# تثبيت حزم الإنتاج والتطوير معاً (ضروري للـ build)
RUN npm ci --frozen-lockfile


# ── Stage 2: البناء ───────────────────────────────────────────────────────────
FROM node:18-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# رابط الـ API عند البناء (يمرر عبر ARG في docker-compose)
ARG  BACKEND_URL=http://backend:8000
ENV  BACKEND_URL=$BACKEND_URL
ENV  DOCKER_BUILD=true
ENV  NEXT_TELEMETRY_DISABLED=1

RUN npm run build


# ── Stage 3: Runtime (Standalone) ────────────────────────────────────────────
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME="0.0.0.0"

# مستخدم غير جذري
RUN addgroup --system --gid 1001 nodejs \
 && adduser  --system --uid 1001 nextjs

# ملفات المشروع من مرحلة البناء
COPY --from=builder /app/public                         ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static     ./.next/static

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=15s \
    CMD wget -qO- http://localhost:3000/login || exit 1

CMD ["node", "server.js"]
