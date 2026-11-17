"""Run local MOSS transcription with anonymous speaker identifiers."""
import json
import math
from pathlib import Path
import sys

import av
from moss_transcribe_diarize import parse_transcript
from moss_transcribe_diarize.mlx import load_model

path, model, output = map(Path, sys.argv[1:])
with av.open(str(path)) as media:
    stream = media.streams.audio[0]
    duration = float(stream.duration * stream.time_base) if stream.duration else (
        media.duration / av.time_base if media.duration else 0
    )
if not math.isfinite(duration) or not 0 < duration <= 1800:
    raise ValueError("MOSS expects an audio file with a known duration of 0 to 1800 seconds.")
model = load_model(model, strict=True)
max_tokens = min(8192, max(512, math.ceil(duration * 16)))
generated = model.generate(str(path), max_tokens=max_tokens, temperature=0.0)
segments = []
for item in parse_transcript(generated.text):
    start, end = float(item.start), float(item.end)
    if math.isfinite(start) and math.isfinite(end) and 0 <= start <= end:
        segments.append({"start_s": start, "end_s": end, "speaker": item.speaker, "text": item.text})
output.write_text(json.dumps({
    "backend": "moss_mlx_8bit",
    "source": str(path),
    "duration_s": duration,
    "segments": segments,
    "generated_tokens": generated.generation_tokens,
    "token_limit": max_tokens,
    "may_be_truncated": generated.generation_tokens >= max_tokens,
}, ensure_ascii=False), encoding="utf-8")
