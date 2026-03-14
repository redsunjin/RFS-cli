# Installation Guide

## Purpose

This document defines the baseline installation, verification, and recovery flow for `rfs-cli`.
It covers the current local-first workflow and the simplest tool-style install path.

## Prerequisites

- Python `3.9+`
- [`uv`](https://docs.astral.sh/uv/)
- A reachable LLM runtime for normal agent workflows
  - LM Studio: `http://127.0.0.1:1234`
  - Ollama: `http://127.0.0.1:11434`

## Development install

Use this path when working in the repository directly.

```bash
cd /Users/Agent/ps-workspace/rfs-cli
uv sync --all-groups
uv run rfs --help
```

## Tool-style local install

Use this path when you want `rfs` available directly in the shell.

```bash
cd /Users/Agent/ps-workspace/rfs-cli
uv tool install .
rfs --help
```

## Tool-style Git install

Use this path when installing from the remote repository.

```bash
uv tool install git+https://github.com/redsunjin/RFS-cli.git
rfs --help
```

## First run

Interactive terminals should start with:

```bash
rfs
```

Manual onboarding remains available:

```bash
rfs init
rfs llm status
```

## Verification checklist

After install, verify these steps:

1. `rfs --help` or `uv run rfs --help` works.
2. `rfs llm status --state-dir .rfs --format json` returns a valid payload.
3. `rfs` enters onboarding or shell in an interactive terminal.
4. `rfs ask "검색을 시작하려면 어떻게 해?" --state-dir .rfs --format json` returns a valid payload.
5. `rfs doctor --verbose --state-dir .rfs --format json` reports current workspace health.

## Workspace state

The default workspace state directory is:

```text
.rfs/
```

Important files:

- `.rfs/config.json`
- `.rfs/index.json`
- `.rfs/shell-memory.json`
- `.rfs/drive-token.json`
- `.rfs/drive-cache.json`

## Recovery

If the workspace state becomes stale or invalid:

1. inspect `.rfs/config.json`
2. rebuild the index with `rfs index run`
3. if needed, move or remove `.rfs/` and start again with `rfs`

Example:

```bash
mv .rfs .rfs.backup
rfs
```

## Current limits

- Normal agent workflows require an LLM configuration
- Google Drive live search is still disabled while the cached command surface is being finalized
- A real Obsidian smoke run depends on a real vault path existing in the environment
