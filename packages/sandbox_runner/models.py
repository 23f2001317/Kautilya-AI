# packages/sandbox-runner/src/models.py
"""Data models for ephemeral sandbox execution and test verification."""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class RuntimeType(str, Enum):
    """Supported application runtimes for ephemeral sandboxing."""

    PYTHON = "python"
    NODE = "node"
    GO = "go"
    UNKNOWN = "unknown"


class SandboxConfig(BaseModel):
    """Configuration for provisioning an isolated ephemeral sandbox environment."""

    sandbox_id: str
    target_repo_path: str
    network_disabled: bool = Field(
        default=True, description="Enforce strict network isolation inside sandbox"
    )
    timeout_seconds: float = Field(
        default=10.0, description="Max allowed execution duration before timeout"
    )
    environment_vars: dict[str, str] = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    """Low-level execution results of a command run within the sandbox."""

    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    execution_time_ms: float
    timed_out: bool = False


class VerificationReport(BaseModel):
    """High-level verification evaluation parsed from test execution output."""

    sandbox_id: str
    runtime: RuntimeType
    status: str = Field(description="'passed' or 'failed'")
    passed_tests: int = 0
    failed_tests: int = 0
    errors: list[str] = Field(default_factory=list)
    raw_logs: str = ""
    duration_ms: float = 0.0
    exit_code: int = 0
    patch_applied: bool = False
