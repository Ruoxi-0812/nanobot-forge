# Agent Instructions

## Coding Workflow

When given a coding task, follow this loop:
1. **Understand** — Use `read_file`, `glob`, `grep` to explore the workspace and understand the codebase.
2. **Plan** — For multi-step tasks, outline the approach and confirm with the user before making changes.
3. **Act** — Use `write_file` or `edit_file` to create or modify code.
4. **Execute** — Use `run_code` to run the file, or `exec` for shell commands.
5. **Observe** — Read stdout, stderr, and exit codes carefully to understand what happened.
6. **Debug** — If the code fails, analyze the error, fix it, and re-run. Repeat until success.
7. **Validate** — Use `run_tests` to verify the implementation passes the test suite.

## Debugging Rules

- Never declare a task complete until the code runs successfully.
- Capture the full error message before attempting a fix.
- Fix one issue at a time and re-run to confirm before moving on.
- If stuck after 3 attempts, explain the issue to the user and ask for guidance.

## Scheduled Reminders

Before scheduling reminders, check available skills and follow skill guidance first.
Use the built-in `cron` tool to create/list/remove jobs (do not call `nanobot cron` via `exec`).
Get USER_ID and CHANNEL from the current session (e.g., `8281248569` and `telegram` from `telegram:8281248569`).

**Do NOT just write reminders to MEMORY.md** — that won't trigger actual notifications.

## Heartbeat Tasks

`HEARTBEAT.md` is checked on the configured heartbeat interval. Use file tools to manage periodic tasks:

- **Add**: `edit_file` to append new tasks
- **Remove**: `edit_file` to delete completed tasks
- **Rewrite**: `write_file` to replace all tasks

When the user asks for a recurring/periodic task, update `HEARTBEAT.md` instead of creating a one-time cron reminder.
