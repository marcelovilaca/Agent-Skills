---
name: "local-video-dubber"
description: "Run the local YouTube video dubbing pipeline."
license: "MIT"
compatibility: "Requires Windows."
metadata:
  author: "marcelovilaca, Hermes Agent"
  hermes_tags: "video, dubbing, YouTube, WhisperX, Qwen3-TTS, local"
  version: "0.1.3"
---

# Local Video Dubber

Run the local Python pipeline to transcribe and diarize a YouTube video, translate its speech, synthesize dubbed speech, and produce synchronized MP3s. 

## When to Use

- Use when the user invokes this skill or gives a YouTube URL to dub.
- Do not run when the user only asks about the script, dependencies, or how dubbing works.

## Prerequisites

- Windows project installed at `<PROJECT_ROOT>`; use its `.venv` Python.
- FFmpeg and CUDA-enabled PyTorch/WhisperX/Qwen3-TTS installed.
- A Hugging Face read token in `HF_TOKEN` and accepted terms for `pyannote/speaker-diarization-community-1`.
- LM Studio server reachable at `http://127.0.0.1:1234/api/v1` with its local API token stored in `LM_API_TOKEN` if authentication is enabled. The current server returns HTTP 401 without auth, so a token is required here.

## How to Run

1. Extract the YouTube URL from the user's message. If absent or ambiguous, ask for the link.
2. Carry forward target languages already specified for this same video task, even if a later skill invocation only repeats the URL. Only when no target has been specified in the active task, dub to every supported target other than the detected source language (English, Portuguese, Russian, Chinese, Italian, German, Spanish, French).
3. Before inference, verify that `<PROJECT_ROOT>\local_dubber.py` exists and the venv Python can show `--help` using `terminal`.
4. Check `http://127.0.0.1:1234/api/v1/models` with a short timeout. If it returns 401, confirm `LM_API_TOKEN` is available to the process; never request or output the token in chat. Then smoke-test `/api/v1/chat` with one short translation using the selected local text model; a successful `/models` response proves connectivity, not inference. Prefer an explicitly tested `--lmstudio-model` over `auto` if translation is slow or times out.
5. Run through `terminal` with the URL quoted, `--all-target-languages` when targets were not specified, and `--lmstudio-url` only if the configured endpoint differs. Use a long timeout appropriate for video duration and model downloads.
6. Report the resulting MP3 paths only after verifying each returned path exists and has nonzero size. Outputs must be `<TRANSLATIONS_ROOT>\<video title>\<video title>_(<language>).mp3`.

## Safety and Failure Handling

- Never print, request, or embed Hugging Face/API secrets in chat or commands. The script reads `HF_TOKEN` from the environment; if it is missing, explain that the user must provide it through their secure local environment and accept the model terms.
- The script refuses to overwrite existing dubbed MP3s. Ask before rerunning with `--overwrite`.
- Translation completes before speech synthesis. Use `torch.bfloat16` for Qwen3-TTS when `torch.cuda.is_bf16_supported()` is true, otherwise `torch.float32`; FP16 can trigger a code-predictor CUDA device-side assertion even with ample VRAM. Smoke-test one real voice-clone generation before a long synthesis after changing precision. The script waits for at least 7.5 GiB of free GPU VRAM before loading Qwen3-TTS; if the required headroom does not become available within its timeout, stop rather than bypassing this safety check.
- If LM Studio `/chat` times out after `/models` succeeds, test an explicit local text model before retrying; `auto` may select a slow model, and the CLI can repeat earlier pipeline phases. Inspect cached transcript/translation artifacts and final output paths before retrying.
- Do not claim completion unless the command succeeds and every expected MP3 is verified on disk.

## Verification

- Confirm the process exit code is zero.
- For every target language, confirm the exact expected MP3 path exists and its size is greater than zero.
- If any phase fails, report the phase and exact actionable blocker; do not report partial outputs as complete.
