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

- Runs a Python file in the workspace and captures stdout, stderr, and exit code
- Prefer this over `exec python <file>` for Python execution — it validates the file exists first
- Supports optional command-line args and a configurable timeout (default 30s, max 300s)
- Output is truncated at 10,000 characters
- Use this for: running scripts, testing individual modules, reproducing errors

## run_tests — Run the Test Suite

- Runs pytest in the workspace and returns a pass/fail summary
- Specify `path` to run a specific test file or directory; omit to run all tests
- Use `verbose=true` to see individual test names and results
- Timeout defaults to 120s — increase for large test suites (max 600s)
- Always run this after modifying code to confirm nothing is broken

## sandbox_exec — Sandboxed Python Snippet

- Executes a Python code snippet (not a file) with import restrictions
- Blocked by default: os, subprocess, sys, socket, ctypes, shutil, pickle, and more
- Short timeout (default 10s, max 60s) — use for quick computations or logic checks
- Use this to safely test isolated code fragments without file system access
- Not a substitute for `run_code` when you need full environment access

## exec — Safety Limits

- Commands have a configurable timeout (default 60s)
- Dangerous commands are blocked (rm -rf, format, dd, shutdown, etc.)
- Output is truncated at 10,000 characters
- `restrictToWorkspace` config can limit file access to the workspace

## glob — File Discovery

- Use `glob` to find files by pattern before falling back to shell commands
- Simple patterns like `*.py` match recursively by filename
- Use `entry_type="dirs"` when you need matching directories instead of files
- Use `head_limit` and `offset` to page through large result sets
- Prefer this over `exec` when you only need file paths

## grep — Content Search

- Use `grep` to search file contents inside the workspace
- Default behavior returns only matching file paths (`output_mode="files_with_matches"`)
- Supports optional `glob` filtering plus `context_before` / `context_after`
- Supports `type="py"`, `type="ts"`, `type="md"` and similar shorthand filters
- Use `fixed_strings=true` for literal keywords containing regex characters
- Use `output_mode="files_with_matches"` to get only matching file paths
- Use `output_mode="count"` to size a search before reading full matches
- Use `head_limit` and `offset` to page across results
- Prefer this over `exec` for code and history searches
- Binary or oversized files may be skipped to keep results readable

## cron — Scheduled Reminders

- Please refer to cron skill for usage.
