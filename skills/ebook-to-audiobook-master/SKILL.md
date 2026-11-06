---
name: "ebook-to-audiobook-master"
description: "Create chaptered Portuguese audiobooks from Markdown."
license: "MIT"
compatibility: "Requires Windows."
metadata:
  author: "marcelovilaca, Hermes Agent"
  hermes_related_skills: "pdf-to-epub-master"
  hermes_tags: "audiobook, TTS, Portuguese, FFmpeg, Markdown, audio"
  version: "0.1.3"
---

# Ebook to Audiobook Master

Produce a resumable, chapter-by-chapter Portuguese audiobook from the cleaned Markdown in a book directory. Default to OpenRouter's Text-to-Speech API with model `heygen/heygen-voice-1-turbo:free`, voice `gareth`, and MP3 output. Respect audiobook exclusions, the TTS engine's limits, and the hard 5,000-character maximum; never claim completion for missing or unverified audio. If the user explicitly requests another engine or voice, follow it exactly—do not silently substitute.

## When to Use

- The user wants chapter MP3s made from a cleaned Markdown book.
- Audiobook generation must honor `metadata_and_exclusions.json` and `EXCLUDE_FROM_AUDIO` markers.
- Don't use for transcribing existing audio or dubbing video.

## Inputs and Defaults

