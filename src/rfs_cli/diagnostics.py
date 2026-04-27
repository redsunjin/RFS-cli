from __future__ import annotations

from pathlib import Path
from typing import Optional

from rfs_cli.config import (
    load_config,
    load_index,
    load_shell_memory,
    resolve_config_path,
    resolve_index_path,
    resolve_shell_memory_path,
)
from rfs_cli.llm import get_llm_status
from rfs_cli.models import AppConfig
from rfs_cli.providers import build_provider_status


def summarize_doctor_file(path: Path) -> dict[str, object]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "valid": False,
        "error": None,
        "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
    }


def collect_config_diagnostics(state_dir: Path) -> tuple[dict[str, object], Optional[AppConfig]]:
    config_path = resolve_config_path(state_dir=state_dir)
    data = summarize_doctor_file(config_path)
    if not data["exists"]:
        return data, None

    try:
        app_config = load_config(state_dir=state_dir)
    except ValueError as exc:
        data["error"] = str(exc)
        return data, None

    data.update(
        {
            "valid": True,
            "schema_version": app_config.schema_version,
            "source_count": len(app_config.sources),
            "enabled_source_count": sum(1 for source in app_config.sources if source.enabled),
            "source_ids": [source.id for source in app_config.sources],
            "llm_configured": bool(app_config.llm and app_config.llm.enabled),
            "llm_provider": app_config.llm.provider if app_config.llm else None,
            "drive_configured": bool(app_config.drive and app_config.drive.enabled),
            "default_output_format": app_config.default_output_format,
        }
    )
    return data, app_config


def collect_index_diagnostics(state_dir: Path) -> dict[str, object]:
    index_path = resolve_index_path(state_dir=state_dir)
    data = summarize_doctor_file(index_path)
    if not data["exists"]:
        return data

    try:
        index_store = load_index(state_dir=state_dir)
    except ValueError as exc:
        data["error"] = str(exc)
        return data

    if index_store is None:
        return data

    data.update(
        {
            "valid": True,
            "schema_version": index_store.schema_version,
            "generated_at": index_store.generated_at,
            "document_count": len(index_store.documents),
            "source_ids": sorted({document.source_id for document in index_store.documents}),
            "file_types": sorted({document.file_type for document in index_store.documents}),
        }
    )
    return data


def collect_shell_memory_diagnostics(state_dir: Path) -> dict[str, object]:
    memory_path = resolve_shell_memory_path(state_dir=state_dir)
    data = summarize_doctor_file(memory_path)
    if not data["exists"]:
        return data

    try:
        memory = load_shell_memory(state_dir=state_dir)
    except ValueError as exc:
        data["error"] = str(exc)
        return data

    if memory is None:
        return data

    data.update(
        {
            "valid": True,
            "schema_version": memory.schema_version,
            "session_id": memory.session_id,
            "event_count": len(memory.events),
            "updated_at": memory.updated_at,
        }
    )
    return data


def collect_llm_runtime_diagnostics(app_config: Optional[AppConfig]) -> dict[str, object]:
    if app_config is None or app_config.llm is None or not app_config.llm.enabled:
        return {
            "configured": False,
            "provider": None,
            "model": None,
            "base_url": None,
            "reachable": False,
            "available_models": [],
            "default_model_available": None,
            "error": None,
        }
    return get_llm_status(app_config.llm)


def collect_provider_diagnostics(app_config: Optional[AppConfig]) -> dict[str, object]:
    tool_providers = app_config.tool_providers if app_config is not None else {}
    status = build_provider_status(None, tool_providers)
    providers = status["providers"]
    issue_count = sum(
        len(provider.get("issues") or [])
        for provider in providers
        if provider.get("configured")
    )
    status["issue_count"] = issue_count
    return status


def build_doctor_suggestions(
    config: dict[str, object],
    index: dict[str, object],
    shell_memory: dict[str, object],
    llm_runtime: dict[str, object],
    providers: dict[str, object],
) -> list[str]:
    suggestions: list[str] = []
    if config.get("exists") and not config.get("valid"):
        suggestions.append("Inspect `.rfs/config.json` or rerun `rfs init` to rebuild the config.")
        return suggestions

    if not llm_runtime.get("configured"):
        suggestions.append("Run `rfs` or `rfs init` to configure the required LLM flow.")
        return suggestions

    if not llm_runtime.get("reachable"):
        suggestions.append(
            "Check that the configured LLM runtime is running, then retry `rfs llm status`."
        )

    if config.get("valid") and not config.get("source_count"):
        suggestions.append("Run `rfs index add <path> --source local|obsidian` to add a source.")

    if index.get("exists") and not index.get("valid"):
        suggestions.append(
            "Inspect `.rfs/index.json` or rerun `rfs index run` to rebuild the index."
        )
    elif config.get("source_count") and not index.get("exists"):
        suggestions.append("Run `rfs index run` to build the local index.")

    if shell_memory.get("exists") and not shell_memory.get("valid"):
        suggestions.append("Move or remove `.rfs/shell-memory.json` if shell state needs a reset.")

    if providers.get("issue_count"):
        suggestions.append(
            "Run `rfs provider status qa_claw` to inspect provider issues, then rerun "
            "`rfs provider setup-qa-claw <repo_root>` if the repo root or allowlist is wrong."
        )

    if not suggestions:
        suggestions.append("No immediate release-readiness issues were detected.")
    return suggestions
