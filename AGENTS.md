# AGENTS.md

Language Tools is a small monorepo of self-hostable language utilities: a translation app and a transliteration app (currently Japanese, with furigana), backed by local/self-hosted models and services.

## Layout

- `apps/translate` — translation web app (Next.js). Talks to self-hosted LLM translation models (llama.cpp) and the language detection service.
- `apps/transliterate` — transliteration web app (Next.js). Talks to the transliterate service.
- `packages/ui` — shared UI package (`@qzl/ui`): shadcn-style components, hooks and lib helpers used by both apps.
- `services/language-detection` — Python service for language detection.
- `services/transliterate` — Python service for transliteration.

## Tech stack (rough)

- pnpm workspace with Turborepo at the root; run scripts via `pnpm`/`turbo` (`dev`, `build`, `lint`, `typecheck`, `test`, ...).
- Apps are Next.js + React with Tailwind CSS; shared components live in `packages/ui`.
- Python services with their own `requirements.txt`/`pyproject.toml` and Dockerfiles.
- Biome for lint/format, vitest for tests.
- Deployment via docker-compose / Coolify.

<!-- BEGIN:turborepo-agent-rules -->

# This is NOT the Turborepo you know

Turborepo configuration, task behavior, and CLI commands can vary between installed versions and may differ from your training data. Resolve the `turbo` package from this file's directory or relevant workspace; in monorepos, it may not be visible from the repository root. For example, run `node -p "require.resolve('turbo/package.json')"` from a workspace that depends on `turbo`.

Read `docs/README.md` inside that installed package first, then read the relevant pages from its `docs/` directory before changing Turborepo configuration or commands. Heed deprecation notices. These bundled docs match the installed package version and are available without network access.

This block is written and re-added by `turbo` before repository-scoped commands when an AI agent is detected. In the Turborepo source repository, its template is defined in `crates/turborepo-cli/src/cli/agent_guidance.rs`. Removing the managed block while updates are enabled means a later qualifying invocation will add it again. Set `"agentGuidance": false` in the root `turbo.json` or `turbo.jsonc` to opt out; this does not remove an existing block. Keep the block committed with your work to avoid an uncommitted change on the next agent invocation.
<!-- END:turborepo-agent-rules -->
