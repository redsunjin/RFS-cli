# Release Checklist

## Purpose

This checklist defines the current release-readiness baseline for `rfs-cli`.
It is intended for personal releases and repeatable local verification.

## Docs

- [ ] README reflects the current install and quickstart flow
- [ ] planning docs reflect the current scope and stage
- [ ] user-facing agent profile matches the current runtime behavior
- [ ] onboarding and agent-contract documents match runtime behavior
- [ ] versioning policy reflects the current release scope

## Quality gates

- [ ] `uv run pytest`
- [ ] `uv run ruff check .`
- [ ] `uv build`

## Runtime verification

- [ ] `rfs --help` or `uv run rfs --help`
- [ ] `rfs llm status --state-dir .rfs --format json`
- [ ] `rfs doctor --verbose --state-dir .rfs --format json`
- [ ] `rfs ask "검색을 시작하려면 어떻게 해?" --state-dir .rfs --format json`
- [ ] `rfs shell` starts in an interactive terminal

## Baseline smoke

- [ ] local source add/run/search/show flow passes
- [ ] fixture-based smoke remains green
- [ ] real local-data smoke remains green
- [ ] Obsidian real-data smoke is run, or the environment-specific waiver is recorded

## Packaging

- [ ] built wheel includes runtime prompt assets
  - `rfs_cli/llm_onboarding.md`
  - `rfs_cli/agent_contract.md`

## Release notes

- [ ] release scope is summarized
- [ ] known limitations are summarized
- [ ] next stage priorities are recorded
