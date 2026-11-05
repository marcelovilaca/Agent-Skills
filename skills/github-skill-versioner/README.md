# GitHub Skill Versioner

This skill maintains portable Hermes-authored skills in the public [`marcelovilaca/Agent-Skills` repository](https://github.com/marcelovilaca/Agent-Skills). It covers ownership checks, per-skill technical/how-to guides, portability, versioning, publishing, and remote verification.

Consulte o [SKILL.md](SKILL.md) para ver as instruções completas.

## How to Use

Use this skill when adding, updating, reviewing, or publishing a skill, or when checking the Hermes publisher plugin.

Before adding or changing a skill, inspect its `SKILL.md` and any scripts, references, or assets. Create or update that skill's sibling `README.md` with the required `## How to Use` and `## Technical Details` sections. Do not use the repository root README as a substitute. If source materials are missing, state that plainly in the guide rather than inventing capabilities.

For a manual publication, preview first from the repository checkout:

```sh
python scripts/publish_skills.py --repo <repository-path> --home <HERMES_HOME> --dry-run
```

Review the proposed skills, README guides, redactions, and warnings. After resolving issues, publish without `--dry-run`. After a skill lifecycle edit, inspect the publisher log and verify the exact remote commit and GitHub Actions result.

## Technical Details

- **Ownership filter:** only active skills marked `created_by: agent` or `created_by: learn` in the active Hermes usage registry are exported. Installed, bundled, third-party, and otherwise unowned skills are excluded.
- **Required package:** each skill directory contains `SKILL.md` and `README.md`; optional text resources can live in `scripts/`, `references/`, or `assets/`. The publisher refuses a source skill without the guide. The validator checks the required README sections and link back to `SKILL.md`.
- **Portability/security:** standard Agent Skills frontmatter is emitted; local paths are sanitized and credential patterns, unsafe files, invalid frontmatter, remote divergence, and unrelated working-tree changes are blocking errors. Do not weaken those checks to get a publish through.
- **Versioning:** new skills use a valid source SemVer when available (otherwise `0.1.0`); changed content/resources increment the patch version unless an explicit higher version is supplied. README changes count as package content.
- **Automation:** the enabled Hermes publisher plugin runs after skill create/patch/edit lifecycle events. Manual operation uses the same `scripts/publish_skills.py` script.
- **Verification:** run `python -m unittest discover -s tests -v` and `python scripts/validate_skills.py`; then confirm the remote `main` commit, skill files, catalog entry, and corresponding GitHub Actions validation.
- **Requirements:** Hermes Agent for lifecycle automation; Python with `ruamel.yaml`, Git, the repository checkout, and valid GitHub write authorization for publishing.

The canonical checklist and safety rules are in [SKILL.md](SKILL.md); repository-wide structure and contributing requirements are in [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md).
