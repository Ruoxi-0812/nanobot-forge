"""Execute a Python code snippet in a sandboxed environment with import restrictions."""

from __future__ import annotations

import asyncio
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Any

from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.schema import IntegerSchema, StringSchema, tool_parameters_schema

_MAX_OUTPUT = 5_000

_DEFAULT_BLOCKED: list[str] = [
    "os", "subprocess", "sys", "socket", "ctypes",
    "shutil", "tempfile", "pickle", "importlib",
    "multiprocessing", "threading",
]

_WRAPPER_TEMPLATE = textwrap.dedent("""\
    import sys as _sys_internal

    _BLOCKED = {blocked!r}

    class _BlockImporter:
        def find_module(self, name, path=None):
            if name.split('.')[0] in _BLOCKED:
                return self
            return None
        def load_module(self, name):
            raise ImportError(f"Import of '{{name}}' is blocked in sandbox mode")

    _sys_internal.meta_path.insert(0, _BlockImporter())

    # --- user code ---
    {code}
""")


@tool_parameters(
    tool_parameters_schema(
        code=StringSchema("Python code snippet to execute in the sandbox"),
        timeout=IntegerSchema(
            10,
            description="Execution timeout in seconds (default 10, max 60)",
            minimum=1,
            maximum=60,
        ),
        required=["code"],
    )
)
class PythonSandboxTool(Tool):
    """Execute a Python snippet with restricted imports and a short timeout."""

    def __init__(
        self,
        blocked_imports: list[str] | None = None,
        timeout: int = 10,
    ):
        self.blocked_imports = blocked_imports if blocked_imports is not None else _DEFAULT_BLOCKED
        self.default_timeout = timeout

    @property
    def name(self) -> str:
        return "sandbox_exec"

    @property
    def description(self) -> str:
        blocked_preview = ", ".join(self.blocked_imports[:6])
        return (
            "Execute a Python code snippet in a sandboxed environment with import restrictions. "
            f"Blocked imports include: {blocked_preview}, and more. "
            "Use this for quick logic checks on isolated code fragments. "
            "For full execution with file system access, use run_code instead."
        )

    async def execute(
        self,
        code: str,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> str:
        effective_timeout = min(timeout or self.default_timeout, 60)
        wrapped = _WRAPPER_TEMPLATE.format(blocked=self.blocked_imports, code=code)

        tmp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as f:
                f.write(wrapped)
                tmp_path = f.name

            process = await asyncio.create_subprocess_exec(
                sys.executable,
                tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
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
                label = "Sandbox violation" if "blocked in sandbox mode" in stderr_text else "STDERR"
                parts.append(f"{label}:\n{stderr_text}")
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
            return f"Error in sandbox execution: {e}"
        finally:
            if tmp_path:
                Path(tmp_path).unlink(missing_ok=True)
