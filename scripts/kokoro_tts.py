"""Render one local Kokoro voice as a PCM WAV file."""
from pathlib import Path
import sys

from mlx_audio.tts.utils import load
import numpy as np
import soundfile as sf
import spacy


model_dir, voice, speed, output = sys.argv[1:]
language = voice[0]
if language == "a" and not spacy.util.is_package("en_core_web_sm"):
    raise SystemExit("Install the pinned English spaCy resources with bin/install kokoro.")

model = load(Path(model_dir), model_type="kokoro")
with sf.SoundFile(output, mode="w", samplerate=model.sample_rate, channels=1, subtype="PCM_16") as wav:
    for segment in model.generate(sys.stdin.read(), voice=voice, lang_code=language, speed=float(speed)):
        wav.write(np.asarray(segment.audio, dtype=np.float32))
