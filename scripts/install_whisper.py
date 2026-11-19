"""Install a pinned whisper.cpp CLI and verify its local model files."""
import argparse
import fcntl
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime"
COMMIT = "d1be6fde11ac6e0407606b4e42fe72d34add8037"
SOURCE = f"https://codeload.github.com/ggml-org/whisper.cpp/tar.gz/{COMMIT}"
SOURCE_SHA = "645445da884df6dbd52b30f82d7be7c01d1767c938714e477e786b88d529e9f4"
MODELS = (
    ("ggerganov/whisper.cpp", "5359861c739e955e79d9a303bcbc70fb988958b1",
     "ggml-large-v3-turbo-q8_0.bin", "317eb69c11673c9de1e1f0d459b253999804ec71ac4c23c17ecf5fbe24e259a1"),
    ("ggml-org/whisper-vad", "9ffd54a1e1ee413ddf265af9913beaf518d1639b",
     "ggml-silero-v6.2.0.bin", "2aa269b785eeb53a82983a20501ddf7c1d9c48e33ab63a41391ac6c9f7fb6987"),
)


def matches(path: Path, digest: str) -> bool:
    if not path.is_file():
        return False
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest() == digest


def fetch(url: str, target: Path, digest: str, reuse: Path | None = None) -> None:
    if matches(target, digest):
        return
    if reuse is not None and not matches(reuse, digest):
        raise SystemExit(f"Cannot reuse {reuse.name}. It must match the pinned SHA-256.")
    with tempfile.TemporaryDirectory(dir=target.parent) as staging:
        partial = Path(staging) / target.name
        if reuse is None:
            subprocess.run(["curl", "-fsSL", "--retry", "2", "-o", str(partial), url], check=True)
        else:
            shutil.copyfile(reuse, partial)
        if not matches(partial, digest):
            raise SystemExit(f"SHA-256 mismatch for {target.name}.")
        partial.replace(target)


def build(destination: Path) -> None:
    binary = destination / "whisper-cli"
    if os.access(binary, os.X_OK):
        return
    with tempfile.TemporaryDirectory(prefix="whisper-build-", dir=RUNTIME) as temp:
        stage = Path(temp)
        archive = stage / "source.tar.gz"
        fetch(SOURCE, archive, SOURCE_SHA)
        subprocess.run(["tar", "-xzf", str(archive), "-C", str(stage)], check=True)
        cmake = ["uv", "tool", "run", "--from", "cmake==4.4.5", "cmake"]
        output = stage / "build"
        subprocess.run([*cmake, "-S", str(stage / f"whisper.cpp-{COMMIT}"), "-B", str(output),
                        "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF",
                        "-DGGML_METAL=ON", "-DGGML_METAL_EMBED_LIBRARY=ON",
                        "-DWHISPER_BUILD_TESTS=OFF", "-DWHISPER_BUILD_EXAMPLES=ON"], check=True)
        subprocess.run([*cmake, "--build", str(output), "--target", "whisper-cli",
                        "--parallel", "6"], check=True)
        (output / "bin/whisper-cli").replace(binary)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reuse-from", type=Path, help="Directory containing both pinned GGML files")
    args = parser.parse_args()
    for program in ("uv", "ffmpeg"):
        if shutil.which(program) is None:
            parser.error(f"Install {program} and make it available on PATH.")
    runtime = RUNTIME / "whisper"
    model_dir = RUNTIME / "models/whisper"
    runtime.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    with (runtime / "install.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        build(runtime)
        for repo, revision, filename, digest in MODELS:
            reuse = args.reuse_from / filename if args.reuse_from else None
            fetch(f"https://huggingface.co/{repo}/resolve/{revision}/{filename}", model_dir / filename, digest, reuse)
            print(f"SHA-256 verified {filename}", flush=True)


if __name__ == "__main__":
    main()
