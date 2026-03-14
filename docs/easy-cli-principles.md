# Easy CLI Principles

## Date

2026-03-15

## Purpose

This document captures what "easy to use" should mean for `rfs-cli`, especially when the user starts from a task goal rather than command syntax.

## Working definition

An easy CLI helps the user complete a task with the least possible amount of command memorization, guesswork, and recovery pain.

## Core principles

### 1. One obvious starting point

The user should know how to begin without reading the whole manual.

For `rfs-cli`, that means:

- `rfs` should be the default entry point
- the first screen should decide between onboarding, shell, or the next safe step
- the user should not need to choose between many top-level entry commands up front

### 2. Task-first guidance

The interface should understand requests such as "find my roadmap note" or "add my vault" before it expects exact syntax.

That means:

- accept plain-language input where possible
- recommend a concrete command
- ask for only one missing detail when needed

### 3. Predictable command shape

Commands should feel learnable after a few uses.

That means:

- keep top-level verbs short and stable
- make similar actions look similar
- avoid introducing experimental top-level commands too early

### 4. Progressive disclosure

The CLI should not dump every option at the beginning.

That means:

- show one recommended command first
- reveal advanced flags only when useful
- keep `--help` readable for first-time users

### 5. Good defaults

A beginner should succeed without supplying many flags.

That means:

- choose sensible default output and paths
- infer likely source or state when confidence is high
- reduce required options for common flows

### 6. Recovery-first errors

Errors should explain how to recover, not only what failed.

That means:

- say why the request could not proceed
- show the next corrective command
- distinguish missing setup, missing index, empty result, and invalid path clearly

### 7. Visible local state

Users should not have to guess what the tool already knows.

That means:

- show whether LLM setup exists
- show whether sources are registered
- show whether an index exists and how stale it is
- make `doctor` and status-like guidance easy to reach

### 8. Safe action boundaries

The CLI should make it clear when it is suggesting, inspecting, or changing state.

That means:

- separate read-only help from state-changing commands
- avoid surprising writes
- add confirmation or explicitness where the action is risky

### 9. Short, concrete language

Friendly does not mean verbose.

That means:

- lead with the next action
- keep explanations short
- prefer examples that can be copied directly

### 10. Bounded AI assistance

AI help should make the CLI easier, not vaguer.

That means:

- keep AI grounded in implemented commands
- do not invent unsupported capabilities
- treat machine-readable contracts as stable product surface

## What an easy CLI can be used for

An easy CLI is especially useful when the user knows the goal, but not the command.

### Personal knowledge retrieval

Examples:

- finding notes, documents, or snippets across local folders
- searching an Obsidian vault without remembering index commands
- opening the right document after a vague request

Why a simple CLI helps:

- users think in topics, not flags
- AI can translate a task into search and inspection steps

### Local workspace and file inspection

Examples:

- checking what files exist in a folder
- previewing a file
- understanding project state without knowing shell tools deeply

Why a simple CLI helps:

- many useful local tasks are repetitive but syntax-heavy
- a guided CLI reduces fear of "wrong command" usage

### Setup and onboarding

Examples:

- configuring the LLM provider
- registering a note folder or vault
- performing the first index run

Why a simple CLI helps:

- first-run friction is where many CLI tools fail
- a task-first guide can carry the user to the first success faster

### Diagnostics and recovery

Examples:

- finding out why search returns nothing
- checking whether the config is broken
- understanding whether the index is missing or stale

Why a simple CLI helps:

- users often need diagnosis more than raw feature depth
- recovery guidance is more important than a generic error line

### Repeated operational tasks

Examples:

- running the same search pattern often
- checking repository summary
- scanning TODOs in a project

Why a simple CLI helps:

- once the pattern is learned, the CLI becomes both teachable and automatable
- the same command can serve both human and agent usage

### AI-assisted local tool gateway

Examples:

- asking "search my notes for roadmap and show the best result"
- asking "what should I do next to set this up?"
- asking "why is this not working?" and getting a bounded next step

Why a simple CLI helps:

- the AI layer becomes a command guide, not a separate product
- the user stays inside a real tool surface instead of unbounded chat

## Where easy CLI fits best

Easy CLI design works especially well when:

- the tool has a clear task domain
- most actions can be expressed as a few stable verbs
- local state can be inspected and explained
- safety matters, but full GUI overhead is unnecessary

It works less well when:

- the product is mostly open-ended conversation
- the system cannot inspect its own state reliably
- the actions are so broad that no stable command model exists

## What this means for `rfs-cli`

For this project, "easy CLI" should first improve:

1. startup flow through bare `rfs`
2. task-to-command mapping in `rfs ask`
3. multi-turn task help inside `rfs shell`
4. empty-state and error recovery messaging

It should not first expand:

- new top-level commands
- broad chat behavior outside the documented tool domain
- unstable JSON guidance payloads

## Validation questions

The next implementation slices should be judged with questions like:

- Can a first-time user reach a successful search without reading the full command tree?
- When the tool cannot proceed, does it recommend the next safe command?
- Does the guidance stay short and grounded in current local state?
- Can the same flow serve both human text mode and bounded agent use?
