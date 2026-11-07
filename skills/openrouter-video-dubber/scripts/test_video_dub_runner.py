"""Offline regression tests for video_dub_runner.py (stdlib unittest only)."""
from __future__ import annotations

import io
import json
import os
import shutil
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

import video_dub_runner as runner

TEST_SCRATCH = Path.home() / "AppData" / "Local" / "hermes" / "cache" / "scratch"
TEST_SCRATCH.mkdir(parents=True, exist_ok=True)
tempfile.tempdir = str(TEST_SCRATCH)


class ManifestTests(unittest.TestCase):
    def test_init_creates_noninteractive_secret_free_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "job.json"
            with mock.patch("sys.stdout", new_callable=io.StringIO), mock.patch("sys.stderr", new_callable=io.StringIO):
                result = runner.main(["init", "--file", "source.mp4", "--model", runner.FREE_TRANSLATION_MODELS[0], "--output-root", tmp, "--out", str(path)])
            self.assertEqual(result, 0)
            job = runner.load_job(path)
            self.assertEqual(job["source"]["path"], "source.mp4")
            self.assertEqual(job["target_language"], "Portuguese")
            self.assertFalse(any(job["approvals"].values()))

    def test_init_refuses_to_overwrite_an_existing_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "job.json"
            path.write_text("sentinel", encoding="utf-8")
            with mock.patch("sys.stdout", new_callable=io.StringIO), mock.patch("sys.stderr", new_callable=io.StringIO):
                result = runner.main(["init", "--file", "source.mp4", "--model", runner.FREE_TRANSLATION_MODELS[0], "--out", str(path)])
            self.assertEqual(result, 2)
            self.assertEqual(path.read_text(encoding="utf-8"), "sentinel")

    def test_new_job_uses_exact_allowlist_and_portuguese_default(self):
        job = runner.new_job(
            url="https://www.youtube.com/watch?v=example",
            local_path=None,
            translation_model=runner.FREE_TRANSLATION_MODELS[0],
        )
        self.assertEqual(job["target_language"], "Portuguese")
        self.assertEqual(job["target_language_code"], "pt")
        self.assertEqual(job["settings"]["chunk_seconds"], 300)
        self.assertFalse(any(job["approvals"].values()))
        self.assertEqual(job["translation_model"], "google/gemma-4-26b-a4b-it:free")
        self.assertEqual(job["output_root"], str(Path.home() / "Translations"))

    def test_rejects_both_or_missing_sources(self):
        with self.assertRaisesRegex(runner.RunnerError, "exactly one source"):
            runner.new_job(url="https://example.com/a", local_path="a.mp4", translation_model=runner.FREE_TRANSLATION_MODELS[0])
        with self.assertRaisesRegex(runner.RunnerError, "exactly one source"):
            runner.new_job(url=None, local_path=None, translation_model=runner.FREE_TRANSLATION_MODELS[0])

    def test_rejects_non_allowlisted_translation_model(self):
        with self.assertRaisesRegex(runner.RunnerError, "allowlist"):
            runner.new_job(url=None, local_path="a.mp4", translation_model="paid/model")

    def test_manifest_rejects_credential_fields_and_secret_values(self):
        job = runner.new_job(url=None, local_path="a.mp4", translation_model=runner.FREE_TRANSLATION_MODELS[0])
        job["api_key"] = "not-displayed"
        with self.assertRaisesRegex(runner.RunnerError, "must not contain API keys"):
            runner.validate_job(job)
        job.pop("api_key")
        job["settings"]["comment"] = "sk-or-v1-1234567890abcdef"
        with self.assertRaisesRegex(runner.RunnerError, "must not contain API keys"):
            runner.validate_job(job)

    def test_manifest_serialization_never_stores_environment_secrets(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {
            "OPENROUTER_API_KEY": "sk-or-v1-test-secret-value",
            "ELEVENLABS_API_KEY": "xi-test-secret-value",
        }):
            job = runner.new_job(url=None, local_path="a.mp4", translation_model=runner.FREE_TRANSLATION_MODELS[0])
            path = Path(tmp) / "job.json"
            runner.save_job(path, job)
            contents = path.read_text(encoding="utf-8")
            self.assertNotIn("sk-or-v1-test-secret-value", contents)
            self.assertNotIn("xi-test-secret-value", contents)
            self.assertNotIn("api_key", contents.lower())

    def test_non_portuguese_language_requires_valid_code(self):
        with self.assertRaisesRegex(runner.RunnerError, "target_language_code"):
            runner.new_job(url=None, local_path="a.mp4", translation_model=runner.FREE_TRANSLATION_MODELS[0], target_language="Klingon")
        job = runner.new_job(url=None, local_path="a.mp4", translation_model=runner.FREE_TRANSLATION_MODELS[0], target_language="Spanish", language_code="es")
        self.assertEqual(job["target_language_code"], "es")


