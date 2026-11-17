"""Install the official Omni Small release assets without opening the setup window."""

from concurrent.futures import ThreadPoolExecutor
import fcntl
import hashlib
from pathlib import Path
import shutil
import subprocess


RELEASE = "https://github.com/hanxiao/omni-macos/releases/download/embed-weights-v1"
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".runtime/omni-small"
DESTINATION = Path.home() / "Library/Application Support/Omni/small"
SUPPORT_FILES = {
    "config.json": "8074de43ca910f2a1922be18664268a101531813bc41d3a96f80d55695b8749c",
    "tokenizer.json": "7bbf567d9e053a72f0bd8ea475e672d10d537578f6adb521ab42da2badfa8bef",
    "tokenizer_config.json": "b78dba953d672b6e7e73276b47644527c5e8c59036d78ffb1abd9617187b95ee",
}
PARTS = {
    "model.safetensors.part1": "316ef0a3b8f079a92d7102b2974bdf918943d6f00ded942d8754611a5b534651",
    "model.safetensors.part2": "00b18586c5f45d5276a70fcefc6e7d9e0553582b0e85d6b43541fe3f90f9acce",
}
PART_BYTES = {"model.safetensors.part1": 1_900_000_000, "model.safetensors.part2": 1_218_851_470}
TRANSFER_BYTES = 32 * 1024 * 1024
WEIGHTS_DIGEST = "9f338be199dcd3f99e3d35d5f54c8da47d06b562fee91748464a4c803ecc75b5"


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(16 * 1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def fetch(entry):
    name, expected = entry
    path = CACHE / name
    if path.is_file() and digest(path) == expected:
        return path
    partial = path.with_name(path.name + ".partial")
    url = f"{RELEASE}/small-{name}"
    if name in PART_BYTES:
        fetch_ranges(url, partial, PART_BYTES[name])
    else:
        subprocess.run(["curl", "--http1.1", "-fsSL", "--retry", "2", "--output", str(partial), url], check=True)
    if digest(partial) != expected:
        raise RuntimeError(f"Pinned Omni asset failed SHA-256 validation: {partial}")
    partial.replace(path)
    print(f"Verified {name}", flush=True)
    return path


def fetch_ranges(url, partial, size):
    offset = partial.stat().st_size if partial.exists() else 0
    if offset > size:
        raise RuntimeError(f"Partial file exceeds the expected size: {partial}")
    segment = partial.with_suffix(".segment")
    try:
        while offset < size:
            end = min(size, offset + TRANSFER_BYTES) - 1
            transfer = subprocess.run(
                ["curl", "--http1.1", "-fsSL", "--connect-timeout", "15", "--max-time", "85",
                 "--retry", "2", "--retry-all-errors", "--range", f"{offset}-{end}",
                 "--output", str(segment), "--write-out", "%{http_code} %header{content-range}", url],
                check=True, stdout=subprocess.PIPE, text=True,
            )
            status, _, content_range = transfer.stdout.strip().partition(" ")
            if status != "206" or content_range != f"bytes {offset}-{end}/{size}":
                raise RuntimeError(f"Invalid HTTP range for {partial.name} at byte {offset}")
            if segment.stat().st_size != end - offset + 1:
                raise RuntimeError(f"Truncated HTTP range for {partial.name} at byte {offset}")
            with partial.open("ab") as target, segment.open("rb") as source:
                shutil.copyfileobj(source, target, length=TRANSFER_BYTES)
            offset = end + 1
            print(f"{partial.name}: {offset:,}/{size:,} bytes", flush=True)
    finally:
        segment.unlink(missing_ok=True)


def install():
    if DESTINATION.exists():
        files = {**SUPPORT_FILES, "model.safetensors": WEIGHTS_DIGEST}
        if all((DESTINATION / name).is_file() and digest(DESTINATION / name) == sha for name, sha in files.items()):
            print(f"Omni Small is verified at {DESTINATION}")
            return
        raise SystemExit(f"Omni Small already has files at {DESTINATION}. Keep using that model or choose its install directory explicitly in Omni.")

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(fetch, {**SUPPORT_FILES, **PARTS}.items()))

    stage = CACHE / "install"
    stage.mkdir(exist_ok=True)
    for name in SUPPORT_FILES:
        shutil.copyfile(CACHE / name, stage / name)
    weights = stage / "model.safetensors"
    with weights.open("wb") as combined:
        for name in PARTS:
            with (CACHE / name).open("rb") as part:
                shutil.copyfileobj(part, combined, length=16 * 1024 * 1024)
    if digest(weights) != WEIGHTS_DIGEST:
        raise RuntimeError("Combined Omni model failed SHA-256 validation")
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    stage.rename(DESTINATION)
    for name in (*SUPPORT_FILES, *PARTS):
        (CACHE / name).unlink()
    print(f"Installed verified Omni Small at {DESTINATION}")


if __name__ == "__main__":
    CACHE.mkdir(parents=True, exist_ok=True)
    with (CACHE / "install.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        install()
