# Monorepo build: context is the repo root, so the @qzl/ui workspace package is
# available. See https://pnpm.io/docker for the pnpm base image approach.
FROM ghcr.io/pnpm/pnpm:12 AS build
RUN pnpm runtime set node 26 -g

WORKDIR /app

# Install workspace deps for the target app plus its local deps (@qzl/ui).
COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./
COPY apps/translate/package.json apps/translate/
COPY apps/transliterate/package.json apps/transliterate/
COPY packages/ui/package.json packages/ui/
RUN --mount=type=cache,id=pnpm,target=/var/cache/pnpm \
  pnpm install --store-dir /var/cache/pnpm --frozen-lockfile --filter "qzl-translate..."

# Build only the translate app (source-exported @qzl/ui needs no build step).
COPY . .
RUN pnpm --filter qzl-translate build

# Standalone output keeps the monorepo path layout: apps/translate/server.js.
FROM node:26-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system nodejs && adduser --system --ingroup nodejs nextjs

COPY --from=build --chown=nextjs:nodejs /app/apps/translate/.next/standalone ./
COPY --from=build --chown=nextjs:nodejs /app/apps/translate/.next/static ./apps/translate/.next/static
COPY --from=build --chown=nextjs:nodejs /app/apps/translate/public ./apps/translate/public

USER nextjs
EXPOSE 3000
ENV PORT=3000 HOSTNAME=0.0.0.0
CMD ["node", "apps/translate/server.js"]
