"""Download the approved official artifacts, pinned to revisions and SHA-256."""

import argparse
import concurrent.futures
import configparser
import hashlib
import json
from pathlib import Path
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/models.lock.json"
SELECTION = {
    "LFM3-1.7B-GGUF": ["LFM3-1.7B-BF16.gguf", "LFM3-1.7B-Q4_K_M.gguf"],
    "LFM2.5-8B-A1B-GGUF": ["LFM2.5-8B-A1B-Q8_0.gguf"],
    "LFM2.5-24B-A2B-GGUF": [
        "LFM2.5-24B-A2B-Q8_0.gguf", "LFM2.5-24B-A2B-Q4_K_M.gguf"
    ],
    "LFM3-VL-2B-GGUF": ["LFM3-VL-2B-BF16.gguf", "mmproj-LFM3-VL-2B-BF16.gguf"],
}


def checksum(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def lock_models():
    artifacts = []
    for repo, filenames in SELECTION.items():
        url = f"https://huggingface.co/api/models/LiquidAI/{repo}?blobs=true"
        with urllib.request.urlopen(url, timeout=30) as response:
            metadata = json.load(response)
        siblings = {f["rfilename"]: f for f in metadata["siblings"]}
        for filename in filenames:
            entry = siblings[filename]
            artifacts.append({
                "repo": f"LiquidAI/{repo}", "revision": metadata["sha"],
                "file": filename, "size": entry["size"],
                "sha256": entry["lfs"]["sha256"],
                "path": f"models/{repo}/{filename}",
            })
    MANIFEST.write_text(json.dumps({"artifacts": artifacts}, indent=2) + "\n")


def acquire(entry):
    path = ROOT / entry["path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size == entry["size"]:
        if checksum(path) == entry["sha256"]:
            print(f"Verified existing {entry['file']}", flush=True)
            return
        raise RuntimeError(f"Checksum mismatch on existing {path}")
    partial = path.with_suffix(path.suffix + ".partial")
    hub = (f"https://huggingface.co/{entry['repo']}/resolve/"
           f"{entry['revision']}/{entry['file']}?download=true")
    # The registry serves the exact same content-addressed LiquidAI GGUF bytes.
    registry = f"https://registry.ollama.ai/v2/library/lfm2.5/blobs/sha256:{entry['sha256']}"
    print(f"Downloading {entry['file']} ({entry['size'] / 1e9:.2f} GB)", flush=True)
    for attempt, url in enumerate((registry, registry, hub, registry, hub)):
        if partial.is_file() and partial.stat().st_size >= entry["size"]:
            break
        if attempt:
            time.sleep(2)
        transfer = subprocess.run([
            "curl", "--fail", "--location", "--silent", "--show-error", "--http1.1",
            "--connect-timeout", "25", "--speed-time", "90", "--speed-limit", "32768",
            "--continue-at", "-", "--output", str(partial), url,
        ])
        if transfer.returncode == 0:
            break
    if not partial.is_file():
        raise RuntimeError(f"No bytes received: {entry['file']}")
    if partial.stat().st_size != entry["size"] or checksum(partial) != entry["sha256"]:
        raise RuntimeError(f"Downloaded artifact failed validation: {partial}")
    partial.replace(path)
    print(f"SHA-256 verified {entry['file']}", flush=True)


def selected_artifacts(models):
    entries = json.loads(MANIFEST.read_text())["artifacts"]
    if "all" in models:
        return entries
    preset = configparser.ConfigParser()
    preset.read_string("[metadata]\n" + (ROOT / "config/models.ini").read_text())
    selected = set(models)
    if "default" in selected:
        selected.remove("default")
        selected.update({"lfm-fast", "lfm-vision"})
    unknown = selected - (set(preset.sections()) - {"metadata", "*"})
    if unknown:
        raise ValueError(f"Unknown LFM model selection: {', '.join(sorted(unknown))}")
    selected.add("lfm-fast")
    paths = {value for name in selected for key, value in preset[name].items() if key in {"model", "mmproj"}}
    locked = {entry["path"]: entry for entry in entries}
    return [locked[path] for path in sorted(paths)]


def reuse(entry, source):
    dest = ROOT / entry["path"]
    candidate = source / entry["path"]
    if dest.exists() or not candidate.is_file() or candidate.stat().st_size != entry["size"]:
        return
    partial = dest.with_suffix(dest.suffix + ".partial")
    if partial.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    # The normal acquisition path checks and promotes these bytes before use.
    subprocess.run(["/bin/cp", "-c", str(candidate), str(partial)], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", nargs="*", default=["all"])
    parser.add_argument("--reuse-from", type=Path, help="Existing LFM root with the same pinned artifacts.")
    args = parser.parse_args()
    if not MANIFEST.exists():
        lock_models()
    try:
        entries = selected_artifacts(args.models)
    except ValueError as error:
        parser.error(str(error))
    if args.reuse_from:
        for entry in entries:
            reuse(entry, args.reuse_from.resolve(strict=True))
    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as pool:
        for future in concurrent.futures.as_completed([pool.submit(acquire, entry) for entry in entries]):
            future.result()
