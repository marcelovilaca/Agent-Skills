---
name: "ebook-to-audiobook-master"
description: "Create chaptered pt-BR audiobooks from Markdown."
license: "MIT"
metadata:
  author: "marcelovilaca, Hermes Agent"
  hermes_related_skills: "pdf-to-epub-master"
  hermes_tags: "audiobook, TTS, Portuguese, FFmpeg, Markdown, audio"
  version: "0.2.0"
---

# Ebook to Audiobook Master

Create a resumable, chapter-by-chapter Brazilian Portuguese (pt-BR) audiobook from one prepared Markdown source and its matching exclusion metadata. The default engine is OpenRouter HeyGen free TTS; never claim completion for missing or unverified audio.

## When to Use

- The user wants chapter/section MP3s from a cleaned Markdown book.
- The audiobook must honor `metadata_and_exclusions.json` and `EXCLUDE_FROM_AUDIO` markers.
- Do not use for transcribing existing audio or dubbing video.
- This skill does not prepare raw PDF/TXT sources; require the prepared Markdown and matching exclusion JSON. Use the related preparation skill separately if needed.

## Always-on rules

- Use exactly one `.md` in `Source/` and its matching `metadata_and_exclusions.json`; stop if missing, invalid, or ambiguous. Final files go under the book directory's `Audio/`.
- Default TTS: OpenRouter endpoint `https://openrouter.ai/api/v1/audio/speech`, model `heygen/heygen-voice-1-turbo:free`, voice `gareth`, `response_format: "pcm"`, converted to MP3. Never change the provider, model, voice, or format automatically; never remove `:free`. If the user explicitly chooses another engine/voice, honor that choice using its documented format and limits; ask before sending text to an endpoint they did not clearly select. If the chosen route is unavailable, preserve state and stop rather than falling back.
- Hard ceiling: 5,000 Unicode code points and 5,000 UTF-8 bytes per request, or a lower provider limit. Enforce both counts and recount each final payload immediately before submission.
- This skill supports pt-BR only: require source metadata/input language `pt-BR` and stop if the prepared source is in another language. Do not add an undocumented `language` field. Reject an explicitly non-Portuguese `Content-Language`; disclose if the provider did not independently confirm the regional variant.
- Speak each track title once at the start. If adding a spoken-title prefix, remove the duplicate source heading from the body.
- Never print/store credentials. Resolve the configured key from the environment or active Hermes credential source; do not ask for a duplicate key if Hermes already has one.
- Do not install tools or send book text to any service other than the selected endpoint without user approval.
- Do not start a later track before the user's choice. A `timed_out` per-track prompt authorizes exactly one next track; only explicit option 3 enables auto-continue for all remaining. Even in auto-continue, generate and deliver one verified track at a time.

## Runbook

