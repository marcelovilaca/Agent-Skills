# Agent-Skills

Portable agent skills authored with Hermes Agent, backed up and versioned in a public GitHub repository.

**Repository:** <https://github.com/marcelovilaca/Agent-Skills>

## Portable format

Each skill lives in `skills/<name>/SKILL.md` and follows the open [Agent Skills specification](https://agentskills.io/specification): YAML frontmatter begins with `name` and `description`; optional `license`, `compatibility`, and string-valued `metadata` follow. Supporting files live beside `SKILL.md` in `scripts/`, `references/`, or `assets/`.

This shared format is supported by Hermes Agent, OpenAI Codex, Claude Code, OpenClaw, and Pi. Import compatibility does not guarantee that a host implements every tool or command named by a skill; host-specific requirements are declared in `compatibility` and in the instructions.

## Use a skill

- **Hermes Agent:** `hermes skills install https://raw.githubusercontent.com/marcelovilaca/Agent-Skills/main/skills/<skill-name>/SKILL.md`
- **OpenAI Codex, OpenClaw, or Pi:** place the skill directory under the project's `.agents/skills/` or the user's `~/.agents/skills/`.
- **Claude Code:** place the skill directory under the project's `.claude/skills/` or the user's `~/.claude/skills/`.

For each host, follow its current skill discovery rules. Keep the directory name identical to the `name` field.

## Automatic Hermes backup

The repository root is also a Hermes plugin. Try the normal scan first:

```sh
hermes plugins install marcelovilaca/Agent-Skills --enable
```

This repository includes skill examples and a publisher that runs Git; Hermes may flag those patterns as security findings. Review the findings and the publisher source. Only if the findings are the expected skill examples and the reviewed Git publisher, use Hermes' documented override:

```sh
hermes plugins install marcelovilaca/Agent-Skills --enable --force
```

The `on_skill_lifecycle` hook waits briefly after a Hermes skill is created or patched, then runs `scripts/publish_skills.py`. It exports active skills whose Hermes usage registry says `created_by: agent` or `created_by: learn`; catalog-installed and bundled skills are never mirrored. The publisher converts frontmatter to the portable format, normalizes legacy underscore names to hyphenated names, preserves supporting text resources, increments patch versions on content changes, commits, pushes to `main`, and verifies the remote commit.

The publisher fails closed on credential patterns, absolute local paths, unscannable binary resources, invalid frontmatter, remote divergence, and uncommitted edits outside its managed paths. Known personal roots are replaced with generic placeholders before scanning. Fix the source and rerun; do not bypass the checks.

Manual preview / publish:

```sh
python scripts/publish_skills.py --repo <checkout> --home <HERMES_HOME> --dry-run
python scripts/publish_skills.py --repo <checkout> --home <HERMES_HOME>
```

Automatic-sync logs are written locally to `<HERMES_HOME>/logs/agent-skills-publisher.log`. The plugin does not store GitHub credentials; Git uses the machine's configured GitHub credential helper.

## Authoring requirements

- Use the standard Agent Skills fields only at the top level; place nonstandard author/version details in string-valued `metadata`.
- Keep names lowercase and hyphen-separated, matching the directory name. Keep descriptions clear and within the 1,024-character standard limit.
- Declare host, OS, network, or command requirements. Prefer portable instructions and relative resource paths.
- Do not include secrets, personal data, project-specific private material, or absolute machine paths.
- Preserve any per-skill license stated in its source. No repository-wide license is implied unless one is added explicitly.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for versioning and review rules.
