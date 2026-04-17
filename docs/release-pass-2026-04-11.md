# Release Pass 2026-04-11

## Scope

Run the current release-readiness baseline against the repository state on 2026-04-11.

## Commands run

Quality gates:

- `uv run pytest`
- `uv run ruff check .`
- `uv build`

Runtime verification:

- `uv run rfs --help`
- `uv run rfs llm status --state-dir .rfs --format json`
- `uv run rfs doctor --verbose --state-dir .rfs --format json`
- `uv run rfs ask "검색을 시작하려면 어떻게 해?" --state-dir .rfs --format json`
- `printf 'exit\n' | uv run rfs shell --state-dir .rfs`

Smoke verification:

- fixture local source add/run/search/show flow using a temporary state dir seeded with the current `.rfs/config.json`
- build artifact inspection for:
  - `rfs_cli/llm_onboarding.md`
  - `rfs_cli/agent_contract.md`

## Results

### Passed

- `uv run pytest`
- `uv run ruff check .`
- `uv build`
- `uv run rfs --help`
- `uv run rfs doctor --verbose --state-dir .rfs --format json`
- `uv run rfs ask "검색을 시작하려면 어떻게 해?" --state-dir .rfs --format json`
- `printf 'exit\n' | uv run rfs shell --state-dir .rfs`
- fixture local source add/run/search/show flow
- built wheel and sdist include runtime prompt assets

### Environment-blocked or partial

- `uv run rfs llm status --state-dir .rfs --format json`
  - config exists and is valid
  - configured provider is `lmstudio`
  - configured endpoint `http://127.0.0.1:1234` was not reachable in the current environment

## Findings

### 1. Baseline CLI is runnable now

The packaged `rfs` entrypoint works and the main command surface is available.

### 2. Current environment is not runtime-ready for live LLM calls

The configured LM Studio endpoint is not running, so live provider-dependent flows are not currently fully available in this environment.

### 3. Fresh state dirs still require LLM configuration before normal CLI flows

A fresh temporary state dir failed `index add` until a valid `config.json` with LLM settings was present.
This is consistent with the current product direction, but it remains a usability tradeoff worth documenting and possibly revisiting later.

## Release-readiness assessment

- code quality gate: pass
- packaging baseline: pass
- CLI entrypoint baseline: pass
- local fixture smoke baseline: pass
- live LLM runtime baseline: blocked by local environment

## Recommendation

Do not treat the current environment as fully release-ready for live guided runtime use until the configured LLM endpoint is reachable again.

For the next official slice, prefer a bounded design slice from the paused queue rather than the blocked Drive smoke path.

Recommended next official slice:

1. design the NestClaw adapter boundary for API or CLI invocation
2. keep Google Drive real smoke paused until credentials or token state are available
3. keep compiled wiki as a candidate track
