# rfs-cli

```text
 ____  _____    _    ______   __   _____ ___  ____    ____  _____    _
|  _ \| ____|  / \  |  _ \ \ / /  |  ___/ _ \|  _ \  / ___|| ____|  / \
| |_) |  _|   / _ \ | | | \ V /   | |_ | | | | |_) | \___ \|  _|   / _ \
|  _ <| |___ / ___ \| |_| || |    |  _|| |_| |  _ <   ___) | |___ / ___ \
|_| \_\_____/_/   \_\____/ |_|    |_|   \___/|_| \_\ |____/|_____/_/   \_\

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
```

`rfs-cli` is a personal knowledge and developer utility CLI agent designed for three modes of use:

- Human-first local workflows
- Non-developer-friendly task guidance
- AI-friendly tool execution with structured output
- CLI-native agent guidance with a consistent style

The project starts with local knowledge retrieval for Obsidian vaults and filesystem content, then expands into developer utilities, Google Drive integration, and agent-oriented commands.

The product direction is not just "a CLI with many commands." The goal is to turn `rfs-cli` into one coherent local-first agent that can use its own tools, explain them, and keep a recognizable operating style instead of behaving like a generic chat wrapper.
That agent now assumes a configured LLM as part of normal onboarding, and its runtime persona is R2-D2-inspired.

## Project goals

- Search and inspect personal knowledge across local files and Obsidian notes
- Add practical developer commands that are useful during day-to-day work
- Expose stable, machine-readable commands that AI agents can call safely
- Turn the CLI into a tool-using agent with a clear identity and grounded behavior
- Build the system incrementally from a small, usable MVP
- Make the CLI approachable for users who know the task they want, but not the command syntax

## Product direction

`rfs-cli` is being shaped as a CLI-native agent:

- it should use tools, not just describe them
- it should preserve a consistent voice and interaction style
- it should guide the user toward concrete commands instead of generic answers
- it should stay grounded in its real capabilities, local state, and configured sources

## Document map

- [Project charter](./docs/project-charter.md)
- [Product spec](./docs/product-spec.md)
- [Architecture](./docs/architecture.md)
- [Roadmap](./docs/roadmap.md)
- [MVP plan](./docs/mvp-plan.md)
- [MVP status](./docs/mvp-status.md)
- [Next phase plan](./docs/next-phase-plan.md)
- [Installation guide](./docs/installation.md)
- [Versioning policy](./docs/versioning-policy.md)
- [Release checklist](./docs/release-checklist.md)
- [Smoke checklist](./docs/smoke-checklist.md)
- [QA report](./docs/qa-report.md)
- [Work groups](./docs/work-groups.md)
- [Idea track](./docs/idea-track.md)
- [Easy CLI principles](./docs/easy-cli-principles.md)
- [Research export format](./docs/research-export-format.md)
- [LLM onboarding guide](./docs/llm-onboarding.md)
- [Agent profile](./docs/agent-profile.md)
- [Agent contract](./docs/agent-contract.md)
- [TODO plan](./docs/todo.md)
- [Agent operating model](./AGENTS.md)

## Initial product shape

Planned command groups:

- `rfs index`
- `rfs search`
- `rfs show`
- `rfs init`
- `rfs shell`
- `rfs doctor`
- `rfs dev`
- `rfs agent`
- `rfs llm`
- `rfs ask`
- `rfs drive`
- `rfs research`

## Selected stack

- Python 3.9+
- `uv` for environment and dependency management
- Typer for CLI command handling
- Pydantic for config and payload models
- Pytest and Ruff for validation

## Command naming rules

- Top-level verbs stay short: `index`, `search`, `show`, `dev`, `agent`, `drive`
- `dev` and `agent` hold specialist subcommands
- Human workflows default to text output
- Agent workflows default to JSON output where appropriate

## Current implementation baseline

The current codebase includes:

- project scaffolding
- source registration and local JSON index storage
- indexed search with metadata-aware filters and source-aware ranking
- indexed document lookup with source metadata
- file preview support
- project statistics
- agent-safe file listing and text search
- required LLM setup and guided CLI usage with `rfs ask`
- documented agent contract plus source-aware guidance for `rfs ask`
- deterministic short follow-up questions for ambiguous `rfs ask` requests
- workspace-state grounding for natural-language guidance inside `rfs shell`
- matching deterministic follow-up behavior inside `rfs shell`
- interactive shell mode with saved session memory and internal tool execution
- a local `doctor` command for state and runtime diagnostics
- a Google Drive auth/config baseline with local token storage, cache-backed metadata retrieval, and live metadata-only `drive search`
- a first `research export` command that writes curated local bundles with a manifest and document files
- required onboarding through `rfs init` and a packaged LLM guide
- default interactive startup through `rfs` itself

Google Drive sync breadth and broader metadata enrichment remain roadmap work.

## Quickstart

```bash
uv sync --all-groups
uv run rfs
uv run rfs llm status
uv run rfs doctor --verbose --format json
uv run rfs index add /path/to/obsidian-vault --source obsidian
uv run rfs index add /path/to/local-notes --source local
uv run rfs index run
uv run rfs search "agent memory" --format json
uv run rfs show <document-id> --format json
uv run rfs dev find-todo --path . --format json
uv run rfs research export "agent systems" --output ./exports/agent-systems --format json
```

The default workspace state directory is `.rfs/`.

## Installation

Development usage:

```bash
cd /Users/Agent/ps-workspace/rfs-cli
uv sync --all-groups
uv run rfs --help
```

Tool-style local install:

```bash
cd /Users/Agent/ps-workspace/rfs-cli
uv tool install .
rfs --help
```

Tool-style Git install:

```bash
uv tool install git+https://github.com/redsunjin/RFS-cli.git
rfs --help
```

For the full install, verification, and recovery flow, see [Installation guide](./docs/installation.md).
For versioning rules, see [Versioning policy](./docs/versioning-policy.md).
For release sign-off criteria, see [Release checklist](./docs/release-checklist.md).

## LLM-assisted usage

`rfs-cli` requires an LLM provider for normal agent workflows:

- `ollama`
- `lmstudio`
- OpenAI-compatible HTTP APIs

Example:

```bash
uv run rfs
uv run rfs llm status
uv run rfs ask "How do I add my Documents folder and search markdown files only?"
```

The easiest entry point is `rfs` in an interactive terminal. It now chooses onboarding or shell automatically. `rfs init` remains the explicit manual onboarding path. If the LLM is not configured, agent workflows should redirect the user back to onboarding instead of pretending to operate normally.

The current conversational layer is intentionally narrow: it helps users discover and operate supported commands. Expanding that into a stronger agent with state-aware guidance and follow-up questions is part of the next planning track.

The runtime agent persona is R2-D2-inspired: compact, task-oriented, and operational without turning into full character roleplay.

## Shell mode

`rfs shell` is the first step toward a CLI-native agent workflow.

Inside the shell you can:

- type direct `rfs` commands without the `rfs` prefix
- ask natural-language questions if an LLM is configured
- run internal commands with `/run ...`
- run external CLI tools with `!<command>`
- persist conversation and tool history in `.rfs/shell-memory.json`

## Working principles

- Start with local-first value before remote integrations
- Prefer small commands with explicit input and output contracts
- Design every command so it can return either human-readable text or JSON
- Keep documentation ahead of implementation changes
