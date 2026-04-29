"""Linter and formatter tool with auto-detection."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.schema import BooleanSchema, StringSchema, tool_parameters_schema

_MAX_OUTPUT = 10_000


@tool_parameters(
    tool_parameters_schema(
        path=StringSchema(
            "File or directory to lint (relative to workspace). Defaults to '.' for the whole project."
        ),
        tool=StringSchema(
            "Linter/formatter to use. Auto-detected if omitted. "
            "Supported: 'ruff' (Python), 'pylint' (Python), 'eslint' (JS/TS), 'prettier' (JS/TS/CSS).",
            nullable=True,
        ),
        fix=BooleanSchema(
            description="Auto-fix issues where supported (default false). "
            "ruff and eslint support --fix; prettier formats in place.",
            default=False,
        ),
        required=[],
    )
)
class LintTool(Tool):
    """Run a linter or formatter on workspace code with auto-detection."""

    def __init__(self, workspace: str = "."):
        self.workspace = Path(workspace).resolve()

    @property
    def name(self) -> str:
        return "lint"

    @property
    def description(self) -> str:
        return (
            "Lint or format code in the workspace. "
            "Auto-detects ruff/pylint for Python and eslint/prettier for JS/TS. "
            "Set fix=true to apply auto-fixes. "
            "Always run this before committing to catch style and logic issues."
        )

    async def execute(
        self,
        path: str = ".",
        tool: str | None = None,
        fix: bool = False,
        **kwargs: Any,
    ) -> str:
        target = self._resolve(path)
        if not target.exists():
            return f"Error: path not found: {path}"

        linter = tool or self._detect(target)
        if not linter:
            return (
                "Error: could not auto-detect a linter. "
                "Install ruff (Python) or eslint (JS/TS), or specify tool= explicitly."
            )

        cmd = self._build_cmd(linter, target, fix)
        if cmd is None:
            return f"Error: unsupported tool '{linter}'. Supported: ruff, pylint, eslint, prettier."

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace),
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=60
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return f"Error: {linter} timed out after 60 seconds"

            out = stdout.decode("utf-8", errors="replace")
            err = stderr.decode("utf-8", errors="replace").strip()

            parts = [f"Tool: {linter}", f"Path: {path}"]
            if out.strip():
                parts.append(out)
            if err:
                parts.append(f"STDERR:\n{err}")
            parts.append(f"\nExit code: {process.returncode}")

            result = "\n".join(parts)
            if len(result) > _MAX_OUTPUT:
                half = _MAX_OUTPUT // 2
                result = (
                    result[:half]
                    + f"\n\n... ({len(result) - _MAX_OUTPUT:,} chars truncated) ...\n\n"
                    + result[-half:]
                )
            return result

        except FileNotFoundError:
            return f"Error: '{linter}' is not installed or not found in PATH"
        except Exception as e:
            return f"Error running {linter}: {e}"

    def _detect(self, target: Path) -> str | None:
        """Auto-detect linter based on project files."""
        ws = self.workspace

        # Check for Python project
        has_python = (
            any(ws.glob("*.py"))
            or any(ws.glob("**/*.py"))
            or (ws / "pyproject.toml").exists()
            or (ws / "setup.py").exists()
        )

        # Check for JS/TS project
        has_js = (
            (ws / "package.json").exists()
            or any(ws.glob("**/*.ts"))
            or any(ws.glob("**/*.js"))
        )

        if has_python:
            # Prefer ruff, fall back to pylint
            import shutil
            if shutil.which("ruff"):
                return "ruff"
            if shutil.which("pylint"):
                return "pylint"

        if has_js:
            import shutil
            if shutil.which("eslint"):
                return "eslint"
            if shutil.which("prettier"):
                return "prettier"

        return None

    def _build_cmd(self, linter: str, target: Path, fix: bool) -> list[str] | None:
        t = str(target)
        if linter == "ruff":
            cmd = ["ruff", "check", t]
            if fix:
                cmd.append("--fix")
            return cmd
        if linter == "pylint":
            return ["pylint", t, "--output-format=text"]
        if linter == "eslint":
            cmd = ["eslint", t]
            if fix:
                cmd.append("--fix")
            return cmd
        if linter == "prettier":
            if fix:
                return ["prettier", "--write", t]
            return ["prettier", "--check", t]
        return None

    def _resolve(self, path: str) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        return self.workspace / p
