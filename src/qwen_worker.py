"""Qwen speech recognition or alignment using pinned local snapshots."""
import json
from pathlib import Path
import subprocess
import sys
import wave

import numpy as np
from mlx_qwen3_asr import transcribe
from mlx_qwen3_asr.forced_aligner import ForcedAligner


def read_audio(path: Path, limit: int) -> np.ndarray:
    if path.suffix.lower() == ".wav":
        try:
            with wave.open(str(path), "rb") as stream:
                if stream.getnchannels() == 1 and stream.getframerate() == 16000 and stream.getsampwidth() == 2:
                    return np.frombuffer(stream.readframes(limit * 16000 + 1), "<i2").astype(np.float32) / 32768
        except wave.Error:
            pass
    demuxer = {".aiff": "aiff", ".aif": "aiff", ".m4a": "mov"}.get(path.suffix.lower(), path.suffix.lower()[1:])
    raw = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-protocol_whitelist", "file,pipe", "-f", demuxer, "-i", str(path),
         "-map", "0:a:0", "-t", str(limit + 0.01), "-f", "s16le", "-ac", "1", "-ar", "16000", "pipe:1"],
        check=True, stdout=subprocess.PIPE,
    ).stdout
    return np.frombuffer(raw, "<i2").astype(np.float32) / 32768


models, output = map(Path, sys.argv[1:])
request = json.load(sys.stdin)
limit = 120 if "text" in request else 1800
audio = read_audio(Path(request["path"]), limit)
duration = audio.size / 16000
aligner = str(models / "qwen-align")
if duration <= 0 or duration > limit:
    raise ValueError("Use at most 120 seconds for direct alignment or 30 minutes for transcription.")

if "text" in request:
    words = ForcedAligner(model_path=aligner).align(audio, request["text"], request["language"])
    result = {
        "backend": "qwen3_forced_aligner", "language": request["language"],
        "segments": [
            {"text": word.text, "start_s": word.start_time, "end_s": word.end_time}
            for word in words
        ],
    }
else:
    variant = request["variant"]
    checkpoint, size = ("qwen-large", "1_7b") if variant == "qwen-large" else ("qwen-asr", "0_6b")
    transcription = transcribe(
        audio, model=str(models / checkpoint), language=request.get("language"),
        return_timestamps=True, forced_aligner=aligner,
    )
    result = {
        "backend": f"qwen3_asr_{size}_8bit", "language": transcription.language,
        "text": transcription.text, "may_be_truncated": transcription.truncated,
        "segments": [
            {"text": segment["text"], "start_s": segment["start"], "end_s": segment["end"]}
            for segment in (transcription.segments or [])
        ],
    }

result.update({"source": request["path"], "duration_s": duration, "segment_unit": "word_or_language_token"})
output.write_text(json.dumps(result, ensure_ascii=False, allow_nan=False), encoding="utf-8")
