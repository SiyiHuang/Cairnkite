"""Independent MiniCPM OCR and Jev scoring over local images."""
import json
from pathlib import Path
import sys

from mlx_vlm import generate, load
from mlx_vlm.models.minicpm_ocr_jev import score
from mlx_vlm.prompt_utils import apply_chat_template

model_path, output = map(Path, sys.argv[1:])
request = json.load(sys.stdin)
model, processor = load(str(model_path))

if request["operation"] == "document":
    prompt = apply_chat_template(processor, model.config, "Convert this page to markdown.", num_images=1)
    generated = generate(
        model, processor, prompt, image=[request["image"]], max_tokens=4096, temperature=0.0,
    )
    result = {
        "backend": "minicpm_ocr_1_0_8bit", "text": generated.text,
        "generated_tokens": generated.generation_tokens, "may_be_truncated": generated.generation_tokens >= 4096,
    }
else:
    scores = score(model, processor, request["original"], request["rendered"], request["text"])
    result = {
        "backend": "minicpm_ocr_jev_8bit", "probability_consistent": scores["prob_1"],
        "probability_inconsistent": scores["prob_0"],
    }

output.write_text(json.dumps(result, ensure_ascii=False, allow_nan=False), encoding="utf-8")
