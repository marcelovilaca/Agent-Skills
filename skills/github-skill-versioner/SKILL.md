---
name: "github-skill-versioner"
description: "Version and publish portable Hermes-authored agent skills."
compatibility: "Requires Hermes Agent for automatic lifecycle publishing; manual Git and Python workflow otherwise."
metadata:
  author: "marcelovilaca"
  version: "0.1.3"
---

# GitHub Skill Versioner

Keep skills authored in Hermes in the public `marcelovilaca/Agent-Skills` repository in the open Agent Skills format. The repository is the portable backup and distribution source; Hermes-only automation is an optional plugin, not part of the skill format.

## When to Use

- Create, update, review, or publish a skill authored in Hermes.
- Check whether Hermes lifecycle publishing is installed and enabled.
- Do not use to mirror third-party, catalog-installed, bundled, or otherwise unowned skills.

## Portability Rules

1. Every published skill directory must contain a root `SKILL.md` and a root `README.md` technical/how-to guide. Optional `scripts/`, `references/`, and `assets/` live beside them.
2. Use a lowercase, hyphen-separated `name` matching the directory name. Include non-empty `description`; optional standard fields are `license`, `compatibility`, and `metadata` containing string values. Keep Hermes-only extensions out of top-level frontmatter.
3. Write instructions around capabilities available across agents. If a procedure depends on Hermes tools or a particular platform, document that dependency and provide a manual alternative where practical.
4. Never publish credentials, personal data, private project material, or machine-specific absolute paths. Replace local paths with user-configurable placeholders.
5. Preserve original supporting files only when they are required by the skill and safe to publish.

## Per-skill README Guides

Every skill added to or maintained in `marcelovilaca/Agent-Skills` must have its own `skills/<skill-name>/README.md`. Create or update this guide whenever the skill is added or its behavior, requirements, tools, or outputs change. Never rely on the repository-level README as a substitute.

Write from the source `SKILL.md` and inspect any included scripts, references, and assets before describing them. Keep claims factual; explicitly label missing companion files, unimplemented scripts, or tool-dependent output. A guide must include these exact sections so the repository validator can check it:

- `## How to Use` — triggers, inputs, short quick start, and a usable example.
- `## Technical Details` — prerequisites, tools/commands, files and outputs, workflow, verification, safety, and limitations.

Link to the sibling with a relative Markdown target such as `[SKILL.md](SKILL.md)`; a plain text mention is not a link and will fail validation. Keep paths relative and omit credentials, personal data, and machine-specific paths. Store the README beside the local Hermes skill before publishing; the publisher copies it, hashes it, and refuses a skill source without it. For existing repository skills that lack guides, create them during the documentation migration.

## Versioning and Publishing

1. Determine authorship from the active profile's skill-usage registry: export only active skills marked `created_by: agent` or `learn`; never mirror installed, bundled, third-party, or otherwise unowned skills.
2. New published skills start at `0.1.0` unless the source provides a valid semver version. On a content change, increment the patch version unless the author explicitly advanced it.
3. Before the dry run, inventory the full set of skills discovered from the active usage registry: the publisher checks every active `created_by: agent` or `learn` source, not only the skills changed in this publish. Ensure each discovered source directory already has its own guide; for every added or changed skill, create or update that guide beside the source `SKILL.md` (not only in the repository checkout). If backfilling documentation for skills already in the repository, place each guide in its matching active Hermes source directory so the publisher can copy it. Every guide must include `## How to Use`, `## Technical Details`, and a sibling `SKILL.md` link; verify claims against the actual source files before proceeding.
4. For an initial or manual publish, run `scripts/publish_skills.py --repo <repository-path> --home <HERMES_HOME> --dry-run`. Review the managed/changed slugs and proposed versions, then inspect source README files and support resources directly; the dry-run summary is not a full per-file diff. Compare each selected source directory's relative file inventory with `skills/<slug>/` in the repository before publishing, because the publisher replaces the destination directory. If an intended repository-only file exists, merge it into the active source first and rerun the dry run. Fix content, redaction, or portability issues rather than weakening checks. Remove `--dry-run` only after reviewing the complete package set.
5. The Hermes publisher plugin invokes the same script after successful `created`, `patched`, and `edited` lifecycle events; `edited` includes supporting-file writes/removals. The publisher fails closed on missing README guides, secrets, unsafe files, invalid frontmatter, remote divergence, or unrelated working-tree changes. Read its log and fix the cause; do not bypass publisher checks.
6. Verify the exact reported commit on the remote branch and confirm every published `skills/*/` folder contains both `SKILL.md` and `README.md` before saying the backup succeeded.

## Hermes Plugin Setup and Verification

1. Install and enable the repository plugin with `hermes plugins install marcelovilaca/Agent-Skills --enable`.
2. If Hermes blocks installation on its security scan, inspect every finding and review the plugin source and flagged skill content. Use the documented `--force` override only when the remaining findings match the reviewed Git publisher or expected skill examples; never use it to skip the publisher's secret, path, or repository-state checks.
3. Confirm `hermes plugins doctor <plugin-id-or-path>` reports successful import/registration and a lifecycle hook, then confirm `hermes plugins list --plain --no-bundled` shows the plugin as enabled.
4. After a real skill mutation, inspect `<HERMES_HOME>/logs/agent-skills-publisher.log`; require return code 0 and a verified commit, or an explicit no-change result. Avoid creating throwaway probe skills because the hook may publish them.

## Verification

- Confirm each exported skill has a valid standard `SKILL.md`, portable name, and matching directory name.
- Confirm every exported skill folder contains an accurate `README.md` with the required usage/technical sections and no unsupported claims.
- Run `python -m unittest discover -s tests -v` and the repository's skill validator.
- Confirm the remote `main` points to the publisher's exact commit, not merely a newer local `HEAD`; verify that every published `skills/<slug>/` path contains both `SKILL.md` and `README.md` (and that intended support files remain). Check the corresponding GitHub Actions validation run and require its `headSha` to match that exact commit with a successful conclusion.
- The standard format allows skills to be imported by Hermes Agent, OpenAI Codex, Claude Code, OpenClaw, and Pi; it does not guarantee that every host can execute every tool named in an individual skill.
