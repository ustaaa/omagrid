import importlib.util
from pathlib import Path
import tempfile
import unittest

CHECKER = Path(__file__).with_name("check-omagrid-identity.py")
spec = importlib.util.spec_from_file_location("check_omagrid_identity", CHECKER)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

CI = """name: checks
on:
  push:
    branches: [main, pilot]
  pull_request:
  workflow_dispatch:
permissions:
  contents: read
jobs:
  linux:
    runs-on: ubuntu-latest
"""
MAC = """name: mac compile
on:
  workflow_dispatch:
permissions:
  contents: read
jobs:
  build:
    runs-on: macos-latest
    steps:
      - run: cargo build
"""


class WorkflowIdentityTests(unittest.TestCase):
    def validate(self, ci=CI, mac=MAC, extra=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ci.yml").write_text(ci)
            (root / "macos-check.yml").write_text(mac)
            if extra:
                (root / extra).write_text("name: extra\n")
            return checker.validate_workflows(root)

    def test_accepts_only_ci_and_manual_macos_compile_workflows(self):
        self.assertEqual(self.validate(), [])

    def test_rejects_unlisted_workflow(self):
        self.assertTrue(any("Unexpected active workflow" in e for e in self.validate(extra="release.yml")))

    def test_ci_requires_main_and_pilot_and_rejects_release_job(self):
        bad_branches = CI.replace("[main, pilot]", "[main]")
        self.assertTrue(any("branches must be exactly main and pilot" in e for e in self.validate(ci=bad_branches)))
        release_job = CI + "  release:\n    runs-on: ubuntu-latest\n"
        self.assertTrue(any("must not define release" in e for e in self.validate(ci=release_job)))

    def test_macos_is_manual_read_only_and_compile_only(self):
        pr_trigger = MAC.replace("  workflow_dispatch:\n", "  workflow_dispatch:\n  pull_request:\n")
        self.assertTrue(any("manual-only" in e for e in self.validate(mac=pr_trigger)))
        writable = MAC.replace("contents: read", "contents: write")
        self.assertTrue(any("read-only contents" in e for e in self.validate(mac=writable)))
        extra_permission = MAC.replace("  contents: read", "  contents: read\n  id-token: write")
        self.assertTrue(any("read-only contents" in e for e in self.validate(mac=extra_permission)))
        unpinned = MAC.replace("uses: none", "uses: actions/checkout@v4")
        unpinned = unpinned.replace("- run: cargo build", "- uses: actions/checkout@v4\n      - run: cargo build")
        self.assertTrue(any("Unpinned action" in e for e in self.validate(mac=unpinned)))
        signed = MAC.replace("cargo build", "cargo build && codesign app")
        self.assertTrue(any("only compile" in e for e in self.validate(mac=signed)))


if __name__ == "__main__":
    unittest.main()
