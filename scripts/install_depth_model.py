"""Download and compile Apple's pinned Depth Anything V2 Small FP16 package."""

import fcntl
import hashlib
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / ".runtime/models/depth-anything"
PACKAGE = "DepthAnythingV2SmallF16.mlpackage"
SOURCE = "https://huggingface.co/apple/coreml-depth-anything-v2-small/resolve/cfef6f6f2a70783dedc0bfae40cecbc2052285d3"
FILES = {
    "Manifest.json": "2883ae290c48fe916dc5ececac03a7d847fa277165a49ef5652fa1d2b9cb55f7",
    "Data/com.apple.CoreML/model.mlmodel": "44ac97a3efcfd52113183fb2862ff59cd0368e9ec2e30a90a54980dd11407042",
    "Data/com.apple.CoreML/weights/weight.bin": "fa60d9b6a155734f59029ebb882fd54e549bfaee3539c1a9cbd2cbbab64a0fed",
}


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def install() -> None:
    package = ASSETS / PACKAGE
    for relative, expected in FILES.items():
        path = package / relative
        if path.is_file() and checksum(path) == expected:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        part = path.with_suffix(path.suffix + ".part")
        subprocess.run(["curl", "-fsSL", "--retry", "2", "--continue-at", "-",
                        "-o", str(part), f"{SOURCE}/{PACKAGE}/{relative}"], check=True)
        if checksum(part) != expected:
            raise RuntimeError(f"Depth Anything resource checksum mismatch: {relative}")
        part.replace(path)
    compiled = ASSETS / "model.mlmodelc"
    if not compiled.is_dir():
        subprocess.run([str(ROOT / "native/.build/release/apple-specialists"), "compile-coreml", str(package), str(compiled)],
                       check=True)
    (ASSETS / ".verified").write_text("apple/coreml-depth-anything-v2-small@cfef6f6f2a70783dedc0bfae40cecbc2052285d3\n", encoding="utf-8")


if __name__ == "__main__":
    ASSETS.mkdir(parents=True, exist_ok=True)
    with (ASSETS / "install.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        install()
