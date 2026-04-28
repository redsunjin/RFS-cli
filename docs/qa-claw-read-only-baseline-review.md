# qa_claw Read-Only Baseline Review

Date: 2026-04-28

## Goal

Decide whether the current qa_claw runtime set is sufficient as a bounded read-only baseline before any broader provider expansion.

## Review target

- repository: `/Users/Agent/ps-workspace/qa_claw_works/qa_claw`
- worktree root: `/Users/Agent/ps-workspace/qa_claw_works/qa_claw_worktrees`
- reviewed capabilities:
  - `scan_secrets`
  - `verify_worktrees`
  - `check_authz_consistency`
  - `check_observability_evidence`
  - `run_backend_regression`

## What was validated

The baseline was exercised through the current `rfs-cli` provider surface:

- `rfs provider setup-qa-claw`
- `rfs provider status qa_claw`
- `rfs provider run qa_claw scan_secrets`
- `rfs provider run qa_claw verify_worktrees`
- `rfs provider run qa_claw check_authz_consistency`
- `rfs provider run qa_claw check_observability_evidence`
- `rfs provider run qa_claw run_backend_regression`

## Issue found during review

The initial real-repo run exposed a runtime portability gap:

- Python-based qa_claw capabilities inherited a Python 3.9 interpreter from the active `rfs-cli` venv
- `run_backend_regression` failed on modern qa_claw type syntax (`dict | None`)
- this was not a qa_claw contract problem; it was an interpreter selection problem in `rfs-cli`

## Fix applied

`rfs-cli` now resolves a provider-compatible local Python interpreter for Python-based qa_claw capabilities, preferring Python 3.10 or newer when available.

This keeps the runtime bounded while avoiding false failures caused only by the caller venv version.

## Real-run result

After the interpreter portability fix:

- `scan_secrets`: pass
- `verify_worktrees`: pass
- `check_authz_consistency`: pass
- `check_observability_evidence`: pass
- `run_backend_regression`: pass

Observed note:

- `run_backend_regression` still emits provider-side `ResourceWarning` lines on stderr under Python 3.14, but the test run itself completes successfully with `OK`
- this is a qa_claw/provider-noise issue, not an `rfs-cli` contract failure

## Conclusion

The current five-capability qa_claw runtime set is sufficient as the first bounded read-only provider baseline.

That means:

- no broader provider expansion is needed right now
- no write-capable provider runtime should be opened yet
- no NestClaw runtime execution should start before a new explicit official slice

## Recommendation

1. Freeze the current qa_claw read-only baseline.
2. Move the official loop away from provider expansion.
3. Return the next official local work to compiled-wiki promotion-prep, starting with the first small wiki-lint fixture set.

## Evidence

- real qa_claw status/config review through `rfs provider status qa_claw`
- real qa_claw capability runs through the five `rfs provider run qa_claw ...` commands above
- portability tests in `tests/test_providers.py`
