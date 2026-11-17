"""Emit Qwen3-ASR partial and final transcripts from a live PCM pipe."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import BinaryIO, Iterator

import numpy as np
from mlx_qwen3_asr.streaming import feed_audio, finish_streaming, init_streaming, streaming_metrics


SAMPLE_RATE = 16000
SAMPLE_BYTES = 2
MAX_REPLAY_SECONDS = 30 * 60


def transcribe_stream(source: BinaryIO, model: Path, chunk_seconds: float, language: str | None) -> Iterator[dict]:
    state = init_streaming(model=str(model), sample_rate=SAMPLE_RATE,
                           chunk_size_sec=chunk_seconds, language=language)
    total_samples = 0
    chunk_bytes = state.chunk_size_samples * SAMPLE_BYTES
    while data := source.read(chunk_bytes):
        if len(data) % SAMPLE_BYTES:
            raise ValueError("PCM input ended with an incomplete 16-bit sample.")
        pcm = np.frombuffer(data, dtype="<i2")
        total_samples += pcm.size
        previous_chunk = state.chunk_id
        state = feed_audio(pcm, state)
        if state.chunk_id != previous_chunk:
            yield {"event": "partial", "audio_seconds": total_samples / SAMPLE_RATE,
                   "text": state.text, "stable_text": state.stable_text}
    state = finish_streaming(state)
    yield {"event": "final", "audio_seconds": total_samples / SAMPLE_RATE, "text": state.text,
           "language": state.language, "metrics": streaming_metrics(state)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Read 16 kHz mono s16le PCM from stdin and emit NDJSON transcripts.")
    parser.add_argument("model", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--language", help="Pass a supported Qwen language, or omit to detect it.")
    parser.add_argument("--chunk-seconds", type=float, default=2.0)
    parser.add_argument("--file", type=Path, help="Decode an existing recording and replay its chunks with ffmpeg.")
    args = parser.parse_args()
    if not 0.5 <= args.chunk_seconds <= 5:
        parser.error("--chunk-seconds must be between 0.5 and 5.")
    if args.file is None and sys.stdin.isatty():
        parser.error("Pipe raw PCM from your audio source. For WAV, decode it with ffmpeg first.")
    if args.file is None:
        for event in transcribe_stream(sys.stdin.buffer, args.model, args.chunk_seconds, args.language):
            print(json.dumps(event, ensure_ascii=False), flush=True)
        return
    with subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-protocol_whitelist", "file,pipe", "-i", str(args.file),
                           "-map", "0:a:0", "-t", str(MAX_REPLAY_SECONDS + 0.01), "-ac", "1", "-ar", str(SAMPLE_RATE),
                           "-f", "s16le", "-"],
                          stdout=subprocess.PIPE) as decoder:
        try:
            for event in transcribe_stream(decoder.stdout, args.model, args.chunk_seconds, args.language):
                if event["event"] == "final":
                    if decoder.wait() != 0:
                        raise ValueError("ffmpeg could not decode the input audio.")
                    if not 0 < event["audio_seconds"] <= MAX_REPLAY_SECONDS:
                        raise ValueError("Replay requires a nonempty recording of at most 30 minutes.")
                print(json.dumps(event, ensure_ascii=False), flush=True)
        finally:
            if decoder.poll() is None:
                decoder.terminate()


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(1)
    except ValueError as error:
        sys.exit(str(error))
