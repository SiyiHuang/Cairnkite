"""Exercise shared LFM staging without changing the live LaunchAgent."""

import configparser
from hashlib import sha256
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backends/lfm/scripts"))
import service


class ServiceStagingTest(unittest.TestCase):
    def test_default_checkout_preserves_valid_optional_models(self):
        with TemporaryDirectory(prefix="lfm-staging-") as temporary:
            root = Path(temporary) / "checkout"
            install = Path(temporary) / "installed"
            plist = Path(temporary) / "LaunchAgents/local.lfm.inference.plist"
            for base in (root, install):
                (base / "config").mkdir(parents=True)
                (base / "models").mkdir()
                (base / ".runtime/llama-test").mkdir(parents=True)
            (install / ".runtime/llama-test/llama-server").touch()
            (root / "config/runtime.lock.json").write_text('{"version":"test"}')
            (root / "config/server-network.sb").write_text("fixture")
            (root / "config/models.ini").write_text(
                "version = 1\n\n"
                "[lfm-fast]\nmodel = models/fast.gguf\n\n"
                "[lfm-reason]\nmodel = models/reason.gguf\n\n"
                "[lfm-tools]\nmodel = models/tools.gguf\n\n"
                "[lfm-vision]\nmodel = models/vision.gguf\nmmproj = models/projector.gguf\n"
            )
            entries = []
            for base, name, data in (
                (root, "fast", b"fast"), (install, "reason", b"reason"),
                (install, "tools", b"tools"), (root, "vision", b"vision"),
                (install, "projector", b"projector"),
            ):
                relative = f"models/{name}.gguf"
                (base / relative).write_bytes(data)
                entries.append({"path": relative, "size": len(data), "sha256": sha256(data).hexdigest()})
            (root / "config/models.lock.json").write_text(json.dumps({"artifacts": entries}))
            (install / "models/tools.gguf").write_bytes(b"wrong")

            with patch.multiple(service, ROOT=root, INSTALL=install, PLIST=plist), \
                    patch.object(service, "launchctl") as launchctl, patch.object(service, "job_loaded", return_value=False):
                service.start(partial=True)
                with self.assertRaisesRegex(SystemExit, "models/tools.gguf"):
                    service.start(partial=False)

            config = configparser.ConfigParser()
            config.read_string("[metadata]\n" + (install / "config/models.ini").read_text())
            self.assertEqual(set(config.sections()), {"metadata", "lfm-fast", "lfm-reason", "lfm-vision"})
            self.assertEqual((install / "models/reason.gguf").read_bytes(), b"reason")
            self.assertEqual((install / "models/projector.gguf").read_bytes(), b"projector")
            self.assertEqual((install / "models/fast.gguf").read_bytes(), b"fast")
            self.assertEqual(launchctl.call_count, 2)
            self.assertTrue(plist.is_file())


if __name__ == "__main__":
    unittest.main()
