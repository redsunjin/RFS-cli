from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from rfs_cli.models import AppConfig, DriveCacheStore, IndexStore, ShellMemory

DEFAULT_STATE_DIR = ".rfs"
DEFAULT_CONFIG_NAME = "config.json"
DEFAULT_INDEX_NAME = "index.json"
DEFAULT_SHELL_MEMORY_NAME = "shell-memory.json"
DEFAULT_DRIVE_TOKEN_NAME = "drive-token.json"
DEFAULT_DRIVE_CACHE_NAME = "drive-cache.json"


def resolve_state_dir(state_dir: Optional[Path] = None) -> Path:
    return (state_dir or Path.cwd() / DEFAULT_STATE_DIR).resolve()


def resolve_config_path(
    config_path: Optional[Path] = None,
    state_dir: Optional[Path] = None,
) -> Path:
    if config_path is not None:
        return config_path.resolve()
    return resolve_state_dir(state_dir) / DEFAULT_CONFIG_NAME


def resolve_index_path(index_path: Optional[Path] = None, state_dir: Optional[Path] = None) -> Path:
    if index_path is not None:
        return index_path.resolve()
    return resolve_state_dir(state_dir) / DEFAULT_INDEX_NAME


def resolve_shell_memory_path(
    memory_path: Optional[Path] = None,
    state_dir: Optional[Path] = None,
) -> Path:
    if memory_path is not None:
        return memory_path.resolve()
    return resolve_state_dir(state_dir) / DEFAULT_SHELL_MEMORY_NAME


def resolve_drive_token_path(
    token_path: Optional[Path] = None,
    state_dir: Optional[Path] = None,
) -> Path:
    if token_path is not None:
        return token_path.resolve()
    return resolve_state_dir(state_dir) / DEFAULT_DRIVE_TOKEN_NAME


def resolve_drive_cache_path(
    cache_path: Optional[Path] = None,
    state_dir: Optional[Path] = None,
) -> Path:
    if cache_path is not None:
        return cache_path.resolve()
    return resolve_state_dir(state_dir) / DEFAULT_DRIVE_CACHE_NAME


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_config(
    config_path: Optional[Path] = None,
    state_dir: Optional[Path] = None,
) -> AppConfig:
    resolved_path = resolve_config_path(config_path=config_path, state_dir=state_dir)
    if not resolved_path.exists():
        return AppConfig()

    data = json.loads(resolved_path.read_text(encoding="utf-8"))

    try:
        return AppConfig.model_validate(data)
    except ValidationError as exc:
        message = exc.errors()[0]["msg"] if exc.errors() else "Invalid configuration."
        raise ValueError(message) from exc


def save_config(
    config: AppConfig,
    config_path: Optional[Path] = None,
    state_dir: Optional[Path] = None,
) -> Path:
    resolved_path = resolve_config_path(config_path=config_path, state_dir=state_dir)
    ensure_parent(resolved_path)
    resolved_path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
    return resolved_path


def load_index(
    index_path: Optional[Path] = None,
    state_dir: Optional[Path] = None,
) -> Optional[IndexStore]:
    resolved_path = resolve_index_path(index_path=index_path, state_dir=state_dir)
    if not resolved_path.exists():
        return None

    data = json.loads(resolved_path.read_text(encoding="utf-8"))

    try:
        return IndexStore.model_validate(data)
    except ValidationError as exc:
        message = exc.errors()[0]["msg"] if exc.errors() else "Invalid index."
        raise ValueError(message) from exc


def save_index(
    index_store: IndexStore,
    index_path: Optional[Path] = None,
    state_dir: Optional[Path] = None,
) -> Path:
    resolved_path = resolve_index_path(index_path=index_path, state_dir=state_dir)
    ensure_parent(resolved_path)
    resolved_path.write_text(index_store.model_dump_json(indent=2), encoding="utf-8")
    return resolved_path


def load_shell_memory(
    memory_path: Optional[Path] = None,
    state_dir: Optional[Path] = None,
) -> Optional[ShellMemory]:
    resolved_path = resolve_shell_memory_path(memory_path=memory_path, state_dir=state_dir)
    if not resolved_path.exists():
        return None

    data = json.loads(resolved_path.read_text(encoding="utf-8"))

    try:
        return ShellMemory.model_validate(data)
    except ValidationError as exc:
        message = exc.errors()[0]["msg"] if exc.errors() else "Invalid shell memory."
        raise ValueError(message) from exc


def save_shell_memory(
    memory: ShellMemory,
    memory_path: Optional[Path] = None,
    state_dir: Optional[Path] = None,
) -> Path:
    resolved_path = resolve_shell_memory_path(memory_path=memory_path, state_dir=state_dir)
    ensure_parent(resolved_path)
    resolved_path.write_text(memory.model_dump_json(indent=2), encoding="utf-8")
    return resolved_path


def load_drive_cache(
    cache_path: Optional[Path] = None,
    state_dir: Optional[Path] = None,
) -> Optional[DriveCacheStore]:
    resolved_path = resolve_drive_cache_path(cache_path=cache_path, state_dir=state_dir)
    if not resolved_path.exists():
        return None

    data = json.loads(resolved_path.read_text(encoding="utf-8"))

    try:
        return DriveCacheStore.model_validate(data)
    except ValidationError as exc:
        message = exc.errors()[0]["msg"] if exc.errors() else "Invalid Drive cache."
        raise ValueError(message) from exc


def save_drive_cache(
    cache_store: DriveCacheStore,
    cache_path: Optional[Path] = None,
    state_dir: Optional[Path] = None,
) -> Path:
    resolved_path = resolve_drive_cache_path(cache_path=cache_path, state_dir=state_dir)
    ensure_parent(resolved_path)
    resolved_path.write_text(cache_store.model_dump_json(indent=2), encoding="utf-8")
    return resolved_path