- Required: `book_directory` (normally `<AUDIOBOOKS_ROOT>\<Author>\<Title>\`).
- Use exactly one prepared Markdown source in `Source\` and its matching `Source\metadata_and_exclusions.json`. If either is missing or ambiguous, stop and ask; do not guess which book file to narrate. If the user supplies a PDF or plain-text source and explicitly asks to prepare it, run `pdf_to_epub_master` on that exact source, verify the resulting Markdown and exclusion JSON, and use only those prepared files; never narrate the raw input.
- Final files go to `Audio\` under the book directory.
- Hard limit: at most 5,000 characters per submitted TTS chunk, or the engine's lower limit if stricter.
- Speak each chapter title once at the beginning of its audio, unless the user requests otherwise.
- Default TTS: OpenRouter endpoint `https://openrouter.ai/api/v1/audio/speech`; model exactly `heygen/heygen-voice-1-turbo:free`; voice exactly `gareth`; final audiobook output is MP3. OpenRouter's live response for this exact free model rejected `response_format: "mp3"` with HTTP 400 (`HeyGen Voice only supports response_format "pcm"`), so request PCM and convert it to MP3 with FFmpeg; never substitute the paid base model.
- Send one request per chunk with JSON shaped like `{"model":"heygen/heygen-voice-1-turbo:free","input":"<filtered chunk text>","voice":"gareth","response_format":"pcm"}`. Replace the placeholder with the actual non-empty chunk text. Save the raw PCM using its true extension and transcode to MP3; never label PCM bytes as `.mp3`.
- Use exactly `heygen/heygen-voice-1-turbo:free`. The reference documentation describes the standard paid base model; it does not override this requested free model. Never remove `:free` or fall back to `heygen/heygen-voice-1-turbo`. If OpenRouter rejects the free model ID or reports it unavailable, stop and report that blocker.
- For Brazilian Portuguese, require prepared source metadata language `pt-BR` and submit cleaned Portuguese text. The documented OpenRouter HeyGen request schema has no `language` field: do not add an undocumented parameter or switch models/voices to simulate one. Rely on provider language detection from the text; record requested/input language and `Content-Language` when returned, reject a returned non-Portuguese language, and disclose when regional output was not independently confirmed.

## Prerequisites

Use `terminal` to verify the input files and discover FFmpeg/ffprobe before generating audio. For the default OpenRouter route, resolve `OPENROUTER_API_KEY` from the process environment or the active Hermes home `.env` file (`$HERMES_HOME/.env`) without printing or exposing its value. Do not conclude the key is missing just because a nested terminal process does not inherit it; inspect Hermes-managed credentials safely. If a credential is present in the Hermes auth pool but not available to the direct request process, use Hermes's configured credential resolution rather than asking for a duplicate key. Stop and ask the user only if no configured credential can be accessed securely. Send requests only to `https://openrouter.ai/api/v1/audio/speech` with `Authorization: Bearer $OPENROUTER_API_KEY` and `Content-Type: application/json`. Use the exact model and voice specified above and the response format currently supported by that model. The selected free HeyGen model has been observed to support PCM only; convert its response to the required final MP3 files with FFmpeg. Never print, log, or store API keys, passwords, or access tokens. Do not use the generic `text_to_speech` tool unless it can demonstrably use this exact OpenRouter model and `gareth` voice. Request approval before installing tools or sending book text to a service other than the selected OpenRouter endpoint.

## Procedure

1. **Inspect source and exclusions.** Read the single main `.md` file under `Source\` and parse `Source\metadata_and_exclusions.json` as UTF-8 JSON. Validate the JSON and note excluded section types/titles. Do not use JSON's stored excluded text as narration. If there are multiple candidate Markdown files, invalid JSON, or no chapter headings, stop and ask how to proceed.

2. **Extract chapters and filter.** Parse chapters in source order using level-one headings matching `# Chapter <number>...` (case-insensitive; accept the source's exact chapter titles). Narrate only content inside those chapter boundaries; omit pre-chapter matter and any recognized TOC, preface, foreword, bibliography, reference lists, index, or editor/translator/publisher sections identified in the JSON. Remove each complete `<!-- EXCLUDE_FROM_AUDIO: ... -->` marker, including multiline markers, before TTS. If a marked block is malformed or an exclusion cannot be mapped confidently, stop that chapter and report it rather than risking narration of excluded text. Strip Markdown syntax without removing prose: retain headings/lists as readable words, remove formatting markers and decorative image markup, and do not read raw HTML, URLs, footnote markers, or page numbers. Preserve narrative paragraphs, dialogue, and meaningful text. Before generation, build an ordered track list and record each track's sequence, source chapter number (if any), title, and filtered character count in the progress manifest. Keep source numbering distinct from track sequence: progress denominators count all included tracks, including an introduction and an unnumbered epilogue/coda, while labels preserve the source chapter number/title. For an unnumbered epilogue/coda, assign a synthetic sort sequence after the highest numbered source track; do not imply that the source heading itself was numbered. For each chapter or included section, compare the number of removed `EXCLUDE_FROM_AUDIO` markers with matching `inline_exclusions` records; resolve any mismatch before TTS. Include an unnumbered epilogue/coda after the last numbered chapter as a separate final track unless exclusions metadata excludes it; use its own heading boundary and audit its inline exclusions instead of silently omitting it. Before the first TTS request, run a read-only preflight over every numbered chapter and included epilogue/coda: validate boundaries, marker-to-metadata counts, malformed markers, and chunkability under the configured ceiling; estimate each track's chunk count and resolve any section that cannot be safely filtered or split. Do not submit any book text until every included section passes this preflight.

3. **Chunk at safe boundaries.** Split each chapter at sentence endings (`.`, `!`, `?`, or `…`), keeping closing quotation marks/brackets with the sentence. Avoid false sentence boundaries in decimals, common abbreviations, initials, and ellipses. Pack consecutive complete sentences into chunks no longer than 5,000 characters and no longer than the provider's limit, counting with the provider's documented method as well as Unicode code points. If the provider's counting rule is unclear, conservatively enforce both code-point and UTF-8-byte counts against the ceiling. Preserve paragraph order and use paragraph breaks between paragraphs. Never exceed the limit. If one sentence itself exceeds the limit, split first at the nearest comma or semicolon under the limit; if neither exists, use the nearest safe word boundary. Record every such exceptional split in the manifest. Recount final payloads after cleanup/formatting, immediately before submitting them to TTS.

4. **Prepare resumable working data.** Create `temp_audio_chunks\Chapter_<NN>\` under the book directory and write a manifest containing the source/filtered-text hash, chapter number/title, requested engine and voice ID, chunk order/text hashes, and each chunk's status. Do not store credentials. Before rebuilding a manifest, load it and retain statuses for chunks whose source/filter hash, chunk-text hash, model, and voice still match; never reset matching completed chunks to pending, because that can repeat provider calls on resume. Reuse a completed MP3 only after ffprobe and full-decode checks. If matching PCM was received but conversion was interrupted, resume from the saved PCM instead of calling TTS again. If a partial or corrupt MP3 exists, move it to a timestamped backup before converting again. Use sequential names `chunk_001.mp3`, `chunk_002.mp3`, etc. When the TTS response is PCM, first save it as `chunk_001.pcm` (or equivalent actual extension), then transcode and validate the MP3 chunk before stitching; never give raw PCM a `.mp3` extension.

5. **Generate audio.** Submit chunks sequentially to `POST https://openrouter.ai/api/v1/audio/speech` using the exact JSON fields `model: "heygen/heygen-voice-1-turbo:free"`, the non-empty chunk text as `input`, `voice: "gareth"`, and `response_format: "pcm"` (this exact model returned HTTP 400 when MP3 was requested and stated it supports PCM only). Authenticate with the configured `OPENROUTER_API_KEY` bearer token; set `Content-Type: application/json`. A successful response is raw audio bytes, not JSON: write the PCM body directly to a `.pcm` file and record `X-Generation-Id` and `Content-Type` when present. Do not call `response.json()` on a successful response. OpenRouter's model page identifies this exact model as 44.1 kHz mono PCM, and its TTS API docs define PCM as 16-bit little-endian. Convert using FFmpeg input options `-f s16le -ar 44100 -ac 1`; transcode to a true MP3 `.mp3` chunk, then verify it is non-empty and decodable before marking complete. For non-2xx responses, read the documented JSON error body; treat 400/401/402/403/404/413 as request/configuration blockers, retry 429 with bounded backoff, and retry transient 502/503/524/529 failures only a limited number of times. Use the book-wide preflight estimate to decide whether a chapter will take several minutes; for long chapters, start one chapter process with `terminal(background=true, pty=true, notify=true)` and track it through its completion notification. Keep chapter processing serial—never queue later chapter requests while the current chapter is generating or mastering. When a notified background job is still running after a `process_manage.wait` window expires, do independent source or manifest audits and rely on the completion notification instead of repeatedly waiting or busy-polling. If a foreground wrapper times out, inspect the process session and manifest before resuming, because the process may still be alive or may have completed some chunks. If a chunk still fails or PCM format details are unavailable, stop that chapter, keep valid working chunks and the manifest for resumption, and report the status/code/message. Never mark a chapter complete from text-only or partial provider responses.

6. **Stitch and master each chapter.** Inspect chunk codecs, sample rates, and channels. Use FFmpeg's concat demuxer with a correctly escaped `filelist.txt` only when the inputs are stream-compatible. If they are not, first transcode them to a common intermediate format/sample rate/channel layout or use a suitable FFmpeg filter concat; do not rely on a concat command that drops, corrupts, or reorders audio. Encode the stitched master as MP3 with `libmp3lame` quality 2 and apply the requested loudness target: `loudnorm=I=-16:TP=-1.5:LRA=11`. Apply loudness normalization to the whole chapter, not independently to each chunk. If FFmpeg fails, preserve working chunks and report the error.

7. **Name outputs and resume safely.** Save each chapter as `<Book Name>-<Chapter Number padded to 2 digits>-<Chapter Title>.mp3` in `Audio\` (example: `The Great Gatsby-01-Chapter One.mp3`). Sanitize Windows-invalid filename characters and trailing spaces/dots; use a neutral `Chapter <number>` when no title exists, and report any substitutions. Before rendering a chapter, check for the exact expected output. If it exists and ffprobe/FFmpeg confirms nonzero duration and decodable audio, skip it as complete. If it exists but is invalid, preserve it under a clearly marked backup name before regenerating; never silently overwrite a valid file. Record skipped/generated status in the manifest.

8. **Verify, preview, and report.** Verify every new chapter MP3 is non-empty, decodable, and has a positive ffprobe duration. Include previously verified skipped files when computing total audiobook duration; list generated and skipped chapters separately. After each chapter master passes verification, create a 30-second preview clip from its beginning (or the full chapter if shorter), save it under `Audio/Previews/` with a `-preview.mp3` suffix, and verify the clip is non-empty and decodable. Only after the master and preview pass verification, delete that chapter's temporary chunk audio and file list; keep failed chapter chunks/manifests for resumption. Deliver the full chapter path and playable preview, then follow the Chapter-by-Chapter Delivery and User Choice gate. Do not start or queue the next chapter until the user's choice allows it. Report progress as `Track X/N complete` (or explicitly skipped/failed), with the source chapter number/title shown separately when present; the denominator must count every included audio track, including an introduction and epilogue/coda. Give exact output and preview paths, duration per track, total audiobook duration, and any exclusions or chunk-limit exceptions. Do not claim all chapters complete if any chapter failed or remains unverified. After the final track, run `scripts/verify_audiobook_outputs.py <book_directory>` to compare source track coverage, the progress/chunk manifests, the configured engine/voice against the user-selected values (defaulting to the exact free HeyGen model and Gareth when no override is recorded), exclusion counts, chunk limits, progress-to-manifest output paths, MP3 and preview decodability, and total duration before reporting completion.

## Chapter-by-Chapter Delivery and User Choice

- Work serially: generate, stitch, master, and verify one chapter at a time. Never submit or queue TTS requests for a later chapter while waiting for the user's decision on the current one.
- After a chapter MP3 is verified, create a 30-second preview from the start of the final master with FFmpeg; use the whole chapter if it is shorter than 30 seconds. Save it as `Audio/Previews/<Book Name>-<NN>-<Chapter Title>-preview.mp3`, verify it is non-empty and decodable, and keep the complete chapter MP3 unchanged.
- Present the exact full MP3 path and attach/deliver the full MP3 and preview as playable media (use `MEDIA:` paths in Hermes desktop). State the chapter number, duration, and that verification passed. Do not use a text-only description as the preview.
- Then use `clarify` to ask the user to choose one:
  1. `Continue to the next chapter (ask me again afterward)`.
  2. `Re-create this chapter`.
  3. `Continue through all remaining chapters without asking again`.
- Choice 1 starts only the next chapter; after its verified preview and path are delivered, ask the same question again. Choice 2 preserves the current valid MP3 under a timestamped backup name, rebuilds only that chapter with the same source/model/voice/settings, re-verifies the MP3 and preview, delivers both again, and asks again. Never silently overwrite the prior result.
- Choice 3 enables auto-continue for the rest of this book: set `auto_continue: true` in a book-level progress manifest and merge each chapter's status, output, preview, and duration into it, preserving prior chapter records (including verified existing tracks) rather than rebuilding the manifest. Generate strictly one chapter at a time and still deliver the path and playable preview after every verified chapter. Do not ask for another choice during auto-continue or after the final remaining chapter; provide the final summary.
- When auto-continue is false, ask after the final chapter too and explain that continuing only finishes the book while recreating rebuilds the final chapter. When auto-continue is true, do not reopen the choice prompt.
- If the `clarify` tool is unavailable, present the same three choices in chat and pause. If the user choice is unanswered, cancelled, or times out, leave the verified current track complete, do not queue or generate another track, and pause; state the available choices in chat and wait for the user's next message rather than automatically re-opening the prompt. Never assume the user wants to continue. If generation, stitching, verification, or preview creation fails, report the blocker and preserve resumable files; do not present an unverified preview or advance to another chapter.

## Output Layout

```text
<AUDIOBOOKS_ROOT>\<Author>\<Title>\
├── Source\
│   ├── <Title>.md
│   └── metadata_and_exclusions.json
├── temp_audio_chunks\
│   └── Chapter_<NN>\   # retained only if interrupted/failed
└── Audio\
    ├── <Book Name>-01-<Chapter Title>.mp3
    └── ...
```

Preview clips are saved under `Audio/Previews/`, alongside the per-chapter MP3 files.

## Pitfalls

- Provider limits and character-count rules differ; 5,000 is a hard ceiling, not an assumption about every API's maximum.
- OpenRouter success responses contain raw audio bytes, not JSON. Only parse JSON on error responses. This exact HeyGen free model currently supports PCM only; preserve its true `.pcm` extension and transcode to MP3 with FFmpeg before stitching.
- Always use the literal model ID `heygen/heygen-voice-1-turbo:free`. Never remove `:free` or try the standard paid base model as a fallback; if the free model is unavailable, stop and report it.
- Markdown audio markers may span lines. Remove the full marked block before text cleaning and TTS; keep chapter extraction aligned with the JSON exclusions.
- FFmpeg concat demuxing requires compatible input streams. Inspect or normalize before stitching, and normalize loudness after concatenation.
- Existing chapter files are resumable only after validating their audio. Do not skip a zero-byte, corrupt, or wrong-format file.


## Verification Checklist

- [ ] Exactly one source Markdown file and valid matching exclusions JSON.
- [ ] Only chapter narrative was included; excluded sections/comments and formatting artifacts were filtered.
- [ ] Every submitted chunk is within both the 5,000-character ceiling and provider-specific limit.
- [ ] Requested TTS engine and voice ID were used for every new chunk.
- [ ] Chunk order is correct; each final chapter MP3 is decodable with positive duration.
- [ ] Every completed chapter has a verified preview clip, and both full audio path and playable media were delivered.
- [ ] The user was asked to continue, recreate the current chapter, or auto-continue before another chapter began (unless auto-continue was selected).
- [ ] Existing valid chapter files were skipped; invalid ones were preserved before replacement.
- [ ] Temporary audio was removed only after successful chapter verification; failures remain resumable.
- [ ] Progress, generated/skipped paths, per-chapter durations, total duration, and any failures are reported accurately.
