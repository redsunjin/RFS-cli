# Smoke Checklist

Run this checklist before calling the current state MVP-ready.

## Environment

- [ ] `uv sync --all-groups`
- [ ] `uv run pytest`
- [ ] `uv run ruff check .`

## Knowledge flow

- [ ] `uv run rfs index add <obsidian-root> --source obsidian`
- [ ] `uv run rfs index add <local-root> --source local`
- [ ] `uv run rfs index run`
- [ ] `uv run rfs search "<query>" --format json`
- [ ] `uv run rfs show <document-id-or-path> --format json`

## Developer flow

- [ ] `uv run rfs dev project-stats --path . --format json`
- [ ] `uv run rfs dev git-summary --path . --format json`
- [ ] `uv run rfs dev find-todo --path . --format json`

## Agent flow

- [ ] `uv run rfs agent list-files . --format json`
- [ ] `uv run rfs agent find-text "TODO" . --format json`

## Validation notes

- [ ] JSON payloads include `schema_version`, `command`, `ok`, `data`, and `error`
- [ ] Failure cases return structured error codes
- [ ] Ignored directories such as `.git`, `.venv`, and `.obsidian` are not scanned
