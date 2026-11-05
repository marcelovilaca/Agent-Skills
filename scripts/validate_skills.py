#!/usr/bin/env python3
"""Validate the portable Agent Skills catalog in this repository."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from ruamel.yaml import YAML

from publish_skills import NAME_RE, SEMVER_RE, parse_frontmatter, scan_public_content

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_TOP_LEVEL = {"name", "description", "license", "compatibility", "metadata"}


def validate(root: Path = ROOT) -> list[str]:
    problems: list[str] = []
    catalog_path = root / "catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.exists() else {"skills": {}}
    skills_root = root / "skills"
    for skill_file in sorted(skills_root.glob("*/SKILL.md")) if skills_root.exists() else []:
        folder = skill_file.parent.name
        try:
            text = skill_file.read_text(encoding="utf-8")
            metadata, _body = parse_frontmatter(text)
            name = metadata.get("name")
            description = metadata.get("description")
            if not isinstance(name, str) or not NAME_RE.fullmatch(name) or len(name) > 64:
                raise ValueError("name must use lowercase letters, numbers, and single hyphens (max 64)")
            if name != folder:
                raise ValueError(f"name {name!r} does not match folder {folder!r}")
            if not isinstance(description, str) or not description.strip() or len(description) > 1024:
                raise ValueError("description is required and must be at most 1,024 characters")
            extra = set(metadata) - ALLOWED_TOP_LEVEL
            if extra:
                raise ValueError("non-standard top-level fields: " + ", ".join(sorted(extra)))
            guide_file = skill_file.parent / "README.md"
            if not guide_file.is_file():
                raise ValueError("missing README.md technical and how-to guide")
            guide_text = guide_file.read_text(encoding="utf-8")
            if not re.search(r"(?im)^##\s+How to Use\s*$", guide_text):
                raise ValueError("README.md must include a '## How to Use' section")
            if not re.search(r"(?im)^##\s+Technical Details\s*$", guide_text):
                raise ValueError("README.md must include a '## Technical Details' section")
            if not re.search(r"\[[^\]\n]+\]\(SKILL\.md\)", guide_text):
                raise ValueError("README.md must include a Markdown link to sibling SKILL.md")
            compatibility = metadata.get("compatibility")
            if compatibility is not None and (not isinstance(compatibility, str) or not 1 <= len(compatibility) <= 500):
                raise ValueError("compatibility must be a string of 1–500 characters")
            custom = metadata.get("metadata", {})
            if not isinstance(custom, dict) or any(not isinstance(value, str) for value in custom.values()):
                raise ValueError("metadata must be a mapping whose values are all strings")
            scan_public_content(text, skill_file.relative_to(root).as_posix())
            for resource in skill_file.parent.rglob("*"):
                if resource.is_file():
                    resource_text = resource.read_text(encoding="utf-8")
                    scan_public_content(resource_text, resource.relative_to(root).as_posix())
        except Exception as exc:
            problems.append(f"{skill_file.relative_to(root).as_posix()}: {exc}")
    if not isinstance(catalog, dict) or not isinstance(catalog.get("skills", {}), dict):
        problems.append("catalog.json: expected a mapping with a skills object")
    else:
        for slug, entry in catalog.get("skills", {}).items():
            if not (skills_root / slug / "SKILL.md").is_file():
                problems.append(f"catalog.json: {slug} has no skills/{slug}/SKILL.md")
            version = entry.get("version", "") if isinstance(entry, dict) else ""
            if not SEMVER_RE.fullmatch(str(version)):
                problems.append(f"catalog.json: {slug} has invalid semantic version {version!r}")
    return problems


def main() -> int:
    issues = validate()
    if issues:
        print("Skill validation failed:", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1
    count = len(list((ROOT / "skills").glob("*/SKILL.md"))) if (ROOT / "skills").exists() else 0
    print(f"Validated {count} portable skills.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
