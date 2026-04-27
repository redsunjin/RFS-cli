# qa_claw Adapter Boundary

## Goal

Define the first provider-specific adapter boundary for qa_claw under the shared local tool-provider contract.

This document remains the provider-boundary source of truth.
The current runtime baseline now implements one bounded capability from this boundary: `scan_secrets`.

## Source inputs reviewed

- `docs/tool-provider-contract.md`
- `/Users/Agent/ps-workspace/qa_claw_works/qa_claw/README.md`
- `/Users/Agent/ps-workspace/qa_claw_works/qa_claw/backend/README.md`
- `/Users/Agent/ps-workspace/qa_claw_works/qa_claw/.github/workflows/ci-gates.yml`
- `/Users/Agent/ps-workspace/qa_claw_works/qa_claw/scripts/setup-worktrees.sh`
- `/Users/Agent/ps-workspace/qa_claw_works/qa_claw/scripts/verify-worktrees.sh`
- `/Users/Agent/ps-workspace/qa_claw_works/qa_claw/security/scan-secrets.sh`
- `/Users/Agent/ps-workspace/qa_claw_works/qa_claw/security/check-authz-matrix-consistency.py`
- `/Users/Agent/ps-workspace/qa_claw_works/qa_claw/observability/check-telemetry-evidence.sh`

## Boundary decision

The first qa_claw adapter should be **script-first**, with the provider treated as a bounded verification and gate runner rather than as an API-first orchestration service.

Why:

- the project README and CI gates emphasize reproducible verification commands
- several high-value checks already exist as allowlistable scripts
- the backend service exists, but the shared `rfs-cli` roadmap already positions qa_claw first as a script-backed workflow and verification provider
- script-first integration is narrower and safer than exposing the whole qa_claw service surface immediately

## Provider descriptor

- `provider_id`: `qa_claw`
- `provider_kind`: `script`
- `display_name`: `qa_claw`
- `version`: current local verification baseline
- `cwd_policy`: fixed to the qa_claw repo root or an explicitly declared target root
- `default_timeout_seconds`: 30 for small checks, higher values only after later review
- `max_output_bytes`: bounded previews only; large logs should be referenced as artifacts

## Preferred invocation style

The first adapter should use allowlisted local commands rooted in the qa_claw repository.

Examples of acceptable command shapes:

- `bash security/scan-secrets.sh .`
- `python3 security/check-authz-matrix-consistency.py .`
- `bash observability/check-telemetry-evidence.sh .`
- `python3 -m unittest discover -s backend/tests -p 'test_*.py'`
- `bash scripts/verify-worktrees.sh ...`

The adapter should not accept arbitrary script paths or raw shell strings.

## First capability set

The first adapter should stay narrow and map only verification-oriented capabilities.

### 1. `verify_worktrees`

- primary commands:
  - `bash scripts/verify-worktrees.sh ...`
- side effect: `read`
- purpose: verify worktree and branch assignments against the planned matrix
- expected output:
  - bounded summary of `ok`, `warnings`, `failed`
  - referenced worktree paths or mismatches

### 2. `scan_secrets`

- primary commands:
  - `bash security/scan-secrets.sh .`
- side effect: `read`
- purpose: detect obvious secret leaks across scoped directories
- expected output:
  - pass/fail summary
  - bounded hit preview when failures exist

### 3. `check_authz_consistency`

- primary commands:
  - `python3 security/check-authz-matrix-consistency.py .`
- side effect: `read`
- purpose: validate AuthZ matrix documentation against backend policy code
- expected output:
  - pass/fail summary
  - first mismatch summary when failures exist

### 4. `check_observability_evidence`

- primary commands:
  - `bash observability/check-telemetry-evidence.sh .`
- side effect: `read`
- purpose: verify required observability and telemetry evidence
- expected output:
  - pass/fail summary
  - missing evidence categories when failures exist

### 5. `run_backend_regression`

- primary commands:
  - `python3 -m unittest discover -s backend/tests -p 'test_*.py'`
- side effect: `read`
- purpose: run backend regression and HTTP-level verification tests
- expected output:
  - pass/fail summary
  - bounded failing test preview when failures exist

## Deferred capabilities

Do not include these in the first adapter boundary:

- qa_claw service API endpoints such as `/api/v1/runs`
- frontend or browser-driven checks
- PR creation scripts
- bootstrap scripts that create or mutate worktrees
- release approval or run-mutation flows

Reason:

- they widen trust and side-effect scope
- they are not needed for the first verification-focused provider boundary
- they require stronger configuration, auth, or mutation review than the first adapter should allow

## Request envelope mapping

The shared provider envelope should map to qa_claw like this:

- `tool_name`: one of `verify_worktrees`, `scan_secrets`, `check_authz_consistency`, `check_observability_evidence`, `run_backend_regression`
- `arguments`: only allowlisted arguments for the chosen capability
- `expected_artifacts`: optional log path or evidence path expectations

The adapter should add execution details internally:

- `repo_root`
- fixed script path
- timeout
- output cap

Those execution details should not widen the public capability contract yet.

## Response boundary

The first adapter should normalize qa_claw results into a bounded provider result with:

- `ok`
- `summary`
- `artifacts`
- `stdout_preview`
- `stderr_preview`
- `truncated`
- `error_codes`

For the script-first adapter:

- `artifacts` may include referenced evidence or report paths
- `stdout_preview` and `stderr_preview` must stay bounded
- raw command output should not be returned unbounded by default

## Error mapping

The first adapter should map qa_claw failures into compact provider-facing codes:

- `COMMAND_NOT_ALLOWED`
- `VERIFY_FAILED`
- `SECRET_SCAN_FAILED`
- `AUTHZ_MISMATCH`
- `OBSERVABILITY_EVIDENCE_MISSING`
- `TEST_FAILURE`
- `PROVIDER_UNAVAILABLE`
- `INVALID_ARGUMENT`

`rfs-cli` should not expose arbitrary raw traces from the provider by default.

## Trust boundary

The first adapter should assume:

- qa_claw owns its own verification rules, scripts, and backend test semantics
- `rfs-cli` is only a bounded runner over an allowlisted verification surface
- `rfs-cli` should not mutate qa_claw state in the first adapter
- path scope and repo root must stay explicit to avoid accidental cross-repo execution

## API deferment rule

qa_claw has a backend service surface, but it should not be the first stable adapter path because:

- the shared `rfs-cli` product direction already frames qa_claw as script-backed first
- script entrypoints line up directly with current CI and local QA gates
- API integration would broaden auth, lifecycle, and mutation scope too early

## Config direction

Do not add this config to `rfs-cli` yet, but the first runtime-facing provider slice will likely need:

- `repo_root`
- optional worktree root
- timeout
- per-capability allowlist

Keep this out of the current config model until runtime provider work is explicitly approved.

## Non-goals

- no automatic service startup
- no arbitrary script execution
- no qa_claw API integration
- no PR creation or worktree creation
- no shell auto-routing into qa_claw

## Recommended next slice

1. compare NestClaw and qa_claw boundaries before any runtime provider config work begins
2. define the smallest shared runtime config model only after both provider boundaries are accepted
3. prototype one read-only provider execution path before considering write-capable provider actions
