# Harness Worksheet: Wiki Lint Runtime

## 1. Work identity

- track: Compiled wiki
- branch_scope: official-loop work on `codex/idea`
- official_active_loop: yes
- promotion_state: official-loop execution
- user_visible_change: `rfs wiki lint` becomes available as the first structural compiled-wiki runtime command

## 2. Scope

- in:
  - implement the first read-only `rfs wiki lint` runtime
  - keep the first runtime structural and fixture-backed
  - support the first bounded issue kinds: `missing_page`, `orphan_page`, `missing_crosslink`
  - fail cleanly for `wiki_missing` and `invalid_wiki_state`
- out:
  - no `wiki plan-ingest` runtime yet
  - no automatic wiki repair
  - no semantic contradiction or stale-claim heuristics yet
- assumptions:
  - the first runtime should accept a knowledge root or direct `wiki/` directory path
  - zero-count categories may remain in the report until stronger heuristics are added

## 3. Record system

- source_of_truth_docs:
  - `docs/wiki-maintenance-model.md`
  - `docs/wiki-lint-report-contract.md`
  - `docs/wiki-directory-conventions.md`
  - `docs/wiki-lint-fixture-set.md`
  - `docs/roadmap.md`
  - `docs/todo.md`
- execution_doc:
  - this worksheet
- handoff_doc_updates:
  - `docs/product-spec.md`
  - `docs/architecture.md`
  - `docs/wiki-lint-report-contract.md`
  - `docs/roadmap.md`
  - `docs/todo.md`

## 4. Evaluators

- static_checks:
  - `python3 scripts/check_harness_sync.py`
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .`
- targeted_tests:
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_wiki.py -q`
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_harness_sync.py -q`
- regression_gate:
  - full CLI suite remains green
- runtime_signals:
  - healthy fixture reports zero issues
  - structural fixtures surface their expected issue kind
  - invalid-state fixture fails with `invalid_wiki_state`

## 5. Guardrails

- do_not_expand_into:
  - write-capable wiki commands
  - unbounded page dumps in lint output
  - semantic contradiction or stale-claim scoring without an accepted heuristic
- escalation_conditions:
  - the first runtime needs configuration state that does not exist yet
  - fixture intent and runtime behavior diverge
- rollback_or_recovery_path:
  - remove only the `wiki lint` runtime while keeping the fixture set and contracts
- promotion_gate:
  - first runtime must remain read-only, bounded, fixture-backed, and JSON-safe

## 6. Drift and hygiene

- likely_drift_points:
  - structural heuristics may evolve without fixture updates
  - text-mode output may drift from the JSON contract
- scheduled_cleanup_rule:
  - decide whether `index.md` requires fixed one-line summaries before `wiki plan-ingest` runtime work begins
- candidate_future_automation:
  - add direct contract tests for recommended-action ordering
- promotion_evidence_artifacts:
  - `tests/test_wiki.py`
  - fixture trees under `tests/fixtures/wiki_lint/`
  - updated roadmap/TODO state
