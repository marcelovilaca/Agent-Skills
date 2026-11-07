# Resumption, mastering, and verification

Use this reference for progress state, chunk recovery, FFmpeg mastering, preview delivery, and final audit.

## Resumable manifests

- Keep a book-level `Audio/audiobook_progress.json` with `auto_continue`, exact model/voice/input language, total track count, and an ordered `track_catalog`. Each catalog record carries stable `track_id`, playback `track_sequence`, exact title, source chapter number only when truly numbered, source range when available, and filtered character/byte and chunk counts.
- Keep `temp_audio_chunks/Chapter_<NN>/manifest.json` per track. Record source/filter hashes, title and source number, requested engine/voice/format, exclusion counts/ranges, exceptional splits, ordered chunk hashes/counts/statuses, and expected final/preview paths. Never store credentials.
- On resume, preserve a chunk status only when source hash, filtered hash, chunk sequence, chunk-text hash, model, and voice all match. Match by both sequence and hash; repeated identical text at different positions must not inherit the wrong record. Never reset matching completed work to pending.
- Reuse a chunk MP3 only after ffprobe and full-decode checks. If MP3 is corrupt/partial, move it to a timestamped backup before converting again. If matching PCM exists after an interrupted conversion, convert that PCM instead of repeating the provider call. Keep failed chunks/manifests for resumption.

## Track naming and mastering

Name playback files `<Book Name>-<Track Sequence padded to 2 digits>-<Sanitized Source Title>.mp3`; sanitize Windows-invalid characters and trailing spaces/dots, and record substitutions. Preserve source chapter number separately from playback sequence. Before writing, validate any existing exact target: skip a valid output; back up an invalid one; never silently overwrite a valid file.

Inspect chunk codec, sample rate, and channels. Use FFmpeg's concat demuxer only when streams are compatible, with an escaped `filelist.txt`; otherwise normalize inputs or use a filter concat. Master the entire track (not each chunk independently) to 44.1 kHz mono MP3 with `loudnorm=I=-16:TP=-1.5:LRA=11`, `libmp3lame`, and quality 2. Set output `-ar 44100 -ac 1`. Verify the master is non-empty, has positive ffprobe duration, and fully decodes. Create a 30-second preview in 44.1 kHz mono (or the whole track if shorter), then verify its duration and full decode.

After both files pass, update chapter and book-level progress with exact paths and duration; count previously verified tracks in the running total. Only then delete temporary chunk audio/text and the file list; retain the chunk manifest for the final verifier. Do not clean failed/interrupted chunks.

## Choice gate and final audit

`auto_continue` remains false until the user explicitly chooses option 3. A `timed_out` per-track `clarify` authorizes exactly one next track, then ask again; it does not set `auto_continue`. Do not promise a fixed five-minute delay because the interface controls the timeout. If the user skips/cancels or the prompt is unavailable/undelivered, pause. When option 3 is selected, still process one track at a time and deliver each verified track before beginning the next.

After the final track, run:

```text
python <skill-directory>/scripts/verify_audiobook_outputs.py <book_directory>
```

Require a successful exit, `all_verified: true`, and zero errors. Review every warning; resolve it or confirm and disclose why it is non-blocking. The verifier checks source track coverage, progress/catalog and chunk manifests, model/voice/PCM settings, exclusion counts, chunk ceilings, exact output-path agreement, MP3/preview decodability, and total duration. Report generated and skipped tracks separately, per-track durations, total duration, any exclusions/splits, and unresolved language/quality caveats. Never call the book complete while any track is pending, failed, or unverified.
