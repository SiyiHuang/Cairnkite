"""Separate a short recording into target and residual WAV files."""

import json
from pathlib import Path
import sys

import mlx.core as mx
from mlx_audio.audio_io import read
from mlx_audio.sts import SAMAudio, save_audio


def main() -> None:
    checkpoint, output = map(Path, sys.argv[1:])
    request = json.load(sys.stdin)
    model = SAMAudio.from_pretrained(checkpoint)
    rate = model.sample_rate
    # Read one extra sample to detect an input over the limit without decoding the full file.
    audio, _ = read(request["path"], sample_rate=rate, nchannels=1, duration=30 + 1 / rate)
    if not 0 < audio.size <= 30 * rate:
        raise ValueError("Use a nonempty recording of at most 30 seconds.")
    mx.random.seed(73)
    result = model.separate(
        audios=mx.array(audio.reshape(1, 1, -1)), descriptions=[request["description"]], ode_decode_chunk_size=50,
    )
    save_audio(result.target[0][:audio.size], request["target_wav"], sample_rate=rate)
    save_audio(result.residual[0][:audio.size], request["residual_wav"], sample_rate=rate)
    output.write_text(json.dumps({
        "backend": "sam_audio_small_mlx",
        "target_wav": request["target_wav"],
        "residual_wav": request["residual_wav"],
        "sample_rate": rate,
        "duration_s": audio.size / rate,
    }), encoding="utf-8")


if __name__ == "__main__":
    main()
