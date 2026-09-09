import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from integrity_guard.cli import run


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.target = self.base / "target"
        self.target.mkdir()
        (self.target / "file.txt").write_text("original")
        self.key = self.base / "key"
        self.baseline = self.base / "baseline.json"
        self.report = self.base / "report.json"

    def call(self, *arguments):
        output, error = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            status = run(list(arguments))
        return status, output.getvalue(), error.getvalue()

    def initialize(self):
        self.assertEqual(self.call("keygen", "--key-file", str(self.key))[0], 0)
        self.assertEqual(self.call("init", str(self.target), "--key-file", str(self.key),
                                   "--baseline", str(self.baseline))[0], 0)

    def test_full_clean_and_changed_flow(self):
        self.initialize()
        status, output, _ = self.call("check", str(self.target), "--key-file", str(self.key),
                                      "--baseline", str(self.baseline), "--report", str(self.report))
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(output)["status"], "clean")
        self.assertEqual(json.loads(self.report.read_text())["status"], "clean")
        (self.target / "file.txt").write_text("changed")
        status, output, _ = self.call("check", str(self.target), "--key-file", str(self.key),
                                      "--baseline", str(self.baseline))
        self.assertEqual(status, 2)
        self.assertEqual(json.loads(output)["modified"], ["file.txt"])

    def test_baseline_not_overwritten_without_force(self):
        self.initialize()
        status, _, error = self.call("init", str(self.target), "--key-file", str(self.key),
                                     "--baseline", str(self.baseline))
        self.assertEqual(status, 3)
        self.assertIn("--force", error)

    def test_tampered_baseline_returns_error_code(self):
        self.initialize()
        baseline = json.loads(self.baseline.read_text())
        baseline["root"] = str(self.base)
        self.baseline.write_text(json.dumps(baseline))
        status, _, error = self.call("check", str(self.target), "--key-file", str(self.key),
                                     "--baseline", str(self.baseline))
        self.assertEqual(status, 3)
        self.assertIn("Assinatura inválida", error)

    def test_watch_once_for_automation(self):
        self.initialize()
        status, output, _ = self.call("watch", str(self.target), "--key-file", str(self.key),
                                      "--baseline", str(self.baseline), "--once")
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(output)["status"], "clean")


if __name__ == "__main__":
    unittest.main()
