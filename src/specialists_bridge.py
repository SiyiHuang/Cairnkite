"""Run approved specialist operations outside the offline LFM client sandbox."""

import asyncio
from contextlib import contextmanager
import json
import os
from pathlib import Path
import signal
import socket
from socketserver import StreamRequestHandler, ThreadingUnixStreamServer
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Thread

from mcp.server.mcpserver.exceptions import ToolError

from lean_check import check


MAX_REQUEST = 96 * 1024
MAX_RESULT = 128 * 1024


def request(path, operation, payload, *, timeout):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(timeout)
        client.connect(path)
        client.sendall(json.dumps({"operation": operation, "arguments": payload}).encode() + b"\n")
        with client.makefile("rb") as reader:
            response = reader.readline(MAX_RESULT + 1)
    if len(response) > MAX_RESULT or not response.endswith(b"\n"):
        raise ValueError("Incomplete specialist bridge response.")
    result = json.loads(response)
    if "error" in result:
        raise RuntimeError(result["error"])
    return result


class SpecialistsHandler(StreamRequestHandler):
    timeout = 25

    def handle(self):
        try:
            line = self.rfile.readline(MAX_REQUEST + 1)
            if len(line) > MAX_REQUEST or not line.endswith(b"\n"):
                raise ValueError("Invalid specialist bridge request.")
            payload = json.loads(line)
            args = payload["arguments"]
            if payload["operation"] == "lean":
                result = check(args["source"], args["declaration"], args.get("statement"), args.get("library", "lean"))
            elif payload["operation"] == "paddle":
                from server import mcp

                tool = asyncio.run(mcp.call_tool("document", {**args, "backend": "paddle"}))
                result = tool.structured_content
            else:
                raise ValueError("Unsupported specialist bridge operation.")
        except (OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired, ToolError) as error:
            result = {"error": str(error)}
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode() + b"\n")


@contextmanager
def local_specialists_socket():
    with TemporaryDirectory(prefix="specialists-") as directory:
        path = str(Path(directory).resolve() / "work.sock")
        with ThreadingUnixStreamServer(path, SpecialistsHandler) as broker:
            serve = Thread(target=broker.serve_forever, daemon=True)
            serve.start()
            try:
                yield path
            finally:
                broker.shutdown()


def launch(command, args):
    root = Path(__file__).resolve().parents[1]
    with local_specialists_socket() as path:
        env = {**os.environ, "LFM_SPECIALISTS_SOCKET": path}
        server_env = {key: env[key] for key in ("LFM_SPECIALISTS_SOCKET", "LFM_TOOLKIT_CONFIG", "OMNI_SOCKET") if key in env}
        config = json.dumps({"mcpServers": {"local_specialists": {
            "command": str(root / "bin/serve"), "env": server_env,
        }}})
        with subprocess.Popen([command, "--mcp-config", config, *args], env=env) as process:
            def terminate(_signal, _frame):
                process.terminate()

            previous = signal.signal(signal.SIGTERM, terminate)
            try:
                return process.wait()
            finally:
                signal.signal(signal.SIGTERM, previous)


if __name__ == "__main__":
    raise SystemExit(launch(sys.argv[1], sys.argv[2:]))
