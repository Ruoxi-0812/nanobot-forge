"""Git operations tool for workspace version control."""

from __future__ import annotations

import asyncio
import re
import shlex
from pathlib import Path
from typing import Any

from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.schema import StringSchema, tool_parameters_schema

_MAX_OUTPUT = 10_000

_BLOCKED_PATTERNS = [
    r"\bpush\b.*--force\b",        # force push
    r"\bpush\b.*-f\b",             # force push shorthand
    r"\breset\b.*--hard\b",        # hard reset
    r"\bclean\b.*-[fdx]+\b",       # clean tracked/untracked files
    r"\breflog\b.*delete\b",       # delete reflog
    r"\bfilter-branch\b",          # rewrite history
    r"\bupdate-ref\b.*-d\b",       # delete ref
]


@tool_parameters(
    tool_parameters_schema(
        command=StringSchema(
            "The git subcommand and arguments. Examples: 'status', 'diff --staged', "
            "'log --oneline -10', 'add src/main.py', 'commit -m \"fix: update auth\"', "
            "'branch feature/new', 'checkout main', 'pull origin main'."
        ),
        required=["command"],
    )
)
class GitTool(Tool):
    """Run git commands in the project workspace."""

    def __init__(self, workspace: str = "."):
        self.workspace = Path(workspace).resolve()

    @property
    def name(self) -> str:
        return "git"

    @property
    def description(self) -> str:
        return (
            "Run git commands in the workspace. "
            "Use for: status checks, staging files (add), committing, diffing, "
            "viewing history (log), branching, pulling, and pushing. "
            "Destructive operations like force-push and hard-reset are blocked."
        )

    async def execute(self, command: str, **kwargs: Any) -> str:
        command = command.strip()
        if not command:
            return "Error: command is required"

        blocked = self._guard(command)
        if blocked:
            return blocked

        parts = ["git"] + shlex.split(command)

        try:
            process = await asyncio.create_subprocess_exec(
                *parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace),
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=30
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return "Error: git command timed out after 30 seconds"

            out = stdout.decode("utf-8", errors="replace")
            err = stderr.decode("utf-8", errors="replace").strip()

            parts_out = []
            if out.strip():
                parts_out.append(out)
            if err:
                parts_out.append(f"STDERR:\n{err}")
            parts_out.append(f"\nExit code: {process.returncode}")

            result = "\n".join(parts_out) if parts_out else "(no output)"
            if len(result) > _MAX_OUTPUT:
                half = _MAX_OUTPUT // 2
                result = (
                    result[:half]
                    + f"\n\n... ({len(result) - _MAX_OUTPUT:,} chars truncated) ...\n\n"
                    + result[-half:]
                )
            return result

        except FileNotFoundError:
            return "Error: git is not installed or not found in PATH"
        except Exception as e:
            return f"Error running git {command}: {e}"

    @staticmethod
    def _guard(command: str) -> str | None:
        lower = command.lower()
        for pattern in _BLOCKED_PATTERNS:
            if re.search(pattern, lower):
                return (
                    f"Error: blocked by safety guard — '{command}' is a destructive git operation. "
                    "Use exec if you intentionally need this."
                )
        return None
