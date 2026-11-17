from hashlib import sha256
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from codex_specialists import flatten_request, restore_calls
import server
from mcp.server.mcpserver.exceptions import ToolError


class ResponsesToolNames(unittest.TestCase):
    def test_namespace_round_trip(self):
        namespace = "mcp__local_specialists"
        alias = namespace + "__document"
        function = {"type": "function", "name": "document", "parameters": {"type": "object"}}
        shell = {"type": "function", "name": "exec_command"}
        call = {"type": "function_call", "namespace": namespace, "name": "document", "call_id": "call_1"}
        observation = {"type": "function_call_output", "call_id": "call_1", "output": "some text"}
        payload = {
            "tools": [{"type": "namespace", "name": namespace, "tools": [function]}, shell],
            "input": [call.copy(), observation],
            "tool_choice": {"type": "function", "namespace": namespace, "name": "document"},
        }

        aliases = flatten_request(payload)

        self.assertEqual(payload["tools"], [{**function, "name": alias}, shell])
        self.assertEqual(payload["tool_choice"], {"type": "function", "name": alias})
        flat_call = {"type": "function_call", "name": alias, "call_id": "call_1"}
        self.assertEqual(payload["input"], [flat_call, observation])

        flat_shell_call = {"type": "function_call", "name": "exec_command", "call_id": "call_2"}
        added = {"type": "response.output_item.added", "item": flat_call.copy()}
        completed = {"type": "response.completed", "response": {"output": [flat_call.copy(), flat_shell_call]}}
        restore_calls(added, aliases)
        restore_calls(completed, aliases)

        self.assertEqual(added["item"], call)
        self.assertEqual(completed["response"]["output"], [call, flat_shell_call])

    def test_plain_prompt(self):
        payload = {"input": "plain text", "tool_choice": "none"}
        self.assertEqual(flatten_request(payload), {})
        self.assertEqual(payload, {"input": "plain text", "tool_choice": "none"})


class SpecialistWorkspace(unittest.TestCase):
    def test_generated_file_and_evidence_stay_in_workspace(self):
        with TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            runtime = root / "runtime"
            runtime.mkdir()
            workspace = root / "state"
            workspace.mkdir()
            artifacts = workspace / "artifacts"
            with patch.multiple(server, RUNTIME=runtime, WORKSPACE=workspace, ARTIFACTS=artifacts):
                file = server.local_artifact("speech", "wav")
                file.write_bytes(b"synthetic fixture")
                self.assertEqual(file.parent, artifacts)
                self.assertEqual(server.scoped_path(str(file)), file)
                outside = root / "external.wav"
                outside.write_bytes(b"outside file")
                link = artifacts / "link.wav"
                link.symlink_to(outside)
                with self.assertRaisesRegex(ToolError, "outside the allowed directories"):
                    server.scoped_path(str(link))

                result = server.bounded_result({"text": "observatory " * 100}, 500)
                identifier = result["result_id"]
                receipt = workspace / "results" / (identifier + ".json")
                self.assertTrue(receipt.is_file())
                self.assertEqual(server.read_evidence(identifier)["json_slice"], receipt.read_text())
                (receipt.parent / ("b" * 32 + ".json")).symlink_to(outside)
                with self.assertRaisesRegex(ToolError, "Invalid local evidence file"):
                    server.read_evidence("b" * 32)

                shared_results = root / "shared-results"
                shared_results.mkdir()
                (runtime / "results").symlink_to(shared_results, target_is_directory=True)
                broker_receipt = runtime / "results" / ("a" * 32 + ".json")
                broker_receipt.write_text('{"text":"broker result"}')
                self.assertEqual(server.read_evidence("a" * 32)["json_slice"], broker_receipt.read_text())

    def test_linked_file_uses_artifact_directory_without_destination(self):
        with TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            workspace = root / "state" / "specialists"
            workspace.mkdir(parents=True)
            cache = root / "omni-cache"
            remote = "/Users/remote/shared/fixture.txt"
            path_hash = sha256(remote.encode()).hexdigest()[:20]
            cached = cache / "fixture-peer" / path_hash / "fixture.txt"
            cached.parent.mkdir(parents=True)
            cached.write_bytes(b"synthetic linked file")
            config = {"allowed_roots": [str(root)], "omni_linked_macs": {"Peer": ["/Users/remote/shared"]},
                      "omni_link_cache_root": str(cache)}
            hit = {"mac": "Peer", "can_open": True, "results": [{"path": remote, "size": cached.stat().st_size}]}
            artifacts = workspace / "artifacts"
            with (
                patch.multiple(server, WORKSPACE=workspace, ARTIFACTS=artifacts),
                patch.object(server, "local_config", return_value=config),
                patch.object(server, "linked_mac_results", return_value=hit) as search,
                patch.object(server, "omni_request", return_value={"local": str(cached), "path": remote}),
            ):
                with self.assertRaisesRegex(ToolError, "Omit output_folder"):
                    server.fetch_linked_mac("Peer", "fixture", remote, str(root))
                search.assert_not_called()
                config["omni_link_cache_root"] = str(root / "other-cache")
                with self.assertRaisesRegex(ToolError, "Check omni_link_cache_root"):
                    server.fetch_linked_mac("Peer", "fixture", remote)
                self.assertFalse(artifacts.exists())
                config["omni_link_cache_root"] = str(cache)
                result = server.fetch_linked_mac("Peer", "fixture", remote)
                copy = Path(result["path"])
                self.assertEqual(copy.parent.parent, artifacts)
                self.assertEqual(copy.name, cached.name)
                self.assertEqual(copy.read_bytes(), cached.read_bytes())
                self.assertEqual(result["sha256"], sha256(cached.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
