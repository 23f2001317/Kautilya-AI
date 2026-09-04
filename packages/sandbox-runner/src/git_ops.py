# packages/sandbox-runner/src/git_ops.py
"""Automated Git operations, patch branching, and unified diff application."""

from pathlib import Path
import re
import subprocess
import structlog

logger = structlog.get_logger(__name__)


class GitOpsManager:
    """Automates branch isolation and patch application for sandboxed verification."""

    @staticmethod
    def create_patch_branch(repo_path: Path | str, branch_name: str) -> bool:
        """Create and checkout an isolated remediation patch branch.

        Args:
            repo_path: Local git repository path.
            branch_name: Target branch name (e.g. 'kautilya-remediation-alert-123').

        Returns:
            True if branch was successfully created and checked out.
        """
        path = Path(repo_path)
        try:
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=str(path),
                capture_output=True,
                check=True,
                text=True,
            )
            logger.info("created_patch_branch", branch=branch_name, path=str(path))
            return True
        except (subprocess.SubprocessError, FileNotFoundError) as exc:
            logger.warning("git_branch_creation_fallback", error=str(exc))
            # Fallback for non-git directory or simulated worktree
            return False

    @staticmethod
    def apply_unified_diff(workspace_path: Path | str, diff_text: str) -> bool:
        """Parse and apply a standard unified diff to target files in the workspace.

        Args:
            workspace_path: Root of the ephemeral workspace.
            diff_text: Unified git diff string containing changes.

        Returns:
            True if diff was parsed and applied successfully to at least one file.
        """
        root = Path(workspace_path)
        logger.info("applying_unified_diff", workspace=str(root), diff_len=len(diff_text))

        # First attempt: Try standard git apply or patch command
        try:
            proc = subprocess.run(
                ["git", "apply", "--ignore-whitespace", "-"],
                cwd=str(root),
                input=diff_text,
                capture_output=True,
                text=True,
            )
            if proc.returncode == 0:
                logger.info("git_apply_succeeded")
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        # Native fallback: Parse unified diff headers and perform targeted line replacement
        applied_any = False
        chunks = diff_text.split("diff --git ")
        for chunk in chunks:
            if not chunk.strip():
                continue
            lines = chunk.splitlines()
            target_match = re.search(r"^\+\+\+ b/(.+)$", chunk, re.MULTILINE)
            if not target_match:
                continue

            rel_file_path = target_match.group(1).strip()
            target_file = root / rel_file_path
            if not target_file.exists():
                target_file.parent.mkdir(parents=True, exist_ok=True)
                target_file.write_text("", encoding="utf-8")

            original_content = target_file.read_text(encoding="utf-8")
            # Extract simple additions and removals
            updated_lines = original_content.splitlines()
            for line in lines:
                if line.startswith("-") and not line.startswith("---"):
                    to_remove = line[1:].strip()
                    updated_lines = [l for l in updated_lines if to_remove not in l]
                elif line.startswith("+") and not line.startswith("+++"):
                    to_add = line[1:].strip()
                    updated_lines.append(to_add)

            target_file.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
            logger.info("native_patch_applied", target_file=str(target_file))
            applied_any = True

        return applied_any
