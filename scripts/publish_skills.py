#!/usr/bin/env python3
"""Export Hermes-authored skills as portable Agent Skills and push to GitHub."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from ruamel.yaml import YAML
except ImportError as exc:  # pragma: no cover - exercised by the runtime guard
    raise SystemExit("Install ruamel.yaml in the Hermes Python environment to publish skills.") from exc

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
DRIVE_PATH_RE = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]:" + re.escape("\\") + r"[^\s`\"<>]+")
SECRET_PATTERNS = (
    ("GitHub token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("cloud/API key", re.compile(r"\b(?:AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{24,})\b")),
    ("bearer token", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{24,}")),
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
)
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".cache"}
SKIP_FILES = {".ds_store", "thumbs.db"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".log", ".jsonl", ".db", ".sqlite", ".sqlite3", ".mp3", ".wav", ".mp4", ".zip", ".exe", ".dll", ".bin"}
MAX_RESOURCE_BYTES = 5 * 1024 * 1024
OWNER_NAME = "marcelovilaca"
OWNER_EMAIL = "marcelovilaca@users.noreply.github.com"
EXPECTED_REMOTE = "marcelovilaca/agent-skills"


def _yaml() -> YAML:
    parser = YAML(typ="safe")
    parser.allow_duplicate_keys = False
    return parser


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    lines = content.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter at byte zero")
    end = next((index for index in range(1, len(lines)) if lines[index].strip() == "---"), None)
    if end is None:
        raise ValueError("SKILL.md has no closing frontmatter delimiter")
    metadata = _yaml().load("".join(lines[1:end]))
    if not isinstance(metadata, dict):
        raise ValueError("SKILL.md frontmatter must be a YAML mapping")
    body = "".join(lines[end + 1:]).lstrip("\r\n")
    if not body.strip():
        raise ValueError("SKILL.md body must not be empty")
    return metadata, body


def normalize_name(value: str) -> str:
    name = str(value).strip().lower().replace("_", "-").replace(" ", "-")
    name = re.sub(r"[^a-z0-9-]+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    if not name or len(name) > 64 or not NAME_RE.fullmatch(name):
        raise ValueError(f"Invalid Agent Skills name after normalization: {value!r}")
    return name


def _string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        return ", ".join(str(item) for item in value) if isinstance(value, (list, tuple)) else ""
    return str(value).strip()


def _platform_compatibility(value: Any) -> str:
    if not value:
        return ""
    platforms = value if isinstance(value, (list, tuple, set)) else [value]
    normalized = sorted({str(platform).strip().lower() for platform in platforms if str(platform).strip()})
    if not normalized or set(normalized) >= {"linux", "macos", "windows"}:
        return ""
    names = {"linux": "Linux", "macos": "macOS", "windows": "Windows"}
    rendered = [names.get(item, item) for item in normalized]
    if len(rendered) == 1:
        return f"Requires {rendered[0]}."
    return "Designed for " + ", ".join(rendered[:-1]) + " and " + rendered[-1] + "."


def render_portable_skill(source: str, name: str, version: str | None = None) -> str:
    original, body = parse_frontmatter(source)
    slug = normalize_name(name)
    description = _string(original.get("description"))
    if not description:
        raise ValueError(f"{slug}: description is required")
    if len(description) > 1024:
        raise ValueError(f"{slug}: description exceeds the 1024-character Agent Skills limit")

    old_meta = original.get("metadata") if isinstance(original.get("metadata"), dict) else {}
    portable_meta: dict[str, str] = {}
    author = _string(original.get("author") or old_meta.get("author"))
    if not author or author.lower() in {"hermes agent", "ai assistant", "assistant", "user, hermes agent"}:
        author = f"{OWNER_NAME}, Hermes Agent"
    portable_meta["author"] = author

    selected_version = _string(version or original.get("version") or old_meta.get("version") or "0.1.0")
    if not SEMVER_RE.fullmatch(selected_version):
        selected_version = "0.1.0"
    portable_meta["version"] = selected_version

    hermes_meta = old_meta.get("hermes") if isinstance(old_meta.get("hermes"), dict) else {}
    tags = hermes_meta.get("tags", old_meta.get("tags"))
    if tags:
        portable_meta["hermes_tags"] = _string(tags)
    category = hermes_meta.get("category", old_meta.get("category"))
    if category:
        portable_meta["hermes_category"] = _string(category)
    related = hermes_meta.get("related_skills")
    if related:
        values = related if isinstance(related, (list, tuple)) else [related]
        portable_meta["hermes_related_skills"] = ", ".join(normalize_name(str(item)) for item in values)

    lines = ["---", f"name: {json.dumps(slug, ensure_ascii=False)}", f"description: {json.dumps(description, ensure_ascii=False)}"]
    license_name = _string(original.get("license"))
    if license_name:
        lines.append(f"license: {json.dumps(license_name, ensure_ascii=False)}")
    compatibility = _string(original.get("compatibility")) or _platform_compatibility(original.get("platforms"))
    if compatibility:
        if len(compatibility) > 500:
            raise ValueError(f"{slug}: compatibility exceeds the 500-character Agent Skills limit")
        lines.append(f"compatibility: {json.dumps(compatibility, ensure_ascii=False)}")
    lines.append("metadata:")
    for key in sorted(portable_meta):
        lines.append(f"  {key}: {json.dumps(portable_meta[key], ensure_ascii=False)}")
    lines.extend(["---", "", body.rstrip(), ""])
    return "\n".join(lines)


def bump_patch(previous: str, declared: str | None) -> str:
    match = SEMVER_RE.fullmatch(previous)
    if not match:
        raise ValueError(f"Invalid previous semantic version: {previous!r}")
    previous_parts = tuple(int(value) for value in match.groups())
    if declared and SEMVER_RE.fullmatch(declared):
        declared_parts = tuple(int(value) for value in declared.split("."))
        if declared_parts > previous_parts:
            return declared
    major, minor, patch = previous_parts
    return f"{major}.{minor}.{patch + 1}"


def sanitize_local_paths(text: str, home: Path | None = None) -> str:
    """Replace known local roots with neutral placeholders before a public export."""
    home = home or Path.home()
    roots = {home, Path.home()}
    variants = set()
    for root in roots:
        variants.update({str(root), str(root).replace("/", "\\"), str(root).replace("\\", "/")})
    for variant in sorted(variants, key=len, reverse=True):
        if variant:
            text = re.sub(re.escape(variant), "<USER_HOME>", text, flags=re.IGNORECASE)
    sep = re.escape("\\")
    audio_root = re.compile(r"(?i)[A-Z]:" + sep + r"AudioBooks")
    project_root = re.compile(r"(?i)[A-Z]:" + sep + r"AI" + sep + r"Scripts")
    translations_root = re.compile(r"(?i)[A-Z]:" + sep + r"Translations")
    text = audio_root.sub("<AUDIOBOOKS_ROOT>", text)
    text = project_root.sub("<PROJECT_ROOT>", text)
    text = translations_root.sub("<TRANSLATIONS_ROOT>", text)
    return text


def scan_public_content(text: str, label: str = "content") -> None:
    for description, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            raise ValueError(f"{label}: blocked possible {description}; review the source before publishing")
    if DRIVE_PATH_RE.search(text):
        raise ValueError(f"{label}: blocked absolute Windows path; use a portable placeholder")
    lowered = text.lower()
    if "/home/" in lowered or "/users/" in lowered or "/mnt/c/users/" in lowered:
        raise ValueError(f"{label}: blocked absolute user-home path; use a portable placeholder")


def _skill_path_for_key(root: Path, key: str) -> Path | None:
    normalized = key.replace(chr(92), "/").replace(":", "/").strip("/")
    candidate = root.joinpath(*[part for part in normalized.split("/") if part])
    if (candidate / "SKILL.md").is_file():
        return candidate
    matches = [path.parent for path in root.rglob("SKILL.md") if path.parent.name == normalized.split("/")[-1]]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(f"Ambiguous Hermes skill registry entry: {key}")
    return None


def discover_managed_skills(skills_root: Path, usage: dict[str, Any]) -> dict[str, Path]:
    discovered: dict[str, Path] = {}
    for key, record in usage.items():
        if not isinstance(record, dict) or record.get("state", "active") != "active":
            continue
        if record.get("created_by") not in {"agent", "learn"}:
            continue
        source_dir = _skill_path_for_key(skills_root, str(key))
        if source_dir is None:
            continue
        source_text = (source_dir / "SKILL.md").read_text(encoding="utf-8-sig")
        frontmatter, _ = parse_frontmatter(source_text)
        slug = normalize_name(_string(frontmatter.get("name") or source_dir.name))
        if slug in discovered and discovered[slug] != source_dir:
            raise ValueError(f"Two Hermes skills normalize to the same portable name: {slug}")
        discovered[slug] = source_dir
    return discovered


def _included_files(source_dir: Path) -> list[Path]:
    result = []
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(source_dir)
        if any(part.lower() in SKIP_DIRS for part in relative.parts):
            continue
        if path.name.lower() in SKIP_FILES or path.name.lower().startswith(".env"):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        if path.stat().st_size > MAX_RESOURCE_BYTES:
            raise ValueError(f"{relative.as_posix()}: resource exceeds the 5 MiB public-export limit")
        result.append(path)
    if not any(path.name == "SKILL.md" and path.parent == source_dir for path in result):
        raise ValueError(f"{source_dir}: missing root SKILL.md")
    if not any(path.name == "README.md" and path.parent == source_dir for path in result):
        raise ValueError(f"{source_dir}: missing root README.md technical and how-to guide")
    return result


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path}: binary or non-UTF-8 skill resources require manual review") from exc


def _digest(files: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(files):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(files[relative].encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def prepare_skill(source_dir: Path, slug: str, previous: dict[str, Any] | None, home: Path) -> tuple[dict[str, str], dict[str, Any]]:
    source_files: dict[str, str] = {}
    for path in _included_files(source_dir):
        relative = path.relative_to(source_dir).as_posix()
        source_files[relative] = sanitize_local_paths(_read_text(path), home)

    source_fm, _ = parse_frontmatter(source_files["SKILL.md"])
    declared = _string(source_fm.get("version") or (source_fm.get("metadata") or {}).get("version"))
    canonical_for_hash = render_portable_skill(source_files["SKILL.md"], slug, version="0.0.0")
    hash_files = dict(source_files)
    hash_files["SKILL.md"] = canonical_for_hash
    source_hash = _digest(hash_files)

    if previous is None:
        version = declared if SEMVER_RE.fullmatch(declared) else "0.1.0"
    else:
        previous_version = _string(previous.get("version") or "0.1.0")
        if source_hash == previous.get("source_sha256"):
            declared_parts = tuple(int(value) for value in declared.split(".")) if declared and SEMVER_RE.fullmatch(declared) else ()
            previous_parts = tuple(int(value) for value in previous_version.split(".")) if SEMVER_RE.fullmatch(previous_version) else ()
            version = declared if declared_parts and declared_parts > previous_parts else previous_version
        else:
            version = bump_patch(previous_version, declared)

    output_files = dict(source_files)
    output_files["SKILL.md"] = render_portable_skill(source_files["SKILL.md"], slug, version=version)
    for relative, text in output_files.items():
        scan_public_content(text, f"{slug}/{relative}")
    entry = {
        "version": version,
        "source_sha256": source_hash,
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    return output_files, entry


def default_hermes_home() -> Path:
    configured = os.environ.get("HERMES_HOME")
    if configured:
        return Path(configured).expanduser()
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA")
        return Path(local) / "hermes" if local else Path.home() / "AppData" / "Local" / "hermes"
    return Path.home() / ".hermes"


def load_catalog(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "skills": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("skills"), dict):
        raise ValueError(f"Invalid version catalog: {path}")
    return data


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return result


def _verify_remote(repo: Path) -> None:
    remote = _git(repo, "remote", "get-url", "origin").stdout.strip().lower()
    normalized = remote.removesuffix(".git").replace("git@github.com:", "https://github.com/")
    if not normalized.endswith("github.com/" + EXPECTED_REMOTE):
        raise RuntimeError(f"origin must point to https://github.com/{EXPECTED_REMOTE}.git")


def _prepare_branch(repo: Path) -> None:
    branch = _git(repo, "branch", "--show-current").stdout.strip()
    if branch != "main":
        raise RuntimeError(f"publisher only writes to main; current branch is {branch or '(detached)'}")
    status = _git(repo, "status", "--porcelain").stdout.splitlines()
    unmanaged = [line[3:] for line in status if line[3:] != "catalog.json" and not line[3:].startswith("skills/")]
    if unmanaged:
        raise RuntimeError("uncommitted files outside publisher-managed paths: " + ", ".join(unmanaged))
    _git(repo, "fetch", "origin", "main")
    local = _git(repo, "rev-parse", "HEAD").stdout.strip()
    remote = _git(repo, "rev-parse", "origin/main").stdout.strip()
    if local == remote:
        return
    local_ancestor = _git(repo, "merge-base", "--is-ancestor", local, remote, check=False).returncode == 0
    remote_ancestor = _git(repo, "merge-base", "--is-ancestor", remote, local, check=False).returncode == 0
    if local_ancestor:
        if status:
            raise RuntimeError("remote main advanced while local publisher files are modified; resolve manually")
        _git(repo, "pull", "--ff-only", "origin", "main")
    elif not remote_ancestor:
        raise RuntimeError("local and remote main have diverged; refusing to overwrite GitHub changes")


def _write_package(destination: Path, files: dict[str, str]) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for relative, text in files.items():
        target = destination.joinpath(*relative.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text.replace("\r\n", "\n").replace("\r", "\n"), encoding="utf-8", newline="\n")


def publish(repo: Path, home: Path, dry_run: bool = False, event_action: str = "manual", skill_name: str = "") -> dict[str, Any]:
    repo = repo.expanduser().resolve()
    home = home.expanduser().resolve()
    skills_root = home / "skills"
    usage_path = skills_root / ".usage.json"
    if not (repo / ".git").exists():
        raise RuntimeError(f"not a Git repository: {repo}")
    if not usage_path.is_file():
        raise RuntimeError(f"Hermes skill usage registry is missing: {usage_path}")

    if not dry_run:
        _verify_remote(repo)
        _prepare_branch(repo)

    usage = json.loads(usage_path.read_text(encoding="utf-8"))
    managed = discover_managed_skills(skills_root, usage)
    catalog_path = repo / "catalog.json"
    catalog = load_catalog(catalog_path)
    entries = catalog["skills"]
    changed: list[str] = []
    versions: dict[str, str] = {}
    prepared: dict[str, tuple[dict[str, str], dict[str, Any]]] = {}

    for slug, source_dir in sorted(managed.items()):
        files, entry = prepare_skill(source_dir, slug, entries.get(slug), home)
        versions[slug] = entry["version"]
        current_entry = entries.get(slug, {})
        current_skill_file = repo / "skills" / slug / "SKILL.md"
        current_text = current_skill_file.read_text(encoding="utf-8") if current_skill_file.is_file() else None
        if current_text != files["SKILL.md"] or entry.get("source_sha256") != current_entry.get("source_sha256"):
            changed.append(slug)
        prepared[slug] = (files, entry)

    if dry_run:
        return {"dry_run": True, "event_action": event_action, "skill_name": skill_name, "managed_count": len(managed), "changed": changed, "versions": versions, "verified": False}
    if not changed and catalog_path.exists():
        head = _git(repo, "rev-parse", "HEAD").stdout.strip()
        return {"dry_run": False, "changed": [], "managed_count": len(managed), "versions": versions, "commit": head, "verified": True, "message": "No portable skill changes to publish."}

    for slug, (files, entry) in prepared.items():
        if slug not in changed:
            continue
        _write_package(repo / "skills" / slug, files)
        entries[slug] = entry
    catalog["schema_version"] = 1
    catalog["skills"] = entries
    catalog["updated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    catalog_path.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    _git(repo, "add", "--all", "--", "skills", "catalog.json")
    if _git(repo, "diff", "--cached", "--quiet", check=False).returncode == 0:
        head = _git(repo, "rev-parse", "HEAD").stdout.strip()
        return {"dry_run": False, "changed": [], "managed_count": len(managed), "versions": versions, "commit": head, "verified": True, "message": "No portable skill changes to publish."}

    summary = ", ".join(f"{slug}@{versions[slug]}" for slug in changed) or "catalog update"
    _git(repo, "-c", f"user.name={OWNER_NAME}", "-c", f"user.email={OWNER_EMAIL}", "commit", "-m", f"chore(skills): publish {summary}")
    _git(repo, "push", "origin", "main")
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    remote_head = _git(repo, "ls-remote", "origin", "refs/heads/main").stdout.split()[0]
    if head != remote_head:
        raise RuntimeError("push completed but remote main did not resolve to the local commit")
    return {"dry_run": False, "changed": changed, "managed_count": len(managed), "versions": versions, "commit": head, "verified": True, "repository": "https://github.com/marcelovilaca/Agent-Skills"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1], help="Agent-Skills repository checkout")
    parser.add_argument("--home", type=Path, default=default_hermes_home(), help="Active Hermes home containing skills/.usage.json")
    parser.add_argument("--dry-run", action="store_true", help="Validate and preview without writing or pushing")
    parser.add_argument("--event-action", default="manual", help="Lifecycle event that triggered this run")
    parser.add_argument("--skill-name", default="", help="Local skill name from the lifecycle event")
    args = parser.parse_args(argv)
    try:
        result = publish(args.repo, args.home, args.dry_run, args.event_action, args.skill_name)
    except Exception as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    result["success"] = True
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
