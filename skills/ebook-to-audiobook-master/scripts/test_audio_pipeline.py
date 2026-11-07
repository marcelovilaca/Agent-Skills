from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import shutil
import struct
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_VERSION = "2"
RECIPE = "s16le-44100-mono-to-mp3-q2;concat-compatible-mp3;loudnorm-I-16-TP-1.5-LRA-11;master-output-44100-mono;30s-preview-output-44100-mono;full-decode"
SAMPLE_RATE = 44_100


class PipelineTestError(RuntimeError):
    pass


def run(command: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        detail = (result.stderr or result.stdout)[-1500:]
        raise PipelineTestError(f"Command failed ({result.returncode}): {command[0]}\n{detail}")
    return result


def hermes_home() -> Path:
    configured = os.environ.get("HERMES_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    unix_default = Path.home() / ".hermes"
    if unix_default.is_dir():
        return unix_default.resolve()
    local_app_data = os.environ.get("LOCALAPPDATA")
    windows_default = Path(local_app_data) / "hermes" if local_app_data else None
    if windows_default and windows_default.is_dir():
        return windows_default.resolve()
    raise PipelineTestError("Cannot locate the active Hermes home. Set HERMES_HOME and rerun.")


def fingerprint(ffmpeg: str, ffprobe: str) -> dict[str, str]:
    ffmpeg_version = run([ffmpeg, "-version"], timeout=30).stdout.splitlines()[0]
    ffprobe_version = run([ffprobe, "-version"], timeout=30).stdout.splitlines()[0]
    fields = {
        "script_version": SCRIPT_VERSION,
        "recipe": RECIPE,
        "platform": platform.system(),
        "ffmpeg": ffmpeg_version,
        "ffprobe": ffprobe_version,
    }
    fields["sha256"] = hashlib.sha256(json.dumps(fields, sort_keys=True).encode("utf-8")).hexdigest()
    return fields


def make_pcm(path: Path, frequency: float, seconds: float = 0.6) -> None:
    samples = int(SAMPLE_RATE * seconds)
    payload = bytearray(samples * 2)
    for index in range(samples):
        value = int(10_000 * math.sin(2 * math.pi * frequency * index / SAMPLE_RATE))
        struct.pack_into("<h", payload, index * 2, value)
    path.write_bytes(payload)


def probe(ffprobe: str, path: Path) -> dict:
    result = run([
        ffprobe, "-v", "error", "-show_entries",
        "format=duration,size:stream=codec_name,sample_rate,channels", "-of", "json", str(path),
    ], timeout=60)
    data = json.loads(result.stdout)
    fmt = data.get("format", {})
    streams = data.get("streams", [])
    if not streams or float(fmt.get("duration", 0)) <= 0 or int(fmt.get("size", 0)) <= 0:
        raise PipelineTestError(f"ffprobe found empty or zero-duration audio: {path.name}")
    stream = streams[0]
    if stream.get("codec_name") != "mp3":
        raise PipelineTestError(f"Expected MP3, found {stream.get('codec_name')!r}: {path.name}")
    return {
        "duration_seconds": float(fmt["duration"]),
        "size_bytes": int(fmt["size"]),
        "codec": stream.get("codec_name"),
        "sample_rate": int(stream.get("sample_rate", 0)),
        "channels": int(stream.get("channels", 0)),
    }


def decode(ffmpeg: str, path: Path) -> None:
    run([
        ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-i", str(path),
        "-f", "null", "-",
    ], timeout=120)


def create_and_run_test(ffmpeg: str, ffprobe: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="ebook_audio_pipeline_test_") as temp_name:
        work = Path(temp_name)
        chunk_paths = []
        chunk_infos = []
        for index, frequency in enumerate((440.0, 660.0), start=1):
            pcm = work / f"chunk_{index:03d}.pcm"
            mp3 = work / f"chunk_{index:03d}.mp3"
            make_pcm(pcm, frequency)
            run([
                ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                "-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", "1", "-i", str(pcm),
                "-c:a", "libmp3lame", "-q:a", "2", str(mp3),
            ])
            info = probe(ffprobe, mp3)
            if info["sample_rate"] != SAMPLE_RATE or info["channels"] != 1:
                raise PipelineTestError(f"Unexpected chunk stream format: {info}")
            decode(ffmpeg, mp3)
            chunk_paths.append(mp3)
            chunk_infos.append(info)

        filelist = work / "filelist.txt"
        lines = []
        for path in chunk_paths:
            escaped = str(path.resolve()).replace("\\", "/").replace("'", "'\\''")
            lines.append(f"file '{escaped}'")
        filelist.write_text("\n".join(lines) + "\n", encoding="utf-8")

        master = work / "master.mp3"
        run([
            ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            "-f", "concat", "-safe", "0", "-i", str(filelist),
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ar", str(SAMPLE_RATE), "-ac", "1", "-c:a", "libmp3lame", "-q:a", "2", str(master),
        ])
        master_info = probe(ffprobe, master)
        decode(ffmpeg, master)
        if master_info["sample_rate"] != SAMPLE_RATE or master_info["channels"] != 1:
            raise PipelineTestError(f"Unexpected mastered stream format: {master_info}")

        preview = work / "preview.mp3"
        run([
            ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            "-i", str(master), "-t", "30", "-ar", str(SAMPLE_RATE), "-ac", "1",
            "-c:a", "libmp3lame", "-q:a", "2", str(preview),
        ])
        preview_info = probe(ffprobe, preview)
        decode(ffmpeg, preview)
        if preview_info["duration_seconds"] > min(30.0, master_info["duration_seconds"]) + 1.0:
            raise PipelineTestError(f"Preview duration exceeds expected limit: {preview_info}")

        return {
            "chunks_tested": len(chunk_infos),
            "chunk_streams": chunk_infos,
            "master": master_info,
            "preview": preview_info,
            "all_files_fully_decoded": True,
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a local synthetic-PCM FFmpeg smoke test; no book text or provider is used."
    )
    parser.add_argument("--force", action="store_true", help="rerun even if the current configuration has a cached pass")
    args = parser.parse_args()

    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        print(json.dumps({"status": "failed", "error": "ffmpeg and ffprobe must both be on PATH"}, indent=2))
        return 1

    try:
        home = hermes_home()
        record_path = home / "cache" / "ebook_to_audiobook_master" / "audio_pipeline_test.json"
        current = fingerprint(ffmpeg, ffprobe)
        if not args.force and record_path.is_file():
            try:
                previous = json.loads(record_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                previous = {}
            if previous.get("status") == "passed" and previous.get("fingerprint", {}).get("sha256") == current["sha256"]:
                print(json.dumps({
                    "status": "cached_pass",
                    "record": str(record_path),
                    "fingerprint": current,
                    "tested_at": previous.get("tested_at"),
                    "note": "Configuration fingerprint matches a previously verified local pipeline test.",
                }, ensure_ascii=False, indent=2))
                return 0

        results = create_and_run_test(ffmpeg, ffprobe)
        record = {
            "status": "passed",
            "tested_at": datetime.now(timezone.utc).isoformat(),
            "fingerprint": current,
            "results": results,
        }
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": "passed",
            "record": str(record_path),
            "fingerprint": current,
            "results": results,
            "provider_called": False,
            "book_text_used": False,
        }, ensure_ascii=False, indent=2))
        return 0
    except (PipelineTestError, OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc), "provider_called": False, "book_text_used": False}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
