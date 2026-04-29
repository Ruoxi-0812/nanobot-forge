"""Package manager tool with auto-detection for pip and npm/yarn/pnpm."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.schema import BooleanSchema, StringSchema, ArraySchema, tool_parameters_schema

_MAX_OUTPUT = 10_000


@tool_parameters(
    tool_parameters_schema(
        action=StringSchema(
            "Package manager action to perform.",
            enum=["install", "uninstall", "list", "update"],
        ),
        packages=ArraySchema(
            items=StringSchema(""),
            description="Package names to install or uninstall. Leave empty for 'list' and 'update all'.",
        ),
        manager=StringSchema(
            "Package manager to use. Auto-detected if omitted. "
            "Supported: 'pip', 'npm', 'yarn', 'pnpm'.",
            nullable=True,
        ),
        dev=BooleanSchema(
            description="Install as a development dependency (npm/yarn/pnpm only, default false).",
            default=False,
        ),
        required=["action"],
    )
)
class PackageManagerTool(Tool):
    """Install, uninstall, and list packages using pip or npm/yarn/pnpm."""

    def __init__(self, workspace: str = ".", python_executable: str = "python"):
        self.workspace = Path(workspace).resolve()
        self.python_executable = python_executable

    @property
    def name(self) -> str:
        return "pkg"

    @property
    def description(self) -> str:
        return (
            "Manage project dependencies using pip (Python) or npm/yarn/pnpm (JS/TS). "
            "Actions: install, uninstall, list, update. "
            "Auto-detects the right package manager from project files."
        )

    async def execute(
        self,
        action: str,
        packages: list[str] | None = None,
        manager: str | None = None,
        dev: bool = False,
        **kwargs: Any,
    ) -> str:
        packages = packages or []
        pkg_manager = manager or self._detect()
        if not pkg_manager:
            return (
                "Error: could not auto-detect a package manager. "
                "Add a requirements.txt or package.json, or specify manager= explicitly."
            )

        cmd = self._build_cmd(pkg_manager, action, packages, dev)
        if cmd is None:
            return f"Error: unsupported action '{action}' for '{pkg_manager}'."

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.workspace),
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=120
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return f"Error: {pkg_manager} timed out after 120 seconds"

            out = stdout.decode("utf-8", errors="replace")
            err = stderr.decode("utf-8", errors="replace").strip()

            parts = [f"Manager: {pkg_manager}", f"Action: {action}"]
            if packages:
                parts.append(f"Packages: {', '.join(packages)}")
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
            return f"Error: '{pkg_manager}' is not installed or not found in PATH"
        except Exception as e:
            return f"Error running {pkg_manager}: {e}"

    def _detect(self) -> str | None:
        """Auto-detect package manager from project files."""
        ws = self.workspace
        import shutil

        # JS/TS: check lock files first (most specific), then package.json
        if (ws / "pnpm-lock.yaml").exists() and shutil.which("pnpm"):
            return "pnpm"
        if (ws / "yarn.lock").exists() and shutil.which("yarn"):
            return "yarn"
        if (ws / "package.json").exists() and shutil.which("npm"):
            return "npm"

        # Python: check for any Python project indicators
        has_python = (
            (ws / "requirements.txt").exists()
            or (ws / "pyproject.toml").exists()
            or (ws / "setup.py").exists()
            or any(ws.glob("*.py"))
        )
        if has_python and shutil.which("pip"):
            return "pip"

        return None

    def _build_cmd(
        self, manager: str, action: str, packages: list[str], dev: bool
    ) -> list[str] | None:
        if manager == "pip":
            if action == "install":
                if not packages:
                    # Install from requirements.txt
                    return [self.python_executable, "-m", "pip", "install", "-r", "requirements.txt"]
                return [self.python_executable, "-m", "pip", "install"] + packages
            if action == "uninstall":
                if not packages:
                    return None
                return [self.python_executable, "-m", "pip", "uninstall", "-y"] + packages
            if action == "list":
                return [self.python_executable, "-m", "pip", "list"]
            if action == "update":
                if not packages:
                    return None
                return [self.python_executable, "-m", "pip", "install", "--upgrade"] + packages
            return None

        # npm / yarn / pnpm
        dev_flag: list[str] = []
        if dev:
            if manager == "npm":
                dev_flag = ["--save-dev"]
            elif manager in ("yarn", "pnpm"):
                dev_flag = ["--dev"]

        if manager == "npm":
            if action == "install":
                return ["npm", "install"] + (packages if packages else []) + dev_flag
            if action == "uninstall":
                return ["npm", "uninstall"] + packages if packages else None
            if action == "list":
                return ["npm", "list", "--depth=0"]
            if action == "update":
                return ["npm", "update"] + packages
        elif manager in ("yarn", "pnpm"):
            if action == "install":
                sub = "add" if packages else "install"
                return [manager, sub] + packages + dev_flag
            if action == "uninstall":
                return [manager, "remove"] + packages if packages else None
            if action == "list":
                return [manager, "list"]
            if action == "update":
                return [manager, "upgrade"] + packages

        return None
