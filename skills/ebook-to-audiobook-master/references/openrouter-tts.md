# OpenRouter TTS route

Use this reference for the default HeyGen route. Never silently substitute a model, voice, endpoint, or provider.

## Credential and request safety

- Resolve `OPENROUTER_API_KEY` from the process environment or the active Hermes home's `.env`; if the shell does not inherit it, read the configured credential source safely. If Hermes has the credential in its auth pool, use Hermes's configured resolution rather than asking for a duplicate. Stop only when no configured credential is accessible.
- Never print, log, store in manifests, or return the key. Redact it from errors. Send text only to `https://openrouter.ai/api/v1/audio/speech` unless the user explicitly approves another service. Do not install tools without approval.
- Default request is one sequential `POST` per non-empty chunk with only these fields: `model: "heygen/heygen-voice-1-turbo:free"`, `input`, `voice: "gareth"`, `response_format: "pcm"`. Set `Authorization: Bearer ...` and `Content-Type: application/json`. Do not add an undocumented `language` field.
- For Portuguese, require source/input language `pt-BR`. Record `Content-Language` when returned, reject an explicitly non-Portuguese value, and disclose when regional Brazilian output was not independently confirmed.

## PCM and errors

- The exact free model supports PCM only; do not remove `:free` or fall back to the paid model. A successful body is raw audio bytes, not JSON. Save it as `.pcm`; record `X-Generation-Id`, `Content-Type`, and `Content-Language` when present. Parse JSON only on non-2xx responses.
- The documented output is 44.1 kHz, mono, 16-bit little-endian PCM. Convert with FFmpeg input options `-f s16le -ar 44100 -ac 1`, then encode a real MP3 chunk with `libmp3lame` quality 2. Verify each chunk is non-empty and fully decodable before marking it complete.
- Treat HTTP 400/401/402/403/404/413 as blockers. Retry 429 and transient 502/503/524/529 only with bounded backoff. If the free model is rejected/unavailable, preserve resumable state and stop; do not try a paid ID or another engine.
- If content type or PCM format is incompatible/unknown, stop and preserve the response and manifest for diagnosis; never relabel arbitrary bytes as PCM/MP3.

## Safe execution

Run `python <skill-directory>/scripts/test_audio_pipeline.py` once for the current FFmpeg/config fingerprint and after tool/settings changes. It creates two short synthetic PCM chunks, transcodes them, tests compatible concat, masters the full track at 44.1 kHz mono with loudnorm, creates a preview, and fully decodes the outputs. It makes no provider call and sends no book text. A successful pass is cached in the active Hermes home; use `--force` to rerun. For an explicitly selected engine with a different documented format, adapt the local test to that format before sending source text.

For tracks expected to take several minutes, start one chapter process using a PTY-backed background terminal with completion notification. Treat its session ID as the process handle, not the launcher's immediate exit code. Use the process manager to check and wait. If a wait window expires while the job is running, inspect manifests/source independently and rely on the completion notification; do not busy-poll or start another chapter.
