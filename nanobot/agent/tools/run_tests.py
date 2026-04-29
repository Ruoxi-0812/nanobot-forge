"""Run the test suite using pytest and return a pass/fail summary."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.schema import BooleanSchema, IntegerSchema, StringSchema, tool_parameters_schema

_MAX_OUTPUT = 10_000


@tool_parameters(
    tool_parameters_schema(
        path=StringSchema(
            "Path to a test file or directory (relative to workspace). "
            "Leave empty to run all tests in the workspace."
        ),
        verbose=BooleanSchema(
            description="Show individual test names and results (default false)",
            default=False,
        ),
        timeout=IntegerSchema(
            120,
            description="Execution timeout in seconds (default 120, max 600)",
            minimum=1,
            maximum=600,
        ),
        required=[],
    )
)
class RunTestsTool(Tool):
    """Run pytest and return a pass/fail summary."""

    def __init__(
        self,
        workspace: str = ".",
        python_executable: str = "python",
        timeout: int = 120,
    ):
        self.workspace = Path(workspace).resolve()
        self.python_executable = python_executable
        self.default_timeout = timeout

    @property
    def name(self) -> str:
        return "run_tests"

    @property
    def description(self) -> str:
        return (
            "Run the test suite using pytest and return a summary of results. "
            "Use this after modifying code to verify correctness. "
            "Specify path to run a subset of tests; omit to run all tests."
        )

    async def execute(
        self,
        path: str = "",
        verbose: bool = False,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> str:
        effective_timeout = min(timeout or self.default_timeout, 600)

        cmd_parts = [self.python_executable, "-m", "pytest", "--tb=short", "--no-header", "-q"]
        if verbose:
            cmd_parts.append("-v")

        if path.strip():
            target = self._resolve_path(path)
            if not target.exists():
                return f"Error: Test path not found: {path}"
            cmd_parts.append(str(target))

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
                return f"Error: Test run timed out after {effective_timeout} seconds"

            output = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace").strip() if stderr else ""

            parts = [output]
            if stderr_text:
                parts.append(f"STDERR:\n{stderr_text}")

            summary = _extract_summary(output)
            if summary:
                parts.append(f"\n--- Summary ---\n{summary}")
            parts.append(f"Exit code: {process.returncode}")

            result = "\n".join(parts)
            if len(result) > _MAX_OUTPUT:
                half = _MAX_OUTPUT // 2
                result = (
                    result[:half]
                    + f"\n\n... ({len(result) - _MAX_OUTPUT:,} chars truncated) ...\n\n"
                    + result[-half:]
                )
            return result

        except Exception as e:
            return f"Error running tests: {e}"

    def _resolve_path(self, path: str) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        return self.workspace / p


def _extract_summary(output: str) -> str:
    lines = output.strip().splitlines()
    summary_lines = []
    for line in reversed(lines):
        stripped = line.strip()
        if re.search(r"(passed|failed|error|warning)", stripped, re.IGNORECASE):
            summary_lines.insert(0, stripped)
            if len(summary_lines) >= 3:
                break
    return "\n".join(summary_lines)
