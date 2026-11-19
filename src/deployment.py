"""Choose deployment paths from task requirements and the target machine."""
from __future__ import annotations

import argparse
from configparser import ConfigParser
from contextlib import closing
from hashlib import sha256
import http.client
import json
import os
import platform
import re
import shutil
import sqlite3
import subprocess
from pathlib import Path
from time import monotonic

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime"
NATIVE = ROOT / "native/.build/release/apple-specialists"
CATALOG = ROOT / "catalog/deployment.json"
LFM_CONFIG = ROOT / "backends/lfm/config"
MACOS_VERSION = r"[0-9]{1,3}(\.[0-9]{1,3}){0,2}"
OMNI_PATHS = (Path.home() / "Applications/Omni.app/Contents/Helpers/omni", Path("/Applications/Omni.app/Contents/Helpers/omni"))
OMNI = next((path for path in OMNI_PATHS if path.is_file()), OMNI_PATHS[0])
OMNI_SOCKET = Path.home() / "Library/Application Support/Omni/omni.sock"

HY_MT_LANGUAGES = {
    "zh": "Simplified Chinese", "zh-hans": "Simplified Chinese", "zh-hant": "Traditional Chinese",
    "en": "English", "fr": "French", "pt": "Portuguese", "es": "Spanish", "ja": "Japanese",
    "tr": "Turkish", "ru": "Russian", "ar": "Arabic", "ko": "Korean", "th": "Thai", "it": "Italian",
    "de": "German", "vi": "Vietnamese", "ms": "Malay", "id": "Indonesian", "tl": "Filipino", "hi": "Hindi",
    "pl": "Polish", "cs": "Czech", "nl": "Dutch", "km": "Khmer", "my": "Burmese", "fa": "Persian",
    "gu": "Gujarati", "ur": "Urdu", "te": "Telugu", "mr": "Marathi", "he": "Hebrew", "bn": "Bengali",
    "ta": "Tamil", "uk": "Ukrainian", "bo": "Tibetan", "kk": "Kazakh", "mn": "Mongolian",
    "ug": "Uyghur", "yue": "Cantonese",
}


def hy_mt_language(language: str) -> str | None:
    tag = language.lower()
    if tag in {"zh-tw", "zh-hk", "zh-mo"}:
        return HY_MT_LANGUAGES["zh-hant"]
    return HY_MT_LANGUAGES.get(tag) or HY_MT_LANGUAGES.get(tag.split("-")[0])


def read_catalog() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def apple_attachment_build() -> bool:
    try:
        marker = (RUNTIME / "apple-fm-sdk/current/.verified").read_text(encoding="utf-8")
    except OSError:
        return False
    sdk = re.search(r"macOS SDK (\d+)", marker)
    return sdk is not None and int(sdk[1]) >= 27


def system_fact(command: list[str], *, env: dict[str, str] | None = None) -> str:
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=4, check=True, env=env).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def machine_facts() -> dict:
    macos = platform.mac_ver()[0]
    model_memory = system_fact(["/usr/sbin/sysctl", "-n", "hw.memsize"]) if macos else ""
    is_arm_mac = bool(macos and system_fact(["/usr/sbin/sysctl", "-n", "hw.optional.arm64"]) == "1")
    return {
        "machine": "arm64" if is_arm_mac else platform.machine(),
        "macos": macos or None,
        "disk_gib": round(shutil.disk_usage(ROOT).free / 1024**3, 1),
        "memory_gib": round(int(model_memory) / 1024**3, 1) if model_memory.isdigit() else None,
    }


def native_probe(args: list[str]) -> dict:
    if not NATIVE.is_file():
        return {}
    result = system_fact([str(NATIVE), *args])
    try:
        return json.loads(result) if result else {}
    except json.JSONDecodeError:
        return {}


def lfm_model_ids() -> list[str]:
    connection = http.client.HTTPConnection("127.0.0.1", 8080, timeout=1)
    try:
        connection.request("GET", "/v1/models")
        response = connection.getresponse()
        if response.status == 200:
            models = json.loads(response.read(512_000))["data"]
            return sorted(model["id"] for model in models if isinstance(model.get("id"), str))
    except (OSError, http.client.HTTPException, ValueError, KeyError, TypeError, AttributeError):
        return []
    finally:
        connection.close()
    return []


