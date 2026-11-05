# Ebook to Audiobook Master

A resumable, chapter-by-chapter workflow for making audiobook MP3s from a cleaned Markdown book. This guide summarizes the operating steps; the companion [SKILL.md](SKILL.md) is authoritative for exclusions, delivery gates, and recovery rules.

## Overview

The workflow reads one Markdown source and its matching exclusion metadata, filters and chunks the included text, generates audio sequentially, converts and masters each chapter, then verifies and previews it. The default route is OpenRouter's TTS endpoint with the exact model `heygen/heygen-voice-1-turbo:free` and voice `gareth`. That model has been observed to accept PCM rather than MP3, so the PCM response is converted to MP3 using FFmpeg. Never silently substitute another model or voice. If the user explicitly requests another engine or voice, follow it exactly; get approval before sending book text to a different service.

## Triggers and Inputs

Use when the user wants chapter MP3s made from cleaned Markdown and audiobook exclusion rules. This is not a transcription or video-dubbing workflow.

Required input is an unambiguous book directory containing exactly one main Markdown file in `Source/` and matching UTF-8 `Source/metadata_and_exclusions.json`. If either is missing/invalid, if multiple Markdown files are candidates, or if chapter boundaries are unclear, stop and ask rather than choosing text to narrate. Final masters go in `Audio/`.

Each chapter title is spoken once at the start unless the user requests otherwise. Every TTS request must be non-empty and no longer than 5,000 characters or the provider's stricter limit.

## Prerequisites

- Windows, as required by the skill.
- The source Markdown and its exclusion JSON, validated before any request.
- `ffmpeg` and `ffprobe` available for PCM conversion, MP3 mastering, and verification.
- For the default route, a securely accessible `OPENROUTER_API_KEY` from the process environment or configured Hermes credentials/environment. Do not assume a nested process's missing environment variable means the credential is unavailable; resolve configured Hermes credentials safely and never display or log the value.
- A secure way to issue HTTPS requests to `https://openrouter.ai/api/v1/audio/speech`.

Do not install tools or send book text to a service other than the selected OpenRouter endpoint without the user's approval. Do not use a generic text-to-speech tool unless it can demonstrably use the exact requested model and voice. If the exact free model is unavailable or rejected, stop and report the blocker; do not fall back to the paid base model.

## How to Use

### Quick start

1. Inspect the book directory. Confirm exactly one `Source/*.md` file and valid `Source/metadata_and_exclusions.json`; verify FFmpeg/ffprobe and secure access to the configured credential without printing it.
2. Read the source and exclusions. Build the complete ordered track list and perform a read-only preflight of every included numbered chapter and eligible epilogue/coda. Reconcile each `EXCLUDE_FROM_AUDIO` marker with its `inline_exclusions` metadata entry. Stop before TTS if any section is ambiguous, malformed, or cannot be safely chunked.
3. Remove full exclusion comments, filter Markdown without dropping prose, omit disallowed matter, then split at safe sentence boundaries. Recount final request text immediately before sending and keep every chunk within both character limits.
4. Generate one track at a time with the exact default request shape:

   ```json
   {
     "model": "heygen/heygen-voice-1-turbo:free",
     "input": "<non-empty filtered chunk text>",
     "voice": "gareth",
     "response_format": "pcm"
   }
   ```

   Authenticate with the configured bearer credential and send `Content-Type: application/json`. A successful response is raw PCM bytes, not JSON. Save it with a `.pcm` extension, then use FFmpeg to convert and validate an MP3 chunk.
5. Stitch compatible chunk streams in order, master the whole chapter as MP3, and apply the whole-track loudness target `loudnorm=I=-16:TP=-1.5:LRA=11`. Verify the master and make a verified 30-second preview (or use the whole track if shorter).
6. Deliver the verified chapter MP3 and playable preview, then pause for the user's choice: continue one chapter, recreate this chapter, or continue the remaining chapters without asking again. Do not start or queue another chapter until the user's choice permits it.
7. After the final track, run the output audit from this skill directory:

   ```sh
   python scripts/verify_audiobook_outputs.py "<book_directory>"
   ```

   The verifier prints a JSON report and returns a nonzero exit status when the audit fails.

### Workflow and outputs

