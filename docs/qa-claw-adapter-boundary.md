# qa_claw Adapter Boundary

## Purpose

This document defines the post-MVP adapter boundary for using `qa_claw` through `rfs-cli`.

`qa_claw` should be treated as a workflow and verification toolkit, not as a general shell wrapper.

## Observed local shape

Based on the current local project:

- `qa_claw` is organized around documentation, sprint plans, worktree assignments, and orchestration runbooks
- its primary executable surface is script-driven
- common operations include worktree setup, worktree verification, sprint bootstrap, and PR helper flows

## Adapter mode

Preferred adapter mode:

- script-runner adapter

The first integration should use explicit script boundaries rather than treating the repo as a generic CLI.

## Initial capability set

Read-first capabilities:

- `worktrees.verify`
- `sprint.plan.inspect`
- `runbook.inspect`

State-changing capabilities:

- `worktrees.setup`
- `sprint.bootstrap`
- `prs.create`

## Confirmation policy

Default confirmation rules:

- `worktrees.verify`, `sprint.plan.inspect`, `runbook.inspect`
  - no extra confirmation by default
- `worktrees.setup`, `sprint.bootstrap`, `prs.create`
  - require explicit confirmation

## Input boundary

The first adapter should pass only structured inputs that match the documented script parameters.

Examples:

- assignments file path
- repo root
- worktree root
- dry-run flag
- fetch policy

The adapter should not accept arbitrary shell fragments.

## Output boundary

The first adapter should normalize results into the shared tool-provider contract shape.

Expected output categories:

- verification summary
- bootstrap summary
- sprint assignment evidence
- PR helper outcome

## Security and safety boundary

- keep script execution rooted to the configured `qa_claw` workspace
- require confirmation before worktree mutation or PR creation
- preserve dry-run support when the upstream script provides it
- do not expose a generic "run any script in the repo" capability

## Not included in the first adapter

- unrestricted script discovery
- arbitrary branch mutation outside documented scripts
- automatic multi-script orchestration without explicit confirmation and policy review
