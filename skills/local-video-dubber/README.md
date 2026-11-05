# Local Video Dubber

## Overview

This guide describes a Windows-based local pipeline that transcribes and diarizes a YouTube video, translates the spoken content, synthesizes dubbed speech, and writes synchronized MP3s. The operating procedure and its safety checks are defined in [SKILL.md](SKILL.md).

Use it only for media the user has rights to process and voices they are authorized to clone. This skill is for performing a dub, not for a general explanation of dubbing or the underlying script.

## How to Use

### Inputs and defaults

- Provide an unambiguous YouTube URL. Ask for it if missing or unclear.
- Target languages may be specified by the user. If none are given, the pipeline targets every supported language except the detected source language: English, Portuguese, Russian, Chinese, Italian, German, Spanish, and French.
- The script is expected at `local_dubber.py` in the configured project root and should be run with that project's `.venv` Python.

### Quick start

First confirm the script and its accepted options in the installed project. The command below shows the default all-target-languages flow; replace the placeholders with the local project and URL, not with credentials:

```text
"<PROJECT_ROOT>/.venv/Scripts/python.exe" "<PROJECT_ROOT>/local_dubber.py" --help
"<PROJECT_ROOT>/.venv/Scripts/python.exe" "<PROJECT_ROOT>/local_dubber.py" "<YOUTUBE_URL>" --all-target-languages
```

For explicitly selected target languages, use only the option syntax shown by that script's `--help`; this guide does not specify a language-selection flag.

### Run workflow

1. Confirm that the input URL and target-language choice are clear.
2. Check that `local_dubber.py` exists and that the virtual-environment Python can display its help.
3. Check the configured LM Studio models endpoint at `http://127.0.0.1:1234/api/v1/models` with a short timeout. If it returns HTTP 401, ensure `LM_API_TOKEN` is configured in the local process environment. Do not disclose the token.
4. Run the pipeline through `terminal`, quote the URL, and allow a long timeout for video processing and model downloads. Use `--all-target-languages` only when the user did not specify targets. Supply `--lmstudio-url` only if the endpoint differs from the documented default.
5. Wait for the command to finish. A translation phase completes before speech synthesis; do not skip the VRAM safety check.
6. Verify every expected language output before reporting completion.

## Prerequisites

- Windows and an installed project checkout containing `local_dubber.py` and its `.venv` Python.
- FFmpeg and CUDA-enabled PyTorch, WhisperX, and Qwen3-TTS installed.
- A Hugging Face read token available securely as `HF_TOKEN`, plus accepted access terms for `pyannote/speaker-diarization-community-1`.
- An LM Studio server reachable at `http://127.0.0.1:1234/api/v1`. The documented server requires its local API token in `LM_API_TOKEN` because unauthenticated model requests return HTTP 401.

Do not assume dependencies or model access are available: verify them in the target installation before running. Never ask the user to paste tokens into chat or include secrets in commands or documentation.

## Technical Details

### Files, tools, and outputs

- **Runner:** `local_dubber.py` in the project root; the script is not included in this skill directory.
- **Python:** the project's `.venv` interpreter.
- **Processing tools/models:** FFmpeg, CUDA-enabled PyTorch, WhisperX, Qwen3-TTS, the Hugging Face diarization model, and the configured local LM Studio server.
- **Output:** one synchronized MP3 per target language, under `<TRANSLATIONS_ROOT>/<video title>/<video title>_(<language>).mp3`.

`<PROJECT_ROOT>` and `<TRANSLATIONS_ROOT>` are configuration placeholders, not fixed paths. The skill does not define the actual root values or a full set of command-line flags; inspect the installed script's help for details.

### Verification

- Require a zero process exit code.
- For each selected target, confirm the exact expected MP3 path exists and has nonzero size.
- Report partial output and the failing phase honestly if transcription, translation, synthesis, or a prerequisite fails. A completed command alone is not proof that all language files were produced.

### Safety and limitations

- Respect copyright, platform terms, and consent for voice cloning. Do not dub media or clone voices without authorization.
- Keep `HF_TOKEN` and `LM_API_TOKEN` in a secure local environment. If `HF_TOKEN` is missing or model terms are unaccepted, stop and explain the blocker.
- The script refuses to overwrite existing dubbed MP3s. Obtain approval before a rerun using `--overwrite`.
- Before loading Qwen3-TTS, the pipeline waits for at least 7.5 GiB of free GPU VRAM. If llama.cpp does not release memory within its timeout, stop; do not bypass the check.
- The skill does not promise that every run can complete: GPU memory, local model availability, network access for downloads, and the installed toolchain can block processing. Do not claim success for unverified or zero-byte files.
