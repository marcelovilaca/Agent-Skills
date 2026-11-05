---
name: github-skill-versioner
description: Version and publish portable Hermes-authored agent skills.
compatibility: "Requires Hermes Agent for automatic lifecycle publishing; manual Git and Python workflow otherwise."
metadata:
  author: "marcelovilaca, Hermes Agent"
  version: "0.1.0"
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

- Hermes authorship is determined from the active profile's skill-usage registry (`created_by: agent` or `learn`). Installed and bundled skills are not exported.
- New published skills start at `0.1.0` unless their source explicitly provides a valid semver version.
- On a content change, the publisher increments the patch version unless the author has explicitly advanced the version.
- Run the repository's `scripts/publish_skills.py --repo <repository-path> --home <HERMES_HOME> --dry-run` to preview. Remove `--dry-run` to stage, commit, push, and verify the remote branch.
- The Hermes publisher plugin invokes the same script after a skill is created or patched. It fails closed on detected secrets, machine paths, invalid frontmatter, unsafe resources, or Git conflicts; inspect its log and fix the source rather than bypassing the checks.
- Do not claim a backup succeeded until the pushed commit is verified on GitHub.

## Verification

- Confirm each exported skill has valid standard `SKILL.md`, a portable name, and matching directory name.
- Run `python -m unittest discover -s tests -v` in the repository.
- Confirm the repository's `main` branch contains the commit reported by the publisher.
- The standard format allows skills to be imported by Hermes Agent, OpenAI Codex, Claude Code, OpenClaw, and Pi; it does not guarantee that every host can execute every tool named by a skill.
