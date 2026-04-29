<div align="center">
  <img src="nanobot-forge_logo.png" alt="nanobot" width="500">
</div>

# 🐈 nanobot-forge: Workspace-based Coding Agent

A **coding-specialized** fork of [nanobot](https://github.com/HKUDS/nanobot) — an ultra-lightweight personal AI agent framework. This version extends nanobot with a workspace coding toolset: code execution, test running, sandboxed evaluation, git operations, linting, and package management — turning the agent into a practical local coding assistant.

---

## 🌟 What's Changed

This fork introduces the following features and modifications on top of the original nanobot project:

### 1. Tool: `run_code` *(New)*

Execute a Python file in the workspace and capture its full output.

- Runs `python <file>` and returns stdout, stderr, and exit code
- Validates the file exists before executing
- Supports optional command-line arguments
- Configurable timeout (default 30s, max 300s)
- Prefer this over `exec python <file>` for Python execution

### 2. Tool: `run_tests` *(New)*

Run the test suite using pytest and return a pass/fail summary.

- Runs `pytest` in the workspace and parses results
- Specify `path` to run a single test file or directory; omit to run all tests
- `verbose=true` shows individual test names
- Configurable timeout (default 120s, max 600s)
- Always run this after modifying code to confirm nothing is broken

### 3. Tool: `sandbox_exec` *(New)*

Execute a Python code snippet in a sandboxed environment with import restrictions.

- Blocks dangerous imports: `os`, `subprocess`, `sys`, `socket`, `ctypes`, `shutil`, `pickle`, and more
- Short execution timeout (default 10s, max 60s)
- Use for quick logic checks on isolated code fragments
- Not a substitute for `run_code` when full environment access is needed

### 4. Tool: `git` *(New)*

Run git commands in the project workspace.

- Supports: `status`, `diff`, `log`, `add`, `commit`, `branch`, `checkout`, `push`, `pull`, `stash`
- Destructive operations (force-push, hard-reset, clean) are blocked by safety guard
- Always runs in the configured workspace directory
- Examples: `git(command="diff --staged")`, `git(command="commit -m 'fix: auth bug'")`

### 5. Tool: `lint` *(New)*

Lint or format code with auto-detection.

- **Python**: auto-detects `ruff` (preferred) or `pylint`
- **JS/TS**: auto-detects `eslint` or `prettier`
- `fix=true` applies auto-fixes in place
- Override with `tool="ruff"` if auto-detection is wrong
- Run before committing to catch style and logic issues early

### 6. Tool: `pkg` *(New)*

Manage project dependencies with auto-detection.

- **Python**: detects `pip` from `requirements.txt` or `pyproject.toml`
- **JS/TS**: detects `pnpm` (lock file) → `yarn` (lock file) → `npm` (package.json)
- Actions: `install`, `uninstall`, `list`, `update`
- `install` with no packages reads from `requirements.txt` / `package.json`
- `dev=true` for npm/yarn/pnpm dev dependencies

### 7. Coding-Focused Agent Identity *(Modified)*

Updated system prompt and agent instructions for a coding workflow:

- Identity: workspace coding agent (not a general assistant)
- Coding loop: **Understand → Plan → Act → Execute → Observe → Debug → Validate → Commit**
- Rules: never declare success until code runs; fix one error at a time; always run tests after changes

### 8. Workspace Configuration *(New)*

A `workspace/` directory at the project root provides ready-to-use agent configuration:

```
workspace/
├── SOUL.md       # Agent identity and execution rules
├── AGENTS.md     # Coding workflow and debugging rules
├── TOOLS.md      # Tool usage notes
├── USER.md       # Developer profile template (fill this in)
├── HEARTBEAT.md  # Periodic task list
└── memory/
    └── MEMORY.md # Long-term memory (managed by agent)
```

Point your `workspace` config to this directory to use it out of the box.

---

## 🚀 Quick Start

### 1. Install

```bash
git clone <your-repo-url>
cd nanobot
pip install -e .
```

### 2. Initialize

```bash
nanobot onboard
```

### 3. Configure

Edit `~/.nanobot/config.json`. Minimum required: an API key and model.

```json
{
  "providers": {
    "anthropic": {
      "apiKey": "sk-ant-xxx"
    }
  },
  "agents": {
    "defaults": {
      "model": "anthropic/claude-opus-4-7",
      "workspace": "/path/to/your/project"
    }
  }
}
```

Point `workspace` to the repository you want the agent to work in. Or use the bundled `workspace/` folder from this repo as a starting point.

### 4. Fill in your developer profile

Edit `workspace/USER.md` (or `~/.nanobot/workspace/USER.md`) to tell the agent about your project, stack, and preferences.

### 5. Run

Interactive CLI mode:

```bash
nanobot agent
```

Single message:

```bash
nanobot agent -m "fix the failing test in tests/test_auth.py"
```

---

## 🛠️ Coding Tools Reference

| Tool | What it does |
|------|-------------|
| `run_code` | Execute a Python file, capture stdout/stderr/exit code |
| `run_tests` | Run pytest, return pass/fail summary |
| `sandbox_exec` | Run a Python snippet with blocked imports (safe eval) |
| `git` | Git operations: status, diff, log, add, commit, push, pull |
| `lint` | Lint/format with ruff, pylint, eslint, or prettier (auto-detected) |
| `pkg` | Install/uninstall/list packages via pip or npm/yarn/pnpm (auto-detected) |
| `read_file` | Read a file from the workspace |
| `write_file` | Write or create a file |
| `edit_file` | Make targeted edits to an existing file |
| `glob` | Find files by pattern (e.g. `**/*.py`) |
| `grep` | Search file contents by regex |
| `exec` | Run any shell command with safety guards |

---

## ⚙️ Configuration Reference

Config file: `~/.nanobot/config.json`

### Providers

| Provider | Purpose | Get API Key |
|----------|---------|-------------|
| `anthropic` | Claude models (recommended) | [console.anthropic.com](https://console.anthropic.com) |
| `openai` | GPT / o-series models | [platform.openai.com](https://platform.openai.com) |
| `openrouter` | Access to all models via one key | [openrouter.ai](https://openrouter.ai) |
| `ollama` | Local models (no API key needed) | — |
| `deepseek` | DeepSeek models | [platform.deepseek.com](https://platform.deepseek.com) |

### Forge Tool Configuration

```json
{
  "tools": {
    "forge": {
      "enable": true,
      "pythonExecutable": "python",
      "runCodeTimeout": 30,
      "runTestsTimeout": 120,
      "sandbox": {
        "blockedImports": ["os", "subprocess", "sys", "socket", "ctypes", "shutil", "tempfile", "pickle"],
        "timeout": 10
      }
    }
  }
}
```

| Field | Description | Default |
|-------|-------------|---------|
| `forge.enable` | Enable all forge coding tools | `true` |
| `forge.pythonExecutable` | Python interpreter for `run_code` and `run_tests` | `"python"` |
| `forge.runCodeTimeout` | Timeout for `run_code` (seconds) | `30` |
| `forge.runTestsTimeout` | Timeout for `run_tests` (seconds) | `120` |
| `forge.sandbox.blockedImports` | Imports blocked in `sandbox_exec` | see above |
| `forge.sandbox.timeout` | Timeout for `sandbox_exec` (seconds) | `10` |

### Agent Defaults

| Field | Description | Default |
|-------|-------------|---------|
| `model` | LLM model to use | `"anthropic/claude-opus-4-5"` |
| `workspace` | Project directory the agent works in | `"~/.nanobot/workspace"` |
| `maxTokens` | Max output tokens per response | `8192` |
| `temperature` | Sampling temperature | `0.1` |
| `maxToolIterations` | Max tool calls per turn | `200` |

<details>
<summary><b>Full config.json example</b></summary>

```json
{
  "agents": {
    "defaults": {
      "workspace": "/path/to/your/project",
      "model": "anthropic/claude-sonnet-4-6",
      "maxTokens": 8192,
      "temperature": 0.1,
      "maxToolIterations": 200
    }
  },
  "providers": {
    "anthropic": {
      "apiKey": "sk-ant-xxx"
    },
    "openai": {
      "apiKey": "sk-xxx"
    }
  },
  "tools": {
    "exec": {
      "enable": true,
      "timeout": 60
    },
    "forge": {
      "enable": true,
      "pythonExecutable": "python",
      "runCodeTimeout": 30,
      "runTestsTimeout": 120,
      "sandbox": {
        "blockedImports": ["os", "subprocess", "sys", "socket", "ctypes", "shutil", "tempfile", "pickle"],
        "timeout": 10
      }
    },
    "web": {
      "enable": true,
      "search": {
        "provider": "duckduckgo"
      }
    },
    "restrictToWorkspace": false
  }
}
```

</details>

---

## 💻 CLI Reference

| Command | Description |
|---------|-------------|
| `nanobot onboard` | Initialize config and workspace |
| `nanobot agent` | Interactive chat mode (primary workflow) |
| `nanobot agent -m "..."` | Send a single message to the agent |
| `nanobot gateway` | Start the gateway (channel bot + cron service) |
| `nanobot cron add` | Add a scheduled task |
| `nanobot cron list` | List scheduled tasks |
| `nanobot cron remove <id>` | Remove a scheduled task |

---

## 📁 Project Structure

```
nanobot/
├── agent/                        # Core agent logic
│   ├── loop.py                   #   Agent loop (LLM ↔ tool execution)
│   ├── context.py                #   Prompt & context builder
│   ├── memory.py                 #   File-based persistent memory
│   ├── skills.py                 #   Skills loader
│   ├── subagent.py               #   Background task execution
│   └── tools/                   #   Built-in tools
│       ├── base.py               #     Tool base class
│       ├── registry.py           #     Dynamic tool registry
│       ├── filesystem.py         #     File read/write/edit/list
│       ├── shell.py              #     Shell command execution
│       ├── search.py             #     Glob and grep tools
│       ├── web.py                #     Web search & fetch
│       ├── run_code.py           #     ★ Execute Python files
│       ├── run_tests.py          #     ★ Run pytest test suite
│       ├── python_sandbox.py     #     ★ Sandboxed Python snippet execution
│       ├── git_tool.py           #     ★ Git operations
│       ├── lint.py               #     ★ Linter/formatter (ruff, eslint, etc.)
│       ├── package_manager.py    #     ★ Package manager (pip, npm, yarn, pnpm)
│       ├── message.py            #     Send messages to user
│       ├── spawn.py              #     Subagent spawning
│       └── cron.py               #     Cron task management
├── channels/                    # Chat channel integrations
│   ├── base.py                  #   Base channel interface
│   ├── manager.py               #   Channel manager
│   ├── websocket.py             #   WebSocket (local API / IDE integration)
│   ├── discord.py               #   Discord
│   └── telegram.py              #   Telegram
├── providers/                   # LLM providers (Anthropic, OpenAI, Ollama, etc.)
├── session/                     # Conversation session management
├── config/                      # Configuration schema & loader (Pydantic)
├── cli/                         # CLI commands
├── bus/                         # Message routing
├── cron/                        # Scheduled task service
├── heartbeat/                   # Proactive wake-up service
├── security/                    # SSRF and network safety
├── skills/                      # Bundled skills (github, weather, tmux, summarize)
└── utils/                       # Helpers
workspace/                       # ★ Ready-to-use agent configuration
├── SOUL.md                      #   Agent identity
├── AGENTS.md                    #   Coding workflow instructions
├── TOOLS.md                     #   Tool usage notes
├── USER.md                      #   Developer profile (fill this in)
├── HEARTBEAT.md                 #   Periodic tasks
└── memory/
    └── MEMORY.md                #   Long-term memory
```

---

## Acknowledgements

This project is based on [nanobot](https://github.com/HKUDS/nanobot) by [HKUDS](https://github.com/HKUDS). Licensed under [MIT](./LICENSE).
