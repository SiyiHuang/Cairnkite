"""Extract source spans with the locally pinned GLiNER checkpoint."""

import json
from pathlib import Path
import re
import sys

from gliner2 import AutoExtractor
from gliner2.processing.word_splitter import resolve_word_splitter


EAST_ASIAN_NO_SPACE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff\U00020000-\U000323af]")


def main() -> None:
    checkpoint, output = map(Path, sys.argv[1:])
    request = json.load(sys.stdin)
    model = AutoExtractor.from_pretrained(str(checkpoint), map_location="cpu", local_files_only=True)
    sources = request["texts"]
    grouped = {"whitespace": [], "char": []}
    for index, source in enumerate(sources):
        splitter = "char" if EAST_ASIAN_NO_SPACE.search(source) else "whitespace"
        grouped[splitter].append(index)
    predictions = {}
    for splitter, indices in grouped.items():
        if not indices:
            continue
        model.processor.word_splitter = resolve_word_splitter(splitter)
        batch = model.batch_extract_entities_long(
            [sources[index] for index in indices], request["labels"], threshold=request["threshold"],
            chunk_size=192, chunk_overlap=32, batch_size=4, include_confidence=True, include_spans=True,
        )
        predictions.update(zip(indices, batch, strict=True))
    documents = []
    for index, source in enumerate(sources):
        entities = predictions[index]["entities"]
        for matches in entities.values():
            for item in matches:
                start, end = item["start"], item["end"]
                if not (0 <= start < end <= len(source) and source[start:end] == item["text"]):
                    raise ValueError("GLiNER returned an entity with inconsistent source offsets.")
        documents.append({"entities": entities})
    output.write_text(json.dumps({"backend": "gliner_2_5_multi", "offset_unit": "unicode_code_points",
                                  "documents": documents}, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
