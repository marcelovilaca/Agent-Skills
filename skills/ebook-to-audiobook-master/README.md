# Ebook to Audiobook Master

Create resumable, chapter-by-chapter Brazilian Portuguese (`pt-BR`) audiobooks from a prepared Markdown source and its matching exclusion metadata. Read [SKILL.md](SKILL.md) for the authoritative runbook and safety rules.

## How to Use

Use this skill when you want chapter or section MP3s from a prepared Markdown book and need exclusions, resumable generation, and verified delivery. It does not prepare raw PDF or TXT files, transcribe audio, or dub video.

Quick start:

1. Prepare a book directory containing exactly one `.md` file under `Source/` and its matching `Source/metadata_and_exclusions.json`. The metadata must identify the source language as `pt-BR`.
2. Run the local FFmpeg smoke test: `python <skill-directory>/scripts/test_audio_pipeline.py`. It uses synthetic audio only; `--force` reruns a cached test.
3. Follow [SKILL.md](SKILL.md) to preflight the whole book, map exclusions, generate tracks serially, verify each MP3 and preview, and run the final audit.

Example request: “Create the pt-BR audiobook for `<book_directory>` from its prepared Markdown and matching exclusion JSON. Use the default OpenRouter voice, verify each track and preview, and ask me before advancing.”

Expected source layout:

```text
<book_directory>/
└── Source/
    ├── <book-title>.md
    └── metadata_and_exclusions.json
```

## Technical Details

### Prerequisites and tools

- Python 3, FFmpeg, and ffprobe available on `PATH`.
- For the default TTS route, a configured OpenRouter credential and access to `https://openrouter.ai/api/v1/audio/speech`.
- The default model is exactly `heygen/heygen-voice-1-turbo:free`, voice `gareth`, requesting PCM and converting it to MP3. The workflow must stop rather than silently switch providers, models, or voices.
- The runbook uses Hermes terminal/process/clarify and `MEDIA:` delivery capabilities. On another host, adapt those tool calls to its local process, user-confirmation, and attachment mechanisms without relaxing the limits or verification rules.

### Workflow, files, and outputs

- `scripts/test_audio_pipeline.py` checks the local synthetic-PCM FFmpeg pipeline and caches a pass for the current tool/configuration fingerprint; it makes no provider call and uses no book text.
- `scripts/verify_audiobook_outputs.py <book_directory>` checks source coverage, progress/manifests, exclusions, chunk limits, MP3s, previews, and duration.
- Final files are written under `<book_directory>/Audio/`; resumable chunk manifests are kept under `<book_directory>/temp_audio_chunks/`.
- Requests are limited to 5,000 Unicode code points and 5,000 UTF-8 bytes, or a lower provider limit. Final masters and 30-second previews are 44.1 kHz mono MP3s.

### Verification, safety, and limitations

- Run the synthetic pipeline test once per FFmpeg/configuration fingerprint and again after relevant changes. After all tracks finish, run `python <skill-directory>/scripts/verify_audiobook_outputs.py <book_directory>` and require `all_verified: true` with zero errors.
- Never store or print credentials. Book text is sent to the selected TTS endpoint; do not use another service without the user's approval.
- The workflow supports `pt-BR` only, requires prepared Markdown plus matching JSON, and does not infer ambiguous exclusions. The provider may not independently confirm the Brazilian regional variant; disclose that limitation when applicable.
- A timed-out per-track choice authorizes only one next track. Book-wide auto-continue requires the user's explicit selection.
