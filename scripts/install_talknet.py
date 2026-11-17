"""Install the pinned TalkNet fork and check both checkpoints before use."""
import fcntl
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile


REVISION = "ac6bbdf175d57500e9f9c3fb1bb12779242d2b95"
SFD_PATH = Path("source/model/faceDetector/s3fd/sfd_face.pth")


def digest_matches(path, expected):
    if not path.is_file():
        return False
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest() == expected


def ensure_file(path, digest, download):
    if digest_matches(path, digest):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".download-", dir=path.parent) as temp:
        pending = Path(temp) / path.name
        subprocess.run([*download, str(pending)], check=True)
        if not digest_matches(pending, digest):
            raise SystemExit(f"Unexpected SHA-256 for {path.name}")
        pending.replace(path)


def install(root):
    marker = root / ".verified"
    marker.unlink(missing_ok=True)
    archive = root / "source.tar.gz"
    curl = ["/usr/bin/curl", "-fsSL", "--max-time", "300", "--retry", "2"]
    ensure_file(archive, "67860b1555d2bef946b681618ab37013abb14ad20b1d09606043ac8700dea400",
                [*curl, f"https://codeload.github.com/nawta/TalkNet-ASD-py312/tar.gz/{REVISION}", "-o"])
    source = root / "source"
    if not source.exists():
        with tempfile.TemporaryDirectory(prefix=".source-", dir=root) as temp:
            with tarfile.open(archive, "r:gz") as bundle:
                prefix = bundle.getmembers()[0].name
                bundle.extractall(temp, filter="data")
            (Path(temp) / prefix).replace(source)
    ensure_file(root / SFD_PATH, "d54a87c2b7543b64729c9a25eafd188da15fd3f6e02f0ecec76ae1b30d86c491",
                [*curl, "https://huggingface.co/nawta/syncnet/resolve/main/sfd_face.pth", "-o"])
    ensure_file(root / "talkset.model", "d985ddd07dca08864a28337726f5b7d91b6426bebc7327f0e9b21cf9ff1cc937",
                [str(Path(sys.executable).with_name("gdown")), "1AbN9fCf9IexMxEKXLQY2KYBlb-IhSEea", "-O"])
    marker.write_text(REVISION + "\n", encoding="utf-8")


if __name__ == "__main__":
    if not shutil.which("ffmpeg"):
        raise SystemExit("TalkNet requires ffmpeg on PATH.")
    root = Path(sys.argv[1]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".install.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        install(root)
