# Harness Worksheet: qa_claw Baseline Review

## 1. Work identity

- track: Post-MVP external tool providers
- branch_scope: official-loop work on `codex/idea`
- official_active_loop: yes
- promotion_state: official-loop verification and closure
- user_visible_change: no new command surface; the current five-capability qa_claw runtime set is reviewed against the real qa_claw repository and its runtime portability issue is closed

## 2. Scope

- in:
  - review whether the current five read-only qa_claw capabilities are sufficient before broader provider expansion
  - validate the runtime against the real qa_claw repository and worktree set
  - close the Python interpreter drift issue discovered during the review
- out:
  - no new provider capability beyond the current five
  - no NestClaw runtime execution
  - no generic provider plugin expansion
- assumptions:
  - the local qa_claw repository remains the review target for this slice
  - broader provider expansion should stay blocked until the current read-only baseline is accepted

## 3. Record system

- source_of_truth_docs:
  - `docs/provider-runtime-config-model.md`
  - `docs/qa-claw-adapter-boundary.md`
  - `docs/roadmap.md`
  - `docs/todo.md`
- execution_doc:
  - this worksheet
- handoff_doc_updates:
  - `docs/qa-claw-read-only-baseline-review.md`
  - `docs/product-spec.md`
  - `docs/architecture.md`
  - `docs/provider-runtime-config-model.md`
  - `docs/tool-provider-contract.md`
  - `docs/roadmap.md`
  - `docs/todo.md`

## 4. Evaluators

- static_checks:
  - `python3 scripts/check_harness_sync.py`
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .`
- targeted_tests:
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_providers.py -q`
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_cli.py -q -k "provider_"`
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_harness_sync.py -q`
- regression_gate:
  - full CLI suite remains green
- runtime_signals:
  - all five qa_claw capabilities run against the real qa_claw repository
  - Python-based capabilities select a provider-compatible interpreter when the active venv is too old

## 5. Guardrails

- do_not_expand_into:
  - write-capable provider execution
  - generic interpreter configuration surface
  - provider artifact streaming
- escalation_conditions:
  - the real qa_claw runtime still fails after interpreter portability hardening
  - broader provider expansion is requested before the current review is accepted
- rollback_or_recovery_path:
  - keep the five-capability baseline but revert the interpreter portability change if it causes regressions
- promotion_gate:
  - the five-capability read-only baseline must be validated against the real qa_claw repository before the official loop moves on

## 6. Drift and hygiene

- likely_drift_points:
  - qa_claw Python runtime requirements may change independently
  - backend regression output may surface provider-side warnings without becoming an rfs-cli failure
- scheduled_cleanup_rule:
  - re-run the baseline review before any future write-capable or NestClaw runtime slice
- candidate_future_automation:
  - add provider-status reporting for selected Python interpreter when provider diagnostics become richer
- promotion_evidence_artifacts:
  - real qa_claw provider run results
  - provider portability tests
  - updated roadmap/TODO state
