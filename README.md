# rfs-cli

`rfs-cli` is a personal knowledge and developer utility CLI designed for two modes of use:

- Human-first local workflows
- AI-friendly tool execution with structured output

The project starts with local knowledge retrieval for Obsidian vaults and filesystem content, then expands into developer utilities, Google Drive integration, and agent-oriented commands.

## Project goals

- Search and inspect personal knowledge across local files and Obsidian notes
- Add practical developer commands that are useful during day-to-day work
- Expose stable, machine-readable commands that AI agents can call safely
- Build the system incrementally from a small, usable MVP

## Document map

- [Project charter](./docs/project-charter.md)
- [Product spec](./docs/product-spec.md)
- [Architecture](./docs/architecture.md)
- [Roadmap](./docs/roadmap.md)
- [TODO plan](./docs/todo.md)
- [Agent operating model](./AGENTS.md)

## Initial product shape

Planned command groups:

- `rfs index`
- `rfs search`
- `rfs show`
- `rfs dev`
- `rfs agent`
- `rfs drive`

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
- indexed search and indexed document lookup
- file preview support
- project statistics
- agent-safe file listing and text search

Google Drive and broader metadata enrichment remain roadmap work.

## Working principles

- Start with local-first value before remote integrations
- Prefer small commands with explicit input and output contracts
- Design every command so it can return either human-readable text or JSON
- Keep documentation ahead of implementation changes
