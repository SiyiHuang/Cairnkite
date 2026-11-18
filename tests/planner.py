"""Validate decision paths independently of installed models or client accounts."""
from contextlib import closing
import json
from pathlib import Path
import re
import sqlite3
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import deployment
from deployment import plan, read_catalog

MAC = {"machine": "arm64", "macos": "26.5", "disk_gib": 100, "memory_gib": 24}


class PlannerTest(unittest.TestCase):
    def test_catalog_references_and_recipes(self):
        catalog = read_catalog()
        self.assertNotRegex(json.dumps(catalog, ensure_ascii=False), r"[\u3400-\u9fff]")
        tree = plan()
        leaves = [leaf for group in tree["tasks"] for leaf in group["choices"]]
        self.assertEqual(len(leaves), len({leaf["id"] for leaf in leaves}))
        referenced = {candidate for leaf in leaves for candidate in leaf["candidates"]}
        self.assertEqual(referenced, set(catalog["backends"]))
        default, optional = (set(tree["profiles"][name]) for name in ("default", "optional"))
        self.assertFalse(default & optional)
        self.assertEqual(default | optional, referenced)
        for identifier, entry in catalog["backends"].items():
            with self.subTest(identifier=identifier):
                recipe, anchor = entry["recipe"].split("#")
                self.assertIn(f'<a id="{anchor}"></a>', (ROOT / recipe).read_text(encoding="utf-8"))
                self.assertTrue(entry["strength"] and entry["tradeoff"] and entry["license"]["name"])
                self.assertLessEqual(set(entry["features"]), set(tree["requirements"]))
                self.assertLessEqual(set(entry.get("unverified_features", [])), set(entry["features"]))
                if entry["delivery"] == "mcp":
                    self.assertTrue(entry["install"] and entry["mcp"]["tool"] and entry.get("local_cli"))
        install_choices = (ROOT / "bin/install").read_text(encoding="utf-8").split('case "${1:-default}" in')[1]
        for entry in catalog["backends"].values():
            for command in entry.get("install", []):
                if command[0] == "bin/install":
                    self.assertRegex(install_choices, rf"(?m)^  [\w|-]*\b{re.escape(command[1])}\b[\w|-]*\)")

    def choose(self, feature, **kwargs):
        return plan(feature, target=kwargs.pop("target", MAC), **kwargs)

    def test_requirements_and_mcp(self):
        self.assertEqual(self.choose("complex-layout", requirements=["formula_markup"])["recommendation"], "paddle")
        self.assertEqual(self.choose("complex-layout", requirements=["formula_markup"], verified_only=True)["recommendation"], "paddle")
        self.assertEqual(self.choose("streaming", requirements=["realtime"], execution="local",
                                     verified_only=True)["recommendation"], "qwen-stream")
        self.assertEqual(self.choose("streaming", requirements=["microphone_input"], execution="local",
                                     verified_only=True)["recommendation"], "qwen-stream")
        self.assertIsNone(self.choose("streaming", execution="mcp")["recommendation"])
        self.assertEqual(self.choose("stream-replay", execution="mcp", verified_only=True)["recommendation"], "qwen-stream-replay")
        self.assertEqual(self.choose("apple-record-lookup", requirements=["tool_calls"], execution="mcp",
                                     verified_only=True)["recommendation"], "apple-fm-python")
        self.assertEqual(self.choose("align-transcript", requirements=["corrected_transcript"], verified_only=True)["recommendation"], "qwen-align")
        self.assertEqual(self.choose("word-timestamps", requirements=["asr_1_7b"], verified_only=True)["recommendation"], "qwen-large")
        self.assertEqual(self.choose("word-timestamps", requirements=["speaker_labels"])["recommendation"], None)
        self.assertEqual(self.choose("speech-activity", requirements=["vad_intervals"],
                                     verified_only=True)["recommendation"], "silero-vad")
        self.assertNotIn("speech-detector", {path["id"] for path in self.choose("speech-activity")["candidates"]})
        self.assertEqual(self.choose("speech-detector-probe")["recommendation"], "speech-detector")
        self.assertEqual(self.choose("semantic-search", use="personal", requirements=["multimodal"], verified_only=True)["recommendation"], "omni")
        self.assertEqual(self.choose("semantic-search", use="personal", requirements=["search_timecodes"], verified_only=True)["recommendation"], "digup")
        self.assertEqual(self.choose("semantic-search", use="commercial", execution="mcp")["recommendation"], "digup")
        linked_copy = self.choose("cross-mac-copy", use="personal", execution="mcp", requirements=["linked_file_copy"])
        self.assertEqual(linked_copy["recommendation"], "omni-linked-copy")
        self.assertEqual(linked_copy["candidates"][0]["mcp"]["tool"], "fetch_linked_mac")
        self.assertIsNone(self.choose("cross-mac-copy", use="personal", verified_only=True)["recommendation"])
        code = self.choose("code-search", use="commercial", requirements=["code_semantic"])
        self.assertEqual(code["recommendation"], "digup")
        self.assertEqual(code["candidates"][1]["mcp"]["arguments"], {"backend": "digup", "code": True})
        self.assertEqual(self.choose("code-search", use="personal", requirements=["unindexed_code"],
                                     execution="mcp", verified_only=True)["recommendation"], "jina-grep")
        self.assertEqual(self.choose("visual-rerank", requirements=["compact_visual_reranker"],
                                     verified_only=True)["recommendation"], "qwen-reranker-4bit")

    def test_profiles(self):
        self.assertEqual(self.choose("scan", profile="default")["recommendation"], "vision")
        self.assertEqual(self.choose("scan", profile="optional")["recommendation"], "paddle")
        self.assertEqual(self.choose("foreground-mask", profile="default")["recommendation"], "apple-foreground")
        self.assertEqual(self.choose("foreground-mask", profile="optional")["candidates"][1]["mcp"]["arguments"],
                         {"task": "segment"})
        plan_result = self.choose("speaker-transcript", profile="default")
        self.assertIsNone(plan_result["recommendation"])
        self.assertEqual(plan_result["candidates"][0]["profile"], "optional")
        self.assertIn("optional profile", plan_result["candidates"][0]["reasons"][0])

    def test_lfm_task_calls_and_license(self):
        extract = self.choose("extract-fields", use="personal", profile="default")
        self.assertEqual(extract["recommendation"], "lfm-fast")
        self.assertEqual(extract["candidates"][0]["mcp"]["tool"], "extract_fields")
        summary = self.choose("summarize", use="personal", profile="default")
        self.assertEqual(summary["candidates"][0]["mcp"], {"server": "local-lfm", "tool": "summarize", "arguments": {}})
        self.assertEqual(summary["candidates"][0]["local_cli"], ["bin/lfm", "local", "summarize"])
        self.assertEqual(self.choose("summarize", use="commercial")["recommendation"], "foundation-models")

    def test_licensing_and_trials(self):
        self.assertIsNotNone(self.choose("semantic-search")["question"])
        self.assertEqual(self.choose("semantic-search", use="personal")["recommendation"], "omni")
        self.assertEqual(self.choose("forecast", use="personal")["recommendation"], "timesfm")
        self.assertEqual(self.choose("forecast", use="production")["recommendation"], "chronos")
        self.assertEqual(self.choose("triage", use="commercial", requirements=["choice_scores"])["recommendation"], "clef")
        self.assertEqual(self.choose("forecast", use="personal", verified_only=True)["recommendation"], "timesfm")
        self.assertEqual(self.choose("forecast", use="production", verified_only=True)["recommendation"], "chronos")
        self.assertIsNotNone(self.choose("robot-control")["question"])
        self.assertIn("offline", self.choose("robot-control", robot_ready=False)["candidates"][0]["setup_note"])
        self.assertEqual(self.choose("robot-control", robot_ready=False, execution="mcp",
                                     verified_only=True)["recommendation"], "smolvla")
        self.assertEqual(self.choose("robot-control", robot_ready=True)["recommendation"], "smolvla-rollout")
        self.assertIsNone(self.choose("robot-control", robot_ready=True, verified_only=True)["recommendation"])
        preflight = self.choose("robot-preflight", requirements=["robot_rollout_preflight"], execution="mcp", verified_only=True)
        self.assertEqual(preflight["recommendation"], "smolvla-preflight")
        self.assertEqual(preflight["candidates"][0]["mcp"]["tool"], "check_smolvla_rollout")

    def test_host_and_language(self):
        self.assertIsNone(self.choose("ocr-second-pass", target={**MAC, "disk_gib": 0})["recommendation"])
        self.assertIsNone(self.choose("pdf-text", target={**MAC, "machine": "x86_64"})["recommendation"])
        self.assertIsNone(self.choose("translate", requirements=["glossary"], translation_pair=("en", "zz"))["recommendation"])
        self.assertEqual(self.choose("translate", requirements=["glossary"], translation_pair=("zh-CN", "zh-TW"))["recommendation"], "hy-mt")
        self.assertIn("16 GiB", self.choose("triage", target={**MAC, "memory_gib": 8})["candidates"][0]["setup_note"])
        with self.assertRaisesRegex(ValueError, "Unknown required features"):
            self.choose("translate", requirements=["nonexistent"])

    def test_lfm_review_budget_uses_weights_and_startup_model(self):
        profile = self.choose("focused-review", use="personal", execution="mcp", verified_only=True)
        q8, q4 = profile["candidates"]
        self.assertEqual(profile["recommendation"], "lfm-reason-q4")
        self.assertEqual(q8["decision"], "excluded")
        self.assertIn("26.97 GiB", q8["reasons"][0])
        self.assertEqual(q4["mcp"]["arguments"], {"model": "lfm-reason-q4"})
        self.assertEqual(q4["weights_gib"], 13.53)
        self.assertEqual(q4["preset_weights_gib"], 16.76)
        low = self.choose("focused-review", use="personal", execution="mcp", target={**MAC, "memory_gib": 16})
        self.assertIsNone(low["recommendation"])
        self.assertTrue(all(candidate["decision"] == "excluded" for candidate in low["candidates"]))
        self.assertEqual(self.choose("focused-review", use="personal", execution="mcp",
                                     target={**MAC, "memory_gib": 32})["recommendation"], "lfm-reason")

    def test_search_uses_the_folder_and_the_requested_index_mode(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            folder = root / "docs"
            folder.mkdir()
            with (
                patch.multiple(deployment, ROOT=root, RUNTIME=root / ".runtime", OMNI=root / "missing-omni"),
                patch.object(deployment, "machine_facts", return_value=MAC),
            ):
                entry = read_catalog()["backends"]["digup"]
                for relative in entry["markers"]:
                    marker = root / relative
                    marker.parent.mkdir(parents=True, exist_ok=True)
                    marker.touch()
                index = deployment.digup_index(folder)
                index.mkdir(parents=True)
                db = index / "code.sqlite"
                with closing(sqlite3.connect(db)) as database, database:
                    database.execute("CREATE TABLE files(id INTEGER PRIMARY KEY, path TEXT)")
                    database.execute("CREATE TABLE segments(file INTEGER, vec BLOB)")
                    database.execute("INSERT INTO files VALUES(1, ?)", (str(folder / "retry.py"),))
                    database.execute("INSERT INTO segments VALUES(1, NULL)")
                self.assertEqual(deployment.digup_index_ready(folder, code=True)[0], "needs_setup")
                with closing(sqlite3.connect(db)) as database, database:
                    database.execute("UPDATE segments SET vec = x'00112233'")

                result = plan("code-search", use="commercial", execution="mcp", folder=folder)
                candidate = next(entry for entry in result["candidates"] if entry["id"] == "digup")
                self.assertEqual(result["recommendation"], "digup")
                self.assertEqual(candidate["readiness"], "installed")
                self.assertEqual(candidate["mcp"]["arguments"], {"backend": "digup", "code": True, "folder": str(folder)})
                self.assertEqual(deployment.digup_index_ready(folder, code=False)[0], "needs_setup")
                self.assertFalse((index / "index.sqlite").exists())

    def test_media_restoration_arguments(self):
        image = self.choose("upscale-image", execution="mcp", verified_only=True)
        video = self.choose("upscale-video", execution="mcp", verified_only=True)
        self.assertEqual(image["recommendation"], "seedvr2")
        self.assertEqual(image["candidates"][0]["mcp"], {"tool": "restore_image", "arguments": {"scale": "2x"}})
        self.assertEqual(video["recommendation"], "seedvr2")
        self.assertEqual(video["candidates"][0]["mcp"]["arguments"], {"backend": "seedvr2", "scale": "2x"})
        self.assertIn("allow_high_memory", video["candidates"][0]["setup_note"])
        native = self.choose("upscale-video", execution="mcp", requirements=["native_video_upscale"], verified_only=True)
        self.assertEqual(native["recommendation"], "apple-video-upscale")
        self.assertEqual(native["candidates"][1]["mcp"]["arguments"], {"backend": "apple", "scale": "2x"})
        fourfold = self.choose("upscale-video-4x", execution="mcp", verified_only=True)
        self.assertEqual(fourfold["recommendation"], "apple-video-upscale")
        self.assertEqual(fourfold["candidates"][0]["mcp"]["arguments"], {"backend": "apple", "scale": "4x"})

    def test_screenshot_and_macos_27_routes(self):
        mac27 = {**MAC, "macos": "27.2"}
        self.assertEqual(self.choose("screenshot-ingest", requirements=["screenshot_automation"],
                                     verified_only=True)["recommendation"], "screenshot-folder")
        self.assertEqual(self.choose("screenshot-ingest", requirements=["shortcuts_folder_trigger"], target=mac27,
                                     verified_only=True)["recommendation"], "shortcuts-folder")
        self.assertIsNone(self.choose("screenshot-ingest", requirements=["shortcuts_folder_trigger"], target=mac27,
                                      execution="mcp", verified_only=True)["recommendation"])
        self.assertEqual(self.choose("screenshot-ingest", requirements=["shortcuts_system_trigger"], target=mac27,
                                     verified_only=True)["recommendation"], "shortcuts-screenshot")
        self.assertEqual(self.choose("screenshot-ingest", execution="mcp", target=mac27,
                                     verified_only=True)["recommendation"], "screenshot-folder")
        self.assertEqual(self.choose("shortcut-automation", requirements=["image_shortcut"],
                                     verified_only=True)["recommendation"], "shortcuts")
        self.assertIsNone(self.choose("visual-question", requirements=["apple_native_images"],
                                      verified_only=True)["recommendation"])
        self.assertEqual(self.choose("visual-question", requirements=["apple_native_images"], target=mac27,
                                     verified_only=True)["recommendation"], "apple-fm-image")
        self.assertEqual(self.choose("app-search", requirements=["app_index_tool"], target=mac27,
                                     verified_only=True)["recommendation"], "core-spotlight")
        semantic = self.choose("app-search", requirements=["app_semantic_index"], target=mac27,
                               execution="mcp", verified_only=True)
        self.assertEqual(semantic["recommendation"], "core-spotlight-semantic")
        self.assertEqual(semantic["candidates"][1]["mcp"], {"tool": "search_apple_notes", "arguments": {"mode": "semantic"}})


if __name__ == "__main__":
    unittest.main()
