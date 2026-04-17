# Harness Worksheet: NestClaw Adapter Boundary

## 1. Work identity

- track: Post-MVP external tool providers
- branch_scope: official-loop work on `codex/idea`
- official_active_loop: yes
- promotion_state: official-loop execution
- user_visible_change: no runtime change yet; provider boundary becomes documented and reviewable

## 2. Scope

- in:
  - define the first NestClaw-specific adapter boundary
  - map the shared provider contract onto the current NestClaw API and local CLI
  - decide preferred transport, capabilities, trust boundary, and non-goals
- out:
  - no runtime `rfs provider` command
  - no live NestClaw execution from `rfs-cli`
  - no config wiring or shell auto-routing
- assumptions:
  - the local NestClaw repository under `/Users/Agent/ps-workspace/NestClaw` reflects the current companion-project baseline
  - the API contract is more stable than the interactive CLI for first integration purposes

## 3. Record system

- source_of_truth_docs:
  - `docs/tool-provider-contract.md`
  - `docs/roadmap.md`
  - `docs/todo.md`
  - `/Users/Agent/ps-workspace/NestClaw/API_CONTRACT.md`
  - `/Users/Agent/ps-workspace/NestClaw/README.md`
- execution_doc:
  - `docs/nestclaw-adapter-boundary.md`
- handoff_doc_updates:
  - `docs/product-spec.md`
  - `docs/architecture.md`
  - `docs/roadmap.md`
  - `docs/todo.md`

## 4. Evaluators

- static_checks:
  - `python3 scripts/check_harness_sync.py`
- targeted_tests:
  - `uv run pytest tests/test_harness_sync.py -q`
- regression_gate:
  - roadmap/TODO sync remains valid after the slice
- runtime_signals:
  - local NestClaw API and CLI shape is inspectable from checked-in docs and code

## 5. Guardrails

- do_not_expand_into:
  - runtime execution integration
  - provider config model changes
  - auth token brokering
  - generic provider marketplace behavior
- escalation_conditions:
  - NestClaw API contract and implementation disagree on the minimum create/run/status path
  - the local repo no longer exposes a stable API-first entrypoint
- rollback_or_recovery_path:
  - keep only the shared provider contract and defer provider-specific boundaries
- promotion_gate:
  - boundary document must state preferred transport, allowed capabilities, side-effect boundaries, and explicit non-goals

## 6. Drift and hygiene

- likely_drift_points:
  - NestClaw API may evolve independently from `rfs-cli` docs
  - local CLI affordances may tempt a broader surface than the first adapter should allow
- scheduled_cleanup_rule:
  - revisit the boundary when runtime provider work actually begins
- candidate_future_automation:
  - compare boundary docs against companion-project contracts automatically
- promotion_evidence_artifacts:
  - `docs/nestclaw-adapter-boundary.md`
  - updated roadmap/TODO state
