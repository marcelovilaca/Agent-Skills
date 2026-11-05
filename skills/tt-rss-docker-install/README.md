# tt-rss Docker Install — How-to Guide

This guide describes the skill's gated workflow for setting up a fresh tt-rss instance with Docker. It follows the official [tt-rss installation guide](https://tt-rss.org/docs/Installation-Guide.html) and [tt-rss GitHub repository](https://github.com/tt-rss/tt-rss). See [SKILL.md](SKILL.md) for the source procedure and safety rules.

## How to Use

### Overview and triggers

Use this skill when the user wants a fresh tt-rss instance under Docker—for example, “install tt-rss docker,” “set up tt-rss,” or “run tt-rss with docker compose.” It guides the preparation, validation, and (only after confirmation) startup of a Compose deployment; it is not a general upgrade or operations guide.

### Inputs and prerequisites

Before beginning, establish the target install directory and ask about any requested config override, backup service, registry/image choice, or port adjustment. The workflow assumes Docker is available with the `docker compose` plugin and that the official docs/repository can be consulted to retrieve the templates. It uses `web_search` or `terminal` with `curl -sL --max-time 15` to inspect source material.

The deployment values to resolve from the user and templates include `TTRSS_DB_PASS`, `ADMIN_USER_PASS`, `HTTP_PORT`, `TTRSS_PLUGINS`, and `ADMIN_USER_ACCESS_LEVEL`. Do not invent passwords, ports, service names, or template contents. Keep real passwords private and do not place them in this guide.

### Quick start

Run the workflow from the chosen install directory. Replace `<install-dir>` with the user's target path; it is a placeholder.

```text
mkdir -p <install-dir>/config.d
```

Then follow the gated sequence **C → B → A**. Ask before each major step:

1. **C — Config:** create `config.d/`. Only if requested, create `config.d/config.php` from the repository's `config.php-dist` (or equivalent), using its `putenv('TTRSS_...')` or `define()` pattern.
2. **B — Edit:** fetch and copy the documented `.env` and Compose templates, edit the requested values, and ensure the `.env` passwords are no longer template defaults. Keep citations to both official URLs in the `.env` header and deployment `README.md`. Do not continue until the user confirms the edits.
3. Validate from the deployment directory:

   ```text
   docker compose config
   ```

   It must parse cleanly, including services, environment, ports, and volumes. Resolve any errors before proceeding.
4. **A — Start:** only after the password edits and start step are explicitly confirmed, run:

   ```text
   docker compose up -d
   docker compose ps
   ```

   Check the configured URL. If the `.env` password is unset, consult the `app` logs for the random password as directed by the skill.

### Verification and safety

- `docker compose config` must succeed before startup; it does not replace the user's confirmation gate.
- Confirm the `db`, `app`, `updater`, and `web-nginx` services and the intended environment, ports, and volume mappings. `backups` is optional.
- Never start with template-default passwords. Ask for confirmation before every major step and do not start containers until the B edits are confirmed.
- If `.env` changes a bind/port mapping, recreate nginx so it rereads the mapping: `docker compose up -d --force-recreate web-nginx`. A restart alone is insufficient.
- If a browser reports that the page cannot load but `curl` returns HTTP 200, do not conclude the container is broken. Use `browser-use` (`new_tab(url)`, `wait_for_load()`, then `page_info()` or a screenshot). If browser loading hangs while `curl` completes in under 0.5 seconds, check nginx static-file serving at `/tt-rss/css/default.css` and `docker compose ps` health before declaring access fully working.

## Technical Details

### Deployment files and sources

The skill creates the deployment folder first, then the following files/directories:

```text
<install-dir>/
  .env
  docker-compose.yml
  config.d/
    config.php        # only when requested
  README.md
```

Fetch `.env-dist`, `config.php-dist`, and the Compose/service template from the official docs or repository rather than reconstructing them from memory. The deployment folder's `README.md` should describe the folder contents, cite both source URLs, give the edit → validate/start → URL quick-start, and note the password-change requirement. Mount `./config.d` read-only at `/opt/tt-rss/config.d` when using the override; without that mount, the override has no effect.

### Compose pattern recorded by the skill

The described service pattern is:

- `db`: `postgres:17-alpine`.
- `app`: `supahgreg/tt-rss:latest` or a GHCR alternative.
- `updater`: the same app image, with `command: /opt/tt-rss/updater.sh`.
- `web-nginx`: `supahgreg/tt-rss-web-nginx:latest`, publishing `${HTTP_PORT}:80`.
- Optional `backups` service.

These are the skill's recorded defaults/pattern, not a substitute for checking the current upstream Compose template. PostgreSQL 18 and later changed the data-volume location to `/var/lib/postgresql`; match the selected image version to the volume mapping in the Compose file. Do not guess an alternative image identifier or volume mapping.

### Tools, outputs, and limits

`web_search` or `terminal`/`curl` is used to inspect upstream files; `terminal` runs `docker compose config`, `docker compose up -d`, and `docker compose ps`. When requested, the output is the deployment tree above and, after user-approved startup, the running Compose services. The skill does not prescribe an upgrade path, backup/restore procedure, or a complete registry/image-selection matrix.

The source `SKILL.md` names `references/confirmation-sequence.md`, `references/docker-compose-services.md`, `references/browser-access.md`, and `references/emoji-update.md`, but those reference files and any scripts are not present in this skill directory in this checkout. This guide therefore does not rely on undocumented details from them.
