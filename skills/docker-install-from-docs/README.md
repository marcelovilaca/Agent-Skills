# Docker install from docs

A docs-first workflow for installing a service with Docker Compose. It requires explicit confirmation gates and source-derived configuration; see [SKILL.md](SKILL.md) for the complete procedure.

## Overview

Read the service's official installation documentation and repository files before creating configuration. Copy documented templates, edit only values the user has approved, validate the Compose model, and start containers only after the configuration/password gate is confirmed. The linked service-pattern references describe a TT-RSS-style deployment; apply service-specific details only when installing that service.

## Triggers and Inputs

Use when the user asks to install a service through Docker after consulting its official documentation and repository. Gather the target service, official documentation URL, repository URL, chosen install directory, required settings, and the user's confirmation for each major phase. Follow any user-specified step labels/order.

Do not guess ports, service names, image tags, database credentials, or config syntax. Fetch the service's actual `.env` template, Compose file, and any config template from its docs/repository first. Cite the docs and repository URLs in the generated install folder's README and in the `.env` header.

## Prerequisites

- Docker with the Compose plugin (`docker compose`, not the legacy `docker-compose` spelling used in this workflow).
- Access to the official docs and repository files for the selected service.
- A target directory and user-approved configuration values.
- Explicit confirmation that environment/password edits are complete before starting containers.

## How to Use

### Quick start

1. Get confirmation for the first setup step. Create the target folder and, for the referenced TT-RSS layout, `config.d/` before writing files.
2. Read official docs and repository templates. Record both source URLs; do not compose values from memory.
3. Create `.env` from the source template and change its passwords and other requested settings. Add the source citations in a comment header. Create `docker-compose.yml` from the documented service definitions. Add `config.d/config.php` only if requested, and base it on the repository's `config.php-dist` or equivalent.
4. Write the install folder's README with its contents, source links, start instructions, and a reminder that default/template passwords must be changed.
5. Review and validate before starting:

   ```sh
   cd <install-directory>
   docker compose config
   ```

   Confirm that services, environment references, ports, and volumes parse as intended. Then obtain explicit confirmation that the `.env` password/configuration changes are complete.
6. Only after that confirmation, start and inspect the stack:

   ```sh
   docker compose up -d
   docker compose ps
   ```

   Open the URL composed from the configured protocol, port, and any documented subpath. If an app password was left unset by the documented configuration, consult the app logs for the generated password; do not assume a template value is active.

### Workflow and files

For the TT-RSS reference layout, the directory contains `.env`, `docker-compose.yml`, `README.md`, and `config.d/`; `config.d/config.php` is conditional on the user's requested override. The example Compose topology is `db`, `app`, `updater`, and `web-nginx`, with optional `backups`. The documented read-only override mount is `./config.d:/opt/tt-rss/config.d:ro`. Use the actual service repository's compose and config files as the authority; this example is not a universal template.

Never write PHP overrides by guessing. Obtain the service's documented `putenv()`/`define()` form first. Where PostgreSQL is used, match the image version to the volume layout: PostgreSQL 18+ changed the data volume path, so an older mount path may be wrong.

## Technical Details

### Real files and tools

- `.env`: copied from the service's documented template; holds local settings and secrets and must not be committed.
- `docker-compose.yml`: service definitions, dependencies, ports, mounts, and volumes based on official docs/repository files.
- `config.d/`: optional override directory; in the TT-RSS pattern it is mounted read-only into both `app` and `updater`.
- `README.md`: file inventory, source URLs, quick-start, and password-change reminder.
- `docker compose config`, `docker compose up -d`, and `docker compose ps`: validation, start, and status commands respectively.

The reference material is in [references/confirmation-sequence.md](references/confirmation-sequence.md), [references/docker-compose-services.md](references/docker-compose-services.md), and [references/browser-access.md](references/browser-access.md). The service's own docs and repository remain authoritative for versions and values.

### Verification and troubleshooting

Run `docker compose config` before `up -d`; check the resulting service names, environment references, ports, and volume paths. After the approved start, inspect `docker compose ps` and verify the exact application URL. For a browser-access issue, first request the exact URL with `curl` and an explicit timeout; a 200 response confirms HTTP service at that URL, while a 404 can indicate a missing subpath and 502/503 an unready upstream. Only claim browser access after browser confirmation when the user asks for it or reports a mismatch.

For TT-RSS's web proxy, `docker port <web-nginx>` can expose the bind address. If the `.env` port/bind mapping changes, recreate the proxy (`docker compose up -d --force-recreate web-nginx`); a restart alone does not re-read the mapping. Compare the container's actual environment when template values and edited values appear inconsistent, without printing secrets.

### Safety and limitations

- Do not start containers before configuration review and explicit password-change confirmation. Never run with template/default passwords merely to test the stack.
- Do not invent service names, ports, passwords, image versions, PHP overrides, or volume paths; do not silently replace a repository template with a generic example.
- The service set, optional backups, image alternatives, and `config.d` mount described here are specific to the linked TT-RSS reference pattern. Other services may require a different topology.
- A successful `curl` does not prove browser rendering or full application health. Browser pages may hang on static/JavaScript resources even when HTML responds quickly; compare exact URL, bind address, and service status before diagnosing.
- Ask before each major step and keep the install README current whenever configuration files change.