---
name: "docker-install-from-docs"
description: "Docker install from docs/repo; gate; verify compose."
metadata:
  author: "marcelovilaca, Hermes Agent"
  version: "1.0.0"
---

# docker-install-from-docs

## When to Use
Use when installing a service via Docker after reading official docs/repo; requires confirmation gate and README updates.

Trigger: installing a service via Docker after reading official installation docs and repo files.

## Always-on rules (this user)

- **Confirmation gate first.** Ask before every major step; follow user's labeled sequence if given (e.g. C → B → A). Do not start containers until B (config/env edits) is confirmed.
- **Source-cite both URLs** (docs page and repo) in `.env` header and `README.md`.
- **Create the folder first**, then `.env` + `docker-compose.yml` + `config.d/` + `README.md`. No file without README update.
- **Fetch config templates from repo/docs** (e.g. `.env-dist`, `config.php-dist`, docs `.env` block, compose file) — never invent DB passes, ports, or service names.
- **Verify before start:** `docker compose config` must parse clean; only then proceed to `up -d`.
- **Password change is a hard gate:** confirm user edited `.env` passwords; do not `up -d` with template defaults.
- **PostgreSQL version caution:** 18+ changed data volume (`/var/lib/postgresql`); match image to compose volume mapping.
- **Config override file:** if user asks for `config.d/` (step C), fetch repo `config.php-dist` (or equivalent) to get correct `putenv()` / `define()` syntax rather than inventing PHP.

## Procedure (order)

1. `mkdir -p <dir>/config.d`
2. Read docs + repo (`web_search` / `browser_exec` / `curl` raw files). Capture `.env` template and compose services.
3. Write `.env`: copy docs template; edit `DB_PASS`, `ADMIN_USER_PASS`, `HTTP_PORT`, access level. Keep source citation header.
4. Write `docker-compose.yml`: include `db` + `app` + `updater` + `web-nginx`; comment GHCR alternatives; optional `backups`; mount `./config.d` ro.
5. Write `config.d/config.php` (step C only when requested): based on repo `config.php-dist` — use `putenv('TTRSS_...')` or `define()`; include source comment.
6. Write `README.md`: folder contents, source URLs, quick-start (`edit .env` → `docker compose up -d` → URL), note that password is changed.
7. Verify: `cd <dir> && docker compose config` (check services, env, ports, volumes).
8. Confirm B: `.env` edits verified (search_files / grep for pass/access/plugins); ask if backups / registry / port adjustments needed.
9. Confirm A: `docker compose up -d`; check `docker compose ps`; access URL; tell user to read `app` logs for random password if `.env` password unset.

## Pitfalls

- Inventing `.env` values instead of copying from docs causes DB/auth mismatches. Copy first, edit second.
- Starting `up -d` before confirming password edit leaks default creds into running container.
- Forgetting `config.d/` mount in compose (`./config.d:/opt/tt-rss/config.d:ro`) makes step C useless.
- Using arbitrary PHP in `config.php` instead of repo's `putenv()` / `define()` syntax; always check `config.php-dist` from repo.
- Skipping `docker compose config` verification; compose errors (volume paths, env refs) only show at up time.
- Confusing `docker compose` vs `docker-compose` on Windows/MSYS; use `docker compose` (plugin form) as docs specify.
+ When user reports browser failure despite `curl` 200, confirm with `browser-use` (`new_tab` → `wait_for_load`) — not just `curl`; `browser-use` can hang on resource-heavy pages (JS/CSS loading) even when HTML is served instantly, so compare timing (`curl` time_total vs hang) before declaring full access.
+ After any `.env` bind change, recreate web-nginx (`docker compose up -d --force-recreate web-nginx`) — `restart` alone does not re-read `.env` port mapping.
+ `web_extract` can time out on raw GitHub URLs; fall back to `curl -sL --max-time 15` in terminal to fetch `config.php-dist` or `.env-dist`.
+ Confusion between `.env` template defaults (e.g., `ttrss`) and user's edited values — verify with `docker exec <app> env`.

## References

- `references/confirmation-sequence.md`: how this user structures work (label sequence, gate per step, README update per iteration).
- `references/docker-compose-services.md`: standard multi-container pattern (db/app/updater/web-nginx + backups + volumes).
- `references/browser-access.md`: curl-first diagnosis when browser reports inaccessible; IPv4 bind (`127.0.0.1`) vs `localhost` fix; URL subpath check.
