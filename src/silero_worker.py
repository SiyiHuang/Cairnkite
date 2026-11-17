"""Find speech intervals using Silero's 16 kHz sequential ONNX model."""
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import onnxruntime as ort


RATE = 16000
FRAME = 512
CONTEXT = 64
BLOCK = 512
MAX_DURATION = 1800


def decode(path):
    audio = subprocess.run([
        "ffmpeg", "-nostdin", "-v", "error", "-i", path, "-map", "0:a:0", "-t", str(MAX_DURATION + 1),
        "-ac", "1", "-ar", str(RATE), "-f", "f32le", "pipe:1",
    ], capture_output=True, check=False)
    if audio.returncode:
        raise ValueError(f"Cannot decode audio: {audio.stderr.decode(errors='replace').strip()}")
    data = np.frombuffer(audio.stdout, dtype="<f4")
    if not 0 < data.size <= RATE * MAX_DURATION:
        raise ValueError(f"Use audio with a duration greater than zero and at most {MAX_DURATION} seconds.")
    if not np.isfinite(data).all():
        raise ValueError("Decoded audio contains non-finite samples.")
    return data


def speech_probabilities(model, audio):
    options = ort.SessionOptions()
    options.inter_op_num_threads = options.intra_op_num_threads = 1
    session = ort.InferenceSession(str(model), sess_options=options, providers=["CPUExecutionProvider"])
    hidden = np.zeros((1, 1, 128), dtype=np.float32)
    cell = hidden.copy()
    previous = np.zeros(CONTEXT, dtype=np.float32)
    for offset in range(0, audio.size, FRAME * BLOCK):
        samples = audio[offset:offset + FRAME * BLOCK]
        frames = (samples.size + FRAME - 1) // FRAME
        chunk = np.zeros((frames, CONTEXT + FRAME), dtype=np.float32)
        chunk[0, :CONTEXT] = previous
        chunk[:, CONTEXT:] = np.pad(samples, (0, frames * FRAME - samples.size)).reshape(frames, FRAME)
        chunk[1:, :CONTEXT] = chunk[:-1, -CONTEXT:]
        previous = chunk[-1, -CONTEXT:].copy()
        values, hidden, cell = session.run(
            ["speech_probs", "hn", "cn"], {"input": chunk, "h": hidden, "c": cell},
        )
        yield from values.reshape(-1)


def speech_ranges(probabilities, length):
    start = quiet_since = None
    ranges = []
    for frame, probability in enumerate(probabilities):
        offset = frame * FRAME
        if start is None:
            if probability >= 0.50:
                start = offset
        elif probability >= 0.35:
            quiet_since = None
        else:
            if quiet_since is None:
                quiet_since = offset
            if offset + FRAME - quiet_since >= RATE * 0.10:
                ranges.append((start, quiet_since))
                start = quiet_since = None
    if start is not None:
        ranges.append((start, length))
    pad = round(RATE * 0.03)
    return [
        {"start_s": round(max(0, start - pad) / RATE, 4), "end_s": round(min(length, end + pad) / RATE, 4)}
        for start, end in ranges if end - start >= RATE * 0.25
    ]


def main():
    request = json.load(sys.stdin)
    audio = decode(request["path"])
    model_dir, output = map(Path, sys.argv[1:])
    model = model_dir / "silero_vad_16k_sequence.onnx"
    ranges = speech_ranges(speech_probabilities(model, audio), audio.size)
    result = {"backend": "silero_vad_16k", "source": request["path"], "duration_s": audio.size / RATE,
              "segment_unit": "speech_activity", "segments": ranges}
    output.write_text(json.dumps(result, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
