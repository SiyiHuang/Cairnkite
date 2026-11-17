"""Use a local Hy-MT2 snapshot for translation with optional terminology hints."""
import json
from pathlib import Path
import sys

from mlx_lm import load, stream_generate
from mlx_lm.sample_utils import make_sampler


def translate(snapshot: Path, request: dict) -> dict:
    model, tokenizer = load(str(snapshot))
    target = request["target_name"]
    glossary = request["glossary"]
    hints = ""
    if glossary:
        hints = "Use these translations where the terms occur:\n" + "\n".join(
            f"{json.dumps(term, ensure_ascii=False)} translates to {json.dumps(rendering, ensure_ascii=False)}"
            for term, rendering in glossary.items()
        ) + "\n\n"
    translations, truncated = [], []
    for text in request["texts"]:
        source = request["source_name"]
        message = f"{hints}Translate the following text from {source} into {target}. Output only the translation.\n\n{text}"
        prompt = tokenizer.apply_chat_template(
            [{"role": "user", "content": message}], tokenize=False, add_generation_prompt=True,
        )
        parts = []
        finish_reason = None
        for response in stream_generate(model, tokenizer, prompt, max_tokens=1536, sampler=make_sampler(temp=0.0)):
            parts.append(response.text)
            finish_reason = response.finish_reason
        translations.append("".join(parts).strip())
        truncated.append(finish_reason == "length")
    return {
        "backend": "hy_mt2_1_8b_8bit", "source_language": request["source_language"],
        "target_language": request["target_language"], "translations": translations, "truncated": truncated,
    }


snapshot, output = map(Path, sys.argv[1:])
result = translate(snapshot, json.load(sys.stdin))
output.write_text(json.dumps(result, ensure_ascii=False, allow_nan=False), encoding="utf-8")
