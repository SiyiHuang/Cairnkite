"""Verify that both actual local Agent CLIs execute a read and use its result."""

import json
from pathlib import Path
import secrets
import subprocess
import tempfile

from lfm_mcp import ROOT


def run_jsonl(command):
    proc = subprocess.run(command, text=True, stdin=subprocess.DEVNULL,
                          capture_output=True, timeout=100, cwd=ROOT)
    if proc.returncode != 0:
        tail = "\n".join((proc.stderr + "\n" + proc.stdout).splitlines()[-8:])
        raise RuntimeError(f"{command[0]} exited {proc.returncode}:\n{tail}")
    return [json.loads(line) for line in proc.stdout.splitlines() if line.startswith("{")]


def codex_read(file, code):
    events = run_jsonl([str(ROOT / "bin/codex-local"), "exec", "--strict-config",
                       "--skip-git-repo-check", "--ephemeral", "--json",
                       f"Use the shell tool to read {file}. Report its inventory code, then stop."])
    items = [e["item"] for e in events if e.get("type") == "item.completed"]
    commands = [i for i in items if i.get("type") == "command_execution"]
    assert any(str(file) in i["command"] and i.get("exit_code") == 0 for i in commands), commands
    messages = [i["text"] for i in items if i.get("type") == "agent_message"]
    assert messages and code in messages[-1], messages
    assert any(e.get("type") == "turn.completed" for e in events), events[-3:]
    return {"model": "lfm-reason", "successful_file_read": True, "correct_answer": True,
            "observed_command": commands[0]["command"].replace(str(file), "<fixture>")}


def claude_read(file, code):
    events = run_jsonl([str(ROOT / "bin/claude-local"), "--print", "--output-format", "stream-json",
                       "--verbose", "--no-session-persistence", "--tools", "Read", "--allowedTools", "Read",
                       "--", f"Use the Read tool to read {file}. Report its inventory code, then stop."])
    blocks = [block for e in events if e.get("type") == "assistant"
              for block in e["message"]["content"] if block["type"] == "tool_use"]
    assert any(b["name"] == "Read" and b["input"]["file_path"] == str(file) for b in blocks), blocks
    reply = next(e for e in reversed(events) if e.get("type") == "result")
    assert not reply["is_error"] and code in reply["result"], reply
    assert set(reply["modelUsage"]) == {"lfm-reason"}, reply["modelUsage"]
    return {"model": "lfm-reason", "successful_file_read": True, "correct_answer": True,
            "observed_tool": "Read"}


def main():
    with tempfile.TemporaryDirectory(dir=ROOT / ".state", prefix="verify-clients-") as directory:
        path = Path(directory).resolve() / "inventory.txt"
        code = f"LFM-{secrets.token_hex(5).upper()}"
        path.write_text(f"INVENTORY-CODE={code}\n")
        report = {"codex": codex_read(path, code), "claude_code": claude_read(path, code)}
    output = ROOT / "logs/verification-clients.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    main()
