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

### Real LM Studio runtime validation

Commands executed successfully:

- `uv run rfs llm status --state-dir .rfs --format json`
- `uv run rfs ask "옵시디언 볼트를 추가하려면 어떻게 해야 해? 한 줄 명령 예시도 줘." --state-dir .rfs --format json`
- `uv run rfs shell --state-dir .rfs`

Observed checks:

- the configured LM Studio endpoint at `http://127.0.0.1:1234` was reachable
- the configured model `qwen3.5-9b-mlx` was available
- `rfs ask` returned a grounded command answer against the real runtime
- provider-specific reasoning tags such as `<think>` and control markers such as `<|im_end|>` are now stripped before output
- shell responses now carry active-session context so the agent no longer tells the user to run `rfs shell` while already inside it

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
- A real Obsidian vault path was not available in this environment. A quick scan under `/Users/Agent` only found the test fixture vault, not a user vault.

## Recommendation

Treat the current codebase as fixture-validated, local-real-data-validated, and real-LM-Studio-validated.
Use an environment-specific waiver for the Obsidian real-data smoke step until a real vault path becomes available.
