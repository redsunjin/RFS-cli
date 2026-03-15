# NestClaw Adapter Boundary

## Purpose

This document defines the post-MVP adapter boundary for using NestClaw through `rfs-cli`.

The boundary is intentionally narrow.
`rfs` should treat NestClaw as an external orchestration service, not as internal core runtime.

## Observed local shape

Based on the current local project:

- NestClaw exposes an API-centered orchestration model
- the core workflow is organized around task creation, task run, task status, task events, approvals, and audit summaries
- the local repo also includes a CLI entrypoint

## Adapter mode

Preferred adapter modes:

1. HTTP service adapter
2. CLI adapter as fallback

The HTTP adapter should be the primary design because the project already exposes a service-style contract.

## Initial capability set

Read-first capabilities:

- `task.status`
- `task.events`
- `approvals.list`
- `audit.summary`

State-changing capabilities:

- `task.create`
- `task.run`
- `approvals.approve`
- `approvals.reject`

## Confirmation policy

Default confirmation rules:

- `task.status`, `task.events`, `approvals.list`, `audit.summary`
  - no extra confirmation by default
- `task.create`, `task.run`, `approvals.approve`, `approvals.reject`
  - require explicit confirmation

## Input boundary

The first adapter should accept only structured inputs that map cleanly to the documented NestClaw contract.

Examples:

- task title
- template type
- task id
- idempotency key
- approval queue id

The adapter should not accept arbitrary shell command text as a pass-through.

## Output boundary

The first adapter should normalize results into the shared tool-provider contract shape.

Expected output categories:

- task lifecycle state
- event history
- approval queue status
- audit summary

## Security and safety boundary

- do not bypass NestClaw approval semantics
- do not expose raw auth secrets through `rfs`
- keep state-changing actions behind confirmation
- preserve NestClaw's own policy and audit model instead of re-implementing it inside `rfs`

## Not included in the first adapter

- deep nested workflow composition
- broad administrative control surface
- policy mutation
- automatic approval actions without explicit user confirmation
