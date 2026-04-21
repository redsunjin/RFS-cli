# Harness Worksheet: Provider Runtime Prototype

## 1. Work identity

- track: Post-MVP external tool providers
- branch_scope: official-loop work on `codex/idea`
- official_active_loop: yes
- promotion_state: official-loop execution
- user_visible_change: `rfs provider run qa_claw scan_secrets` becomes available as the first read-only provider prototype

## 2. Scope

- in:
  - add the first `rfs provider run` command path
  - support only `qa_claw` and `scan_secrets`
  - read `tool_providers.qa_claw` from local config
  - enforce provider enablement and capability allowlist
  - return bounded JSON provider results
- out:
  - no provider setup command
  - no provider status command
  - no NestClaw runtime execution
  - no arbitrary script execution
  - no shell auto-routing into providers
- assumptions:
  - users or tests may prepare the `tool_providers` config block manually for the prototype
  - qa_claw owns the behavior of `security/scan-secrets.sh`

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
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_cli.py -q -k "provider_run"`
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_harness_sync.py -q`
- regression_gate:
  - full CLI test suite should remain available before commit
- runtime_signals:
  - provider command rejects missing config and non-allowlisted capabilities
  - provider result distinguishes accepted invocation from provider check pass/fail

## 5. Guardrails

- do_not_expand_into:
  - arbitrary shell strings
  - provider auto-discovery
  - provider install/start management
  - write-capable NestClaw execution
  - hidden shell routing
- escalation_conditions:
  - command shape requires more than one capability to prove the prototype
  - provider failures cannot be bounded into structured output
- rollback_or_recovery_path:
  - remove the `provider` command group and keep the runtime config model as design-only
- promotion_gate:
  - first command must be read-only, allowlisted, config-backed, and covered by tests

## 6. Drift and hygiene

- likely_drift_points:
  - manual config UX is weak until a setup or status slice exists
  - qa_claw script paths may change independently
- scheduled_cleanup_rule:
  - define provider setup/status UX before adding more provider capabilities
- candidate_future_automation:
  - add contract tests for provider config validation and bounded output
- promotion_evidence_artifacts:
  - provider command tests
  - updated roadmap/TODO state
