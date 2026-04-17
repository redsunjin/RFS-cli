# Harness Worksheet: qa_claw Adapter Boundary

## 1. Work identity

- track: Post-MVP external tool providers
- branch_scope: official-loop work on `codex/idea`
- official_active_loop: yes
- promotion_state: official-loop execution
- user_visible_change: no runtime change yet; qa_claw adapter boundary becomes documented and reviewable

## 2. Scope

- in:
  - define the first qa_claw-specific adapter boundary
  - map the shared provider contract onto the current qa_claw scripts and verification gates
  - decide preferred invocation style, capabilities, trust boundary, and non-goals
- out:
  - no runtime `rfs provider` command
  - no live qa_claw execution from `rfs-cli`
  - no config wiring or shell auto-routing
  - no qa_claw API integration in the first boundary
- assumptions:
  - the local qa_claw repository under `/Users/Agent/ps-workspace/qa_claw_works/qa_claw` reflects the current companion-project baseline
  - script and CI gates are more stable for first integration than the evolving service or UI surface

## 3. Record system

- source_of_truth_docs:
  - `docs/tool-provider-contract.md`
  - `docs/roadmap.md`
  - `docs/todo.md`
  - `/Users/Agent/ps-workspace/qa_claw_works/qa_claw/README.md`
  - `/Users/Agent/ps-workspace/qa_claw_works/qa_claw/backend/README.md`
  - `/Users/Agent/ps-workspace/qa_claw_works/qa_claw/.github/workflows/ci-gates.yml`
- execution_doc:
  - `docs/qa-claw-adapter-boundary.md`
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
  - local qa_claw scripts, CI gates, and backend verification surface are inspectable from checked-in docs and code

## 5. Guardrails

- do_not_expand_into:
  - runtime execution integration
  - provider config model changes
  - qa_claw service API integration
  - generic provider marketplace behavior
- escalation_conditions:
  - qa_claw verification scripts and documented CI gates disagree materially
  - the local repo no longer exposes stable script-backed gate entrypoints
- rollback_or_recovery_path:
  - keep only the shared provider contract and defer provider-specific boundaries
- promotion_gate:
  - boundary document must state preferred invocation style, allowed capabilities, side-effect boundaries, and explicit non-goals

## 6. Drift and hygiene

- likely_drift_points:
  - qa_claw scripts and CI gates may evolve independently from `rfs-cli` docs
  - backend API growth may tempt a broader first boundary than needed
- scheduled_cleanup_rule:
  - revisit the boundary when runtime provider work actually begins
- candidate_future_automation:
  - compare boundary docs against companion-project CI gates automatically
- promotion_evidence_artifacts:
  - `docs/qa-claw-adapter-boundary.md`
  - updated roadmap/TODO state
