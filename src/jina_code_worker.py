"""Rank explicit source files with the pinned Jina MLX code embedding model."""
import json
from pathlib import Path
import runpy
import sys

import mlx.core as mx
from tokenizers import Tokenizer


def source_blocks(path):
    """Keep contiguous line spans and cap each embedding's source payload."""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = 0
    while start < len(lines):
        end = start
        length = 0
        while end < min(start + 40, len(lines)):
            line_length = len(lines[end]) + 1
            if end > start and length + line_length > 2000:
                break
            length += line_length
            end += 1
        excerpt = "\n".join(lines[start:end])
        if excerpt.strip():
            for offset in range(0, len(excerpt), 2000):
                yield start + 1, end, excerpt[offset:offset + 2000]
        start = end


def main():
    model_dir, output = map(Path, sys.argv[1:])
    request = json.load(sys.stdin)
    blocks = [(path, start, end, excerpt) for path in map(Path, request["files"])
              for start, end, excerpt in source_blocks(path)]
    if not blocks:
        output.write_text(json.dumps({"backend": "jina-code-05", "results": []}), encoding="utf-8")
        return

    model_type = runpy.run_path(str(model_dir / "model.py"))["JinaCodeEmbeddingModel"]
    model = model_type(json.loads((model_dir / "config.json").read_text(encoding="utf-8")))
    model.load_weights(list(mx.load(str(model_dir / "model.safetensors")).items()))
    tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
    query = model.encode([request["query"]], tokenizer, task="nl2code").astype(mx.float32)[0]
    hits = []
    for start in range(0, len(blocks), 8):
        batch = blocks[start:start + 8]
        embedded = model.encode([item[3] for item in batch], tokenizer, max_length=1024,
                                task="nl2code", prompt_type="passage")
        scores = (embedded.astype(mx.float32) @ query).tolist()
        hits.extend(
            {"path": str(path), "line_start": first, "line_end": last, "score": score,
             "snippet": excerpt[:400]}
            for (path, first, last, excerpt), score in zip(batch, scores, strict=True)
        )
    hits.sort(key=lambda hit: -hit["score"])
    output.write_text(json.dumps({"backend": "jina-code-05", "results": hits[:request["limit"]]},
                                 ensure_ascii=False, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
