"""Build the pinned Apple Foundation Models Python bindings with the active SDK."""
import fcntl
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime/apple-fm-sdk"
VERSION = "0.2.2"
SOURCE = ("https://files.pythonhosted.org/packages/a1/cb/2275d00b3bcf93501e68d8a76e7783280c65f8407f58fdab674b0677823c/"
          f"apple_fm_sdk-{VERSION}.tar.gz")
DIGEST = "1b5e221e5fc25a424fdeaa579588b65e80d23261c82ad6c7a7734a206b14ef89"


def verify_archive(archive: Path) -> None:
    with archive.open("rb") as contents:
        if hashlib.file_digest(contents, "sha256").hexdigest() != DIGEST:
            raise ValueError(f"Unexpected SHA-256 for apple-fm-sdk {VERSION}.")


def build(package: Path, staging: Path, sdk: str, sdk_version: str) -> None:
    archive = RUNTIME / f"apple_fm_sdk-{VERSION}.tar.gz"
    if not archive.is_file():
        partial = staging / archive.name
        subprocess.run(["/usr/bin/curl", "-fsSL", "--retry", "2", SOURCE, "-o", str(partial)], check=True)
        verify_archive(partial)
        partial.replace(archive)
    verify_archive(archive)
    with tarfile.open(archive) as tar:
        tar.extractall(staging, filter="data")

    source = staging / f"apple_fm_sdk-{VERSION}"
    swift = source / "foundation-models-c/Sources"
    bindings = swift / "FoundationModelsCBindings"
    destination = staging / "package"
    shutil.copytree(source / "src/apple_fm_sdk", destination / "apple_fm_sdk")
    shutil.copy2(source / "LICENSE.md", destination / "LICENSE.apple-fm-sdk.md")
    module = destination / "apple_fm_sdk"
    lib = module / "lib"
    lib.mkdir()
    flags = ["-DFM_HAS_MACOS_27_SDK"] if int(sdk_version.split(".")[0]) >= 27 else []
    subprocess.run([
        "/usr/bin/xcrun", "swiftc", "-sdk", sdk, "-target", "arm64-apple-macosx26.0", "-swift-version", "6", "-O",
        "-emit-library", "-module-name", "FoundationModelsCBindings", *flags,
        "-I", str(swift / "FoundationModelsCDeclarations/include"),
        "-o", str(lib / "libFoundationModels.dylib"), str(bindings / "FoundationModelsCBindings.swift"),
    ], check=True)

    generated = module / "_ctypes_bindings.py"
    with (RUNTIME / "ctypesgen.log").open("w", encoding="utf-8") as log:
        subprocess.run([
            str(Path(sys.executable).with_name("ctypesgen")), str(bindings / "include/FoundationModels.h"),
            "-L", "lib", "-l", "FoundationModels", "-o", str(generated),
        ], stdout=log, stderr=subprocess.STDOUT, check=True)
    code = generated.read_text(encoding="utf-8")
    old = "add_library_search_dirs(['lib'])"
    if code.count(old) != 1:
        raise ValueError("Unexpected ctypesgen library lookup format.")
    generated.write_text(code.replace(old, "add_library_search_dirs([os.path.join(os.path.dirname(__file__), 'lib')])"),
                         encoding="utf-8")
    subprocess.run([sys.executable, "-c", "import apple_fm_sdk; apple_fm_sdk.SystemLanguageModel().is_available()"],
                   env={**os.environ, "PYTHONPATH": str(destination)}, check=True)
    (destination / ".verified").write_text(f"apple-fm-sdk {VERSION}, macOS SDK {sdk_version}\n", encoding="utf-8")
    destination.replace(package)


def main() -> None:
    query = ["/usr/bin/xcrun", "--sdk", "macosx"]
    sdk = subprocess.check_output([*query, "--show-sdk-path"], text=True).strip()
    sdk_version = subprocess.check_output([*query, "--show-sdk-version"], text=True).strip()
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+){0,2}", sdk_version) or int(sdk_version.split(".")[0]) < 26:
        raise ValueError("Apple Foundation Models requires a macOS 26 or newer SDK.")
    package = RUNTIME / f"bindings-{VERSION}-sdk{sdk_version}"
    with (RUNTIME / "install.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with tempfile.TemporaryDirectory(prefix="build-", dir=RUNTIME) as directory:
            staging = Path(directory)
            if not (package / ".verified").is_file():
                build(package, staging, sdk, sdk_version)
            pointer = staging / "current"
            pointer.symlink_to(package.name, target_is_directory=True)
            pointer.replace(RUNTIME / "current")
    print((package / ".verified").read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
