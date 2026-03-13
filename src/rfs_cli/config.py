from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from rfs_cli.models import AppConfig, IndexStore

DEFAULT_STATE_DIR = ".rfs"
DEFAULT_CONFIG_NAME = "config.json"
DEFAULT_INDEX_NAME = "index.json"


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
