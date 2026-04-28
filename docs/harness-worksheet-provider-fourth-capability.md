# Harness Worksheet: Provider Fourth Capability

## 1. Work identity

- track: Post-MVP external tool providers
- branch_scope: official-loop work on `codex/idea`
- official_active_loop: yes
- promotion_state: official-loop execution
- user_visible_change: `rfs provider run qa_claw check_observability_evidence` becomes available as the fourth read-only provider capability

## 2. Scope

- in:
  - add `check_observability_evidence` to the qa_claw allowlisted runtime surface
  - keep the capability argument-free and read-only
  - preserve the existing setup/status/run UX
- out:
  - no fifth qa_claw capability yet
  - no NestClaw runtime execution
  - no generic provider argument expansion
- assumptions:
  - `observability/check-telemetry-evidence.sh` remains the source of truth for this verification rule
  - the capability should stay bounded to repo-root execution only

## 3. Record system

- source_of_truth_docs:
  - `docs/provider-runtime-config-model.md`
  - `docs/qa-claw-adapter-boundary.md`
  - `docs/roadmap.md`
  - `docs/todo.md`
- execution_doc:
  - this worksheet
- handoff_doc_updates:
  - `docs/product-spec.md`
  - `docs/architecture.md`
  - `docs/provider-runtime-config-model.md`
  - `docs/roadmap.md`
  - `docs/todo.md`

## 4. Evaluators

- static_checks:
  - `python3 scripts/check_harness_sync.py`
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .`
- targeted_tests:
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_cli.py -q -k "provider_"`
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_harness_sync.py -q`
- regression_gate:
  - full CLI suite remains green
- runtime_signals:
  - observability evidence capability runs without extra args
  - failures map to `OBSERVABILITY_EVIDENCE_MISSING`

## 5. Guardrails

- do_not_expand_into:
  - API-backed provider runtime
  - arbitrary provider arguments
  - write-capable provider behavior
- escalation_conditions:
  - observability evidence requires richer config than repo root alone
  - capability starts to leak raw traces or unbounded output
- rollback_or_recovery_path:
  - remove only the observability evidence capability and keep the prior read-only set
- promotion_gate:
  - fourth capability must remain read-only, allowlisted, bounded, and test-covered

## 6. Drift and hygiene

- likely_drift_points:
  - observability script paths may evolve independently
  - error messaging may drift from provider boundary docs
- scheduled_cleanup_rule:
  - pick the fifth capability only after the fourth capability remains stable across the next pass
- candidate_future_automation:
  - add tighter contract tests for provider artifact reporting if observability checks start surfacing files
- promotion_evidence_artifacts:
  - provider capability tests
  - updated roadmap/TODO state
