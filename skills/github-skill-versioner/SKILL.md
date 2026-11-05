---
name: "github-skill-versioner"
description: "Version and publish portable Hermes-authored agent skills."
compatibility: "Requires Hermes Agent for automatic lifecycle publishing; manual Git and Python workflow otherwise."
metadata:
  author: "marcelovilaca"
  version: "0.1.1"
---

# GitHub Skill Versioner

Keep skills authored in Hermes in the public `marcelovilaca/Agent-Skills` repository in the open Agent Skills format. The repository is the portable backup and distribution source; Hermes-only automation is an optional plugin, not part of the skill format.

## When to Use

- Create, update, review, or publish a skill authored in Hermes.
- Check whether Hermes lifecycle publishing is installed and enabled.
- Do not use to mirror third-party, catalog-installed, bundled, or otherwise unowned skills.

## Portability Rules

1. Use the Agent Skills directory structure: `<skill-name>/SKILL.md`, with optional `scripts/`, `references/`, and `assets/`.
2. Use a lowercase, hyphen-separated `name` matching the directory name. Include non-empty `description`; optional standard fields are `license`, `compatibility`, and `metadata` containing string values. Keep Hermes-only extensions out of top-level frontmatter.
3. Write instructions around capabilities available across agents. If a procedure depends on Hermes tools or a particular platform, document that dependency and provide a manual alternative where practical.
4. Never publish credentials, personal data, private project material, or machine-specific absolute paths. Replace local paths with user-configurable placeholders.
5. Preserve original supporting files only when they are required by the skill and safe to publish.

## Versioning and Publishing

1. Determine authorship from the active profile's skill-usage registry: export only active skills marked `created_by: agent` or `learn`; never mirror installed, bundled, third-party, or otherwise unowned skills.
2. New published skills start at `0.1.0` unless the source provides a valid semver version. On a content change, increment the patch version unless the author explicitly advanced it.
3. For an initial or manual publish, run `scripts/publish_skills.py --repo <repository-path> --home <HERMES_HOME> --dry-run`. Inspect the proposed skill set, redactions, and portability warnings; fix source content rather than weakening checks. Remove `--dry-run` only after review to stage, commit, push, and verify.
4. The Hermes publisher plugin invokes the same script after successful `created`, `patched`, and `edited` lifecycle events; `edited` includes supporting-file writes/removals. The publisher fails closed on secrets, unsafe files, invalid frontmatter, remote divergence, or unrelated working-tree changes. Read its log and fix the cause; do not bypass publisher checks.
5. Verify the exact reported commit on the remote branch and confirm the published `skills/*/SKILL.md` set before saying the backup succeeded.

## Hermes Plugin Setup and Verification

1. Install and enable the repository plugin with `hermes plugins install marcelovilaca/Agent-Skills --enable`.
2. If Hermes blocks installation on its security scan, inspect every finding and review the plugin source and flagged skill content. Use the documented `--force` override only when the remaining findings match the reviewed Git publisher or expected skill examples; never use it to skip the publisher's secret, path, or repository-state checks.
3. Confirm `hermes plugins doctor <plugin-id-or-path>` reports successful import/registration and a lifecycle hook, then confirm `hermes plugins list --plain --no-bundled` shows the plugin as enabled.
4. After a real skill mutation, inspect `<HERMES_HOME>/logs/agent-skills-publisher.log`; require return code 0 and a verified commit, or an explicit no-change result. Avoid creating throwaway probe skills because the hook may publish them.

## Verification

- Confirm each exported skill has a valid standard `SKILL.md`, portable name, and matching directory name.
- Run `python -m unittest discover -s tests -v` and the repository's skill validator.
- Confirm the remote `main` branch contains the commit reported by the publisher, inspect the exact published skill paths, and check the corresponding GitHub Actions validation run.
- The standard format allows skills to be imported by Hermes Agent, OpenAI Codex, Claude Code, OpenClaw, and Pi; it does not guarantee that every host can execute every tool named in an individual skill.
