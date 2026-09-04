# apps/tests/test_phase3.py
"""Test verification for Phase 3: Ephemeral Sandboxing & Patch Verification."""

import sys
import tempfile
from pathlib import Path

from packages.sandbox_runner.detector import RuntimeDetector
from packages.sandbox_runner.git_ops import GitOpsManager
from packages.sandbox_runner.models import RuntimeType, SandboxConfig
from packages.sandbox_runner.runner import (
    EphemeralSandboxService,
    LocalEphemeralSandboxRuntime,
)


def test_runtime_detector_python() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        p = Path(tmp_dir)
        (p / "pyproject.toml").write_text("[project]\nname='demo'", encoding="utf-8")

        detected = RuntimeDetector.detect_runtime(p)
        assert detected == RuntimeType.PYTHON

        cmd = RuntimeDetector.get_test_command(detected, p)
        assert cmd[1:] == ["-m", "pytest", "-q"]


def test_runtime_detector_node() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        p = Path(tmp_dir)
        (p / "package.json").write_text('{"name": "demo"}', encoding="utf-8")

        detected = RuntimeDetector.detect_runtime(p)
        assert detected == RuntimeType.NODE

        cmd = RuntimeDetector.get_test_command(detected, p)
        assert cmd == ["npm", "test"]


def test_git_ops_apply_unified_diff() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        p = Path(tmp_dir)
        src_file = p / "src" / "db" / "pool.py"
        src_file.parent.mkdir(parents=True, exist_ok=True)
        src_file.write_text(
            "class DBConfig:\n    max_connections: int = 2\n    pool_timeout: int = 2\n",
            encoding="utf-8",
        )

        diff = """diff --git a/src/db/pool.py b/src/db/pool.py
--- a/src/db/pool.py
+++ b/src/db/pool.py
@@ -2,2 +2,2 @@
-    max_connections: int = 2
+    max_connections: int = 50
"""
        applied = GitOpsManager.apply_unified_diff(p, diff)
        assert applied is True
        content = src_file.read_text(encoding="utf-8")
        assert "max_connections: int = 50" in content


def test_ephemeral_sandbox_execution_and_teardown() -> None:
    with tempfile.TemporaryDirectory() as src_dir:
        p = Path(src_dir)
        # Create minimal python test file
        test_file = p / "test_sample.py"
        test_file.write_text(
            "def test_success():\n    assert 1 + 1 == 2\n",
            encoding="utf-8",
        )

        service = EphemeralSandboxService(LocalEphemeralSandboxRuntime())
        config = SandboxConfig(
            sandbox_id="test-sbx-1",
            target_repo_path=str(p),
            network_disabled=True,
            timeout_seconds=8.0,
        )

        report = service.run_verification(config, "")

        assert report.status == "passed"
        assert report.passed_tests >= 1
        assert report.failed_tests == 0
        assert report.duration_ms < 10000.0  # Under 10s per DoD


def test_ephemeral_sandbox_timeout_handling() -> None:
    with tempfile.TemporaryDirectory() as src_dir:
        p = Path(src_dir)
        # Create test that sleeps longer than timeout
        test_file = p / "test_timeout.py"
        test_file.write_text(
            "import time\ndef test_sleep():\n    time.sleep(3)\n",
            encoding="utf-8",
        )

        service = EphemeralSandboxService(LocalEphemeralSandboxRuntime())
        config = SandboxConfig(
            sandbox_id="test-sbx-timeout",
            target_repo_path=str(p),
            network_disabled=True,
            timeout_seconds=0.5,  # short timeout to test guard
        )

        report = service.run_verification(config, "")

        assert report.status == "failed"
        assert any("timed out" in err.lower() for err in report.errors)
