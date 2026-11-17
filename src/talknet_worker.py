"""Run the pinned TalkNet demo with simple private filenames and summarize active face spans."""
import json
from pathlib import Path
import pickle
import shutil
import subprocess
import sys

import cv2
import numpy as np


def active_spans(tracks, scores, start, width, height):
    spans = []
    for track_id, (entry, values) in enumerate(zip(tracks, scores, strict=True)):
        track = entry["track"]
        if len(values) > len(track["frame"]):
            raise ValueError("TalkNet emitted more scores than frames.")
        frames = track["frame"][:len(values)]
        positive = np.flatnonzero(np.asarray(values) >= 0)
        runs = np.split(positive, np.flatnonzero(np.diff(positive) != 1) + 1)
        for run in runs:
            if len(run) == 0:
                continue
            first, last = int(run[0]), int(run[-1])
            mid = (first + last) // 2
            spans.append({
                "track_id": track_id,
                "start_s": round(start + int(frames[first]) / 25, 3),
                "end_s": round(start + (int(frames[last]) + 1) / 25, 3),
                "bbox": [round(float(np.clip(x, 0, limit)), 2)
                         for x, limit in zip(track["bbox"][mid], (width, height, width, height), strict=True)],
                "mean_talknet_score": round(float(np.mean(np.asarray(values)[run])), 3),
            })
    return sorted(spans, key=lambda span: (span["start_s"], span["track_id"]))


def main():
    model_dir, output = map(Path, sys.argv[1:])
    request = json.load(sys.stdin)
    work = output.parent
    checkpoint = model_dir / "talkset.model"
    if not checkpoint.is_file() or not (model_dir / "source/model/faceDetector/s3fd/sfd_face.pth").is_file():
        raise ValueError("Reinstall the pinned TalkNet checkpoints.")
    # Upstream passes a few working filenames through a shell. Only relative,
    # fixed names enter those commands, even when the source path contains spaces.
    path = Path(request["path"])
    (work / ("clip" + path.suffix.lower())).symlink_to(path)
    subprocess.run([
        sys.executable, str(model_dir / "source/demoTalkNet.py"),
        "--videoName", "clip", "--videoFolder", ".", "--pretrainModel", str(checkpoint),
        "--device", request["device"], "--start", str(request["start"]),
        "--duration", str(request["duration"]), "--nDataLoaderThread", "2",
    ], cwd=work, check=True)
    result = work / "clip"
    annotation = result / "pyavi/video_out.avi"
    capture = cv2.VideoCapture(str(annotation))
    try:
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    finally:
        capture.release()
    if count <= 0 or width <= 0 or height <= 0:
        raise ValueError("TalkNet did not produce a playable annotation.")
    with (result / "pywork/tracks.pckl").open("rb") as file:
        tracks = pickle.load(file)
    with (result / "pywork/scores.pckl").open("rb") as file:
        scores = pickle.load(file)
    spans = active_spans(tracks, scores, request["start"], width, height)
    shutil.copyfile(annotation, request["annotated_avi"])
    output.write_text(json.dumps({
        "backend": "talknet", "source": str(path), "device": request["device"],
        "tracks": len(tracks), "frames": count, "analysis_fps": 25, "bbox_format": "xyxy_pixels",
        "segments": spans, "annotated_avi": request["annotated_avi"],
    }, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
