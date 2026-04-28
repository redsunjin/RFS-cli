# Provider Runtime Config Model

## Goal

Define the smallest shared runtime config model that can support both the NestClaw and qa_claw boundaries without adding a generic plugin system or runtime execution yet.

This model began as a design-only slice.
The current baseline now includes four read-only qa_claw runtime capabilities:

- `rfs provider run qa_claw scan_secrets`
- `rfs provider run qa_claw verify_worktrees`
- `rfs provider run qa_claw check_authz_consistency`
- `rfs provider run qa_claw check_observability_evidence`

## Source inputs reviewed

- `docs/tool-provider-contract.md`
- `docs/nestclaw-adapter-boundary.md`
- `docs/qa-claw-adapter-boundary.md`
- `docs/roadmap.md`
- `docs/todo.md`

## Comparison summary

### NestClaw

- provider style: API-first
- primary target: local HTTP endpoint
- first capabilities: `task_create`, `task_run`, `task_status`
- side effects: mixed; includes write actions
- transport-specific needs:
  - `base_url`
  - auth header or token reference
  - tighter control-call timeout defaults

### qa_claw

- provider style: script-first
- primary target: local repository root
- first capabilities:
  - `verify_worktrees`
  - `scan_secrets`
  - `check_authz_consistency`
  - `check_observability_evidence`
  - `run_backend_regression`
- side effects: read-only in the first boundary
- transport-specific needs:
  - `repo_root`
  - optional `worktree_root`
  - per-capability allowlisted command mapping

## Shared runtime invariants

The first shared runtime config should preserve these rules across both providers:

- provider execution remains opt-in and local-first
- capability execution remains allowlisted and explicit
- output stays bounded
- artifacts remain path-bounded
- auth or secret-bearing values are referenced, not copied into logs
- read-only and write-capable capabilities stay distinguishable at the capability level
- no auto-start, auto-discovery, or shell auto-routing is implied

## Smallest shared runtime model

The smallest practical shared runtime model is:

1. one base provider record keyed by provider id
2. one small target block that varies by provider type
3. one optional auth block
4. one explicit capability allowlist

The config should avoid duplicating static descriptor data that already belongs in provider boundary documents.

## Proposed base provider record

Each configured provider should support these fields:

- `enabled`
  - boolean gate for whether the provider may be used at all
- `capability_allowlist`
  - explicit list of capability ids allowed for runtime use
- `target_kind`
  - one of `http` or `repo`
- `target`
  - small provider-specific target block
- `timeout_seconds`
  - bounded runtime timeout for the configured provider
- `max_output_bytes`
  - bounded combined preview size before truncation
- `artifact_root`
  - optional caller-visible root for emitted artifact references
- `auth`
  - optional auth descriptor when the provider needs credentials or headers

## Target block

The target block should stay narrow.

### HTTP target

Used by NestClaw.

- `base_url`

### Repo target

Used by qa_claw.

- `repo_root`
- optional `worktree_root`

The target block should not try to carry arbitrary command templates, shell strings, or provider-specific business rules.

## Auth block

The shared auth shape should stay reference-oriented:

- `kind`
  - `none`
  - `bearer_env`
  - `header_env`
- `env_var`
  - environment variable name when auth is pulled from the environment
- `header_name`
  - required only for `header_env`

This is enough for the first NestClaw boundary and safely absent for qa_claw.

## Why this is the smallest acceptable model

Anything smaller would blur real differences that matter at runtime:

- NestClaw needs an HTTP target and optional auth reference
- qa_claw needs a bounded repo root and no arbitrary command surface
- both need capability allowlisting, timeout control, and bounded output rules

Anything larger would add premature surface:

- no generic plugin registry metadata
- no per-capability shell template config
- no provider startup policy
- no streaming config
- no multi-provider routing policy

## Suggested config shape

This is a design sketch, not a finalized public schema.

```yaml
tool_providers:
  nestclaw:
    enabled: false
    capability_allowlist:
      - task_status
    target_kind: http
    target:
      base_url: http://127.0.0.1:8000
    timeout_seconds: 10
    max_output_bytes: 32768
    auth:
      kind: bearer_env
      env_var: NESTCLAW_TOKEN

  qa_claw:
    enabled: false
    capability_allowlist:
      - verify_worktrees
      - scan_secrets
    target_kind: repo
    target:
      repo_root: /Users/Agent/ps-workspace/qa_claw_works/qa_claw
    timeout_seconds: 30
    max_output_bytes: 32768
```

## Capability policy implications

The runtime layer should continue to trust the provider boundary documents for:

- side-effect level
- capability semantics
- normalized error mapping
- allowed artifacts

The runtime config model should only decide whether a provider is enabled and where its bounded target lives.

## Current prototype

The first runtime prototype and setup surface are intentionally narrow:

- command: `rfs provider run qa_claw scan_secrets`
- command: `rfs provider run qa_claw verify_worktrees`
- command: `rfs provider run qa_claw check_authz_consistency`
- command: `rfs provider run qa_claw check_observability_evidence`
- status: `rfs provider status [qa_claw]`
- setup: `rfs provider setup-qa-claw <repo_root>`
- provider: `qa_claw`
- capabilities:
  - `scan_secrets`
  - `verify_worktrees`
  - `check_authz_consistency`
  - `check_observability_evidence`
- target kind: `repo`
- side effect: read-only
- config source: local `tool_providers.qa_claw` config block

The prototype enforces:

- provider must be configured
- provider must be enabled
- capability must be in `capability_allowlist`
- repo root must exist
- script path must stay inside the repo root
- `verify_worktrees` accepts only bounded assignment inputs
- `check_authz_consistency` stays argument-free
- `check_observability_evidence` stays argument-free
- setup validation should reject missing repo roots and missing allowlisted capability scripts
- stdout and stderr previews must be bounded

The command payload keeps the outer command accepted/failure state separate from the provider result:

- `CommandPayload.ok` says whether the `rfs` invocation was accepted
- `provider_result.ok` says whether the provider check passed

## First prototype recommendation

The first runtime prototype should be read-only and should prefer qa_claw over NestClaw.

Why:

- qa_claw already has a read-only first boundary
- qa_claw scripts line up with current verification gates
- a read-only prototype reduces trust and rollback risk before write-capable provider actions are introduced

The safest first prototype candidates are:

1. `scan_secrets`
2. `verify_worktrees`
3. `run_backend_regression`

## Non-goals

- no provider runtime beyond the bounded qa_claw `scan_secrets`, `verify_worktrees`, `check_authz_consistency`, and `check_observability_evidence` capabilities
- no automatic provider installation or startup
- no command auto-routing from `rfs shell`
- no finalized multi-provider execution JSON schema beyond the prototype payload
- no edge-helper or onboarding-model work in this slice

## Harness conclusion

The current work harness is sufficient for this slice.
No harness-structure change is required.

What is needed is only a slice-specific worksheet because this work compares two completed design boundaries before setting the next official runtime direction.

## Recommended next slice

1. add a fifth read-only qa_claw capability after the observability-evidence pass is accepted
2. prefer `run_backend_regression` as the next bounded capability
3. defer any NestClaw write-capable runtime action until the qa_claw provider UX is stable
