"""Score typed decisions with the pinned MLX Clef joint head."""
import json
from pathlib import Path
import runpy
import sys

from PIL import Image, ImageOps


def main():
    model_dir, output = map(Path, sys.argv[1:])
    request = json.load(sys.stdin)
    image_path = request.pop("image_path", None)
    if image_path:
        with Image.open(image_path) as image:
            if image.width * image.height > 12_000_000:
                raise ValueError("Use an image of at most 12 megapixels.")
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            request["images"] = [image]
    request["model"] = "clef-flash-4bit"
    for question in request["questions"].values():
        if question["type"] == "binary":
            question["type"] = "noul"
    loader = runpy.run_path(str(model_dir / "clef_mlx.py"))["load"]
    result = loader(model_dir).systemone(request, truncate=False)
    for name, answer in result["answers"].items():
        if answer["type"] == "noul":
            probability = answer["noul"]
            result["answers"][name] = {"type": "binary", "probability_true": probability,
                                       "probability_false": round(1 - probability, 4)}
    result["backend"] = "clef_flash_4bit"
    output.write_text(json.dumps(result, ensure_ascii=False, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
