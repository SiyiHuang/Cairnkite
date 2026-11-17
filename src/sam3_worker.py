"""Detect prompted objects with the tokenizer from the pinned SAM3 checkpoint."""

import json
import math
from pathlib import Path
import sys

import cv2
from PIL import Image
from mlx_vlm.generate import wired_limit
from mlx_vlm.models.sam3.generate import Sam3Predictor, SimpleTracker, draw_frame, predict_multi
from mlx_vlm.models.sam3.processing_sam3 import Sam3Processor
from mlx_vlm.utils import load_model
from transformers import AutoTokenizer


def detections(result, width: int, height: int) -> list[dict]:
    rows = []
    for index, (score, box) in enumerate(zip(result.scores, result.boxes, strict=True)):
        x0, y0, x1, y1 = box
        row = {"index": index, "score": float(score), "bbox": [
            float(min(max(x0, 0), width)), float(min(max(y0, 0), height)),
            float(min(max(x1, 0), width)), float(min(max(y1, 0), height)),
        ]}
        if result.track_ids is not None:
            row["track_id"] = int(result.track_ids[index])
        rows.append(row)
    return sorted(rows, key=lambda row: row["score"], reverse=True)


def segment(predictor, request: dict, directory: Path) -> dict:
    with Image.open(request["path"]) as source:
        width, height = source.size
        if width * height > 16_000_000:
            raise ValueError("Use an image of at most 16 million pixels.")
        image = source.convert("RGB")
    result = predict_multi(predictor, image, [request["prompt"]])
    rows = detections(result, width, height)
    for row in rows[:12]:
        path = directory / f"mask-{row['index']}.png"
        Image.fromarray(result.masks[row["index"]] * 255).save(path)
        row["mask_png"] = str(path)
    return {"width": width, "height": height, "detections": rows[:12], "additional_detections": max(0, len(rows) - 12)}


def track(predictor, request: dict, directory: Path) -> dict:
    capture = cv2.VideoCapture(request["path"])
    try:
        fps = capture.get(cv2.CAP_PROP_FPS)
        count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if not capture.isOpened() or not math.isfinite(fps) or fps <= 0 or count <= 0 or count / fps > 30:
            raise ValueError("Use a readable video file of at most 30 seconds.")
        if not 0 < width * height <= 1920 * 1080:
            raise ValueError("Use a video with at most 2,073,600 pixels per frame.")
        path = directory / "tracked.mp4"
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
        tracker = SimpleTracker()
        stride = max(1, math.ceil(fps / request["sample_fps"]))
        annotated = 0
        samples = []
        try:
            if not writer.isOpened():
                raise ValueError("Cannot open the output video encoder.")
            for number in range(count):
                ok, frame = capture.read()
                if not ok:
                    break
                if number % stride == 0:
                    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    result = tracker.update(predict_multi(predictor, image, [request["prompt"]]))
                    rows = detections(result, width, height)
                    samples.append({"frame": number, "time_s": round(number / fps, 3), "detections": rows[:12]})
                writer.write(draw_frame(
                    frame, result.masks, result.scores, result.boxes, request["prompt"],
                    height, width, show_boxes=True, labels=result.labels,
                ))
                annotated += 1
        finally:
            writer.release()
        if not annotated:
            raise ValueError("Video contained no decodable frames.")
        return {"width": width, "height": height, "video_mp4": str(path), "frames": annotated, "fps": fps,
                "samples": samples, "partial": annotated != count}
    finally:
        capture.release()


def main() -> None:
    checkpoint, output = map(Path, sys.argv[1:])
    request = json.load(sys.stdin)
    model = load_model(checkpoint)
    processor = Sam3Processor.from_pretrained(str(checkpoint))
    # This MLX-VLM version otherwise falls back to a CLIP tokenizer from the global cache.
    processor._tokenizer = AutoTokenizer.from_pretrained(checkpoint, local_files_only=True)
    predictor = Sam3Predictor(model, processor, score_threshold=request["threshold"])
    directory = Path(request["artifact_dir"])
    with wired_limit(model):
        action = segment if request["task"] == "segment" else track
        result = action(predictor, request, directory)
    result.update({"backend": "sam3_mlx_bf16", "bbox_format": "xyxy_pixels",
                   "source": request["path"], "prompt": request["prompt"]})
    output.write_text(json.dumps(result, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
