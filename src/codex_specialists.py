"""Make namespaced Codex tool calls usable by the local llama.cpp Responses API."""

from contextlib import closing
from http.client import HTTPConnection, HTTPException
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from threading import Thread

from specialists_bridge import local_specialists_socket


def flatten_request(payload):
    aliases = {}
    functions = []
    for tool in payload.get("tools", []):
        if tool["type"] != "namespace":
            functions.append(tool)
            continue
        namespace = tool["name"]
        for function in tool["tools"]:
            name = function["name"]
            alias = namespace + "__" + name
            aliases[alias] = (namespace, name)
            functions.append({**function, "name": alias})
    if "tools" in payload:
        payload["tools"] = functions
    inputs = payload.get("input", [])
    for item in inputs if isinstance(inputs, list) else []:
        if isinstance(item, dict) and item.get("type") == "function_call" and item.get("namespace"):
            namespace = item.pop("namespace")
            item["name"] = namespace + "__" + item["name"]
    choice = payload.get("tool_choice")
    if isinstance(choice, dict) and choice.get("type") == "function" and choice.get("namespace"):
        choice["name"] = choice.pop("namespace") + "__" + choice["name"]
    return aliases


def restore_calls(value, aliases):
    if isinstance(value, dict):
        if value.get("type") == "function_call" and value.get("name") in aliases:
            value["namespace"], value["name"] = aliases[value["name"]]
        for child in value.values():
            restore_calls(child, aliases)
    elif isinstance(value, list):
        for child in value:
            restore_calls(child, aliases)


class ProviderAdapter(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/v1/responses":
            self.send_error(404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 32 * 1024**2:
                self.send_error(413)
                return
            payload = json.loads(self.rfile.read(size))
            aliases = flatten_request(payload)
        except (TypeError, KeyError, ValueError, AttributeError):
            self.send_error(400, "Malformed Responses request")
            return

        with closing(HTTPConnection("127.0.0.1", 8080, timeout=150)) as backend:
            try:
                backend.request("POST", self.path, json.dumps(payload).encode(), {"Content-Type": "application/json"})
                reply = backend.getresponse()
            except (OSError, HTTPException):
                self.send_error(502, "Local LFM is unavailable")
                return
            content_type = reply.getheader("Content-Type", "application/json")
            self.send_response(reply.status)
            self.send_header("Content-Type", content_type)
            self.send_header("Connection", "close")
            self.end_headers()
            try:
                if content_type.startswith("text/event-stream"):
                    for line in reply:
                        if aliases and line.startswith(b"data: ") and line[6:].strip() != b"[DONE]":
                            event = json.loads(line[6:])
                            restore_calls(event, aliases)
                            line = b"data: " + json.dumps(event).encode() + b"\n"
                        self.wfile.write(line)
                        self.wfile.flush()
                else:
                    body = reply.read()
                    if aliases and reply.status < 400 and content_type.startswith("application/json"):
                        response = json.loads(body)
                        restore_calls(response, aliases)
                        body = json.dumps(response).encode()
                    self.wfile.write(body)
            except (OSError, HTTPException, ValueError):
                # The local client or backend can close an interrupted stream.
                pass

    def log_message(self, *_):
        pass


def launch(command, args):
    toolkit = Path(__file__).resolve().parents[1]
    state = toolkit / "backends/lfm/.state/codex-local"
    with local_specialists_socket() as socket, ThreadingHTTPServer(("127.0.0.1", 0), ProviderAdapter) as adapter:
        server = Thread(target=adapter.serve_forever, daemon=True)
        server.start()
        port = adapter.server_address[1]
        env = {**os.environ, "LFM_CODEX_SPECIALISTS_PORT": str(port), "LFM_SPECIALISTS_SOCKET": socket}
        mcp_env = {
            "LFM_SPECIALISTS_SOCKET": socket,
            "LFM_SPECIALISTS_WORKSPACE": str(state / "specialists"),
            "TMPDIR": str(state / "tmp"),
        }
        if "LFM_TOOLKIT_CONFIG" in env:
            mcp_env["LFM_TOOLKIT_CONFIG"] = env["LFM_TOOLKIT_CONFIG"]
        if "LFM_OMNI_ALLOWED_SOCKET" in env:
            mcp_env["OMNI_SOCKET"] = env["LFM_OMNI_ALLOWED_SOCKET"]
        config = [
            "--disable", "incremental_tools", "--disable", "deferred_tool_world_state",
            "-c", f'model_providers.local-lfm.base_url="http://127.0.0.1:{port}/v1"',
            "-c", "mcp_servers.local_specialists.command=" + json.dumps(str(toolkit / "bin/serve"), ensure_ascii=False),
            "-c", "mcp_servers.local_specialists.tool_timeout_sec=660",
        ]
        for key, value in mcp_env.items():
            config.extend(["-c", f"mcp_servers.local_specialists.env.{key}=" + json.dumps(value, ensure_ascii=False)])
        try:
            with subprocess.Popen([command, *config, *args], env=env) as process:
                def terminate(_signal, _frame):
                    process.terminate()

                previous = signal.signal(signal.SIGTERM, terminate)
                try:
                    return process.wait()
                finally:
                    signal.signal(signal.SIGTERM, previous)
        finally:
            adapter.shutdown()


if __name__ == "__main__":
    raise SystemExit(launch(sys.argv[1], sys.argv[2:]))
