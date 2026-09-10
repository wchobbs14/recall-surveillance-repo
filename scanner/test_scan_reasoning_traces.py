import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCANNER = Path(__file__).with_name("scan_reasoning_traces.py")
POLICY = Path(__file__).with_name("patterns.json")


class ScannerTests(unittest.TestCase):
    def run_scan(self, files, fail_on="high"):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, content in files.items():
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
            report = root / "report.json"
            proc = subprocess.run(
                [sys.executable, str(SCANNER), str(root), "--policy", str(POLICY), "--json-out", str(report), "--fail-on", fail_on],
                text=True,
                capture_output=True,
            )
            data = json.loads(report.read_text(encoding="utf-8"))
            return proc, data

    def test_high_confidence_phrase_blocks(self):
        proc, data = self.run_scan({"app.py": "# Let me think about what the user wants.\n"})
        self.assertEqual(proc.returncode, 1)
        self.assertGreaterEqual(data["counts"]["high"], 1)

    def test_medium_phrase_warns_but_does_not_block_default(self):
        proc, data = self.run_scan({"app.py": "# I should refactor this helper later.\n"})
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(data["counts"]["medium"], 1)

    def test_suppression_skips_next_line(self):
        proc, data = self.run_scan({
            "app.py": "# reasoning-trace-audit: ignore-next-line -- regression fixture\n# Let me think about this case.\n"
        })
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(data["counts"]["high"], 0)

    def test_excluded_path_is_not_scanned(self):
        proc, data = self.run_scan({"scanner/tests/fixtures/leak.txt": "Let me think about the user.\n"})
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(data["counts"]["high"], 0)


if __name__ == "__main__":
    unittest.main()