def lfm_weight_sizes() -> dict[str, tuple[int, int]]:
    """Return pinned bytes for each model and for its deployment with startup models."""
    presets = ConfigParser(interpolation=None)
    presets.read_string("[metadata]\n" + (LFM_CONFIG / "models.ini").read_text(encoding="utf-8"))
    entries = json.loads((LFM_CONFIG / "models.lock.json").read_text(encoding="utf-8"))["artifacts"]
    sizes = {entry["path"]: entry["size"] for entry in entries}
    weights = {}
    for name, preset in presets.items():
        if "model" not in preset:
            continue
        files = [preset[key] for key in ("model", "mmproj") if key in preset]
        if all(file in sizes for file in files):
            weights[name] = sum(sizes[file] for file in files)
    startup = {name for name in weights if presets[name].getboolean("load-on-startup", fallback=False)}
    startup_bytes = sum(weights[name] for name in startup)
    return {name: (size, startup_bytes if name in startup else size + startup_bytes) for name, size in weights.items()}


def digup_index(folder: Path) -> Path:
    return RUNTIME / "indexes/digup" / sha256(os.fsencode(folder)).hexdigest()


def digup_index_ready(folder: Path, *, code: bool) -> tuple[str, str | None]:
    db = digup_index(folder) / ("code.sqlite" if code else "index.sqlite")
    if not db.is_file():
        mode = " --code" if code else ""
        return "needs_setup", f"Build this folder's index with bin/local index-digup{mode} <folder>."
    wal = db.with_name(db.name + "-wal")
    try:
        if wal.exists() and wal.stat().st_size:
            return "needs_setup", "The index has pending writes. Check its status after the writer finishes."
        prefix = folder.as_posix().rstrip("/") + "/"
        cutoff = monotonic() + 0.75
        with closing(sqlite3.connect(db.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)) as connection:
            connection.set_progress_handler(lambda: monotonic() > cutoff, 1000)
            row = connection.execute(
                "SELECT 1 FROM segments JOIN files ON files.id = segments.file "
                "WHERE segments.vec IS NOT NULL AND substr(files.path, 1, length(?)) = ? LIMIT 1",
                (prefix, prefix),
            ).fetchone()
    except (OSError, ValueError, sqlite3.Error):
        return "needs_setup", "Check that this folder's index is readable and compatible with the installed DigUp."
    if row is None:
        return "needs_setup", "This folder's index has no committed search vectors. Build or refresh it first."
    return "installed", "This folder's index contains committed search vectors. Refresh it after source changes."


def omni_folder_ready(folder: Path) -> tuple[str, str | None]:
    configured = os.environ.get("OMNI_SOCKET")
    if not configured and "LFM_SPECIALISTS_WORKSPACE" in os.environ:
        return "needs_setup", "Start Omni and use --with-omni to check this session's index."
    socket = Path(configured) if configured else OMNI_SOCKET
    if not socket.is_absolute() or not socket.is_socket():
        return "needs_setup", "Start Omni to check this folder's source index."
    environment = {key: value for key, value in os.environ.items() if key not in {"OMNI_URL", "OMNI_TOKEN"}}
    raw = system_fact([str(OMNI), "--no-launch", "--socket", str(socket), "--json", "list_sources"], env=environment)
    try:
        sources = json.loads(raw)["sources"]
        source = next((item for item in sources if item.get("kind") == "folder" and item.get("key") == str(folder)), None)
    except (AttributeError, KeyError, TypeError, ValueError):
        return "needs_setup", "Check this folder's source and index in Omni."
    if source is None:
        return "needs_setup", "Check whether Omni covers this exact folder before adding or querying a source."
    if source.get("indexing") or source.get("queued") or not source.get("indexed_files"):
        return "needs_setup", "This Omni source has no completed nonempty index. Check its indexing progress."
    return "installed", "Omni reports indexed files for this folder."


