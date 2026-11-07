from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path


def probe(ffprobe: str, path: Path) -> tuple[float | None, int | None, str | None]:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration,size", "-of", "json", str(path)],
        capture_output=True, text=True, timeout=90,
    )
    if result.returncode:
        return None, None, result.stderr[-1000:]
    try:
        fmt = json.loads(result.stdout)["format"]
        return float(fmt["duration"]), int(fmt["size"]), None
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return None, None, str(exc)


def decode(ffmpeg: str, path: Path) -> tuple[bool, str | None]:
    result = subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-i", str(path), "-f", "null", "-"],
        capture_output=True, text=True, timeout=600,
    )
    return result.returncode == 0, result.stderr[-1000:] if result.returncode else None


def display_duration(seconds: float) -> str:
    whole = int(seconds)
    return f"{whole // 3600}:{(whole % 3600) // 60:02d}:{whole % 60:02d}"


def resolve_track_path(root: Path, value: str | None) -> Path:
    if not value:
        return Path()
    path = Path(value)
    return path if path.is_absolute() else root / path


def find_manifest(root: Path, track_id: str) -> Path | None:
    chunks_root = root / "temp_audio_chunks"
    if track_id.isdigit():
        candidate = chunks_root / f"Chapter_{int(track_id):02d}" / "manifest.json"
        return candidate if candidate.is_file() else None
    for candidate in chunks_root.glob("Chapter_*/manifest.json"):
        try:
            manifest = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if manifest.get("chapter_id") == track_id or manifest.get("chapter_type") == track_id:
            return candidate
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit audiobook source coverage, manifests, MP3s, previews, and total runtime.")
    parser.add_argument("book_directory", type=Path, help="Book directory containing Source/, Audio/, and temp_audio_chunks/")
    args = parser.parse_args()
    root = args.book_directory.expanduser().resolve()
    source_dir = root / "Source"
    progress_path = root / "Audio" / "audiobook_progress.json"
    metadata_path = source_dir / "metadata_and_exclusions.json"
    sources = sorted(source_dir.glob("*.md"))
    errors: list[str] = []
    warnings: list[str] = []
    if len(sources) != 1:
        print(json.dumps({"error": f"Expected exactly one Markdown source in {source_dir}; found {len(sources)}."}, ensure_ascii=False, indent=2))
        return 1
    if not metadata_path.is_file() or not progress_path.is_file():
        missing = [str(p) for p in (metadata_path, progress_path) if not p.is_file()]
        print(json.dumps({"error": "Required metadata/progress file missing.", "missing": missing}, ensure_ascii=False, indent=2))
        return 1
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
        source_bytes = sources[0].read_bytes()
        source_text = source_bytes.decode("utf-8-sig")
        source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    except (OSError, json.JSONDecodeError, UnicodeError) as exc:
        print(json.dumps({"error": f"Could not parse an input file: {exc}"}, ensure_ascii=False, indent=2))
        return 1

    expected = {match.group(1) for match in re.finditer(r"(?im)^#\s*Chapter\s+(\d+)\b[^\n]*$", source_text)}
    book_ordinals = {"primeiro": "1", "segundo": "2", "terceiro": "3", "quarto": "4", "cinco": "5", "quinto": "5", "sexto": "6", "setimo": "7"}
    for match in re.finditer(r"(?im)^#{1,6}\s+([^\n]+?)\s*$", source_text):
        heading = match.group(1).strip()
        normalized = unicodedata.normalize("NFKD", heading).encode("ascii", "ignore").decode("ascii").casefold()
        if normalized in {"proemio", "prologo"}:
            expected.add("proemio")
        book = re.fullmatch(r"livro\s+(primeiro|segundo|terceiro|quarto|cinco|quinto|sexto|setimo)", normalized)
        if book:
            expected.add(book_ordinals[book.group(1)])
    if not expected:
        errors.append("No numbered Chapter, Proémio, or recognized Livro headings found in the source.")
    epilogue = re.search(r"(?im)^#\s*(Epilogue|Epílogo|Coda)\b[^\n]*$", source_text)
    if epilogue:
        labels = " ".join(str(section.get(key, "")) for section in metadata.get("excluded_sections", []) for key in ("type", "title", "heading", "section", "name")).casefold()
        heading_name = epilogue.group(0).lstrip("# ").casefold()
        epilogue_terms = ("epilogue", "epílogo", "coda")
        explicitly_excluded = any(term in labels for term in epilogue_terms) or any(term in heading_name and term in labels for term in epilogue_terms)
        if not explicitly_excluded:
            expected.add("epilogue")

    chapters = progress.get("chapters", {})
    sort_track = lambda item: (0 if item == "proemio" else 2 if item == "epilogue" else 1, int(item) if item.isdigit() else 0)
    missing_ids = sorted(expected - set(chapters), key=sort_track)
    for track_id in missing_ids:
        errors.append(f"Missing progress entry for source track {track_id}.")

    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        print(json.dumps({"error": "FFmpeg and ffprobe must be available on PATH."}, ensure_ascii=False, indent=2))
        return 1

    tracks = []
    total_seconds = 0.0
    verified_ids = []
    # Use the skill defaults unless the user's selected engine/voice are recorded in progress.
    expected_model = progress.get("model") or "heygen/heygen-voice-1-turbo:free"
    expected_voice = progress.get("voice") or "gareth"
    for track_id in sorted(expected, key=sort_track):
        item = chapters.get(track_id)
        if not item:
            continue
        if item.get("status") != "complete":
            errors.append(f"Track {track_id}: progress status is {item.get('status')!r}, not complete.")
            continue

        manifest_path = find_manifest(root, track_id)
        manifest: dict = {}
        if not manifest_path:
            errors.append(f"Track {track_id}: chunk manifest is missing.")
        else:
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"Track {track_id}: chunk manifest cannot be read: {exc}")
                manifest = {}
            if manifest:
                if manifest.get("source_sha256") and manifest["source_sha256"] != source_sha256:
                    errors.append(f"Track {track_id}: manifest source hash does not match the current Markdown.")
                if manifest.get("chapter_status") not in (None, "complete", "skipped_existing_valid"):
                    errors.append(f"Track {track_id}: manifest status is {manifest.get('chapter_status')!r}.")
                if manifest.get("final_verified") is False or manifest.get("preview_verified") is False:
                    errors.append(f"Track {track_id}: manifest marks the final audio or preview unverified.")
                tts = manifest.get("tts", {})
                model = tts.get("model") or manifest.get("model")
                voice = tts.get("voice") or manifest.get("voice")
                if model:
                    if expected_model is None:
                        expected_model = model
                    elif model != expected_model:
                        errors.append(f"Track {track_id}: model mismatch ({model!r}).")
                else:
                    warnings.append(f"Track {track_id}: model is absent from the manifest.")
                if voice:
                    if expected_voice is None:
                        expected_voice = voice
                    elif voice != expected_voice:
                        errors.append(f"Track {track_id}: voice mismatch ({voice!r}).")
                else:
                    warnings.append(f"Track {track_id}: voice is absent from the manifest.")
                response_format = tts.get("response_format")
                if response_format and response_format != "pcm":
                    errors.append(f"Track {track_id}: response format mismatch ({response_format!r}); the selected free HeyGen model requires PCM.")
                elif model == "heygen/heygen-voice-1-turbo:free" and not response_format:
                    warnings.append(f"Track {track_id}: response format is absent from the manifest.")
                removed = manifest.get("exclusion_markers_removed")
                mapped = manifest.get("inline_exclusion_records_for_chapter")
                section_name = "Epílogo" if track_id == "epilogue" else "Proémio" if track_id == "proemio" else f"Chapter {track_id}"
                metadata_inline_count = sum(entry.get("section") == section_name for entry in metadata.get("inline_exclusions", []))
                if mapped is not None and mapped != metadata_inline_count:
                    errors.append(f"Track {track_id}: manifest inline-exclusion count ({mapped}) differs from metadata ({metadata_inline_count}).")
                if removed is not None and removed != metadata_inline_count:
                    errors.append(f"Track {track_id}: removed exclusion-marker count ({removed}) differs from metadata ({metadata_inline_count}).")
                chunks = manifest.get("chunks", [])
                if chunks:
                    if manifest.get("chunk_count") not in (None, len(chunks)):
                        errors.append(f"Track {track_id}: manifest chunk count does not match its chunk records.")
                    ceiling = min(5000, int(manifest.get("max_chunk_characters", 5000)))
                    if any(int(chunk.get("character_count", 0)) > ceiling for chunk in chunks):
                        errors.append(f"Track {track_id}: a recorded chunk exceeds the {ceiling}-character ceiling.")
                    if manifest.get("chapter_status") != "skipped_existing_valid" and any(chunk.get("status") != "complete" for chunk in chunks):
                        errors.append(f"Track {track_id}: one or more chunks are not complete.")
                else:
                    warnings.append(f"Track {track_id}: manifest has no chunk records.")

        output_path = resolve_track_path(root, item.get("output"))
        preview_path = resolve_track_path(root, item.get("preview"))
        for field, label, target_path in (("final_output", "output", output_path), ("preview_output", "preview", preview_path)):
            recorded_path = manifest.get(field)
            if recorded_path and resolve_track_path(root, recorded_path) != target_path:
                errors.append(f"Track {track_id}: progress {label} path differs from its chunk manifest.")
        track_duration = None
        track_ok = True
        for kind, path in (("output", output_path), ("preview", preview_path)):
            if not path.is_file():
                errors.append(f"Track {track_id}: missing {kind} file: {path}")
                track_ok = False
                continue
            duration, size, error = probe(ffprobe, path)
            if duration is None or duration <= 0 or not size:
                errors.append(f"Track {track_id}: {kind} failed ffprobe ({error or 'empty/zero-duration file'}).")
                track_ok = False
                continue
            decoded, decode_error = decode(ffmpeg, path)
            if not decoded:
                errors.append(f"Track {track_id}: {kind} failed full decode ({decode_error}).")
                track_ok = False
                continue
            if kind == "output":
                track_duration = duration
                total_seconds += duration
                recorded = item.get("duration_seconds")
                if recorded is not None and abs(float(recorded) - duration) > 0.2:
                    errors.append(f"Track {track_id}: recorded duration {recorded} differs from ffprobe {duration}.")
            else:
                expected_preview = min(30.0, track_duration) if track_duration is not None else 30.0
                if abs(duration - expected_preview) > 1.0:
                    errors.append(f"Track {track_id}: preview duration {duration:.2f}s is not approximately {expected_preview:.2f}s.")
        tracks.append({"id": track_id, "title": item.get("title"), "duration_seconds": track_duration, "duration_hms": display_duration(track_duration) if track_duration else None, "verified": track_ok})
        if track_ok:
            verified_ids.append(track_id)

    result = {
        "book_directory": str(root),
        "source_markdown": str(sources[0]),
        "expected_track_count": len(expected),
        "verified_track_count": len(verified_ids),
        "missing_track_ids": missing_ids,
        "tracks": tracks,
        "total_duration_seconds": total_seconds,
        "total_duration_hms": display_duration(total_seconds),
        "requested_model": expected_model,
        "requested_voice": expected_voice,
        "warnings": warnings,
        "errors": errors,
        "all_verified": not errors and len(verified_ids) == len(expected),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["all_verified"] else 1


if __name__ == "__main__":
    sys.exit(main())
