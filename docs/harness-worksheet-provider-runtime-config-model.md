# Harness Worksheet: Provider Runtime Config Model

## 1. Work identity

- track: Post-MVP external tool providers
- branch_scope: official-loop work on `codex/idea`
- official_active_loop: yes
- promotion_state: official-loop execution
- user_visible_change: no runtime change yet; shared provider runtime config becomes documented and reviewable

## 2. Scope

- in:
  - compare the accepted NestClaw and qa_claw boundaries
  - define the smallest shared runtime provider config model
  - decide the safest first runtime prototype direction
- out:
  - no runtime `rfs provider` command
  - no live provider execution from `rfs-cli`
  - no config wiring into the implemented CLI
  - no shell auto-routing
- assumptions:
  - the existing provider boundary documents remain the source of truth for provider-specific capability semantics
  - the first runtime prototype should prefer a read-only provider surface

## 3. Record system

- source_of_truth_docs:
  - `docs/tool-provider-contract.md`
  - `docs/nestclaw-adapter-boundary.md`
  - `docs/qa-claw-adapter-boundary.md`
  - `docs/roadmap.md`
  - `docs/todo.md`
- execution_doc:
  - `docs/provider-runtime-config-model.md`
- handoff_doc_updates:
  - `docs/product-spec.md`
  - `docs/architecture.md`
  - `docs/roadmap.md`
  - `docs/todo.md`

## 4. Evaluators

- static_checks:
  - `python3 scripts/check_harness_sync.py`
- targeted_tests:
  - `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_harness_sync.py -q`
- regression_gate:
  - roadmap/TODO sync remains valid after the slice
- runtime_signals:
  - provider boundary differences are explicit and still bounded after the shared config model is defined

## 5. Guardrails

- do_not_expand_into:
  - runtime execution implementation
  - provider command UX
  - provider startup management
  - generic plugin marketplace behavior
- escalation_conditions:
  - the two provider boundary documents imply incompatible runtime invariants
  - the shared config model requires duplicating provider-specific contract logic
- rollback_or_recovery_path:
  - keep only provider-specific boundary documents and defer shared runtime config work
- promotion_gate:
  - the document must clearly separate shared config fields from provider-specific target details and name one bounded next prototype

## 6. Drift and hygiene

- likely_drift_points:
  - provider boundary docs may evolve independently from the shared runtime model
  - config field growth may tempt a broader plugin model than intended
- scheduled_cleanup_rule:
  - revisit the config model when the first runtime prototype begins
- candidate_future_automation:
  - compare the runtime config doc against provider boundary docs during harness checks
- promotion_evidence_artifacts:
  - `docs/provider-runtime-config-model.md`
  - updated roadmap/TODO state
