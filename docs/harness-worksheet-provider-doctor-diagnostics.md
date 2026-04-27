# Harness Worksheet: Provider Doctor Diagnostics

## 1. Work identity

- track: Post-MVP external tool providers
- branch_scope: official-loop work on `codex/idea`
- official_active_loop: yes
- promotion_state: official-loop execution
- user_visible_change: `rfs doctor` now reports provider diagnostics and recovery guidance

## 2. Scope

- in:
  - add provider diagnostics to `rfs doctor`
  - expose provider configured/enabled counts and provider issue counts
  - add doctor guidance for invalid provider config or missing allowlisted scripts
  - keep provider diagnostics bounded to the current qa_claw runtime surface
- out:
  - no new provider capability
  - no NestClaw runtime diagnostics
  - no shell auto-routing changes
- assumptions:
  - `rfs doctor` should stay the first troubleshooting entrypoint
  - deeper provider inspection can still live under `rfs provider status`

## 3. Record system

- source_of_truth_docs:
  - `docs/provider-runtime-config-model.md`
  - `docs/tool-provider-contract.md`
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
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_cli.py -q -k "doctor or provider_"`
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_harness_sync.py -q`
- regression_gate:
  - full CLI test suite remains green
- runtime_signals:
  - doctor shows provider counts
  - doctor points users to provider status/setup when provider config is invalid

## 5. Guardrails

- do_not_expand_into:
  - second provider capability work
  - generic provider health service
  - provider auto-discovery
- escalation_conditions:
  - provider diagnostics cannot stay bounded or deterministic
  - doctor output becomes too coupled to provider-specific runtime details
- rollback_or_recovery_path:
  - keep provider diagnostics under `rfs provider status` only
- promotion_gate:
  - doctor payload and guidance must stay stable and test-covered

## 6. Drift and hygiene

- likely_drift_points:
  - doctor suggestions may drift from provider setup command naming
  - provider diagnostics may lag behind new capabilities
- scheduled_cleanup_rule:
  - revisit doctor guidance whenever a new provider capability is added
- candidate_future_automation:
  - add narrower contract checks for provider diagnostics in doctor payloads
- promotion_evidence_artifacts:
  - doctor/provider tests
  - updated roadmap/TODO state
