"""Execute a Python file and capture its output."""

from __future__ import annotations

import asyncio
import shlex
import sys
from pathlib import Path
from typing import Any

from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.schema import IntegerSchema, StringSchema, tool_parameters_schema

_MAX_OUTPUT = 10_000


@tool_parameters(
    tool_parameters_schema(
        file_path=StringSchema(
            "Path to the Python file to execute (relative to workspace or absolute)"
        ),
        args=StringSchema("Optional command-line arguments to pass to the script"),
        timeout=IntegerSchema(
            30,
            description="Execution timeout in seconds (default 30, max 300)",
            minimum=1,
            maximum=300,
        ),
        required=["file_path"],
    )
)
class RunCodeTool(Tool):
    """Execute a Python file and return stdout, stderr, and exit code."""

    def __init__(
        self,
        workspace: str = ".",
        python_executable: str = "python",
        timeout: int = 30,
    ):
        self.workspace = Path(workspace).resolve()
        self.python_executable = python_executable
        self.default_timeout = timeout

    @property
    def name(self) -> str:
        return "run_code"

    @property
    def description(self) -> str:
        return (
            "Execute a Python file and capture its stdout, stderr, and exit code. "
            "Use this to run scripts, test modules, or reproduce errors. "
            "Prefer this over exec for Python file execution."
        )

    async def execute(
        self,
        file_path: str,
        args: str = "",
        timeout: int | None = None,
        **kwargs: Any,
    ) -> str:
        resolved = self._resolve_path(file_path)
        if not resolved.exists():
            return f"Error: File not found: {file_path}"
        if not resolved.is_file():
            return f"Error: Path is not a file: {file_path}"

        effective_timeout = min(timeout or self.default_timeout, 300)

        cmd_parts = [self.python_executable, str(resolved)]
        if args.strip():
            cmd_parts.extend(shlex.split(args))

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace),
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=effective_timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return f"Error: Execution timed out after {effective_timeout} seconds"

            parts = []
            if stdout:
                parts.append(stdout.decode("utf-8", errors="replace"))
            stderr_text = stderr.decode("utf-8", errors="replace").strip() if stderr else ""
            if stderr_text:
                parts.append(f"STDERR:\n{stderr_text}")
            parts.append(f"\nExit code: {process.returncode}")

            result = "\n".join(parts) if parts else "(no output)"
            if len(result) > _MAX_OUTPUT:
                half = _MAX_OUTPUT // 2
                result = (
                    result[:half]
                    + f"\n\n... ({len(result) - _MAX_OUTPUT:,} chars truncated) ...\n\n"
                    + result[-half:]
                )
            return result

        except Exception as e:
            return f"Error executing file: {e}"

    def _resolve_path(self, file_path: str) -> Path:
        p = Path(file_path)
        if p.is_absolute():
            return p
        return self.workspace / p
