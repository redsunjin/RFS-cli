# Versioning Policy

## Purpose

This document defines the release versioning baseline for `rfs-cli` while the project remains in active pre-1.0 development.

## Current scheme

`rfs-cli` follows a pre-1.0 semantic versioning style:

- `0.y.z`
- `y` changes for new user-visible features, command-surface changes, or breaking contract changes while the project is still pre-1.0
- `z` changes for fixes, docs, tests, and non-breaking internal improvements

## Stable reference points

- `rfs version` is the runtime-facing version command
- `pyproject.toml` and `src/rfs_cli/__init__.py` must carry the same version value
- the first `1.0.0` release is reserved for the point where the CLI command surface and JSON contracts are considered stable

## Release update rule

When preparing a new release:

1. update the version in `pyproject.toml`
2. update the version in `src/rfs_cli/__init__.py`
3. verify `rfs version`
4. run the release checklist

## Examples

- `0.1.0 -> 0.1.1`: docs-only or bug-fix release with no contract break
- `0.1.1 -> 0.2.0`: new command or breaking CLI/JSON behavior during pre-1.0 development
- `0.x.y -> 1.0.0`: first stable release with committed command and output contracts
