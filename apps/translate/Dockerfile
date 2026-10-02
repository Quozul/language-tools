# Per https://pnpm.io/docker: official pnpm base image (no Node bundled);
# pnpm installs the Node runtime itself via `pnpm runtime set`.
FROM ghcr.io/pnpm/pnpm:12 AS build
RUN pnpm runtime set node 26 -g
COPY . /app
WORKDIR /app
RUN --mount=type=cache,id=pnpm,target=/var/cache/pnpm \
    pnpm install --store-dir /var/cache/pnpm --frozen-lockfile
RUN pnpm run build

# Standalone output needs only Node at runtime, so a plain Node image is used here.
FROM node:26-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system nodejs && adduser --system --ingroup nodejs nextjs
COPY --from=build --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=build --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=build --chown=nextjs:nodejs /app/public ./public
USER nextjs
EXPOSE 3000
ENV PORT=3000 HOSTNAME=0.0.0.0
CMD ["node", "server.js"]
