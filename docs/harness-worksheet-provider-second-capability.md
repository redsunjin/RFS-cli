# Harness Worksheet: Provider Second Capability

## 1. Work identity

- track: Post-MVP external tool providers
- branch_scope: official-loop work on `codex/idea`
- official_active_loop: yes
- promotion_state: official-loop execution
- user_visible_change: `rfs provider run qa_claw verify_worktrees` becomes available as the second read-only provider capability

## 2. Scope

- in:
  - add `verify_worktrees` to the qa_claw allowlisted runtime surface
  - extend setup/status to support optional `worktree_root`
  - keep argument input bounded to `--assignment`, `--assignments-file`, and `--check-remote`
  - preserve read-only execution semantics
- out:
  - no third qa_claw capability yet
  - no NestClaw runtime execution
  - no arbitrary provider arguments
- assumptions:
  - `verify-worktrees.sh` remains the source of truth for worktree verification behavior
  - `worktree_root` should stay optional in config but explicit when needed

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
  - verify_worktrees requires bounded assignment input
  - setup/status show optional `worktree_root`

## 5. Guardrails

- do_not_expand_into:
  - generic argument passthrough
  - API-backed provider runtime
  - write-capable provider behavior
- escalation_conditions:
  - verify_worktrees requires broader free-form input than the bounded flags allow
  - config growth starts to look like a generic plugin API
- rollback_or_recovery_path:
  - keep only `scan_secrets` as the runtime capability and leave `verify_worktrees` design-only
- promotion_gate:
  - second capability must remain read-only, allowlisted, config-backed, and test-covered

## 6. Drift and hygiene

- likely_drift_points:
  - worktree-root defaults may drift from real qa_claw usage
  - assignment input contract may widen if not held explicitly
- scheduled_cleanup_rule:
  - choose the third capability only after the bounded argument contract for verify_worktrees is accepted
- candidate_future_automation:
  - add contract tests for assignments-file validation and text-mode output
- promotion_evidence_artifacts:
  - provider capability tests
  - updated roadmap/TODO state
