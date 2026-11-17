"""Run and manage the login-scoped, loopback-only LFM inference server."""

import argparse
import configparser
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys

from download_models import checksum

ROOT = Path(__file__).resolve().parents[1]
LABEL = "local.lfm.inference"
DOMAIN = f"gui/{os.getuid()}"
PLIST = Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"
INSTALL = Path.home() / "Library/Application Support/Local LFM"


def launchctl(*args, check=True):
    return subprocess.run(["/bin/launchctl", *args], check=check)


def job_loaded():
    return subprocess.run(["/bin/launchctl", "print", f"{DOMAIN}/{LABEL}"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def arguments(base):
    runtime = json.loads((ROOT / "config/runtime.lock.json").read_text())
    binary = base / ".runtime" / f"llama-{runtime['version']}" / "llama-server"
    return ["/usr/bin/sandbox-exec", "-f", str(base / "config/server-network.sb"),
            str(binary), "--host", "127.0.0.1", "--port", "8080", "--offline",
            "--models-preset", str(base / "config/models.ini"), "--models-max", "4",
            "--cors-origins", "localhost", "--no-ui", "--no-slots", "--log-verbosity", "3"]


def environment(base):
    cache = base / ".state/llama-cache"
    cache.mkdir(parents=True, exist_ok=True)
    return {"PATH": "/usr/bin:/bin", "HOME": str(Path.home()), "LLAMA_CACHE": str(cache)}


def cached_model_matches(path, entry):
    try:
        return (path.is_file() and path.stat().st_size == entry["size"]
                and checksum(path) == entry["sha256"])
    except OSError:
        return False


def preset_for_available_models(partial, *, reuse_staged=False):
    config = configparser.ConfigParser()
    config.read_string("[metadata]\n" + (ROOT / "config/models.ini").read_text())
    del config["metadata"]
    manifest = json.loads((ROOT / "config/models.lock.json").read_text())
    entries = {entry["path"]: entry for entry in manifest["artifacts"]}
    sources = {}
    files = set()
    missing = set()
    for name in list(config.sections()):
        paths = {value for key, value in config[name].items() if key in {"model", "mmproj"}}
        for path in sorted(paths - sources.keys()):
            local = ROOT / path
            if local.is_file() and local.stat().st_size == entries[path]["size"]:
                sources[path] = ROOT
            elif reuse_staged and cached_model_matches(INSTALL / path, entries[path]):
                sources[path] = INSTALL
            else:
                sources[path] = None
        absent = {path for path in paths if sources[path] is None}
        if absent:
            missing.update(absent)
            del config[name]
        else:
            files.update(path for path in paths if sources[path] == ROOT)
    if (missing and not partial) or "lfm-fast" not in config:
        sys.exit("Verified model files missing: " + ", ".join(sorted(missing)))
    return config, files


def stage_file(relative):
    source, target = ROOT / relative, INSTALL / relative
    if target.is_file():
        src, dst = source.stat(), target.stat()
        if src.st_size == dst.st_size and src.st_mtime_ns == dst.st_mtime_ns:
            return
    target.parent.mkdir(parents=True, exist_ok=True)
    pending = target.with_suffix(target.suffix + ".new")
    subprocess.run(["/bin/cp", "-cp", str(source), str(pending)], check=True)
    pending.replace(target)


def stage_service(partial):
    config, files = preset_for_available_models(partial, reuse_staged=True)
    runtime = json.loads((ROOT / "config/runtime.lock.json").read_text())
    release = Path(".runtime") / f"llama-{runtime['version']}"
    if not (INSTALL / release / "llama-server").is_file():
        shutil.copytree(ROOT / release, INSTALL / release, symlinks=True, dirs_exist_ok=True)
    for relative in sorted(files | {"config/server-network.sb"}):
        stage_file(relative)
    preset = INSTALL / "config/models.ini"
    pending = preset.with_suffix(".new.ini")
    with pending.open("w") as file:
        file.write("version = 1\n\n")
        config.write(file)
    pending.replace(preset)


def run_server():
    preset_for_available_models(False)
    os.chdir(ROOT)
    args = arguments(ROOT)
    os.execve(args[0], args, environment(ROOT))


def job_definition():
    return {
        "Label": LABEL,
        "ProgramArguments": arguments(INSTALL),
        "WorkingDirectory": str(INSTALL),
        "EnvironmentVariables": environment(INSTALL),
        "RunAtLoad": True,
        "KeepAlive": {"SuccessfulExit": False},
        "ThrottleInterval": 15,
        "StandardOutPath": str(INSTALL / "logs/server.stdout.log"),
        "StandardErrorPath": str(INSTALL / "logs/server.stderr.log"),
    }


@contextmanager
def service_lock():
    state = INSTALL / ".state"
    state.mkdir(parents=True, exist_ok=True)
    with (state / "service.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def start(partial):
    with service_lock():
        job = job_definition()
        if PLIST.exists() and plistlib.loads(PLIST.read_bytes()) != job:
            sys.exit(f"A different launch agent already exists at {PLIST}")
        stage_service(partial)
        (INSTALL / "logs").mkdir(exist_ok=True)
        PLIST.parent.mkdir(parents=True, exist_ok=True)
        if not PLIST.exists():
            with PLIST.open("xb") as stream:
                plistlib.dump(job, stream)
        launchctl("enable", f"{DOMAIN}/{LABEL}")
        if not job_loaded():
            launchctl("bootstrap", DOMAIN, str(PLIST))
        else:
            subprocess.run(["/usr/bin/curl", "--noproxy", "*", "-fsS", "-o", "/dev/null",
                            "--retry", "5", "--retry-connrefused", "--retry-delay", "1", "--max-time", "20",
                            "http://127.0.0.1:8080/models?reload=1"], check=True)


def stop(action):
    if not PLIST.exists():
        sys.exit(f"Managed launch agent missing or changed: {PLIST}")
    with service_lock():
        if not PLIST.exists() or plistlib.loads(PLIST.read_bytes()) != job_definition():
            sys.exit(f"Managed launch agent missing or changed: {PLIST}")
        if job_loaded():
            launchctl("bootout", f"{DOMAIN}/{LABEL}")
        if action == "stop":
            launchctl("disable", f"{DOMAIN}/{LABEL}")
        else:
            PLIST.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("run", "start", "stop", "status", "uninstall"))
    parser.add_argument("--available", action="store_true", help="Start during download with available weights")
    args = parser.parse_args()
    action = args.action
    if action == "run":
        run_server()
    elif action == "start":
        start(args.available)
    elif action in {"stop", "uninstall"}:
        stop(action)
    else:
        launchctl("print", f"{DOMAIN}/{LABEL}")


if __name__ == "__main__":
    main()
