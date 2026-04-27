# NestClaw Adapter Boundary

## Goal

Define the first provider-specific adapter boundary for NestClaw under the shared local tool-provider contract.

This document remains design-only for runtime purposes.
No NestClaw runtime execution is implemented in `rfs-cli` yet.

## Source inputs reviewed

- `docs/tool-provider-contract.md`
- `/Users/Agent/ps-workspace/NestClaw/API_CONTRACT.md`
- `/Users/Agent/ps-workspace/NestClaw/README.md`
- `/Users/Agent/ps-workspace/NestClaw/app/main.py`
- `/Users/Agent/ps-workspace/NestClaw/app/cli.py`

## Boundary decision

The first NestClaw adapter should be API-first, with the local interactive CLI treated as a human-debugging fallback rather than the primary machine adapter.

Why:

- the checked-in API contract is explicit about request and response shapes
- the minimum lifecycle is already fixed around `create`, `run`, and `status`
- the interactive CLI is oriented to manual operator use, not stable machine invocation
- API-first integration gives clearer timeout, auth, and output boundaries than screen-driving the CLI

## Provider descriptor

- `provider_id`: `nestclaw`
- `provider_kind`: `api`
- `display_name`: `NestClaw`
- `version`: `0.1.x` contract family for the current API baseline
- `cwd_policy`: not applicable for the primary adapter; HTTP endpoint target must be explicit
- `default_timeout_seconds`: 10 for control calls, higher values only after later review
- `max_output_bytes`: bounded previews only; large reports should be returned as file artifacts or referenced paths

## Preferred transport

The first adapter assumes a local HTTP API target such as:

- `http://127.0.0.1:8000`

The adapter should not assume remote multi-tenant use.
It should stay local-first and caller-configured.

## Auth boundary

NestClaw supports multiple auth/header paths, including:

- `Authorization: Bearer <jwt>`
- `X-SSO-Token`
- trusted SSO headers
- compatibility headers

For the first `rfs-cli` boundary:

- do not broker or mint tokens automatically
- do not embed auth policy inside `rfs-cli`
- require explicit local configuration for whichever header mode is used
- prefer compatibility or local JWT modes only for clearly local operator setups

## First capability set

The first adapter should stay narrow and map only the minimum task lifecycle.

### 1. `task_create`

- NestClaw endpoint: `POST /api/v1/task/create`
- side effect: `write`
- purpose: create a delegated task in `READY` state
- minimum inputs:
  - `title`
  - `template_type`
  - `input`
  - `requested_by`
- expected output:
  - `task_id`
  - `status`
  - `created_at`

### 2. `task_run`

- NestClaw endpoint: `POST /api/v1/task/run`
- side effect: `write`
- purpose: start a previously created task
- minimum inputs:
  - `task_id`
  - optional `idempotency_key`
  - optional `run_mode`
- expected output:
  - `task_id`
  - `status`
  - `started_at`

### 3. `task_status`

- NestClaw endpoint: `GET /api/v1/task/status/{task_id}`
- side effect: `read`
- purpose: inspect the current task state and next action
- expected output:
  - `task_id`
  - `status`
  - optional `current_stage`
  - optional `next_action`
  - optional `result.report_path`
  - optional `approval_reason`

## Deferred capabilities

Do not include these in the first adapter boundary:

- `task_events`
- `approval_list`
- `approval_approve`
- `approval_reject`
- `audit_summary`
- interactive template selection through the NestClaw CLI

Reason:

- they widen trust and role boundaries
- they are less essential than the minimum lifecycle
- approval and audit paths need a stricter review of actor roles and operator responsibilities

## Request envelope mapping

The shared provider envelope should map to NestClaw like this:

- `tool_name`: one of `task_create`, `task_run`, `task_status`
- `arguments`: capability-specific request payload
- `expected_artifacts`: optional report-path expectation for `task_status`

The adapter should add transport details internally:

- `base_url`
- auth headers
- timeout

Those transport details should not widen the public capability contract yet.

## Response boundary

The first adapter should normalize NestClaw responses into a bounded provider result with:

- `ok`
- `summary`
- `artifacts`
- `stdout_preview`
- `stderr_preview`
- `truncated`
- `error_codes`

For the API-first adapter:

- `stdout_preview` should stay empty unless a fallback CLI path is used for diagnostics
- `artifacts` may include a report path when `status == DONE`
- raw HTTP payloads should not be emitted unbounded by default

## Error mapping

The first adapter should map NestClaw errors into compact provider-facing codes:

- `INVALID_REQUEST`
- `POLICY_DENIED`
- `DUPLICATE_REQUEST`
- `TASK_NOT_FOUND`
- `INVALID_TASK_STATE`
- `APPROVAL_REQUIRED`
- `NETWORK_ERROR`
- `AUTH_REQUIRED`
- `PROVIDER_UNAVAILABLE`

`rfs-cli` should not expose arbitrary raw traces from the provider by default.

## Trust boundary

The first adapter should assume:

- NestClaw is responsible for internal orchestration, policy, and task persistence
- `rfs-cli` is only a bounded client over the provider boundary
- `rfs-cli` does not inherit approval authority automatically
- `rfs-cli` should not claim more privileges than the configured NestClaw actor context actually has

## CLI fallback rule

The local NestClaw CLI may be used later for:

- manual debugging
- local demos
- environments where the API is intentionally wrapped by an operator script

But it should not be the first stable adapter path because:

- it is interactive
- it is not described as a machine-stable contract
- it would require input automation and text parsing that the API boundary avoids

## Config direction

Do not add this config to `rfs-cli` yet, but the first runtime-facing provider slice will likely need:

- `base_url`
- auth mode selector
- header or token source reference
- timeout

Keep this out of the current config model until runtime provider work is explicitly approved.

## Non-goals

- no automatic server startup
- no auth token generation
- no approval-queue mutation
- no multi-provider orchestration
- no shell auto-routing into NestClaw

## Recommended next slice

1. design the `qa_claw` adapter boundary as the script-backed contrast case
2. compare both provider boundaries before any runtime config work begins
3. only then consider a narrow provider execution prototype
