"""Run the complete local PaddleOCR-VL pipeline for one rendered page."""
import json
from pathlib import Path
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request


def latex_body(value: str) -> str:
    """Keep the expression even if the recognizer emits only one delimiter."""
    body = value.strip()
    for opening, closing in (("$$", "$$"), (r"\[", r"\]"), (r"\(", r"\)"), ("$", "$")):
        if body.startswith(opening) or body.endswith(closing):
            return body.removeprefix(opening).removesuffix(closing).strip()
    return body


path, runtime, output = map(Path, sys.argv[1:])
model = runtime / "models" / "paddle"
layout = runtime / "models" / "layout"
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
with socket.socket() as listener:
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
url = f"http://127.0.0.1:{port}"
with (Path(os.environ["SPECIALISTS_WORK"]) / "mlx.log").open("wb") as log:
    service = subprocess.Popen(
        [str(runtime / "mlx-vlm/bin/python"), "-m", "mlx_vlm.server",
         "--host", "127.0.0.1", "--port", str(port), "--model", str(model)],
        stdout=log, stderr=subprocess.STDOUT,
    )
    try:
        deadline = time.monotonic() + 90
        while True:
            if service.poll() is not None:
                raise RuntimeError("MLX-VLM stopped during startup.")
            try:
                with opener.open(f"{url}/health", timeout=2) as response:
                    if response.status == 200:
                        break
            except (urllib.error.URLError, TimeoutError):
                pass
            if time.monotonic() >= deadline:
                raise RuntimeError("MLX-VLM did not become ready.")
            time.sleep(0.35)

        started = time.monotonic()
        from paddleocr import PaddleOCRVL
        pipeline = PaddleOCRVL(
            device="cpu",
            pipeline_version="v1.6",
            layout_detection_model_dir=str(layout),
            vl_rec_backend="mlx-vlm-server",
            vl_rec_server_url=f"{url}/",
            vl_rec_api_model_name=str(model),
            vl_rec_max_concurrency=4,
            cpu_threads=4,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_layout_detection=True,
            use_queues=False,
        )
        print(f"Paddle pipeline initialization: {time.monotonic() - started:.2f}s", flush=True)
        started = time.monotonic()
        parsed = next(iter(pipeline.predict(input=str(path))))
        print(f"Paddle page inference: {time.monotonic() - started:.2f}s", flush=True)
        data = parsed.json["res"]
        width, height = data["width"], data["height"]
        blocks = []
        for index, region in enumerate(data["parsing_res_list"], 1):
            x0, y0, x1, y1 = map(float, region["block_bbox"])
            block = {
                "index": index, "kind": region["block_label"], "text": region["block_content"],
                "bbox": [x0 / width, y0 / height, x1 / width, y1 / height],
            }
            if block["kind"] in {"display_formula", "inline_formula", "formula"}:
                block["latex"] = latex_body(block["text"])
            blocks.append(block)
        markdown = parsed.markdown["markdown_texts"]
        output.write_text(json.dumps({
            "backend": "paddleocr_vl_1_6",
            "bbox_format": "normalized_xyxy_top_left",
            "text": markdown,
            "blocks": blocks,
        }, ensure_ascii=False), encoding="utf-8")
    finally:
        if service.poll() is None:
            service.terminate()
            try:
                service.wait(5)
            except subprocess.TimeoutExpired:
                service.kill()
                service.wait()
