import tempfile
import unittest
from pathlib import Path

from scripts.publish_skills import (
    bump_patch,
    discover_managed_skills,
    normalize_name,
    parse_frontmatter,
    render_portable_skill,
    scan_public_content,
    prepare_skill,
    sanitize_local_paths,
)


class PortableSkillTests(unittest.TestCase):
    def test_normalize_name_converts_legacy_underscores(self):
        self.assertEqual(normalize_name("ebook_to_audiobook_master"), "ebook-to-audiobook-master")

    def test_render_uses_standard_fields_and_moves_extensions_to_string_metadata(self):
        source = """---
name: legacy_skill
description: A useful skill.
version: 0.1.0
author: Marcel
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [audio, books]
---

# Body
Keep this instruction.
"""
        rendered = render_portable_skill(source, "legacy-skill", version="0.1.1")
        frontmatter, body = parse_frontmatter(rendered)
        self.assertEqual(frontmatter["name"], "legacy-skill")
        self.assertEqual(frontmatter["license"], "MIT")
        self.assertIn("Windows", frontmatter["compatibility"])
        self.assertNotIn("version", frontmatter)
        self.assertNotIn("author", frontmatter)
        self.assertTrue(all(isinstance(value, str) for value in frontmatter["metadata"].values()))
        self.assertEqual(frontmatter["metadata"]["version"], "0.1.1")
        self.assertIn("Keep this instruction.", body)

    def test_patch_version_increments_and_respects_explicit_upgrade(self):
        self.assertEqual(bump_patch("0.1.4", None), "0.1.5")
        self.assertEqual(bump_patch("0.1.4", "0.2.0"), "0.2.0")
        with self.assertRaises(ValueError):
            bump_patch("not-semver", None)

    def test_secret_scan_rejects_credential_patterns(self):
        with self.assertRaises(ValueError):
            scan_public_content("token ghp_" + "A" * 40, "SKILL.md")

    def test_secret_scan_rejects_machine_home_paths(self):
        with self.assertRaises(ValueError):
            scan_public_content(r"See C:\Users\alice\private\project", "SKILL.md")

    def test_discovery_includes_only_active_hermes_authored_skills(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "owned" / "SKILL.md").parent.mkdir()
            (root / "owned" / "SKILL.md").write_text("---\nname: owned\ndescription: Owned.\n---\nBody\n", encoding="utf-8")
            (root / "installed" / "SKILL.md").parent.mkdir()
            (root / "installed" / "SKILL.md").write_text("---\nname: installed\ndescription: Installed.\n---\nBody\n", encoding="utf-8")
            usage = {
                "owned": {"created_by": "agent", "state": "active"},
                "installed": {"created_by": "installed", "state": "active"},
                "retired": {"created_by": "learn", "state": "archived"},
            }
            found = discover_managed_skills(root, usage)
            self.assertEqual(set(found), {"owned"})
            self.assertEqual(found["owned"], root / "owned")

    def test_local_home_is_redacted_before_publication(self):
        result = sanitize_local_paths(r"Project at C:\Users\alice\private", Path("C:/Users/alice"))
        self.assertIn("<USER_HOME>", result)
        self.assertNotIn("alice", result)

    def test_version_does_not_increase_again_for_unchanged_source(self):
        with tempfile.TemporaryDirectory() as directory:
            source_dir = Path(directory) / "skill"
            source_dir.mkdir()
            source = "---\nname: skill\ndescription: A skill.\nversion: 0.1.0\n---\nBody\n"
            (source_dir / "SKILL.md").write_text(source, encoding="utf-8")
            first_files, first_entry = prepare_skill(source_dir, "skill", None, Path(directory))
            changed_source = source.replace("Body", "Changed body")
            (source_dir / "SKILL.md").write_text(changed_source, encoding="utf-8")
            second_files, second_entry = prepare_skill(source_dir, "skill", first_entry, Path(directory))
            third_files, third_entry = prepare_skill(source_dir, "skill", second_entry, Path(directory))
            self.assertEqual(first_entry["version"], "0.1.0")
            self.assertEqual(second_entry["version"], "0.1.1")
            self.assertEqual(third_entry["version"], "0.1.1")
            self.assertEqual(second_files["SKILL.md"], third_files["SKILL.md"])


if __name__ == "__main__":
    unittest.main()
