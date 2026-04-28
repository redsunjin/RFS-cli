# Harness Worksheet: Provider Fifth Capability

## 1. Work identity

- track: Post-MVP external tool providers
- branch_scope: official-loop work on `codex/idea`
- official_active_loop: yes
- promotion_state: official-loop execution
- user_visible_change: `rfs provider run qa_claw run_backend_regression` becomes available as the fifth read-only provider capability

## 2. Scope

- in:
  - add `run_backend_regression` to the qa_claw allowlisted runtime surface
  - keep the capability argument-free and read-only
  - generalize provider entry-path validation so non-script command forms remain bounded
  - preserve the existing setup/status/run UX
- out:
  - no NestClaw runtime execution yet
  - no generic provider argument expansion
  - no provider artifact streaming or long-log passthrough
- assumptions:
  - `python3 -m unittest discover -s backend/tests -p 'test_*.py'` remains the source of truth for this verification rule
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
  - backend regression capability runs without extra args
  - failures map to `TEST_FAILURE`

## 5. Guardrails

- do_not_expand_into:
  - API-backed provider runtime
  - arbitrary provider arguments
  - write-capable provider behavior
- escalation_conditions:
  - backend regression needs richer runtime configuration than repo root alone
  - unittest entrypoint handling starts to look like a generic command template surface
- rollback_or_recovery_path:
  - remove only the backend regression capability and keep the prior read-only set
- promotion_gate:
  - fifth capability must remain read-only, allowlisted, bounded, and test-covered

## 6. Drift and hygiene

- likely_drift_points:
  - backend test entrypoints may evolve independently
  - status output may drift when capability probe paths are not direct scripts
- scheduled_cleanup_rule:
  - review whether the current qa_claw read-only capability set is sufficient before any broader provider expansion
- candidate_future_automation:
  - add capability-type-specific probe metadata if provider status needs richer reporting than `script_path`
- promotion_evidence_artifacts:
  - provider capability tests
  - updated roadmap/TODO state
