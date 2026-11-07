# OpenRouter Video Dubber

A Windows-only, checkpointed workflow for transcription, translation, voice review/cloning, and dubbed MP3 assembly. Use it only when the user explicitly selects this cloud workflow. See [SKILL.md](SKILL.md) for the complete approval gates and exact model allowlist.

## How to Use

Use for an explicit OpenRouter/ElevenLabs dubbing request, not as the default for generic dubbing. Use only media the user owns and has already consented to use. Provide exactly one YouTube URL or local media file; choose the translation model from the exact free-model list in [SKILL.md](SKILL.md).

Quick start:

1. Check the runner options with `python <skill-directory>/scripts/video_dub_runner.py --help` and run the offline regression suite with `python <skill-directory>/scripts/test_video_dub_runner.py`.
2. Create a secret-free job manifest, then resume it with `run`:

```text
python <skill-directory>/scripts/video_dub_runner.py init --file "<media-file>" --model "google/gemma-4-26b-a4b-it:free" --out "<job-json>" --output-root "<output-root>"
python <skill-directory>/scripts/video_dub_runner.py run "<job-json>"
```

For a YouTube source, replace `--file "<media-file>"` with `--url "<youtube-url>"`. Example request: “Dub my pre-consented video into Brazilian Portuguese using the selected free model; stop at every approval gate and wait for my decision.” After each gate, obtain approval in chat, set only the corresponding manifest approval field, and rerun the job.

## Technical Details

### Prerequisites and files

- Requires Windows, Python 3, FFmpeg and ffprobe; `yt-dlp` is also required for YouTube URLs. The offline test suite uses only local synthetic/test data.
- Live work requires `OPENROUTER_API_KEY` and `ELEVENLABS_API_KEY` in the process environment. Never print or place them in the job manifest.
- `scripts/video_dub_runner.py` provides `init`, `run`, and `status` commands. `scripts/test_video_dub_runner.py` contains offline regression tests. The runner checkpoints progress in the job JSON and project artifacts under `<output-root>/<safe-title>/`; the output root is configurable and defaults to the user's `~/Translations` directory.
- The workflow checks that an OpenRouter transcription endpoint advertises diarization before downloading or uploading media. It stops if no supported endpoint is available.

### Workflow and verification

- The runner processes audio in fixed five-minute transcription chunks, stores transcript/turn checkpoints, translates complete turns in batches, and supports resume. It verifies the final MP3 with FFmpeg and checks its duration against the source.
- Paid transcription requires approval. Transcript and speaker review clips must be approved before translation/voice cloning; speaker names are required before cloning. Voice creation and bulk synthesis each have separate approval gates. Never set an approval field until the user has approved that exact action.
- The default workflow uses OpenRouter for transcription/translation and ElevenLabs for voice cloning/TTS. It does not silently switch to a paid translation model or another provider. It may try the remaining approved free translation models as documented in [SKILL.md](SKILL.md).
- The host must present approval gates to the user and support local file attachments for review clips. On another host, use equivalent confirmation and attachment tools; do not bypass approval gates.
- Limitations: this skill targets Windows; YouTube acquisition depends on `yt-dlp`; transcription stops if diarization is not advertised; the final result contains dubbed dialogue rather than source speech or music. The user must approve any cleanup or overwrite.