class MetadataTests(unittest.TestCase):
    def test_diarization_capability_requires_explicit_available_true(self):
        metadata = {"data": {"endpoints": [
            {"provider_name": "DeepInfra", "supports_diarization": False},
            {"provider_name": "Groq", "supports_diarization": False},
            {"provider_name": "Future", "supports_diarization": True},
            {"provider_name": "Offline", "supports_diarization": True, "status": "offline"},
        ]}}
        self.assertEqual([e["provider_name"] for e in runner.available_diarization_endpoints(metadata)], ["Future"])
        with self.assertRaisesRegex(runner.RunnerError, "Stopped before media download/upload"):
            runner.require_diarization({"data": {"endpoints": [
                {"provider_name": "DeepInfra", "supports_diarization": False},
                {"provider_name": "Groq", "supports_diarization": False},
            ]}})

    def test_price_estimate_only_uses_explicit_audio_rate(self):
        self.assertAlmostEqual(runner.estimate_price_per_minute({"pricing": {"cost_per_second": 0.0002}}), 0.012)
        self.assertEqual(runner.estimate_price_per_minute({"pricing": {"prompt": "0.0001", "completion": "0.0002"}}), None)
        self.assertEqual(runner.endpoint_summary({"data": {"endpoints": []}})["price_per_minute_usd"], None)

    def test_audio_transcription_prompt_rates_report_per_minute_range(self):
        metadata = {"data": {
            "architecture": {"modality": "audio->transcription"},
            "endpoints": [
                {"provider_name": "DeepInfra", "status": 0, "pricing": {"prompt": "0.00000333", "completion": "0"}},
                {"provider_name": "Groq", "status": 0, "pricing": {"prompt": "0.0000111111111111", "completion": "0"}},
            ],
        }}
        summary = runner.endpoint_summary(metadata)
        self.assertAlmostEqual(summary["price_per_minute_usd_range"]["min"], 0.0001998, places=12)
        self.assertAlmostEqual(summary["price_per_minute_usd_range"]["max"], 0.000666666666666, places=12)
        cost = runner.transcription_cost_estimate(60, summary)
        self.assertAlmostEqual(cost["min"], 0.0001998, places=8)
        self.assertAlmostEqual(cost["max"], 0.00066667, places=8)

    def test_provider_metadata_summary_does_not_copy_unneeded_raw_payload(self):
        summary = runner.endpoint_summary({"data": {"endpoints": [{
            "provider_name": "Example", "supports_diarization": True, "private_detail": "keep out",
        }]}})
        self.assertTrue(summary["endpoints"][0]["supports_diarization"])
        self.assertNotIn("private_detail", json.dumps(summary))