def readiness(entry: dict, *, translation_pair: tuple[str, str], locale: str,
              feature: str, folder: Path | None) -> tuple[str, str | None]:
    if entry["delivery"] == "upstream":
        return "upstream_trial", None
    if entry.get("app") == "omni":
        if not OMNI.is_file():
            return "not_installed", None
        if feature == "semantic-search" and folder is not None:
            return omni_folder_ready(folder)
        return "needs_setup", "Configure or verify the local model and source index."
    for marker in entry.get("markers", []):
        if not (ROOT / marker).is_file():
            return "not_installed", None
    if entry.get("lfm_model") and entry["lfm_model"] not in lfm_model_ids():
        return "needs_setup", "Start the loopback LFM service and confirm this model appears in bin/lfm status."
    probe = entry.get("probe")
    if probe in {"shortcut_folder", "shortcut_screenshot"}:
        return "needs_setup", "Check the automation in Shortcuts and test it with a synthetic window image."
    if probe == "apple_translation":
        asset = native_probe(["translation-status", *translation_pair]).get("asset")
        if asset == "unsupported":
            return "unavailable", "Apple Translation does not support this language pair."
        if asset != "installed":
            return "needs_setup", "Install the system translation resources for this language pair."
    elif probe in {"apple_intelligence", "apple_attachment", "speech"}:
        assets = native_probe(["status", locale])
        if probe == "apple_attachment" and not apple_attachment_build():
            return "needs_setup", "Run bin/install apple-fm-python with the macOS 27 SDK active."
        if probe in {"apple_intelligence", "apple_attachment"} and assets.get("foundation_models") != "available":
            return "needs_setup", "Enable Apple Intelligence and confirm system model availability."
        if probe == "speech" and assets.get("speech_available") and "speech_locale" not in assets:
            return "unavailable", f"This Mac does not support {locale} for Apple Speech."
        if probe == "speech" and assets.get("speech_asset") != "installed":
            return "needs_setup", f"Install Apple Speech for {locale}."
    elif probe == "spotlight":
        return "needs_setup", "Confirm the intended folder is indexed by Spotlight."
    elif probe == "digup":
        if folder is not None:
            return digup_index_ready(folder, code=feature == "code-search")
        return "needs_setup", "Build or refresh the intended folder's document or code index."
    elif probe == "whisper":
        if not shutil.which("ffmpeg"):
            return "needs_setup", "Install FFmpeg and make it available on PATH."
    elif probe == "video_scale":
        support = native_probe(["video-scale-status"]).get("supported")
        if support is False:
            return "unavailable", "This Mac does not support VideoToolbox low-latency super resolution."
        if support is None:
            return "needs_setup", "Update the native helper with bin/install core."
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            return "needs_setup", "Install ffmpeg and ffprobe for audio muxing and output verification."
        return "installed", "Use video-scale-status <width> <height> with the native helper to check the requested scale."
    elif probe == "shortcut":
        try:
            configured = json.loads((RUNTIME / "config.json").read_text(encoding="utf-8")).get("allowed_shortcut_ids")
        except (OSError, AttributeError, ValueError):
            configured = None
        if not isinstance(configured, list) or not all(isinstance(value, str) for value in configured):
            return "needs_setup", "Create the intended shortcut and configure its ID."
        installed = system_fact(["/usr/bin/shortcuts", "list", "--show-identifiers"])
        ids = {value.lower() for value in re.findall(r"\(([0-9a-fA-F-]{36})\)$", installed, re.MULTILINE)}
        if ids.isdisjoint(value.lower() for value in configured):
            return "needs_setup", "Create the intended shortcut and configure its ID."
    return "installed", None


def major_version(value: str | None) -> int:
    return int(value.split(".")[0]) if value else 0


