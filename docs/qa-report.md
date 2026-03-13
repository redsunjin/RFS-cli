# QA Report

## Date

2026-03-13

## Scope

- `show` text-mode inspection output
- smoke checklist execution with fixture data
- regression validation for tests and lint

## Results

### Automated validation

- `uv run pytest`: pass
- `uv run ruff check .`: pass

### Fixture-based smoke run

Commands executed successfully:

- `uv sync --all-groups`
- `uv run rfs index add tests/fixtures/obsidian --source obsidian --state-dir /tmp/.../.rfs`
- `uv run rfs index add tests/fixtures/local --source local --state-dir /tmp/.../.rfs`
- `uv run rfs index run --state-dir /tmp/.../.rfs --format json`
- `uv run rfs search "agent systems" --state-dir /tmp/.../.rfs --format json`
- `uv run rfs show tests/fixtures/obsidian/ideas/agent-systems.md --state-dir /tmp/.../.rfs --metadata-only --format json`
- `uv run rfs dev project-stats --path . --format json`
- `uv run rfs dev git-summary --path . --format json`
- `uv run rfs dev find-todo --path . --format json`
- `uv run rfs agent list-files tests/fixtures/local --format json`
- `uv run rfs agent find-text TODO tests/fixtures/local --format json`

Observed checks:

- JSON payloads include `schema_version`, `command`, `ok`, `data`, and `error`
- failure cases are covered by tests for `missing_index`, `invalid_index`, and `git_error`
- ignored directories such as `.git`, `.venv`, and `.obsidian` are excluded from scanning
- multi-source ranking prefers the Obsidian note over the local note for the same query intent

### Real-data local smoke run

Commands executed successfully against `/Users/Agent/Documents`:

- `uv run rfs index add /Users/Agent/Documents --source local --state-dir /tmp/.../.rfs --format json`
- `uv run rfs index run --state-dir /tmp/.../.rfs --format json`
- `uv run rfs search 에이전트 --state-dir /tmp/.../.rfs --format json`
- `uv run rfs show /Users/Agent/Documents/멀티에이전트 병렬 개발 방법론.md --state-dir /tmp/.../.rfs --metadata-only --format json`
- `uv run rfs agent list-files /Users/Agent/Documents --format json`
- `uv run rfs agent find-text 에이전트 /Users/Agent/Documents --format json`

Observed checks:

- local source registration and indexing succeeded with `document_count: 7`
- indexed search returned the expected real markdown note from the user data path
- indexed `show` resolved the real file path without error
- `agent list-files` and `agent find-text` both returned valid JSON payloads on the same root
- no actual Obsidian vault was discovered in the current machine environment, so the real-data smoke run could only validate the local source flow

## Findings

- No blocking defects were found in this QA pass.
- `agent list-files` is intentionally broad and includes files such as `.DS_Store`, `.localized`, and model cache directories; this is noisy but not an MVP blocker.

## Remaining limitation

- The local-source smoke checklist has been executed with real user data.
- A real Obsidian vault path was not available in this environment, so cross-source real-data sign-off is still environment-blocked.

## Recommendation

Treat the current codebase as fixture-validated and local-real-data-validated. Keep final MVP sign-off pending only on one real Obsidian smoke run, or explicitly waive that step for this environment.
