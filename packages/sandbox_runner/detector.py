# packages/sandbox-runner/src/detector.py
"""Runtime and test framework detection for repository worktrees."""

from pathlib import Path
import sys
import structlog

from .models import RuntimeType

logger = structlog.get_logger(__name__)


class RuntimeDetector:
    """Inspects a repository filesystem to identify runtime technology and test command."""

    @staticmethod
    def detect_runtime(workspace_path: Path | str) -> RuntimeType:
        """Inspect directory markers to identify target application language.

        Args:
            workspace_path: Root path of the codebase to inspect.

        Returns:
            Identified RuntimeType enum.
        """
        root = Path(workspace_path)

        if (
            (root / "pyproject.toml").exists()
            or (root / "requirements.txt").exists()
            or (root / "setup.py").exists()
            or any(root.glob("*.py"))
        ):
            return RuntimeType.PYTHON

        if (root / "package.json").exists():
            return RuntimeType.NODE

        if (root / "go.mod").exists():
            return RuntimeType.GO

        return RuntimeType.UNKNOWN

    @staticmethod
    def get_test_command(runtime: RuntimeType, workspace_path: Path | str) -> list[str]:
        """Resolve the standard test execution command for the detected runtime.

        Args:
            runtime: Identified application runtime.
            workspace_path: Root path of the codebase to inspect.

        Returns:
            Command arguments array suitable for execution.
        """
        root = Path(workspace_path)
        logger.info("resolving_test_command", runtime=runtime.value, path=str(root))

        if runtime == RuntimeType.PYTHON:
            # Use current python executable running pytest
            return [sys.executable, "-m", "pytest", "-q"]

        if runtime == RuntimeType.NODE:
            if (root / "pnpm-lock.yaml").exists():
                return ["pnpm", "test"]
            return ["npm", "test"]

        if runtime == RuntimeType.GO:
            return ["go", "test", "./..."]

        return [sys.executable, "-m", "unittest"]
