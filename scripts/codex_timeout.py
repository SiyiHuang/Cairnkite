"""Set a timeout on the project-owned Codex MCP entry, preserving all other text."""
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import tomllib

config = (Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "config.toml").resolve()
command = sys.argv[1]
original = config.read_text(encoding="utf-8")
entry = tomllib.loads(original)["mcp_servers"]["local_specialists"]
if entry.get("command") != command:
    raise SystemExit("Codex local_specialists points elsewhere.")
if "tool_timeout_sec" in entry or "tool_timeout_ms" in entry:
    existing = entry.get("tool_timeout_sec", entry.get("tool_timeout_ms", 0) / 1000)
    if existing < 300:
        raise SystemExit("Increase the Codex local_specialists tool timeout to 360 seconds in config.toml.")
    raise SystemExit(0)

updated, count = re.subn(
    r"(?m)^(\[mcp_servers\.local_specialists\][^\n]*\n)",
    r"\g<1>tool_timeout_sec = 360\n", original,
)
if count != 1 or tomllib.loads(updated)["mcp_servers"]["local_specialists"]["tool_timeout_sec"] != 360:
    raise SystemExit("Add tool_timeout_sec = 360 to the local_specialists entry in Codex config.toml.")
fd, temporary = tempfile.mkstemp(prefix=".local-specialists-", dir=config.parent)
try:
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        os.fchmod(file.fileno(), stat.S_IMODE(config.stat().st_mode))
        file.write(updated)
    if config.read_text(encoding="utf-8") != original:
        raise SystemExit("Codex configuration changed during registration. Run bin/register again.")
    os.replace(temporary, config)
finally:
    Path(temporary).unlink(missing_ok=True)
