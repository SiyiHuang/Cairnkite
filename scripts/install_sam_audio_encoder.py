"""Prepare the pinned T5 assets SAM-Audio resolves by its original repo alias."""

import fcntl
import hashlib
from pathlib import Path
import sys

from huggingface_hub import snapshot_download


REVISION = "a9723ea7f1b39c1eae772870f3b547bf6ef7e6c1"
WEIGHTS_DIGEST = "a90903540cc02cbeb7ff9f823f1a80eb778c7e22426a0e620b01c77a5ec8f5b4"


def install(cache: Path) -> None:
    snapshot = Path(snapshot_download(
        "google-t5/t5-base", revision=REVISION, cache_dir=cache, token=False,
        allow_patterns=["config.json", "model.safetensors", "spiece.model", "tokenizer.json"],
    ))
    with (snapshot / "model.safetensors").open("rb") as weights:
        if hashlib.file_digest(weights, "sha256").hexdigest() != WEIGHTS_DIGEST:
            raise SystemExit("Unexpected T5 encoder weight digest.")
    repo = snapshot.parents[1]
    refs = repo / "refs"
    refs.mkdir(exist_ok=True)
    pending = refs / "local-toolkit-main"
    pending.write_text(REVISION, encoding="utf-8")
    pending.replace(refs / "main")
    alias = cache / "models--t5-base"
    if not alias.is_symlink() and not alias.exists():
        alias.symlink_to(repo.name, target_is_directory=True)
    if alias.resolve() != repo.resolve():
        raise SystemExit(f"Conflicting T5 cache entry at {alias}")
    (cache / ".verified").write_text(REVISION + "\n", encoding="utf-8")


if __name__ == "__main__":
    location = Path(sys.argv[1]).resolve()
    location.mkdir(parents=True, mode=0o700, exist_ok=True)
    with (location / "install.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        install(location)
