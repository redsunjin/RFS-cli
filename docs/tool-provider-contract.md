# Tool Provider Contract

## Purpose

This document defines the shared contract for post-MVP external tool providers used by `rfs-cli`.

The goal is to let `rfs` treat external systems as bounded tools without collapsing the CLI into an unreviewed automation layer.

## Contract goals

- register providers in a consistent shape
- separate provider discovery from provider execution
- distinguish read-only from state-changing actions
- enforce confirmation policy before risky execution
- normalize provider output before surfacing it through `rfs`

## Provider model

Each provider should define:

- `provider_id`
- `display_name`
- `provider_kind`
  - `service`
  - `cli`
  - `script`
- `root_path`
- `invocation_mode`
  - `http`
  - `subprocess`
  - `script-runner`
- `capabilities`
- `confirmation_policy`
- `timeout_seconds`
- `result_format`

## Capability model

Each capability should declare:

- `capability_id`
- `description`
- `access_mode`
  - `read`
  - `write`
  - `mixed`
- `requires_confirmation`
- `expected_inputs`
- `expected_outputs`

## Confirmation policy

Default rules:

- read-only capabilities may run without extra confirmation when the provider is already trusted
- state-changing capabilities should require explicit confirmation
- provider operations that touch approvals, task execution, worktree mutation, or PR creation should default to confirmation

## Result normalization

Provider results should be normalized into a stable structure before they are shown or passed on:

- `provider_id`
- `capability_id`
- `ok`
- `summary`
- `data`
- `error`
- `raw_reference`

The goal is to keep external provider differences away from the main `rfs` command surface.

## Registration boundary

The first provider registration layer should remain post-MVP and explicit.

It should not:

- auto-discover and trust arbitrary local scripts
- treat every repo in the workspace as executable tool inventory
- bypass command, path, or confirmation boundaries

## Execution boundary

The first implementation should keep these constraints:

- provider selection is explicit
- capability selection is explicit
- execution happens only through documented capability ids
- results are bounded and reviewable

## Current intended providers

- NestClaw
- qa_claw

## Out of scope for the first provider layer

- unbounded remote SaaS connectors
- generic shell passthrough disguised as a provider contract
- automatic chaining between providers without explicit policy review
