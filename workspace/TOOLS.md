# Tool Usage Notes

Tool signatures are provided automatically via function calling.
This file documents non-obvious constraints and usage patterns.

## git — Version Control

- Run any git subcommand in the workspace: `status`, `diff`, `log`, `add`, `commit`, `branch`, `checkout`, `push`, `pull`
- Destructive operations (force-push, hard-reset, clean) are blocked — use `exec` if truly needed
- Examples: `git(command="status")`, `git(command="diff --staged")`, `git(command="commit -m 'fix: auth bug'")`
- Use `log --oneline -20` to review recent history before committing

## lint — Lint and Format

- Auto-detects ruff or pylint for Python, eslint or prettier for JS/TS
- Set `fix=true` to apply auto-fixes in place
- Specify `tool=` to override auto-detection (e.g. `tool="ruff"`)
- Run before committing to catch style and logic issues early

## pkg — Package Manager

- Auto-detects pip (Python) or npm/yarn/pnpm (JS/TS) from project files
- Actions: `install`, `uninstall`, `list`, `update`
- `install` with no packages reads from requirements.txt / package.json
- Use `dev=true` for npm/yarn/pnpm dev dependencies
- Examples: `pkg(action="install", packages=["requests"])`, `pkg(action="list")`

## run_code — Execute a Python File

- Runs a Python file and captures stdout, stderr, and exit code
- Supports optional command-line args and a configurable timeout (default 30s)
- Use this for: running scripts, testing individual modules, reproducing errors

## run_tests — Run the Test Suite

- Runs pytest and returns a pass/fail summary
- Specify `path` to run a specific test file or directory; omit for all tests
- Use `verbose=true` to see individual test names
- Always run this after modifying code to confirm nothing is broken

## sandbox_exec — Sandboxed Python Snippet

- Executes a Python code snippet with import restrictions
- Blocked: os, subprocess, sys, socket, ctypes, shutil, pickle, and more
- Short timeout (default 10s) — for quick logic checks only
- Use `run_code` instead when you need full environment access

## exec — Shell Commands

- Commands have a configurable timeout (default 60s)
- Dangerous commands are blocked (rm -rf, format, dd, shutdown, etc.)
- Output is truncated at 10,000 characters

## glob — File Discovery

- Use `glob` to find files by pattern (e.g. `*.py`, `tests/**/*.py`)
- Prefer this over `exec find` when you only need file paths

## grep — Content Search

- Use `grep` to search file contents inside the workspace
- Supports regex patterns and file type filters (`type="py"`, `type="ts"`)
- Use `output_mode="content"` with context lines to see matching code

## cron — Scheduled Reminders

- Please refer to cron skill for usage.