- Extract level-one `# Chapter <number>...` sections in source order. Exclude pre-chapter matter and metadata-designated sections such as TOC, preface, foreword, bibliography, references, index, or publisher/editor matter. A recognized unnumbered epilogue/coda is a separate final track unless excluded.
- Preserve narrative text and paragraph order; omit raw HTML, URLs, footnote markers, page numbers, and decorative image markup. Remove complete, including multiline, `<!-- EXCLUDE_FROM_AUDIO: ... -->` blocks. Do not use text stored in the exclusion JSON as narration.
- Save resumable work under `temp_audio_chunks/Chapter_<NN>/`, including a manifest, chunk files, and concat file list as needed. Preserve matching completed statuses on resume; save PCM as PCM, never with an `.mp3` suffix.
- Save chapter masters under `Audio/` as `<Book Name>-<NN>-<Chapter Title>.mp3`; save previews in `Audio/Previews/` with `-preview.mp3` suffixes. Sanitize Windows-invalid filename characters and report substitutions.
- Keep failed/interrupted chunk data and manifests for resumption. Remove temporary chunk audio only after the master and preview pass verification.

## Technical Details

### Tools, files, and formats

The bundled helper is [scripts/verify_audiobook_outputs.py](scripts/verify_audiobook_outputs.py); it is an auditor, not a TTS generator. The generation process is orchestrated through the skill workflow. The directory layout uses `Source/`, `temp_audio_chunks/`, and `Audio/`, with a book-level `Audio/audiobook_progress.json` and per-track `manifest.json` files.

For the default model, request PCM as observed by the skill; OpenRouter's model page identifies 44.1 kHz mono PCM and its TTS documentation defines PCM as 16-bit little-endian. Convert with FFmpeg input options `-f s16le -ar 44100 -ac 1`. Inspect chunk codec, sample rate, and channel layout before using the concat demuxer; if streams differ, normalize to a compatible intermediate format or use a suitable filter concat. Encode the chapter master with `libmp3lame` quality 2 and apply loudness normalization after stitching, not independently per chunk.

The verifier expects exactly one Markdown source plus exclusion metadata and a progress manifest; it checks expected numbered chapter/epilogue coverage, chunk manifests and recorded chunk limits, model/voice consistency, exclusion counts, output paths, MP3 and preview size/duration/full decode, and total duration. It also requires FFmpeg and ffprobe on `PATH`. Its report includes warnings and errors, per-track results, duration totals, and `all_verified`.

### Verification

Before TTS, confirm source uniqueness, valid JSON, clear boundaries, exclusion-count agreement, and chunkability for every included track. Before marking a chunk complete, check that the converted MP3 is non-empty and decodable. Before marking a track complete, check that the master and preview are non-empty, decodable, and have positive duration; include verified pre-existing tracks in the total and report generated and skipped tracks separately.

Run the bundled verifier after the final track. Its checks do not replace the required human review of text filtering, attribution/language suitability, or delivery choices. A successful process exit and JSON `all_verified: true` are required before claiming the full book is complete.

### Safety and limitations

- Never expose credentials in logs, manifests, or chat. Store source/filter hashes and chunk metadata in manifests, not API secrets.
- Never narrate excluded text or guess which source file/section the user intended. Stop on malformed exclusion markers or unresolved metadata mismatches.
- Never exceed 5,000 characters or a stricter provider limit. If a sentence is too long, split at a safe comma/semicolon or word boundary and record the exception.
- OpenRouter success bodies contain audio bytes, not JSON. Keep the `.pcm` extension until conversion. Use exactly `heygen/heygen-voice-1-turbo:free` for the default route; do not remove `:free` or silently substitute the paid base model.
- Retry rate limits with bounded backoff and transient failures only a limited number of times; request/configuration errors are blockers. Preserve valid chunks and manifests when a track fails.
- Existing masters may be skipped only after validation. Preserve invalid files before regeneration and never silently overwrite a valid chapter.
- The verifier recognizes numbered chapter headings and an optional `Epilogue`, `Epílogo`, or `Coda`; it does not detect arbitrary language/content-quality problems and does not include an introduction in its expected-track set. Provider availability, response limits, voice quality, and generation latency are external and may change.