1. **Discover and preflight.** Verify the source, JSON, language, FFmpeg/ffprobe, and configured credential safely. Run `python <skill-directory>/scripts/test_audio_pipeline.py` once for the current FFmpeg/config fingerprint and after tool or pipeline changes; it uses synthetic audio only. Inspect the book's heading hierarchy and all included sections. Do not send book text until the book-wide read-only preflight passes for every included track. Follow [source filtering and chunking](references/source-filtering-and-chunking.md).
2. **Plan and filter.** Establish ordered boundaries from actual headings. Keep clearly work-authored proemio/prologue/introduction/coda as separate tracks unless metadata excludes; omit non-narrative front/back matter only when metadata or clear structure identifies it. Validate every marker against exact JSON section/range records. Remove unmarked text only when confidently non-narrative, recording its exact range, text, and reason in audio-only metadata; preserve uncertain text and stop if a boundary or exclusion is ambiguous. Leave the prepared source unchanged; apply only conservative audio-only cleanup of nonspoken formatting/page artifacts, preserving narrative prose and meaningful numbering. Follow [source filtering and chunking](references/source-filtering-and-chunking.md).
3. **Chunk.** Split at safe sentence/paragraph boundaries; test initials, abbreviations, decimals, Roman numerals, ellipses, and quoted punctuation. Pack to both 5,000-code-point and 5,000-byte ceilings or the lower provider limit. Split oversized sentences at a comma/semicolon, then a safe word boundary; record each exception, hash, count, and limit. Recount every payload immediately before sending.
4. **Prepare resumable state.** Record an ordered `track_catalog` with stable track ID/sequence, source number only when present, title, source range, filtered counts, and chunk estimates. Save hashes, engine settings, and status in book/per-track manifests. Resume only when source/filter hashes, chunk position/text hash, and engine settings match; reuse only validated audio and never reset matching completed work. Preserve PCM after interrupted conversion and back up invalid outputs. Keep manifests after cleanup. See [resumption and mastering](references/resume-and-mastering.md).
5. **Generate serially.** Send one exact PCM request per chunk, in order. For long tracks, use one PTY-backed background process with completion notification. Stop on HTTP 400/401/402/403/404/413; retry 429 and transient 502/503/524/529 only with bounded backoff. On failure, preserve valid PCM/chunks/manifests and stop that track; never mark partial audio complete or fall back to another model. Follow [OpenRouter TTS](references/openrouter-tts.md).
6. **Master and verify each track.** Concatenate only compatible chunks in order; master the whole track to 44.1 kHz mono MP3 with `libmp3lame` quality 2 and `loudnorm=I=-16:TP=-1.5:LRA=11`. Require positive `ffprobe` duration and full decode. Create and fully verify a 30-second 44.1 kHz mono start preview (or the whole track if shorter). Update progress; delete temporary chunk audio only after both files pass, and retain manifests. See [resumption and mastering](references/resume-and-mastering.md).
7. **Deliver before advancing.** Give the exact full MP3 and preview paths and attach both as playable media using `MEDIA:`. State track number/title, duration, verification, cumulative verified duration, exclusions, chunk exceptions, and language caveat.
8. **Final audit.** After all tracks complete, run `scripts/verify_audiobook_outputs.py <book_directory>`. Require successful exit, `all_verified: true`, and zero errors. Review every warning; resolve it or confirm and disclose that it is non-blocking before claiming completion.

## Chapter-by-chapter delivery and user-choice gate

After each verified MP3 and preview, ask the user to choose:

1. `Continue to the next chapter (ask me again afterward)` — authorize only the next track, then ask again after its delivery.
2. `Re-create this chapter` — preserve the valid current output under a timestamped backup, rebuild only that track with the same settings, verify and deliver again, then ask again.
3. `Continue through all remaining chapters without asking again` — set `auto_continue: true` in the existing book progress manifest without dropping prior records. Continue serially; still deliver each verified track before starting the next, but do not ask again.

Use `clarify` when available. If the outcome is `timed_out`, treat silence as authorization for exactly one next track, deliver it, and ask again; this does not set `auto_continue`. The interface controls the actual timeout duration, so do not promise it is exactly five minutes. At the final-track prompt, `timed_out` means finish and report without recreating. If the user skips/cancels or `clarify` is unavailable or undelivered, pause without advancing. If the user chose option 3, continue serially through all remaining tracks without another prompt, while still delivering each verified track before starting the next.

## Output layout

```text
<book_directory>/
├── Source/<Title>.md
├── Source/metadata_and_exclusions.json
├── temp_audio_chunks/Chapter_<NN>/manifest.json  # retain for final verification
└── Audio/
    ├── audiobook_progress.json
    ├── <Book Name>-<Track Sequence padded to 2 digits>-<Sanitized Source Title>.mp3
    └── Previews/<Book Name>-<Track Sequence padded to 2 digits>-<Sanitized Source Title>-preview.mp3
```

## Completion checklist

- [ ] One prepared Markdown source and valid matching exclusion JSON; all included tracks passed book-wide preflight.
- [ ] Every track title appears once; excluded sections/markers and audio-only notes are mapped and filtered safely.
- [ ] Every request is within limits and uses the selected exact model/voice/format.
- [ ] Each completed track and preview is non-empty, positive-duration, and fully decodable.
- [ ] Progress preserves generated/skipped state, per-track paths/durations, and cumulative total.
- [ ] The user-choice gate was honored; no later track was started prematurely.
- [ ] Final verifier reports all tracks verified before claiming completion.
