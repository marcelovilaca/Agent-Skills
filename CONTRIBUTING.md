# Contributing skills

## Required structure

```text
skills/<lowercase-hyphen-name>/
├── SKILL.md
├── README.md     # technical and how-to guide (required)
├── scripts/       # optional
├── references/    # optional
└── assets/        # optional
```

`SKILL.md` must start at byte zero with YAML frontmatter. Required fields are `name` and `description`. The name must be 1–64 lowercase letters/digits/hyphens, with no leading, trailing, or consecutive hyphen, and must match the directory name. Description length is 1–1,024 characters. Optional standard fields are `license`, `compatibility` (up to 500 characters), and `metadata` (string values only).

Every skill directory must also contain a root `README.md` for people using or maintaining the skill. Include `## How to Use` and `## Technical Details`, explain prerequisites, workflows, files/tools and limitations from the source skill, and link to `SKILL.md`. Do not claim missing scripts or capabilities. Update this guide whenever the skill's behavior or requirements change; the publisher and validator reject a skill without it.

Store version and author in metadata, for example:

```yaml
metadata:
  author: "marcelovilaca, Hermes Agent"
  version: "0.1.0"
```

Do not add Hermes-only top-level frontmatter fields such as `platforms` or `version`; express requirements in `compatibility` and retain host-specific metadata as strings under `metadata`.

## Portability and privacy

- Prefer relative paths and instructions usable by multiple agents.
- Name platform-specific tools and provide a manual alternative where practical.
- Do not publish credentials, personal data, proprietary project material, build outputs, or machine-specific absolute paths.
- Keep scripts self-contained and explain dependencies. Keep references focused and load them only when needed.
- Respect the original license. The repository has no blanket license; omit a license field unless the source has a confirmed license.

## Versioning

Use semantic versions. A new skill starts at `0.1.0` unless its source already has a valid version. The publisher increments the patch component when content or supporting files change. Authors may advance a version explicitly; the publisher does not reduce it.

## Validation

Run these from the repository root before publishing:

```sh
python -m unittest discover -s tests -v
python scripts/validate_skills.py
python scripts/publish_skills.py --repo . --home <HERMES_HOME> --dry-run
```

The Hermes lifecycle publisher automatically validates, versions, commits, pushes, and verifies the remote `main` commit after a skill is created or patched. It only exports active skills marked `agent` or `learn` in the active Hermes usage registry. Investigate any rejected publish rather than disabling secret/path checks.
