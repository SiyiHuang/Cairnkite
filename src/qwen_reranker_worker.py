"""Use Qwen's official rerank prompt and binary score on MLX."""
import json
from pathlib import Path
import sys

import mlx.core as mx
from mlx_vlm import load
from mlx_vlm.utils import prepare_inputs
from PIL import Image, ImageOps


def load_image(path):
    with Image.open(path) as original:
        if original.width * original.height > 28_000_000:
            raise ValueError("Resize candidate images to at most 28 megapixels.")
        image = ImageOps.exif_transpose(original).convert("RGB")
    image.thumbnail((1344, 1344), Image.Resampling.LANCZOS)
    return image


def main():
    model_dir, output = map(Path, sys.argv[1:])
    request = json.load(sys.stdin)
    model, processor = load(str(model_dir))
    tokenizer = processor.tokenizer
    template = (model_dir / "additional_chat_templates/reranker.jinja").read_text(encoding="utf-8")
    yes, no = (tokenizer.get_vocab()[word] for word in ("yes", "no"))
    scores = []
    for candidate in request["candidates"]:
        images = [load_image(candidate["image"])] if candidate.get("image") else None
        document = [{"type": "image"}] if images else []
        if candidate.get("text"):
            document.append({"type": "text", "text": candidate["text"]})
        prompt = tokenizer.apply_chat_template([
            {"role": "query", "content": request["query"]},
            {"role": "document", "content": document},
        ], chat_template=template, tokenize=False, add_generation_prompt=True)
        inputs = prepare_inputs(processor, images=images, prompts=prompt)
        ids = inputs.pop("input_ids")
        mask = inputs.pop("attention_mask", None)
        result = model(ids, mask=mask, **inputs)
        logits = result.logits[0, -1].astype(mx.float32)
        scores.append(mx.sigmoid(logits[yes] - logits[no]).item())
    output.write_text(json.dumps({"backend": "qwen3-vl-reranker-2b", "scores": scores}, allow_nan=False),
                      encoding="utf-8")


if __name__ == "__main__":
    main()
