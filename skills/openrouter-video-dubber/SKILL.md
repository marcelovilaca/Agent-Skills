---
name: "openrouter-video-dubber"
description: "Dub videos with OpenRouter STT and ElevenLabs TTS."
license: "MIT"
compatibility: "Requires Windows."
metadata:
  author: "marcelovilaca, Hermes Agent"
  hermes_related_skills: "local-video-dubber"
  hermes_tags: "video, dubbing, OpenRouter, ElevenLabs, transcription, voice-cloning"
  version: "0.1.0"
---

# OpenRouter Video Dubber

Use this cloud workflow only when the user explicitly invokes this skill or asks for OpenRouter/ElevenLabs dubbing. Generic dubbing requests use `local-video-dubber`; do not silently switch backends. A reusable Python runner handles API requests, checkpoints, retries, and assembly so the skill does not rebuild the pipeline in chat.

## When to Use

- The user explicitly requests `/openrouter-video-dubber`, OpenRouter transcription/translation, or ElevenLabs voice cloning/TTS.
- Inputs may be YouTube URLs or local video/audio files. If both are supplied, ask which is authoritative.
- Do not use for generic dubbing requests; local dubbing remains the default.

## Prerequisites

- Windows, Python 3, `ffmpeg`/`ffprobe`, and `yt-dlp` for YouTube URLs.
- `OPENROUTER_API_KEY` and `ELEVENLABS_API_KEY` in the local process environment. Never request or print either value; check presence only. The runner never stores credentials in `job.json`.
- The user’s standing constraint is to use only proprietary videos they own and have pre-consent to use; do not add a repeated rights/consent prompt.

## Workflow

1. Ask for the source if missing. If both a URL and local file are present, ask which to use. Default target is Portuguese; honor an explicit target-language request.
2. Ask the user to choose a translation model from this exact free-model list; preserve IDs verbatim and recheck availability at run time:
   - `google/gemma-4-26b-a4b-it:free`
   - `nvidia/nemotron-3.5-lightning:free`
   - `google/gemma-4-31b-it:free`
   - `nvidia/nemotron-3-ultra-550b-a55b:free`
   - `nvidia/nemotron-3.5-super-vl:free`
3. Use `scripts/video_dub_runner.py` to create a non-interactive `job.json` without secrets. Run offline tests and local dependency/key-presence checks before network work.
4. Check OpenRouter’s endpoint metadata for `openai/whisper-large-v3-turbo` before downloading or uploading media. If no available endpoint advertises diarization, stop and ask the user; do not send a known-unsupported `diarize` request or switch models silently. If support is advertised, verify the OpenRouter key with `GET /api/v1/key` and ElevenLabs access with `GET /v1/user/subscription` before downloading media; then smoke-test a short clip with `verbose_json` and diarization before full transcription.
5. For YouTube, use `yt-dlp` to extract audio. If it fails, stop and ask for a local media file; do not spend time cycling through download methods. Convert audio to MP3 for processing. Create fixed 5-minute transcription chunks, moving each boundary to the nearest silence with no overlap. If a transcription chunk fails after bounded backoff, preserve completed chunks and stop.
6. Before paid transcription, report the duration and current endpoint price estimate/range (or say it is unavailable), then ask for approval. Save each successful chunk with global timestamps. After all chunks, save the full transcript and create an 8–10 second MP3 review clip per speaker. Show only a compact speaker summary in chat, attach the clips with `MEDIA:`, and wait for approval of the transcript and speaker clips before translation or cloning.
7. Group same-speaker segments across gaps up to 1 second into complete turns. Translate in adaptive batches of whole turns, never one request per segment. Smoke-test one short turn with the selected free model and reuse its translated result; then continue in batches. Default to natural, faithful Brazilian Portuguese. Validate IDs, speakers, and non-empty text; repair once, then try the selected free model and subsequent list entries once each. If a model fails mid-run, use the next free model for remaining batches and record the model per batch. Do not use paid fallback. Do not pause for a separate translation review. Ask the user to name each speaker before voice creation/cloning; retain diarized labels until names are supplied.
8. Automatically assemble 1–2 minutes of clean, non-overlapping MP3 speech per speaker (minimum 1 minute, target 2). If a speaker lacks enough usable audio, stop and ask whether to provide more audio, use a preset voice, or cancel. Before creating any ElevenLabs voices or generating TTS, report estimated voice count, characters, account usage/limits if available, and estimated time/cost; ask once for approval.
9. Create persistent voice clones through the direct ElevenLabs API and save voice IDs. Use `eleven_v4_turbo` for TTS. Generate one short preview in the selected target language per cloned voice and wait for approval before bulk synthesis. Never delete remote voices without approval.
10. Synthesize one request per complete speaker turn; split only turns that exceed API limits. Use at most two concurrent requests, checkpoint every success, and use bounded exponential backoff. Resume matching checkpoints and saved voice IDs; ask before overwriting an existing final MP3.
11. Fit every turn to its original time interval, even if heavy time-stretching is needed. Assemble dubbed dialogue only (no source speech/music) into one MP3. Save all project artifacts under the configured `output_root` (default `~/Translations`); `<TRANSLATIONS_ROOT>\<safe video title>\`; use `<safe title>_(Portuguese).mp3` for the final file. Ask before any cleanup.
12. Run in the foreground; use a monitored background process only if a batch would exceed the 10-minute foreground limit. Report only milestones, not per-turn logs.

## Verification

- Checkpoint and validate every expected turn; no partial dub may be reported as complete.
- Verify the final MP3 exists, is non-empty, decodes with `ffmpeg`, and matches the source duration within encoding tolerance.
- Keep the manifest at `<TRANSLATIONS_ROOT>\<safe title>\job.json` when the title is known; otherwise keep it in `<TRANSLATIONS_ROOT>\.jobs\<stable-id>.json`. Keep transcript, translation, speaker map, voice IDs, turn files, estimates, actual models, and verification results in the project artifacts. In chat, give a concise status, paths (including the manifest), models actually used, and the exact blocker if incomplete.
- Ask before overwriting or deleting local artifacts; never delete ElevenLabs voices without explicit approval.

## Runner

Use `terminal` with `python3 <skill-dir>/scripts/video_dub_runner.py --help`. Run `python3 <skill-dir>/scripts/test_video_dub_runner.py` before any live request. Create a secret-free manifest with `init --url "<URL>"` or `init --file "<local path>"`, the exact selected `--model`, and persistent `--out "<job-manifest-path>"` when the title is not yet known. Set `--output-root` only when the user chooses a different destination. Then run `python3 <skill-dir>/scripts/video_dub_runner.py run "<job.json>"` repeatedly. If the title is known, the manifest may live at `<output-root>/<safe title>/job.json`; the runner permits that manifest as the only pre-existing file. At every gate, ask the user in chat and set only the matching `approvals.*` field true after approval; never add credentials. After transcript assembly, attach each generated 8–10 second speaker clip with `MEDIA:` before requesting transcript/sample approval. Keep the manifest and all checkpoints for resumption. Run foreground; use monitored background only when a batch would exceed ten minutes.
