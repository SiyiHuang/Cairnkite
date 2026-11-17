"""Recreate the project-local dependencies and verify the pinned artifacts."""

import argparse
import fcntl
import json
from pathlib import Path
import subprocess

from download_models import ROOT, checksum, selected_artifacts


def setup_runtime(reuse_from):
    runtime = json.loads((ROOT / "config/runtime.lock.json").read_text())
    runtime_dir = ROOT / ".runtime"
    runtime_dir.mkdir(exist_ok=True)
    archive = runtime_dir / runtime["url"].rsplit("/", 1)[-1]
    if not archive.exists():
        partial = archive.with_suffix(".partial")
        candidate = reuse_from / ".runtime" / archive.name if reuse_from else None
        if candidate and candidate.is_file():
            subprocess.run(["/bin/cp", "-c", str(candidate), str(partial)], check=True)
        else:
            subprocess.run(["curl", "-fsSL", "--retry", "2", "-o", str(partial), runtime["url"]], check=True)
        if checksum(partial) != runtime["sha256"]:
            raise RuntimeError(f"Checksum mismatch: {partial}")
        partial.replace(archive)
    if checksum(archive) != runtime["sha256"]:
        raise RuntimeError(f"Checksum mismatch: {archive}")
    unpacked = runtime_dir / f"llama-{runtime['version']}"
    binary = unpacked / "llama-server"
    if not binary.is_file() or not (unpacked / "llama-completion").is_file():
        subprocess.run(["tar", "-xzf", str(archive), "-C", str(runtime_dir)], check=True)
    version = subprocess.run([str(binary), "--version"], check=True, capture_output=True, text=True)
    if runtime["commit"][:9] not in version.stdout + version.stderr:
        raise RuntimeError(f"Unexpected installed runtime: {binary}")


def setup(models, reuse_from):
    for name in (".state", "logs", "inbox"):
        (ROOT / name).mkdir(mode=0o700, exist_ok=True)
    subprocess.run(["uv", "venv", "--allow-existing", "--python", "3.12", ".venv"],
                   cwd=ROOT, check=True)
    subprocess.run(["uv", "pip", "sync", "--python", ".venv/bin/python", "requirements.lock"],
                   cwd=ROOT, check=True)
    setup_runtime(reuse_from)
    command = [str(ROOT / ".venv/bin/python"), str(ROOT / "scripts/download_models.py"), *models]
    if reuse_from:
        command.extend(["--reuse-from", str(reuse_from)])
    subprocess.run(command, check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", nargs="*", default=["all"])
    parser.add_argument("--reuse-from", type=Path)
    parser.add_argument("--runtime-only", action="store_true", help="Install the shared llama.cpp binaries only.")
    options = parser.parse_args()
    try:
        selected_artifacts(options.models)
        reuse_from = options.reuse_from.resolve(strict=True) if options.reuse_from else None
    except (ValueError, FileNotFoundError) as error:
        parser.error(str(error))
    (ROOT / ".runtime").mkdir(exist_ok=True)
    with (ROOT / ".runtime/setup.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if options.runtime_only:
            setup_runtime(reuse_from)
        else:
            setup(options.models, reuse_from)
