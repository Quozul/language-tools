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
