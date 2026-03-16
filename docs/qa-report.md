# QA Report

## Date

2026-03-15

## Scope

- `show` text-mode inspection output
- smoke checklist execution with fixture data
- regression validation for tests and lint

## Results

### Automated validation

- `uv run pytest`: pass
- `uv run ruff check .`: pass

### Recovery-first text validation

Commands executed successfully:

- `uv run rfs llm status --state-dir /tmp/.../.rfs`
- `uv run rfs search agent --state-dir /tmp/.../.rfs`

Observed checks:

- human-facing empty-state copy now uses short Korean-first recovery text
- key blocked flows now point to one next safe command instead of only raw error text
- JSON error shape stayed stable while text-mode recovery copy improved

### Real LM Studio runtime validation

Commands executed successfully:

- `uv run rfs llm status --state-dir .rfs --format json`
- `uv run rfs ask "옵시디언 볼트를 추가하려면 어떻게 해야 해? 한 줄 명령 예시도 줘." --state-dir .rfs --format json`
- `uv run rfs ask "검색을 시작하려면 어떻게 해?" --state-dir .rfs --format json`
- `uv run rfs shell --state-dir .rfs`

Observed checks:

- the configured LM Studio endpoint at `http://127.0.0.1:1234` was reachable
- the configured model `qwen3.5-9b-mlx` was available
- `rfs ask` returned a grounded command answer against the real runtime
- `rfs ask` returned a deterministic follow-up question for an underspecified search-start request
- provider-specific reasoning tags such as `<think>` and control markers such as `<|im_end|>` are now stripped before output
- shell responses now carry active-session context so the agent no longer tells the user to run `rfs shell` while already inside it
- shell responses now mirror the same deterministic follow-up behavior for underspecified requests

### Release-readiness install-flow smoke

Commands executed successfully:

- `uv sync --all-groups`
- `uv run rfs --help`
- `uv run rfs llm status --state-dir .rfs --format json`
- `uv run rfs doctor --verbose --state-dir .rfs --format json`
- `uv run rfs ask "검색을 시작하려면 어떻게 해?" --state-dir .rfs --format json`
- `uv tool install --reinstall .`
- `rfs --help`
- `rfs doctor --state-dir .rfs --format json`
- `rfs --state-dir .rfs`

Observed checks:

- the documented development install flow remained valid
- the tool-style install path was refreshed successfully with `uv tool install --reinstall .`
- the refreshed global `rfs` command exposed the same latest command surface as `uv run rfs`
- `rfs doctor` returned valid workspace and LM Studio health data from both dev-style and tool-style entrypoints
- `rfs ask` returned the expected deterministic follow-up for an underspecified search-start request
- bare `rfs` entered the interactive shell directly when LLM setup already existed, and the session exited cleanly with `/exit`

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

### Google Drive integration validation

Commands executed successfully:

- `uv run pytest`
- `uv run ruff check .`
- `uv run rfs drive status --state-dir .rfs --format json`

Observed checks:

- command-level integration tests now cover cache hit, cache expiry refetch, and cache invalidation by page-size change
- the live `rfs drive search` command is wired to the cache-backed metadata adapter
- `rfs drive status` now exposes cache path, cache entry count, and cache validity details

Commands attempted but environment-blocked:

- `uv run rfs drive search proposal --state-dir .rfs --format json`
- `uv run rfs drive auth --state-dir /tmp/rfs-drive-real-smoke --format json`

Observed blocker:

- the current environment has no configured Drive source in `.rfs/config.json`
- no `GOOGLE_DRIVE_CLIENT_ID` or `GOOGLE_DRIVE_CLIENT_SECRET` env vars were present
- no local `drive-token.json` was discovered under the workspace paths that were checked
- because of that, the real Google Drive smoke pass could not complete in this environment
- the same blocker was rechecked on 2026-03-17 and still applied: `.rfs/` had only `config.json` and `shell-memory.json`, with no Drive token state

## Findings

- No blocking defects were found in this QA pass.
- `agent list-files` is intentionally broad and includes files such as `.DS_Store`, `.localized`, and model cache directories; this is noisy but not an MVP blocker.

## Remaining limitation

- The local-source smoke checklist has been executed with real user data.
- A real Obsidian vault path was not available in this environment. A quick scan under `/Users/Agent` only found the test fixture vault, not a user vault.
- A real Google Drive smoke pass is still blocked in this environment until Drive client secrets or a persisted Drive token become available.

## Recommendation

Treat the current codebase as fixture-validated, local-real-data-validated, real-LM-Studio-validated, release-readiness-smoke-validated, and Drive-integration-test-validated in the current environment.
Use environment-specific waivers for the Obsidian real-data smoke step and the Google Drive real-runtime smoke step until the required local paths and credentials become available.
