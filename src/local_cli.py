"""Call the same validated tool directly, without an MCP client or hosted agent."""
import argparse
import asyncio
import fcntl
import json
import sys

from mcp.server.mcpserver.exceptions import ToolError

from deployment import digup_index
from screenshot_watch import new_images
from server import SCREENSHOT_TYPES, document, mcp, run_digup, scoped_path


def index_digup(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="bin/local index-digup", description="Build a DigUp index for one allowlisted folder.")
    parser.add_argument("folder")
    parser.add_argument("--code", action="store_true", help="Index source code and repository documentation.")
    args = parser.parse_args(argv)
    try:
        folder = scoped_path(args.folder, directory=True)
        index = digup_index(folder)
        index.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (index / ".build.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ToolError("An index build is already running for this folder.") from None
            options = ["--code"] if args.code else []
            print(run_digup(folder, ["index", str(folder), *options], timeout=3600), end="")
    except ToolError as error:
        parser.exit(1, f"{error}\n")


def watch_screenshots(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="bin/local watch-screenshots", description="OCR new images in an allowlisted folder.")
    parser.add_argument("folder")
    args = parser.parse_args(argv)
    try:
        folder = scoped_path(args.folder, directory=True)
        for path in new_images(folder, SCREENSHOT_TYPES):
            try:
                result = document(str(path), backend="vision")
            except ToolError as error:
                result = {"source": str(path), "error": str(error)}
            print(json.dumps(result, ensure_ascii=False, allow_nan=False), flush=True)
    except KeyboardInterrupt:
        return
    except (OSError, ToolError) as error:
        parser.exit(1, f"{error}\n")


async def main():
    parser = argparse.ArgumentParser(description="Run a local tool with a JSON argument object on stdin.")
    tools = await mcp.list_tools()
    parser.add_argument("tool", choices=sorted(tool.name for tool in tools))
    args = parser.parse_args()
    try:
        request = {} if sys.stdin.isatty() else json.loads(sys.stdin.read() or "{}")
        if not isinstance(request, dict):
            raise ValueError("Provide a JSON object on stdin.")
        result = await mcp.call_tool(args.tool, request)
        print(json.dumps(result.structured_content, ensure_ascii=False, indent=2, allow_nan=False))
    except (ValueError, ToolError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    if sys.argv[1:2] == ["index-digup"]:
        index_digup(sys.argv[2:])
    elif sys.argv[1:2] == ["watch-screenshots"]:
        watch_screenshots(sys.argv[2:])
    else:
        asyncio.run(main())
