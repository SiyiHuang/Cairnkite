"""Exercise the installed tools through their stdio MCP transport."""
import argparse
import asyncio
import json
import math
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
DEMO = Path.home() / "LocalSpecialists/demo"


async def main(full: bool, expanded: bool, apple: bool, text_models: bool, digup: bool) -> None:
    DEMO.mkdir(mode=0o700, parents=True, exist_ok=True)
    for fixture in (ROOT / "tests/fixtures").iterdir():
        target = DEMO / fixture.name
        if target.exists() and fixture.read_bytes() != target.read_bytes():
            raise SystemExit(f"Fixture path already contains different data: {target}")
        if not target.exists():
            shutil.copyfile(fixture, target)

    async with stdio_client(StdioServerParameters(command=str(ROOT / "bin/serve"))) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert {tool.name for tool in tools.tools} == {
                "align_audio", "check_smolvla_rollout", "classify_sound", "decide", "document", "estimate_depth", "extract_apple_fields", "extract_entities", "fetch_linked_mac", "focus_text",
                "forecast_series", "generate_lean_proof", "inspect_apple_attachment", "inspect_apple_image", "lookup_apple_record", "plan_deployment", "predict_coreml",
                "preview_robot_actions",
                "read_evidence", "rerank_visual", "restore_image", "restore_video",
                "run_apple_shortcut",
                "score_ocr", "search", "search_apple_notes", "search_code", "search_linked_mac", "status",
                "active_video_speakers", "check_lean_proof", "extract_apple_foreground",
                "segment_objects", "separate_audio", "synthesize_speech", "text_analysis",
                "transcribe", "translate", "wait_for_screenshot",
            }

            async def call(tool: str, **args):
                start = time.monotonic()
                result = await session.call_tool(tool, args)
                assert not result.is_error, result.content
                payload = result.structured_content
                if payload is None:
                    payload = json.loads(result.content[0].text)
                print(
                    f"{tool} {payload.get('backend', '')}: {time.monotonic() - start:.2f}s",
                    flush=True,
                )
                return payload

            status = await call("status")
            assert status["apple"]["vision_available"]
            options = await call("plan_deployment", feature="align-transcript", execution="local", verified_only=True)
            assert options["recommendation"] == "qwen-align"
            commercial = await call("plan_deployment", feature="semantic-search", use="commercial", execution="mcp")
            assert commercial["recommendation"] == "digup"
            pdf = str(DEMO / "calibration.pdf")
            audio = str(DEMO / "meeting.wav")
            text = await call("document", path=pdf)
            assert text["backend"] == "pdfkit" and text["page_count"] == 2 and "PRISM-852" in text["text"]
            scan = await call("document", path=pdf, page=2, max_chars=12000)
            assert scan["backend"] == "apple_vision" and scan["page"] == 2 and "ORBIT-741" in scan["text"]
            assert scan["lines"] and scan["tables"] and "Venus" in scan["text"]
            for line in scan["lines"]:
                x0, y0, x1, y1 = line["bbox"]
                assert 0 <= x0 <= x1 <= 1 and 0 <= y0 <= y1 <= 1
            barcode = await call("document", path=str(DEMO / "barcode.png"), backend="barcodes")
            assert [code["payload"] for code in barcode["codes"]] == ["LOCAL-SPECIALISTS-QR-731"]
            tags = await call("text_analysis", text="Apple opened an office in Berlin. Maria Lopez joined the team.")
            assert tags["languages"][0]["language"] == "en" and tags["offset_unit"] == "utf16"
            assert any(item["text"] == "Berlin" and item["tag"] == "PlaceName" for item in tags["entities"])

            truncated = await call("document", path=pdf, page=2, max_chars=500)
            offset, chunks = 0, []
            while offset is not None:
                page = await call("read_evidence", result_id=truncated["result_id"], max_chars=12000, offset=offset)
                offset = page["next_offset"]
                chunks.append(page["json_slice"])
            assert json.loads("".join(chunks))["tables"] == scan["tables"]

            denied = await session.call_tool("document", {"path": str(ROOT / "tests/fixtures/calibration.pdf")})
            assert denied.is_error and "outside the allowed directories" in denied.content[0].text

            if digup:
                for query, expected, locator in (
                    ("finding the North Star for telescope alignment", str(DEMO / "telescope-guide.txt"), {}),
                    ("ORBIT-741 11:40", pdf, {"page": 2}),
                    ("copper prism is ready", audio, {"segment": "audio", "start_s": 0}),
                ):
                    result = await call("search", folder=str(DEMO), query=query, backend="digup")
                    first = result["results"][0]
                    assert first["path"] == expected and all(first[k] == v for k, v in locator.items()), first

            if apple:
                speech = await call("transcribe", path=audio, backend="apple", locale="en-US")
                assert "copper prism" in speech["segments"][0]["text"].lower()
                assert all(0 <= part["start_s"] < part["end_s"] <= speech["duration_s"] for part in speech["segments"])
                translation = await call("translate", texts=["The book is on the table."],
                                         source_language="en", target_language="zh-Hans", backend="apple")
                assert "书" in translation["translations"][0] and "桌" in translation["translations"][0]
                focus = await call("focus_text", text="Marina owns the inspection, scheduled for June 17.",
                                   question="Who is responsible and when?")
                assert "Marina" in focus["text"] and "June 17" in focus["text"]
                extracted = await call("extract_apple_fields",
                                       text="The copper prism inspection was moved to June 17. The owner is Marina. The budget is pending.",
                                       fields={"owner": "Name of the person responsible for the inspection", "date": "Date of the inspection",
                                               "budget": "Confirmed budget amount"})
                assert extracted["fields"] == {"owner": "Marina", "date": "June 17", "budget": None}
                missing = await call("extract_apple_fields",
                                     text="The project is approved. The phone number and last name are unknown.",
                                     fields={"phone": "Telephone number", "last_name": "Family name",
                                             "status": "Explicit approval status"})
                assert missing["fields"] == {"phone": None, "last_name": None, "status": "approved"}, missing
                if status["apple_spotlight_ranked"]:
                    ranked = await call("search_apple_notes", path=str(DEMO / "spotlight-notes.json"),
                                        question="pastries made with tree nuts", mode="semantic")
                    assert ranked["backend"] == "apple_core_spotlight_ranked" and ranked["text"] is None
                    assert ranked["matches"] and ranked["matches"][0]["id"] == "food", ranked
                picture = str(DEMO / "observatory.png")
                image = await call("inspect_apple_image", path=picture)
                assert image["classifications"] and "overall_score" in image["aesthetics"]
                same = await call("inspect_apple_image", path=picture, comparison=picture)
                different = await call("inspect_apple_image", path=picture, comparison=str(DEMO / "barcode.png"))
                assert 0 <= same["distance"] < different["distance"]
                model = str(DEMO / "relu.mlmodel")
                description = await call("predict_coreml", model=model)
                assert description["input_features"]["x"]["shape"] == [3]
                numeric = await call("predict_coreml", model=model, inputs={"x": {"values": [-2, 0, 3]}})
                assert numeric["prediction"]["y"]["values"] == [0, 0, 3]
                sound = await call("classify_sound", path=audio)
                assert all(0 <= window["start_s"] < window["end_s"] <= sound["duration_s"] for window in sound["windows"])
                assert any(label["label"] == "speech" for window in sound["windows"] for label in window["classifications"])
                audio_result = await call("synthesize_speech", text="The copper prism is ready.", voice="Samantha")
                artifact = Path(audio_result["audio_wav"])
                try:
                    assert audio_result["duration_s"] > 0 and audio_result["sample_rate"] == 22050
                    assert artifact.read_bytes()[0:4] == b"RIFF"
                finally:
                    artifact.unlink(missing_ok=True)
                if shutil.which("ffmpeg") and shutil.which("ffprobe"):
                    scale = subprocess.run(
                        [str(ROOT / "native/.build/release/apple-specialists"), "video-scale-status", "320", "192"],
                        capture_output=True, text=True, check=True, timeout=10,
                    )
                    if 2 in json.loads(scale.stdout)["scale_factors"]:
                        with TemporaryDirectory(prefix="apple-video-", dir=DEMO) as scratch:
                            clip = Path(scratch) / "clip.mp4"
                            subprocess.run(
                                ["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=320x192:rate=8",
                                 "-frames:v", "2", "-c:v", "libx264", str(clip)],
                                check=True, timeout=15,
                            )
                            video = await call("restore_video", path=str(clip), backend="apple", scale="2x", max_frames=1)
                            artifact = Path(video["output_mp4"])
                            try:
                                assert (video["width"], video["height"], video["frames"], video["audio_tracks"]) == (640, 384, 1, 0)
                                assert abs(video["duration_s"] - 0.125) < 0.001
                            finally:
                                artifact.unlink(missing_ok=True)

            if text_models:
                if status["lean"]:
                    verified = await call("check_lean_proof", declaration="prove", statement="True",
                                          source="theorem prove : True := True.intro")
                    assert verified["accepted"] and verified["statement_checked"] and verified["axioms"] == []
                    for source, axioms in (
                        ("theorem prove : False := by sorry", ["sorryAx"]),
                        ('local notation "False" => True\ntheorem prove : False := True.intro', []),
                    ):
                        rejected = await call("check_lean_proof", source=source, declaration="prove", statement="False")
                        assert rejected["compiled"] and not rejected["accepted"] and rejected["axioms"] == axioms
                        assert rejected["statement_checked"] == bool(axioms)
                sources = ["Apple CEO Tim Cook announced iPhone 15 in Cupertino yesterday.",
                           "周岩在上海复核仪器。", "The project lead Alice is visiting 北京。"]
                result = await call("extract_entities", texts=sources,
                                    labels={"person": "Person name / 人名", "city": "A city or municipality / 城市名"})
                expected = [("Tim Cook", "Cupertino"), ("周岩", "上海"), ("Alice", "北京")]
                for source, document, (person, city) in zip(sources, result["documents"], expected, strict=True):
                    for label, value in (("person", person), ("city", city)):
                        match = document["entities"][label][0]
                        assert source[match["start"]:match["end"]] == match["text"] == value
                targets = [120 + 0.65 * i + 7 * math.sin(i * math.pi / 3) for i in range(90)]
                cycles = [i % 6 for i in range(90)]
                backends = ("chronos", "timesfm") if status["timesfm"] else ("chronos",)
                for backend in backends:
                    result = await call("forecast_series", targets={"flow": targets[:84]}, horizon=6, backend=backend,
                                        past_covariates={"cycle": cycles[:84]}, future_covariates={"cycle": cycles[84:]})
                    assert result["quantile_levels"] == [0.1, 0.5, 0.9]
                    rows = result["forecast"]["flow"]
                    assert len(rows) == 6 and all(len(row) == 3 and all(map(math.isfinite, row)) and row == sorted(row) for row in rows)

            if full:
                async def check_audio(backend: str):
                    recording = await call("transcribe", path=audio, backend=backend)
                    segments = recording["segments"]
                    assert "copper prism" in segments[0]["text"].lower()
                    assert all(0 <= part["start_s"] <= part["end_s"] <= 11 for part in segments)
                    if backend == "moss":
                        assert {part["speaker"] for part in segments} == {"S01", "S02"}
                    return recording

                speech, moss, paddle, omni = await asyncio.gather(
                    check_audio("apple"),
                    check_audio("moss"),
                    call("document", path=pdf, page=2, backend="paddle", max_chars=12000),
                    call("search", folder=str(DEMO), query="finding the North Star for telescope alignment", limit=3),
                )
                assert speech["backend"] == "apple_speech" and moss["backend"] == "moss_mlx_8bit"
                assert any(block["kind"] == "table" and "11:40" in block["text"] for block in paddle["blocks"])
                assert omni["results"] and omni["results"][0]["path"].endswith("/telescope-guide.txt")
            if expanded:
                formula_path = str(DEMO / "formula-page.png")
                if status["paddle"]:
                    page = await call("document", path=formula_path, backend="paddle", max_chars=10000)
                    formulas = [block for block in page["blocks"] if block["kind"] == "display_formula"]
                    assert len(formulas) == 2
                    assert r"\sum" in formulas[0]["latex"] and r"\int" in formulas[1]["latex"], formulas
                    assert all(not block["latex"].endswith((r"\]", r"\)", "$")) for block in formulas)
                    assert all(0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1
                               for box in (block["bbox"] for block in formulas))
                proofread = await call("document", path=formula_path, backend="minicpm", max_chars=10000)
                formula_text = "".join(proofread["text"].split())
                assert r"\sum_{k=2}^{n}\frac{k^{2}+3}{k+1}" in formula_text, formula_text
                assert r"\int_{0}^{t}\frac{x^{2}}{\sqrt{1+x^{4}}}" in formula_text, formula_text
                if status["qwen_asr"]:
                    stream = await call("transcribe", path=audio, backend="qwen-stream", language="English")
                    assert [p["audio_seconds"] for p in stream["partials"]] == [2, 4, 6, 8, 10]
                    assert stream["metrics"]["chunks_processed"] == 6 and "11:40" in stream["text"]
                if status["silero"]:
                    intervals = await call("transcribe", path=audio, backend="silero")
                    assert intervals["segment_unit"] == "speech_activity" and len(intervals["segments"]) == 4
                    assert all(0 <= segment["start_s"] < segment["end_s"] <= intervals["duration_s"]
                               for segment in intervals["segments"])
                independent, words, aligned, translation = await asyncio.gather(
                    call("document", path=pdf, page=2, backend="minicpm"),
                    call("transcribe", path=audio, backend="qwen", language="English"),
                    call("align_audio", path=audio, text="The copper prism is ready.", language="English"),
                    call("translate", texts=["Check the copper prism."], source_language="en",
                         target_language="zh-Hans", backend="hy-mt", glossary={"copper prism": "青铜棱镜"}),
                )
                assert "ORBIT-741" in independent["text"] and "11:40" in independent["text"]
                assert "copper prism" in words["text"].lower() and len(words["segments"]) >= 10
                assert any(segment["text"].lower() == "prism" for segment in aligned["segments"])
                for result in (words, aligned):
                    assert all(0 <= part["start_s"] <= part["end_s"] <= result["duration_s"] for part in result["segments"])
                assert "青铜棱镜" in translation["translations"][0] and translation["truncated"] == [False]
                if status["qwen_large"]:
                    large = await call("transcribe", path=audio, backend="qwen-large", language="English")
                    assert large["backend"] == "qwen3_asr_1_7b_8bit"
                    assert "copper prism" in large["text"].lower() and len(large["segments"]) >= 10
                    assert all(0 <= part["start_s"] <= part["end_s"] <= large["duration_s"] for part in large["segments"])
                apple_plan = await call("plan_deployment", feature="translate", execution="mcp")
                apple_path = next(entry for entry in apple_plan["candidates"] if entry["id"] == "apple-translation")
                if apple_path["readiness"] == "installed":
                    result = await call("translate", texts=["The book is on the table."], source_language="en", target_language="zh-Hans")
                    assert "书" in result["translations"][0] and "桌" in result["translations"][0]
                else:
                    print("Apple Translation sample skipped. Install the en → zh-Hans resources to exercise it.")
            print("Smoke test passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--expanded", action="store_true")
    parser.add_argument("--apple", action="store_true", help="Also exercise installed English Speech, en→zh-Hans Translation and Apple Intelligence.")
    parser.add_argument("--text-models", action="store_true", help="Exercise installed GLiNER and Chronos with source-span and forecast checks.")
    parser.add_argument("--digup", action="store_true", help="Check the prepared DigUp demo index and evidence locations.")
    args = parser.parse_args()
    asyncio.run(main(args.full, args.expanded, args.apple, args.text_models, args.digup))
