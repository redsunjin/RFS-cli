# Tool Provider Contract

## Goal

Define a shared boundary for local companion tool providers without introducing a runtime integration too early.

## Current status

This document began as a design-first contract.
The current baseline now includes a narrow qa_claw runtime path plus setup and status UX, but not a generic provider platform.

## Scope

The first contract should cover local companion projects such as:

- NestClaw as an API or CLI-backed orchestration provider
- qa_claw as a script-backed workflow or verification provider

The shared contract exists to:

- keep future provider integrations consistent
- make capability boundaries explicit before implementation
- preserve the local-first agent model and JSON safety rules

## Non-goals for this slice

- no generic provider marketplace command surface
- no provider auto-discovery
- no background daemon or long-running service manager
- no stable public runtime JSON schema for provider execution yet
- no remote multi-tenant registry or marketplace model
- no execution of arbitrary unreviewed shell templates

## Provider descriptor

Each future provider should define:

- `provider_id`: stable internal identifier
- `provider_kind`: one of `api`, `cli`, or `script`
- `display_name`: user-facing name
- `version`: provider-side contract or release version when relevant
- `capabilities`: named operations the provider exposes
- `required_config`: local settings or environment variables needed before use
- `trust_boundary`: what the provider can read, write, or call
- `cwd_policy`: whether execution is fixed, caller-scoped, or not applicable
- `default_timeout_seconds`: bounded execution timeout
- `max_output_bytes`: bounded output size before truncation or failure

## Capability descriptor

Each capability should define:

- `capability_id`: stable internal identifier
- `summary`: short human description
- `side_effect_level`: `read`, `write`, or `mixed`
- `input_contract`: documented expected arguments or payload shape
- `output_contract`: documented result shape or artifact expectation
- `failure_modes`: expected error categories
- `invocation_notes`: provider-specific restrictions or prerequisites

## Invocation envelope

The shared contract should expect a compact machine-readable envelope around provider execution, even before a public runtime schema is finalized.

Expected request metadata:

- `request_id`
- `tool_name`
- `arguments`
- `expected_artifacts`

Expected bounded response metadata:

- `ok`
- `summary`
- `artifacts`
- `stdout_preview`
- `stderr_preview`
- `truncated`
- `error_codes`

## Safety rules

- Provider integration must stay opt-in and locally configured
- Provider execution must use explicit argument boundaries instead of raw shell string interpolation
- Provider execution must use allowlisted commands, scripts, or endpoints rather than arbitrary templates
- Provider execution must keep working-directory scope explicit and bounded
- Output must remain bounded and machine-readable where possible
- Errors must map into structured `code` and `message` patterns instead of leaking raw stack traces by default
- Providers should prefer summarized, paginated, or manifest-style output over unbounded raw blobs
- Path-boundary checks should apply to provider-declared artifacts and working paths
- Secret-bearing values should be redactable before user-facing output is emitted
- Read-only versus state-changing capabilities must stay distinguishable at the contract level
- Provider-side side effects must never be hidden behind a read-only looking capability name

## Current runtime separation

The current runtime surface is intentionally narrow.
Five read-only runtime capabilities are implemented:

- `rfs provider run qa_claw scan_secrets`
- `rfs provider run qa_claw verify_worktrees`
- `rfs provider run qa_claw check_authz_consistency`
- `rfs provider run qa_claw check_observability_evidence`
- `rfs provider run qa_claw run_backend_regression`

For Python-based qa_claw capabilities, the runtime may resolve a provider-compatible local interpreter before execution so that caller-venv version drift does not create false provider failures.

The setup/status UX is also intentionally narrow:

- `rfs provider status [qa_claw]`
- `rfs provider setup-qa-claw <repo_root>`

That still means:

- no generic provider marketplace
- no provider auto-discovery
- no provider install or startup manager
- no shell auto-routing into companion providers
- no NestClaw runtime execution yet
- no arbitrary script execution
- no promise that this document is a finalized multi-provider public execution schema
- no finalized plugin-loading protocol yet
- no promised streaming or cross-provider orchestration behavior yet

## Expected documentation sequence

The shared contract should be defined first.
After that, each provider gets its own boundary document:

1. shared tool-provider contract
2. NestClaw adapter boundary
3. qa_claw adapter boundary
4. shared runtime provider config model
5. one bounded runtime prototype
6. bounded setup/status UX for that prototype

## Design intent

The purpose of this contract is not to broaden `rfs-cli` into a generic plugin host immediately.
It is to make future companion integrations deliberate, reviewable, and safe before any runtime execution path is added.