def plan(
    feature: str | None = None, *, use: str = "unspecified", requirements: list[str] | None = None,
    execution: str = "agent", verified_only: bool = False, target: dict | None = None,
    profile: str | None = None,
    translation_pair: tuple[str, str] = ("en", "zh-Hans"), locale: str = "en-US",
    robot_ready: bool | None = None, folder: Path | None = None,
) -> dict:
    """Return the ordered candidates and any constraints that rule each one out."""
    catalog = read_catalog()
    default_backends = set(catalog["default_backends"])
    profiles = {
        "default": catalog["default_backends"],
        "optional": [identifier for identifier in catalog["backends"] if identifier not in default_backends],
    }
    leaves = {leaf["id"]: (group, leaf) for group in catalog["tasks"] for leaf in group["choices"]}
    if feature is None:
        return {"tasks": catalog["tasks"], "requirements": catalog["requirements"], "profiles": profiles}
    if feature not in leaves:
        raise ValueError(f"Unknown feature {feature!r}. List the decision tree without a feature first.")
    group, leaf = leaves[feature]
    must_have = set(requirements or [])
    unknown = must_have - set(catalog["requirements"])
    if unknown:
        raise ValueError(f"Unknown required features: {', '.join(sorted(unknown))}.")
    host = machine_facts() if target is None else target
    candidates = []
    macos = major_version(host.get("macos"))
    weights = lfm_weight_sizes() if any(catalog["backends"][candidate].get("lfm_model")
                                       for candidate in leaf["candidates"]) else {}
    for entry_id in leaf["candidates"]:
        entry = catalog["backends"][entry_id]
        entry_profile = "default" if entry_id in default_backends else "optional"
        reasons = []
        if profile and entry_profile != profile:
            reasons.append(f"This path belongs to the {entry_profile} profile.")
        platform_rule = entry["platform"]
        if platform_rule.get("macos") and macos < platform_rule["macos"]:
            reasons.append(f"This path requires macOS {platform_rule['macos']} or newer.")
        if platform_rule.get("arm64") and host.get("machine") != "arm64":
            reasons.append("This path requires Apple Silicon.")
        if execution == "local" and "local_cli" not in entry["features"]:
            reasons.append("This path does not offer a documented local CLI workflow here.")
        if execution == "mcp" and entry["delivery"] != "mcp":
            reasons.append("This path is not integrated with this repository's MCP server.")
        if entry_id == "smolvla" and robot_ready is True:
            reasons.append("The MCP tool previews only recorded observations.")
        if entry_id == "smolvla-rollout" and robot_ready is False:
            reasons.append("Physical rollout needs a calibrated robot and cameras.")
        if entry_id == "hy-mt":
            source, translation_target = map(hy_mt_language, translation_pair)
            if not source or not translation_target or source == translation_target:
                reasons.append("Hy-MT2 requires a pair of distinct supported languages.")
        missing = must_have - set(entry["features"])
        if missing:
            reasons.append(f"Missing verified or documented features: {', '.join(sorted(missing))}.")
        if use in {"commercial", "production"} and entry["license"]["policy"] != "permissive":
            reasons.append(f"License needs another choice for {use}: {entry['license']['name']}.")
        if use == "personal" and entry["license"]["policy"] == "research_only":
            reasons.append("This license is limited to research or separately authorized use.")
        if verified_only:
            unverified = must_have.intersection(entry.get("unverified_features", []))
            if entry["evidence"] != "verified":
                reasons.append("The requested selection requires project-verified inference.")
            elif unverified:
                reasons.append(f"Features awaiting project verification: {', '.join(sorted(unverified))}.")
        resources = {}
        memory = host.get("memory_gib")
        if sizes := weights.get(entry.get("lfm_model")):
            model_gib, preset_gib = (size / 1024**3 for size in sizes)
            resources = {"weights_gib": round(model_gib, 2), "preset_weights_gib": round(preset_gib, 2)}
            if memory is not None and preset_gib > memory:
                reasons.append(f"Pinned model and startup weights use {preset_gib:.2f} GiB, above this target's {memory:g} GiB.")
        if reasons:
            state, note = "unsupported", None
        elif target is not None:
            state, note = "unknown_on_target", None
        else:
            state, note = readiness(entry, translation_pair=translation_pair, locale=locale, feature=feature, folder=folder)
        needed_disk = entry.get("disk_gib")
        free_disk = host.get("disk_gib")
        if not reasons and state != "installed" and needed_disk and free_disk is not None and free_disk < needed_disk:
            reasons.append(f"Plan for at least {needed_disk} GiB of free disk for this installation.")
        if state == "unavailable" and note:
            reasons.append(note)
        decision = "excluded" if reasons else (
            "trial_required" if entry["evidence"] == "upstream" else "eligible"
        )
        if not reasons and entry_id == "smolvla" and not robot_ready:
            note = "Use offline replay first. Physical execution needs a calibrated robot and camera."
        recommended_memory = entry.get("recommended_memory_gib")
        if not reasons and recommended_memory and memory is not None and memory < recommended_memory:
            note = f"The upstream author recommends at least {recommended_memory} GiB of memory. Trial on this host first."
        candidate = {"id": entry_id, "profile": entry_profile, "decision": decision, "readiness": state,
                     "reasons": reasons, "setup_note": note, **entry,
                     **entry.get("workflows", {}).get(feature, {}), **resources}
        mcp = candidate.get("mcp", {})
        if folder is not None and mcp.get("tool") == "search":
            candidate["mcp"] = {**mcp, "arguments": {**mcp["arguments"], "folder": str(folder)}}
        candidates.append(candidate)

    available = [entry for entry in candidates if entry["decision"] != "excluded"]
    ready = [entry for entry in available if entry["readiness"] == "installed" and entry["evidence"] == "verified"]
    preferred = next(iter(ready or available), None)
    follow_up = None
    if use == "unspecified" and preferred and preferred["license"]["policy"] != "permissive":
        follow_up = "Confirm whether this use is personal, commercial, production, or research before installing."
    elif preferred and preferred["id"] == "smolvla" and robot_ready is None:
        follow_up = "Will you use offline replay or a calibrated robot and camera?"
    return {
        "task": group["id"], "feature": feature, "choice": leaf["label"], "prompt": leaf["prompt"],
        "target": host, "execution": execution, "use": use, "requirements": sorted(must_have), "profile": profile,
        "folder": str(folder) if folder is not None else None,
        "recommendation": preferred["id"] if preferred and not follow_up else None,
        "candidates": candidates, "question": follow_up,
        "delivery_note": (
            "Use the local CLI or the documented upstream local command for private data."
            if execution == "local" else
            "The models run locally. A hosted agent may receive tool arguments and results."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Choose a local specialist without installing anything.")
    parser.add_argument("feature", nargs="?", help="Task leaf ID. Omit to list the decision tree.")
    parser.add_argument("--require", action="append", default=[], help="Required capability ID. Repeat as needed.")
    parser.add_argument("--use", choices=("personal", "commercial", "production", "research"), default="unspecified")
    parser.add_argument("--execution", choices=("agent", "mcp", "local"), default="agent")
    parser.add_argument("--profile", choices=("default", "optional"), help="Limit choices for a task to this deployment profile.")
    parser.add_argument("--verified-only", action="store_true")
    parser.add_argument("--locale", default="en-US", help="BCP-47 locale for Apple Speech.")
    parser.add_argument("--source-language", default="en", help="BCP-47 source for Apple Translation.")
    parser.add_argument("--target-language", default="zh-Hans", help="BCP-47 target for Apple Translation.")
    parser.add_argument("--robot-ready", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--machine", choices=("arm64", "x86_64"), help="Plan for another host instead of probing this one.")
    parser.add_argument("--macos", help="Target macOS version. Omit with --machine for a non-macOS target.")
    parser.add_argument("--disk-gib", type=float, help="Free disk on the target host, in GiB.")
    parser.add_argument("--memory-gib", type=float, help="Unified memory on the target host, in GiB.")
    parser.add_argument("--folder", type=Path, help="Check existing indexes for this local search folder.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output.")
    args = parser.parse_args()
    if args.macos is not None and not re.fullmatch(MACOS_VERSION, args.macos):
        parser.error("--macos requires a version such as 26 or 26.5.")
    for capacity in (args.disk_gib, args.memory_gib):
        if capacity is not None and not (0 <= capacity < float("inf")):
            parser.error("Capacity options require finite nonnegative numbers.")
    if not args.machine and any(value is not None for value in (args.macos, args.disk_gib, args.memory_gib)):
        parser.error("Set --machine when planning for another system or hardware.")
    if args.folder is not None and args.machine:
        parser.error("Use --folder for this Mac's indexes, or --machine to plan another device.")
    folder = None
    if args.folder is not None:
        try:
            folder = args.folder.expanduser().resolve(strict=True)
        except (OSError, RuntimeError, ValueError):
            parser.error("--folder must be an existing local directory.")
        if not folder.is_dir():
            parser.error("--folder must be an existing local directory.")
    for locale in (args.locale, args.source_language, args.target_language):
        if not re.fullmatch(r"[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*", locale):
            parser.error("Use BCP-47 language IDs such as en-US or zh-Hans.")
    target = {"machine": args.machine, "macos": args.macos, "disk_gib": args.disk_gib,
              "memory_gib": args.memory_gib} if args.machine else None
    try:
        result = plan(args.feature, use=args.use, requirements=args.require, execution=args.execution, profile=args.profile,
                      verified_only=args.verified_only, target=target, locale=args.locale, robot_ready=args.robot_ready,
                      translation_pair=(args.source_language, args.target_language), folder=folder)
    except ValueError as error:
        parser.error(str(error))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.feature is None:
        print(f"Default backends: {', '.join(result['profiles']['default'])}\n")
        for group in result["tasks"]:
            print(group["label"])
            for leaf in group["choices"]:
                print(f"  {leaf['id']:24} {leaf['label']}")
        print("\nUse bin/plan <feature> or bin/plan --json for the requirements and branches.")
    else:
        print(result["choice"])
        print(result["prompt"])
        print(f"Candidate: {result['recommendation'] or '—'}")
        if result["question"]:
            print(result["question"])
        for entry in result["candidates"]:
            print(f"\n{entry['id']} [{entry['profile']}, {entry['decision']}, {entry['evidence']}, {entry['readiness']}]")
            print(entry["strength"])
            print(entry["tradeoff"])
            if "mcp" in entry:
                mcp = entry["mcp"]
                arguments = " " + json.dumps(mcp["arguments"], ensure_ascii=False) if mcp.get("arguments") else ""
                print(f"  MCP: {mcp.get('server', 'local_specialists')}.{mcp['tool']}{arguments}")
            for note in [*entry["reasons"], entry["setup_note"]]:
                if note:
                    print(f"  {note}")
            if entry.get("evidence_note"):
                print(entry["evidence_note"])
            print(f"  {entry['license']['name']} · {entry['recipe']}")
        print(f"\n{result['delivery_note']}")


if __name__ == "__main__":
    main()
