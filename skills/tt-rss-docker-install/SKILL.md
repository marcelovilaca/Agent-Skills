---
name: "tt-rss-docker-install"
description: "Install tt-rss with Docker."
metadata:
  author: "marcelovilaca, Hermes Agent"
  version: "1.0.0"
---

# When to Use
Use when a user wants a fresh tt-rss instance under Docker, starting from the official documentation (tt-rss.org/docs/Installation-Guide.html) and the GitHub repository (github.com/tt-rss/tt-rss). Triggers: "install tt-rss docker", "set up tt-rss", "run tt-rss with docker compose".

## Always‑on rules (this user)

- **Confirmation gate first.** Ask before every major step; follow the user‑supplied sequence C → B → A (config → edit → start). Do not start containers until B (env edits) is confirmed.
- **Source‑cite both URLs** (docs page and repo) in the `.env` header and `README.md`.
- **Create the folder first**, then `.env` + `docker-compose.yml` + `config.d/` + `README.md`. No file without a README update.
- **Fetch config templates from repo/docs** (`.env-dist`, `config.php-dist`, compose file) — never invent DB passes, ports, or service names.
- **Verify before start:** `docker compose config` must parse clean; only then proceed to `up -d`.
- **Password change is a hard gate:** confirm user edited `.env` passwords; do not `up -d` with template defaults.
- **PostgreSQL version caution:** 18+ changed data volume (`/var/lib/postgresql`); match image to compose volume mapping.
- **Config override file:** if user asks for `config.d/` (step C), fetch repo `config.php-dist` (or equivalent) to get correct `putenv()` / `define()` syntax rather than inventing PHP.
- **Browser‑first diagnosis:** when a browser reports inability to load the page but `curl` returns `200`, do **not** assume the container is broken. Run `browser-use` (`new_tab(url)` → `wait_for_load()` → `page_info()` / screenshot). If `browser-use` hangs while `curl` finishes in <0.5 s, the page has resource/JS loading issues – check nginx static‑file serving (`/tt-rss/css/default.css`) and `docker compose ps` health before declaring full access.
- **After any `.env` bind change**, recreate `web-nginx` (`docker compose up -d --force-recreate web-nginx`) – `restart` alone does not re‑read `.env` port mapping.

## Procedure (order)

1. `mkdir -p <dir>/config.d`
2. Read docs + repo (`web_search` / `curl -sL --max-time 15` raw files). Capture `.env` template and compose services.
3. Write `.env`: copy docs template; edit `TTRSS_DB_PASS`, `ADMIN_USER_PASS`, `HTTP_PORT`, `TTRSS_PLUGINS`, `ADMIN_USER_ACCESS_LEVEL`. Keep source citation header.
4. Write `docker-compose.yml`: include `db` (postgres:17‑alpine), `app` (supahgreg/tt-rss:latest or GHCR alternative), `updater` (same image, `command: /opt/tt-rss/updater.sh`), `web-nginx` (supahgreg/tt-rss-web-nginx:latest, ports `${HTTP_PORT}:80`), optional `backups`. Mount `./config.d` ro.
5. Write `config.d/config.php` (step C only when requested): based on repo `config.php-dist` — use `putenv('TTRSS_...')` or `define()`; include source comment.
6. Write `README.md`: folder contents, source URLs, quick‑start (`edit .env` → `docker compose up -d` → URL), note that password is changed.
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
- Browser failure despite `curl` 200: always run `browser-use` first; a hang with fast `curl` indicates resource/JS loading, not a dead container.
- After changing `HTTP_PORT` in `.env`, **recreate** `web-nginx`; a simple `restart` will not pick up the new port mapping.

## References

- `references/confirmation-sequence.md`: how this user structures work (label sequence, gate per step, README update per iteration).
- `references/docker-compose-services.md`: standard multi‑container pattern (db/app/updater/web-nginx + backups + volumes).
- `references/browser-access.md`: curl‑first diagnosis when browser reports inaccessible; IPv4 bind (`127.0.0.1`) vs `localhost` fix; URL subpath check.
- `references/emoji-update.md`: how to change category emoji titles and verify persistence after container restart.
