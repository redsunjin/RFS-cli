# Harness Worksheet: Provider Setup and Status UX

## 1. Work identity

- track: Post-MVP external tool providers
- branch_scope: official-loop work on `codex/idea`
- official_active_loop: yes
- promotion_state: official-loop execution
- user_visible_change: `rfs provider status` and `rfs provider setup-qa-claw` become available for the first provider runtime

## 2. Scope

- in:
  - add provider status UX for configured and unconfigured providers
  - add qa_claw setup UX that writes the `tool_providers` config block
  - validate repo root and allowlisted capability scripts at setup time
  - keep the runtime surface limited to qa_claw and `scan_secrets`
- out:
  - no NestClaw runtime setup
  - no generic provider setup wizard
  - no shell auto-routing into providers
  - no second provider capability yet
- assumptions:
  - qa_claw remains the only supported runtime provider in this slice
  - setup validation should catch obvious repo-root and script-path mistakes before run time

## 3. Record system

- source_of_truth_docs:
  - `docs/tool-provider-contract.md`
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
  - `docs/tool-provider-contract.md`
  - `docs/roadmap.md`
  - `docs/todo.md`

## 4. Evaluators

- static_checks:
  - `python3 scripts/check_harness_sync.py`
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .`
- targeted_tests:
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_cli.py -q -k "provider_(status|setup|run)"`
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_harness_sync.py -q`
- regression_gate:
  - full CLI test suite remains green
- runtime_signals:
  - unconfigured status gives a next step
  - setup writes config successfully
  - invalid repo roots are rejected before runtime

## 5. Guardrails

- do_not_expand_into:
  - generic provider marketplace UX
  - arbitrary script execution
  - NestClaw runtime setup
  - hidden provider routing from shell
- escalation_conditions:
  - setup UX requires provider-specific branching beyond qa_claw
  - status output cannot stay bounded and concise
- rollback_or_recovery_path:
  - remove setup/status commands and keep runtime access only for manually prepared configs
- promotion_gate:
  - setup and status must remain config-backed, bounded, and covered by tests

## 6. Drift and hygiene

- likely_drift_points:
  - setup defaults may drift from documented runtime config fields
  - qa_claw script paths may evolve independently
- scheduled_cleanup_rule:
  - add doctor-visible provider diagnostics before expanding capability count
- candidate_future_automation:
  - extend contract tests to cover invalid provider configs in text mode and JSON mode
- promotion_evidence_artifacts:
  - provider setup/status tests
  - updated roadmap/TODO state
