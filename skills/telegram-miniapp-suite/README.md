# Telegram Mini App Suite

## Overview

This is a build and debugging recipe for a multi-app Telegram WebApp suite: several React/Vite frontends, a grammY bot hub, a Fastify API, and PostgreSQL. It assumes work in the Pixel Archive Suite or a comparable existing monorepo; it is not a standalone generator or a complete deployment manual. The source workflow is in [SKILL.md](SKILL.md), and the companion frontend setup is described by [react-vite-miniapp-setup](../../react-vite-miniapp-setup/SKILL.md).

## How to Use

### Inputs and prerequisites

- An existing target repository/root; keep its path configurable and consult `docs/ARCHITECTURE.md` in that project.
- The source recipe uses npm workspaces. Its recorded compatible stack is React 19, Vite 7, `@vitejs/plugin-react` 5, grammY 1.46, `@grammyjs/runner` 2.0.3, Fastify 5, Drizzle 0.45, `postgres` 3.4 (postgres.js), and TypeScript 5.9. Treat these as a known working version set from the recipe, not a claim that they are the newest versions or a universal upgrade mandate.
- Node/npm compatible with the target repo's manifests and lockfile.
- Docker Compose and a working Docker engine for the documented local PostgreSQL setup.
- A target-repository `DATABASE_URL` for migration/seeding and bot/API configuration required by that repo. The skill does not specify all environment-variable names or provide credentials; do not invent them or commit secrets.

### Quick start: local database and checks

From the target repository root, start the database and run the root migration script:

```bash
docker compose up -d
npm run db:migrate
```

With `DATABASE_URL` configured, seed from the API service directory:

```bash
cd services/api
npm run db:seed
```

Then run the repository's applicable verification scripts (listed below) and start the bot/API/frontend using the actual scripts in the target checkout. This skill does not define a canonical server-start command; inspect that repository's package scripts instead of guessing.

## Technical Details

### Components and real project files

- **Frontends:** four mini apps built with React/Vite; the related setup uses `apps/<app-name>/`, `src/`, a shared `design-system/`, and outputs to `public/<app-name>/`. A mini app served from a subpath needs relative Vite asset URLs (`base: './'`).
- **Bot:** a grammY hub launches the apps and handles Telegram-only actions such as creating invoice links or sending native audio messages.
- **API:** Fastify service under `services/api/`; it mediates authentication, entitlements, persistence, and bot-only actions.
- **Database:** PostgreSQL. The local recipe uses a Compose service named `pixel-archive-db` with `postgres:17-alpine`.
- **Architecture:** `docs/ARCHITECTURE.md` in the target project.
- **Migrations:** `services/api/src/db/migrate.ts` applies numbered plain `.sql` migrations and records them in a `_migrations` ledger. The recipe avoids `drizzle-kit push` because it requires an interactive TTY and does not use `drizzle-kit migrate` for these plain SQL files.

These paths/scripts describe the project expected by the recipe; this skill directory itself contains only the skill instructions, not the suite application, database, or verification scripts. Confirm that the corresponding files exist in the target checkout before running them.

### Verification scripts named by the recipe

The suite recipe names these project-level checks:

- `scripts/verify-initdata.mjs` — accepts/rejects Telegram WebApp init-data signatures.
- `scripts/verify-bot.mjs` — checks bot keyboard rows, `web_app` payloads, and HTTPS URLs.
- `scripts/verify-design-system.mjs` — static checks against built CSS for each app.
- `scripts/verify-render.tsx` — server-renders real components and checks markup.
- `scripts/verify-api.mjs` — live API/Postgres checks including auth/internal-route failures, entitlement unlock, progress, bookmarks, and media content type.
- `scripts/verify-reader.ts` — opens a real PDF/EPUB, checks document content/navigation, and round-trips a reader position.
- `scripts/audit-layout.mjs` — layout audit used with headless Chrome over CDP, including a self-test for clipped text and collapsed boxes that still paint.

The skill names the scripts but does not provide their invocation arguments. Check the target repository and its package scripts for the supported way to run each one. Browser-based checks remain valuable: server rendering cannot detect every blank page, clipped caption, or overlap.

### Integration and safety rules

- Validate Telegram init data on the server. A client-side `premium=true` query parameter or Telegram's `User.is_premium` flag is not authoritative entitlement proof; the recipe uses a Telegram Stars (`XTR`) subscription as the source of truth.
- Only the bot can create an invoice link. Route a purchase request through the API to a secret-guarded bot endpoint, then open the returned Telegram link. Do not put bot credentials in a mini app.
- Telegram may suspend HTML5 audio in a minimized WebApp. For background playback, the documented approach sends a native audio message using `bot.api.sendAudio`; persist the user's chat ID when the bot sees the user and guard the internal API-to-bot route. A mini app cannot message a user by itself.
- For recurring schema changes, use the project's numbered SQL migration runner and ledger; do not switch migration tools without verifying how this repository tracks applied files.
- Inspect the installed grammY TypeScript declarations when calling APIs: `Api` class methods can be positional while raw API/types payloads are object-shaped. Use the method signatures for the installed version.

### Limitations and operational pitfalls

- The source provides a known working stack and debugging notes, not a general guarantee that current dependency releases are compatible. Respect the target repository's lockfile and package scripts.
- `docs/ARCHITECTURE.md`, the listed scripts, services, database schema, and environment configuration must be present in the target application repository; they are not distributed in this skill folder.
- Docker may be stopped or unreachable. Check that the daemon is available before interpreting a database connection refusal as a migration failure.
- A successful Vite build does not ensure that an app served from `/<app-name>/` loads; check for `base: './'` and verify the actual page.
- Browser auditing has false-positive risks: scrollable content (`overflow: auto`/`scroll`) remains reachable, unlike content clipped by `overflow: hidden`. Test the auditor with known failures before relying on its output.
- Never include actual tokens, database passwords, or other credentials in this README, logs, commands, or client bundles.