class DeterministicHelperTests(unittest.TestCase):
    def test_safe_title_removes_windows_invalid_characters_and_reserved_names(self):
        self.assertEqual(runner.safe_title('  A/B:C?  '), "A_B_C_")
        self.assertEqual(runner.safe_title("CON"), "_CON")
        self.assertEqual(runner.safe_title("..."), "video")

    def test_safe_component_is_collision_resistant_for_speaker_paths(self):
        self.assertNotEqual(runner.safe_component("speaker/A"), runner.safe_component("speaker_A"))
        self.assertNotIn("/", runner.safe_component("speaker/A"))

    def test_parse_silence_times_and_chunk_boundaries_are_monotonic(self):
        stderr = "silence_start: 291.500\nsilence_end: 293.000 | silence_duration: 1.500\nsilence_start: 598.0"
        times = runner.parse_silence_times(stderr)
        self.assertEqual(times, [291.5, 293.0, 598.0])
        ranges = runner.chunk_ranges(660, times)
        self.assertEqual(len(ranges), 3)
        self.assertAlmostEqual(ranges[0][1], 293.0)
        self.assertAlmostEqual(ranges[1][0], ranges[0][1])
        self.assertAlmostEqual(ranges[-1][1], 660)
        for left, right in zip(ranges, ranges[1:]):
            self.assertAlmostEqual(left[1], right[0])

    def test_chunking_ignores_silence_far_from_nominal_five_minute_cut(self):
        ranges = runner.chunk_ranges(700, [100.0])
        self.assertEqual(ranges, [(0.0, 300.0), (300.0, 600.0), (600.0, 700.0)])

    def test_chunking_without_silence_falls_back_to_five_minute_boundaries(self):
        self.assertEqual(runner.chunk_ranges(640, []), [(0.0, 300.0), (300.0, 600.0), (600.0, 640.0)])

    def test_transcript_normalization_adds_global_timestamps_and_stable_ids(self):
        response = {"segments": [
            {"start": 1.25, "end": 2.5, "speaker_id": "speaker_0", "text": " Olá "},
            {"start": 5, "end": 7, "speaker": "speaker_1", "text": "Oi"},
        ]}
        transcript = runner.normalize_transcript([response], [{"index": 0, "start": 300, "end": 600}], 900)
        self.assertEqual(transcript["segments"][0]["id"], "segment_00000")
        self.assertEqual(transcript["segments"][0]["start"], 301.25)
        self.assertEqual(transcript["segments"][0]["end"], 302.5)
        self.assertEqual(transcript["segments"][1]["speaker"], "speaker_1")

    def test_normalize_transcript_uses_word_level_speaker_labels(self):
        response = {
            "segments": [{"start": 0, "end": 1.5, "text": "hello there"}],
            "words": [
                {"start": 0, "end": 0.6, "word": "hello", "speaker": "speaker_0", "speaker_label": "A"},
                {"start": 0.7, "end": 1.5, "word": "there", "speaker": "speaker_0", "speaker_label": "A"},
            ],
        }
        transcript = runner.normalize_transcript([response], [{"index": 0, "start": 0, "end": 2}], 2)
        self.assertEqual(transcript["segments"][0]["speaker"], "speaker_0")

    def test_transcript_clamps_local_segments_to_chunk_bounds(self):
        response = {"segments": [{"start": -2, "end": 400, "speaker_id": "speaker_0", "text": "edge"}]}
        transcript = runner.normalize_transcript([response], [{"index": 1, "start": 300, "end": 600}], 900)
        self.assertEqual(transcript["segments"][0]["start"], 300)
        self.assertEqual(transcript["segments"][0]["end"], 600)

    def test_same_speaker_segments_group_across_gap_up_to_one_second(self):
        segments = [
            {"id": "s1", "speaker": "A", "start": 0.0, "end": 1.0, "text": "Oi"},
            {"id": "s2", "speaker": "A", "start": 2.0, "end": 3.0, "text": " tudo bem?"},
            {"id": "s3", "speaker": "A", "start": 4.01, "end": 5.0, "text": "Depois"},
            {"id": "s4", "speaker": "B", "start": 5.1, "end": 6.0, "text": "Sim"},
        ]
        turns = runner.group_turns(segments)
        self.assertEqual(len(turns), 3)
        self.assertEqual(turns[0]["text"], "Oi tudo bem?")
        self.assertEqual(turns[0]["segment_ids"], ["s1", "s2"])
        self.assertEqual(turns[0]["id"], "turn_00000")

    def test_translation_validation_preserves_ids_speakers_and_nonempty_text(self):
        turns = [{"id": "turn_1", "speaker": "A"}, {"id": "turn_2", "speaker": "B"}]
        translated = runner.validate_translations({"translations": [
            {"id": "turn_1", "speaker": "A", "text": "Olá"},
            {"id": "turn_2", "speaker": "B", "text": "Sim"},
        ]}, turns)
        self.assertEqual(translated, {"turn_1": "Olá", "turn_2": "Sim"})
        for invalid in (
            {"translations": [{"id": "turn_1", "speaker": "A", "text": "Olá"}]},
            {"translations": [{"id": "turn_1", "speaker": "B", "text": "Olá"}, {"id": "turn_2", "speaker": "B", "text": "Sim"}]},
            {"translations": [{"id": "turn_1", "speaker": "A", "text": ""}, {"id": "turn_2", "speaker": "B", "text": "Sim"}]},
        ):
            with self.subTest(invalid=invalid), self.assertRaises(runner.RunnerError):
                runner.validate_translations(invalid, turns)

    def test_parse_json_accepts_fenced_object(self):
        self.assertEqual(runner.parse_json_text('```json\n{"translations":[]}\n```'), {"translations": []})

    def test_adaptive_batches_never_split_turns_and_obey_count_and_char_limits(self):
        turns = [{"id": str(i), "text": "x" * n} for i, n in enumerate((4, 4, 7, 2))]
        batches = runner.adaptive_batches(turns, max_turns=3, max_chars=8)
        self.assertEqual([[t["id"] for t in batch] for batch in batches], [["0", "1"], ["2"], ["3"]])
        self.assertEqual([t["id"] for batch in batches for t in batch], ["0", "1", "2", "3"])

    def test_split_text_only_splits_oversized_turns_and_respects_character_limit(self):
        self.assertEqual(runner.split_text("Short turn.", 30), ["Short turn."])
        text = "First sentence. Second sentence is longer. Third sentence."
        parts = runner.split_text(text, 20)
        self.assertGreater(len(parts), 1)
        self.assertTrue(all(0 < len(part) <= 20 for part in parts))
        self.assertEqual(" ".join(parts).replace(" .", "."), text)

    def test_preview_text_uses_the_selected_speakers_translated_turn(self):
        translated = [
            {"id": "turn_0", "speaker": "speaker_0", "text": "First speaker speaks."},
            {"id": "turn_1", "speaker": "speaker_1", "text": "Olá, que bom estar aqui. Próxima frase."},
        ]
        self.assertEqual(runner.preview_text_for_speaker(translated, "speaker_1"), "Olá, que bom estar aqui.")
        self.assertEqual(runner.preview_text_for_speaker(translated, "missing", fallback="fallback"), "fallback")

    def test_sample_plan_caps_at_two_minutes_and_detects_short_speaker(self):
        segments = [
            {"speaker": "A", "start": 0, "end": 80},
            {"speaker": "B", "start": 80, "end": 130},
            {"speaker": "A", "start": 130, "end": 220},
        ]
        plan, insufficient = runner.sample_plan(segments)
        self.assertAlmostEqual(sum(end - start for start, end in plan["A"]), 120)
        self.assertEqual(insufficient, {"B": 50})

    def test_atempo_chain_supports_heavy_stretch_with_valid_factors(self):
        chain = runner.atempo_chain(8.0)
        factors = [float(part.split("=")[1]) for part in chain.split(",")]
        self.assertAlmostEqual(__import__("math").prod(factors), 8.0, places=5)
        self.assertTrue(all(0.5 <= factor <= 2.0 for factor in factors))
        slow = runner.atempo_chain(0.125)
        slow_factors = [float(part.split("=")[1]) for part in slow.split(",")]
        self.assertAlmostEqual(__import__("math").prod(slow_factors), 0.125, places=5)

    def test_oversized_turns_split_and_time_intervals_remain_contiguous(self):
        job = runner.new_job(url=None, local_path="a.mp4", translation_model=runner.FREE_TRANSLATION_MODELS[0])
        job["settings"]["tts_max_chars"] = 12
        items = runner.build_tts_items([{"id": "turn_1", "speaker": "A", "start": 10, "end": 16, "text": "One two three four five."}], job)
        self.assertGreater(len(items), 1)
        self.assertTrue(all(len(item["text"]) <= 12 for item in items))
        self.assertEqual(items[0]["start"], 10)
        self.assertAlmostEqual(items[-1]["end"], 16)
        for left, right in zip(items, items[1:]):
            self.assertAlmostEqual(left["end"], right["start"])

    def test_redaction_scrubs_environment_values_from_saved_json(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "private-or-key-123"}):
            path = Path(tmp) / "artifact.json"
            runner.atomic_write_json(path, {"text": "payload private-or-key-123"})
            saved = path.read_text(encoding="utf-8")
            self.assertNotIn("private-or-key-123", saved)
            self.assertIn("[REDACTED]", saved)


class OfflinePipelineTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe are required")
    def test_real_ffmpeg_fit_assembly_and_decode_verification_offline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tools = {"ffmpeg": runner.require_tool("ffmpeg"), "ffprobe": runner.require_tool("ffprobe")}
            raw = root / "tone.mp3"
            fitted = root / "fitted.mp3"
            final = root / "final.mp3"
            runner.run_process([tools["ffmpeg"], "-hide_banner", "-nostdin", "-y", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100:duration=1.5", "-ac", "1", "-codec:a", "libmp3lame", "-q:a", "3", str(raw)], timeout=60, tool_label="ffmpeg synthetic test source")
            runner.fit_audio_to_duration(raw, fitted, 2.5, tools)
            items = [{"path": str(fitted), "start": 0.5, "end": 3.0, "duration": 2.5}]
            runner.assemble_dialogue(items, 4.0, final, tools, overwrite=False)
            verified = runner.verify_output(final, items, 4.0, tools)
            self.assertTrue(verified["verified"])
            self.assertGreater(verified["final_bytes"], 0)
            self.assertLessEqual(abs(verified["final_duration"] - 4.0), 1.5)

    def test_final_assembly_refuses_overwrite_without_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            final = Path(tmp) / "existing.mp3"
            final.write_bytes(b"preserve")
            with mock.patch.object(runner, "run_process") as process:
                with self.assertRaisesRegex(runner.RunnerError, "only after user approval"):
                    runner.assemble_dialogue([{"path": str(final), "start": 0, "duration": 1}], 1, final, {"ffmpeg": "ffmpeg"}, overwrite=False)
            process.assert_not_called()
            self.assertEqual(final.read_bytes(), b"preserve")

    def test_openrouter_key_preflight_returns_only_safe_limit_fields(self):
        payload = {"data": {"limit": 5.0, "limit_remaining": 3.25, "usage": 1.75, "label": "private-label", "hash": "secret-hash"}}
        with mock.patch.object(runner, "request_json", return_value=payload) as request:
            result = runner.openrouter_key_info("not-logged", 10)
        self.assertEqual(result, {"limit": 5.0, "limit_remaining": 3.25, "usage": 1.75})
        self.assertEqual(request.call_args.args[0], f"{runner.OPENROUTER_BASE}/key")
        self.assertNotIn("hash", json.dumps(result))

    def test_elevenlabs_preflight_checks_cloning_capability_and_returns_safe_fields(self):
        payload = {"tier": "creator", "character_count": 100, "character_limit": 1000,
                   "voice_slots_used": 2, "voice_limit": 10, "can_use_instant_voice_cloning": True,
                   "xi_api_key_preview": "do-not-save"}
        with mock.patch.object(runner, "request_json", return_value=payload) as request:
            result = runner.elevenlabs_subscription_info("not-logged", 10)
        self.assertEqual(result["tier"], "creator")
        self.assertEqual(result["character_count"], 100)
        self.assertTrue(result["can_use_instant_voice_cloning"])
        self.assertNotIn("xi_api_key_preview", json.dumps(result))
        self.assertEqual(request.call_args.args[0], f"{runner.ELEVENLABS_BASE}/user/subscription")

    def test_prepare_project_allows_job_manifest_as_the_only_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "Episode"
            job_path = project / "job.json"
            job = runner.new_job(url=None, local_path="source.mp4", translation_model=runner.FREE_TRANSLATION_MODELS[0], output_root=tmp)
            runner.save_job(job_path, job)
            result = runner.prepare_project(job, job_path, "Episode")
            self.assertEqual(result, project)
            self.assertEqual(job["state"]["project_dir"], str(project.resolve()))
            self.assertTrue(job_path.is_file())

    def test_diarization_gate_stops_before_any_source_download_or_upload(self):
        with tempfile.TemporaryDirectory() as tmp:
            job_path = Path(tmp) / "job.json"
            job = runner.new_job(url="https://youtube.com/watch?v=x", local_path=None, translation_model=runner.FREE_TRANSLATION_MODELS[0], output_root=tmp)
            runner.save_job(job_path, job)
            unsupported = {"data": {"endpoints": [
                {"provider_name": "DeepInfra", "supports_diarization": False},
                {"provider_name": "Groq", "supports_diarization": False},
            ]}}
            with mock.patch.object(runner, "ensure_environment", return_value={"OPENROUTER_API_KEY": "hidden", "ELEVENLABS_API_KEY": "hidden"}), \
                 mock.patch.object(runner, "ensure_tools", return_value={"ffmpeg": "ffmpeg", "ffprobe": "ffprobe", "yt-dlp": "yt-dlp"}), \
                 mock.patch.object(runner, "get_endpoint_metadata", return_value=unsupported), \
                 mock.patch.object(runner, "prepare_source") as prepare:
                with self.assertRaisesRegex(runner.RunnerError, "Stopped before media download/upload"):
                    runner.run_pipeline(job_path)
                prepare.assert_not_called()

    def test_invalid_elevenlabs_credential_stops_before_media_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            job_path = Path(tmp) / "job.json"
            job = runner.new_job(url="https://youtube.com/watch?v=x", local_path=None, translation_model=runner.FREE_TRANSLATION_MODELS[0], output_root=tmp)
            runner.save_job(job_path, job)
            supported = {"data": {"endpoints": [{"provider_name": "supported", "supports_diarization": True}]}}
            with mock.patch.multiple(
                runner,
                ensure_environment=mock.DEFAULT,
                ensure_tools=mock.DEFAULT,
                get_endpoint_metadata=mock.DEFAULT,
                openrouter_key_info=mock.DEFAULT,
                elevenlabs_subscription_info=mock.DEFAULT,
                prepare_source=mock.DEFAULT,
            ) as patched:
                patched["ensure_environment"].return_value = {"OPENROUTER_API_KEY": "hidden", "ELEVENLABS_API_KEY": "hidden"}
                patched["ensure_tools"].return_value = {"ffmpeg": "ffmpeg", "ffprobe": "ffprobe", "yt-dlp": "yt-dlp"}
                patched["get_endpoint_metadata"].return_value = supported
                patched["openrouter_key_info"].return_value = {"limit_remaining": 1.0}
                patched["elevenlabs_subscription_info"].side_effect = runner.RunnerError("invalid key")
                with self.assertRaisesRegex(runner.RunnerError, "invalid key"):
                    runner.run_pipeline(job_path)
                patched["prepare_source"].assert_not_called()

    def test_transcription_request_uses_approved_model_and_verbose_diarization_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            audio = Path(tmp) / "sample.mp3"
            audio.write_bytes(b"fake mp3 bytes")
            expected_payload = None
            def fake_request(url, **kwargs):
                nonlocal expected_payload
                expected_payload = kwargs["payload"]
                self.assertEqual(url, f"{runner.OPENROUTER_BASE}/audio/transcriptions")
                return {"segments": []}
            with mock.patch.object(runner, "request_json", side_effect=fake_request):
                response = runner.transcribe_mp3(audio, "unlogged-secret", 10)
            self.assertEqual(response, {"segments": []})
            self.assertEqual(expected_payload["model"], "openai/whisper-large-v3-turbo")
            self.assertEqual(expected_payload["response_format"], "verbose_json")
            self.assertEqual(expected_payload["timestamp_granularities"], ["segment", "word"])
            self.assertIs(expected_payload["diarize"], True)
            self.assertEqual(expected_payload["input_audio"]["format"], "mp3")
            import base64
            self.assertEqual(base64.b64decode(expected_payload["input_audio"]["data"]), b"fake mp3 bytes")

    def test_clone_failure_is_checkpointed_as_uncertain_and_never_repeated_automatically(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            sample = project / "sample.mp3"
            sample.parent.mkdir(parents=True)
            sample.write_bytes(b"voice sample bytes")
            job_path = root / "job.json"
            job = runner.new_job(url=None, local_path="source.mp4", translation_model=runner.FREE_TRANSLATION_MODELS[0], output_root=tmp)
            job["speakers"] = {"speaker_0": {"name": "Speaker One"}}
            job["state"]["project_dir"] = str(project)
            job["state"]["voice_samples"] = {"speaker_0": str(sample)}
            job["settings"]["api_attempts"] = 1
            runner.save_job(job_path, job)
            translated = [{"id": "turn_0", "speaker": "speaker_0", "text": "Olá"}]
            tools = {"ffmpeg": "ffmpeg", "ffprobe": "ffprobe"}
            with mock.patch.object(runner, "clone_voice", side_effect=runner.RunnerError("ambiguous network failure")) as clone:
                with self.assertRaisesRegex(runner.RunnerError, "no automatic duplicate"):
                    runner.clone_and_preview_voices(job, job_path, translated, "not-used", tools)
            clone.assert_called_once()
            saved = runner.load_job(job_path)
            self.assertEqual(saved["state"]["clone_requests"]["speaker_0"]["status"], "pending")
            with mock.patch.object(runner, "clone_voice") as repeated:
                with self.assertRaisesRegex(runner.RunnerError, "may have reached ElevenLabs"):
                    runner.clone_and_preview_voices(saved, job_path, translated, "not-used", tools)
            repeated.assert_not_called()

    def test_translation_fallback_wraps_after_selected_last_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            project.mkdir()
            job_path = root / "job.json"
            job = runner.new_job(url=None, local_path="a.mp4", translation_model=runner.FREE_TRANSLATION_MODELS[-1], output_root=tmp)
            job["state"]["project_dir"] = str(project)
            job["settings"]["api_attempts"] = 1
            runner.save_job(job_path, job)
            turn = {"id": "turn_0", "speaker": "A", "start": 0, "end": 1, "text": "Hello"}
            used_models = []
            def fake_translate(batch, model, target_language, key, timeout, repair=None):
                used_models.append(model)
                if model == runner.FREE_TRANSLATION_MODELS[-1]:
                    raise runner.RunnerError("simulated selected-model failure")
                item = batch[0]
                content = json.dumps({"translations": [{"id": item["id"], "speaker": item["speaker"], "text": "Olá"}]})
                return {"content": content, "response": {}}
            with mock.patch.object(runner, "model_ids_available", return_value=set(runner.FREE_TRANSLATION_MODELS)), mock.patch.object(runner, "translate_request", side_effect=fake_translate):
                result = runner.translate_turns([turn], job, job_path, "not-used")
            self.assertEqual(used_models, [runner.FREE_TRANSLATION_MODELS[-1], runner.FREE_TRANSLATION_MODELS[0]])
            self.assertEqual(result[0]["model"], runner.FREE_TRANSLATION_MODELS[0])
        captured = {}
        def fake_request(url, **kwargs):
            captured["url"] = url
            captured.update(kwargs)
            return b"audio"
        with mock.patch.object(runner, "request_bytes", side_effect=fake_request):
            self.assertEqual(runner.tts_bytes("voice/with-slash", "Texto", "pt", "not-logged", 10), b"audio")
        self.assertTrue(captured["url"].endswith("/voice%2Fwith-slash?output_format=mp3_44100_128"))
        self.assertEqual(json.loads(captured["body"]), {"text": "Texto", "model_id": "eleven_v4_turbo", "language_code": "pt"})

    def test_prepare_source_reuses_project_mp3_after_crash_before_manifest_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            project.mkdir()
            source_mp3 = project / "source.mp3"
            source_mp3.write_bytes(b"existing encoded audio")
            job_path = root / "job.json"
            job = runner.new_job(url=None, local_path=str(root / "input.mp4"), translation_model=runner.FREE_TRANSLATION_MODELS[0], output_root=tmp)
            job["state"]["project_dir"] = str(project)
            runner.save_job(job_path, job)
            with mock.patch.object(runner, "ffprobe_duration", return_value=12.0), mock.patch.object(runner, "run_process") as process:
                reused = runner.prepare_source(job, job_path, {"ffmpeg": "ffmpeg", "ffprobe": "ffprobe"})
            self.assertEqual(reused, source_mp3)
            process.assert_not_called()
            self.assertEqual(job["state"]["source_mp3"], str(source_mp3.resolve()))

    def test_ytdlp_title_failure_requests_local_media_instead_of_other_download_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            job_path = Path(tmp) / "job.json"
            job = runner.new_job(url="https://youtube.com/watch?v=x", local_path=None, translation_model=runner.FREE_TRANSLATION_MODELS[0], output_root=tmp)
            with mock.patch.object(runner, "run_process", side_effect=runner.RunnerError("tool failed")):
                with self.assertRaisesRegex(runner.RunnerError, "ask the user for a local media file"):
                    runner.prepare_source(job, job_path, {"yt-dlp": "yt-dlp", "ffmpeg": "ffmpeg", "ffprobe": "ffprobe"})

    def test_smoke_test_accepts_word_level_diarization_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            source = project / "source.mp3"
            smoke = project / "smoke_test.mp3"
            source.write_bytes(b"source")
            smoke.write_bytes(b"smoke")
            response = {
                "segments": [{"start": 0, "end": 1, "text": "hello"}],
                "words": [{"start": 0, "end": 0.5, "word": "hello", "speaker": "speaker_0", "speaker_label": "A"}],
            }
            with mock.patch.object(runner, "transcribe_mp3", return_value=response):
                runner.smoke_test(source, project, "not-used", {"ffmpeg": "ffmpeg", "ffprobe": "ffprobe"}, 10, 1, 0)

    def test_api_retry_does_not_repeat_permanent_client_errors(self):
        calls = []
        def permanent_failure():
            calls.append(1)
            raise runner.RunnerError("HTTP 400")
        with self.assertRaises(runner.RunnerError):
            runner.api_retry(permanent_failure, attempts=3, base_delay=0)
        self.assertEqual(len(calls), 1)

    def test_api_retry_retries_transient_errors_with_bounded_attempt_count(self):
        calls = []
        def transient_failure():
            calls.append(1)
            if len(calls) < 3:
                raise runner.TransientRunnerError("HTTP 503")
            return "ok"
        with mock.patch.object(runner.time, "sleep") as sleep:
            result = runner.api_retry(transient_failure, attempts=3, base_delay=1)
        self.assertEqual(result, "ok")
        self.assertEqual(len(calls), 3)
        self.assertEqual(sleep.call_count, 2)

    def test_prepare_review_samples_writes_short_mp3_for_each_speaker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            project.mkdir()
            source = project / "source.mp3"
            source.write_bytes(b"source")
            job_path = root / "job.json"
            job = runner.new_job(url=None, local_path="source.mp4", translation_model=runner.FREE_TRANSLATION_MODELS[0], output_root=tmp)
            job["state"]["project_dir"] = str(project)
            job["state"]["source_mp3"] = str(source)
            runner.save_job(job_path, job)
            transcript = {"segments": [
                {"speaker": "speaker_0", "start": 0, "end": 12, "text": "first speaker"},
                {"speaker": "speaker_1", "start": 12, "end": 24, "text": "second speaker"},
            ]}
            def fake_clip(_source, output, _start, _duration, _ffmpeg):
                Path(output).write_bytes(b"review clip")
            with mock.patch.object(runner, "_ffmpeg_clip", side_effect=fake_clip), mock.patch.object(runner, "ffprobe_duration", side_effect=[9.5, 8.5]):
                paths = runner.prepare_review_samples(transcript, job, job_path, {"ffmpeg": "ffmpeg", "ffprobe": "ffprobe"})
            self.assertEqual(set(paths), {"speaker_0", "speaker_1"})
            self.assertTrue(all(Path(path).is_file() for path in paths.values()))
            self.assertEqual(job["state"]["speaker_review_samples"]["speaker_0"]["duration"], 9.5)

    def test_transcription_chunk_recovers_saved_response_without_paid_repeat(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            transcriptions = project / "transcriptions"
            transcriptions.mkdir(parents=True)
            response_path = transcriptions / "chunk_0000.json"
            response_path.write_text(json.dumps({"segments": [{"start": 0, "end": 1, "text": "hello"}]}), encoding="utf-8")
            chunk_audio = project / "chunk.mp3"
            chunk_audio.write_bytes(b"existing audio")
            job_path = root / "job.json"
            job = runner.new_job(url=None, local_path=str(chunk_audio), translation_model=runner.FREE_TRANSLATION_MODELS[0], output_root=tmp)
            job["state"]["project_dir"] = str(project)
            runner.save_job(job_path, job)
            with mock.patch.object(runner, "transcribe_mp3", side_effect=AssertionError("would resend paid chunk")) as transcribe:
                responses = runner.transcribe_chunks([{"index": 0, "start": 0, "end": 5, "path": str(chunk_audio)}], job, job_path, "not-used")
            transcribe.assert_not_called()
            self.assertEqual(responses[0]["segments"][0]["text"], "hello")
            self.assertTrue(runner.load_job(job_path)["state"]["transcription_chunks"]["0"]["complete"])

    def test_transcription_chunk_success_is_checkpointed_immediately(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            audio = project / "chunk.mp3"
            audio.write_bytes(b"not decoded in this mocked test")
            job_path = Path(tmp) / "job.json"
            job = runner.new_job(url=None, local_path=str(audio), translation_model=runner.FREE_TRANSLATION_MODELS[0], output_root=tmp)
            job["state"]["project_dir"] = str(project)
            runner.save_job(job_path, job)
            with mock.patch.object(runner, "transcribe_mp3", return_value={"segments": [{"start": 0, "end": 1, "text": "hi"}]}):
                responses = runner.transcribe_chunks([{"index": 0, "start": 0, "end": 5, "path": str(audio)}], job, job_path, "not-used")
            self.assertEqual(len(responses), 1)
            saved = runner.load_job(job_path)
            self.assertTrue(saved["state"]["transcription_chunks"]["0"]["complete"])
            self.assertIn("transcription", saved["state"]["completed"])

    def test_http_error_body_and_configured_secret_are_not_exposed(self):
        secret = "sk-or-v1-test-secret-123456789"
        error = urllib.error.HTTPError("https://example.test", 401, "Unauthorized", {}, io.BytesIO(secret.encode()))
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": secret}), mock.patch.object(runner.urllib.request, "urlopen", side_effect=error):
            with self.assertRaises(runner.RunnerError) as context:
                runner.request_bytes("https://example.test", headers={"Authorization": "Bearer " + secret})
        self.assertNotIn(secret, str(context.exception))
        self.assertIn("HTTP 401", str(context.exception))

    def test_completed_translation_checkpoint_does_not_require_live_model_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            project.mkdir()
            job_path = root / "job.json"
            job = runner.new_job(url=None, local_path="a.mp4", translation_model=runner.FREE_TRANSLATION_MODELS[0], output_root=tmp)
            job["state"]["project_dir"] = str(project)
            runner.save_job(job_path, job)
            turn = {"id": "turn_0", "speaker": "A", "start": 0, "end": 1, "duration": 1, "text": "Hello"}
            expected = {**turn, "original_text": "Hello", "text": "Olá", "model": runner.FREE_TRANSLATION_MODELS[0]}
            (project / "translated_turns.json").write_text(json.dumps({"turns": [expected]}), encoding="utf-8")
            with mock.patch.object(runner, "model_ids_available", side_effect=AssertionError("completed checkpoint should not query models")) as models:
                result = runner.translate_turns([turn], job, job_path, "not-used")
            models.assert_not_called()
            self.assertEqual(result[0]["text"], "Olá")

    def test_translation_api_checks_exact_selected_model_availability_before_calls(self):
        job = runner.new_job(url=None, local_path="a.mp4", translation_model=runner.FREE_TRANSLATION_MODELS[0])
        job["state"]["project_dir"] = tempfile.gettempdir()
        with mock.patch.object(runner, "model_ids_available", return_value={"other/model"}), mock.patch.object(runner, "translate_request") as request:
            with self.assertRaisesRegex(runner.RunnerError, "No remaining allowlisted free translation model"):
                runner.translate_turns([{"id": "turn_0", "speaker": "A", "start": 0, "end": 1, "text": "Hello"}], job, Path(tempfile.gettempdir()) / "unused-job.json", "hidden")
            request.assert_not_called()


    def test_translation_auto_fallback_when_selected_model_is_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            job = runner.new_job(url=None, local_path="a.mp4", translation_model=runner.FREE_TRANSLATION_MODELS[0], output_root=tmp)
            job["state"]["project_dir"] = tmp
            turn = {"id": "turn_0", "speaker": "A", "start": 0, "end": 1, "text": "Hello"}
            used_models = []
            def fake_translate(batch, model, target_language, key, timeout, repair=None):
                used_models.append(model)
                item = batch[0]
                return {"content": json.dumps({"translations": [{"id": item["id"], "speaker": item["speaker"], "text": "Olá"}]}), "response": {}}
            with mock.patch.object(runner, "model_ids_available", return_value={runner.FREE_TRANSLATION_MODELS[1]}), mock.patch.object(runner, "translate_request", side_effect=fake_translate):
                result = runner.translate_turns([turn], job, Path(tmp) / "job.json", "hidden")
            self.assertEqual(used_models, [runner.FREE_TRANSLATION_MODELS[1]])
            self.assertEqual(result[0]["model"], runner.FREE_TRANSLATION_MODELS[1])

    def test_translation_smoke_tests_one_turn_then_reuses_it_in_remaining_batches(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            job_path = Path(tmp) / "job.json"
            job = runner.new_job(url=None, local_path="a.mp4", translation_model=runner.FREE_TRANSLATION_MODELS[0], output_root=tmp)
            job["state"]["project_dir"] = str(project)
            job["settings"]["translation_batch_size"] = 12
            runner.save_job(job_path, job)
            turns = [
                {"id": f"turn_{i}", "speaker": "A", "start": i, "end": i + 1, "text": f"Line {i}"}
                for i in range(3)
            ]
            calls = []
            def fake_translate(batch, model, target_language, key, timeout, repair=None):
                calls.append([item["id"] for item in batch])
                return {"content": json.dumps({"translations": [
                    {"id": item["id"], "speaker": item["speaker"], "text": "translated"} for item in batch
                ]}), "response": {}}
            with mock.patch.object(runner, "model_ids_available", return_value=set(runner.FREE_TRANSLATION_MODELS)), mock.patch.object(runner, "translate_request", side_effect=fake_translate):
                translated = runner.translate_turns(turns, job, job_path, "hidden")
            self.assertEqual(calls, [["turn_0"], ["turn_1", "turn_2"]])
            self.assertEqual(len(translated), 3)
            self.assertTrue(runner.load_job(job_path)["state"]["translation_smoke_test"]["passed"])

    def test_translation_resume_continues_from_last_successful_fallback_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            project.mkdir()
            job_path = root / "job.json"
            job = runner.new_job(url=None, local_path="a.mp4", translation_model=runner.FREE_TRANSLATION_MODELS[0], output_root=tmp)
            job["state"]["project_dir"] = str(project)
            job["settings"]["api_attempts"] = 1
            job["settings"]["translation_batch_size"] = 1
            runner.save_job(job_path, job)
            first = {"id": "turn_1", "speaker": "A", "start": 0, "end": 1, "text": "Hello"}
            second = {"id": "turn_2", "speaker": "A", "start": 2, "end": 3, "text": "Goodbye"}
            used_models = []
            def fake_translate(batch, model, target_language, key, timeout, repair=None):
                used_models.append(model)
                if model == runner.FREE_TRANSLATION_MODELS[0]:
                    raise runner.RunnerError("simulated model failure")
                item = batch[0]
                content = json.dumps({"translations": [{"id": item["id"], "speaker": item["speaker"], "text": "translated"}]})
                return {"content": content, "response": {}}
            with mock.patch.object(runner, "model_ids_available", return_value=set(runner.FREE_TRANSLATION_MODELS)), mock.patch.object(runner, "translate_request", side_effect=fake_translate):
                runner.translate_turns([first], job, job_path, "not-used")
            self.assertEqual(used_models, [runner.FREE_TRANSLATION_MODELS[0], runner.FREE_TRANSLATION_MODELS[1]])
            used_models.clear()
            resumed = runner.load_job(job_path)
            resumed["state"].pop("translation_current_model", None)
            runner.save_job(job_path, resumed)
            resumed = runner.load_job(job_path)
            with mock.patch.object(runner, "model_ids_available", return_value=set(runner.FREE_TRANSLATION_MODELS)), mock.patch.object(runner, "translate_request", side_effect=fake_translate):
                result = runner.translate_turns([first, second], resumed, job_path, "not-used")
            self.assertEqual(used_models, [runner.FREE_TRANSLATION_MODELS[1]])
            self.assertEqual(len(result), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
