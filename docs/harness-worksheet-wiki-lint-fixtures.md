# Harness Worksheet: Wiki Lint Fixtures

## 1. Work identity

- track: Compiled wiki
- branch_scope: official-loop work on `codex/idea`
- official_active_loop: yes
- promotion_state: official-loop execution
- user_visible_change: no runtime command yet; the first small fixture set for `wiki lint` becomes explicit and reusable

## 2. Scope

- in:
  - define the first fixture set for `wiki lint`
  - add small reusable Markdown fixture trees under `tests/fixtures/`
  - keep the fixture set focused on first-version structural lint cases
- out:
  - no `wiki lint` runtime command yet
  - no ingest-plan runtime work
  - no semantic contradiction or staleness inference engine yet
- assumptions:
  - first runtime lint should start with structural issues before broader semantic checks
  - fixture trees should follow the documented `wiki/` directory conventions exactly

## 3. Record system

- source_of_truth_docs:
  - `docs/wiki-maintenance-model.md`
  - `docs/wiki-lint-report-contract.md`
  - `docs/wiki-directory-conventions.md`
  - `docs/roadmap.md`
  - `docs/todo.md`
- execution_doc:
  - this worksheet
- handoff_doc_updates:
  - `docs/wiki-lint-fixture-set.md`
  - `docs/roadmap.md`
  - `docs/todo.md`

## 4. Evaluators

- static_checks:
  - `python3 scripts/check_harness_sync.py`
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .`
- targeted_tests:
  - fixture trees remain readable as plain Markdown and path-bounded under `tests/fixtures/wiki_lint/`
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_harness_sync.py -q`
- regression_gate:
  - full CLI suite remains green after fixture additions
- runtime_signals:
  - the next `wiki lint` implementation can map each first-version structural category to a concrete fixture

## 5. Guardrails

- do_not_expand_into:
  - runtime implementation in this slice
  - hidden fixture-only file conventions not reflected in docs
  - semantic lint heuristics not yet justified by the contract
- escalation_conditions:
  - fixture design starts to require a config model that does not exist yet
  - first-version categories cannot be represented cleanly with small Markdown trees
- rollback_or_recovery_path:
  - remove only the wiki-lint fixture set and keep the higher-level wiki contracts
- promotion_gate:
  - the fixture set must stay small, structural, reviewable, and directly reusable for the next runtime slice

## 6. Drift and hygiene

- likely_drift_points:
  - fixture names may drift from the issue kinds they are meant to exercise
  - later runtime heuristics may stop matching the original fixture intent
- scheduled_cleanup_rule:
  - update fixture docs whenever a new lint category becomes runtime-supported
- candidate_future_automation:
  - add a dedicated wiki-lint test module once the command exists
- promotion_evidence_artifacts:
  - fixture trees under `tests/fixtures/wiki_lint/`
  - updated roadmap/TODO state
