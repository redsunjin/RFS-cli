from __future__ import annotations

import io
import json
import os
import shlex
import subprocess
import sys
import uuid
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import click
import typer
from pydantic import ValidationError
from typer.main import get_command

from rfs_cli import __version__
from rfs_cli.config import (
    load_config,
    load_drive_cache,
    load_index,
    load_shell_memory,
    resolve_config_path,
    resolve_drive_cache_path,
    resolve_drive_token_path,
    resolve_shell_memory_path,
    resolve_state_dir,
    save_config,
    save_index,
    save_shell_memory,
)
from rfs_cli.diagnostics import (
    build_doctor_suggestions,
    collect_config_diagnostics,
    collect_index_diagnostics,
    collect_llm_runtime_diagnostics,
    collect_shell_memory_diagnostics,
)
from rfs_cli.drive import (
    fetch_drive_file_metadata,
    load_drive_credentials,
    run_drive_installed_app_auth,
)
from rfs_cli.guidance import (
    build_guidance_runtime_context,
    build_shell_guidance_history,
    format_guidance_response,
    interpret_user_intent,
    plan_command_suggestion,
    render_guidance_response,
)
from rfs_cli.indexing import build_index, build_source_id, resolve_index_document, search_index
from rfs_cli.llm import (
    ask_llm,
    default_api_key_env,
    default_base_url,
    default_model_hint,
    get_llm_status,
    load_onboarding_document,
    normalize_provider,
)
from rfs_cli.models import (
    AppConfig,
    CommandPayload,
    CommandSuggestion,
    DriveAuthConfig,
    DriveCacheConfig,
    DriveConfig,
    DriveFileRecord,
    ErrorPayload,
    GuidanceResponse,
    LLMConfig,
    ShellEvent,
    ShellMemory,
    SourceConfig,
    ToolProviderRuntimeConfig,
    UserIntent,
)
from rfs_cli.providers import ProviderExecutionError, run_tool_provider
from rfs_cli.registry import get_note_record, list_note_records
from rfs_cli.research import export_research_bundle
from rfs_cli.services import (
    find_todo_markers,
    git_summary,
    list_files,
    live_search,
    preview_file,
    project_stats,
)

APP_HELP_TEXT = """Start here: run `rfs` in an interactive terminal.

Recommended next step:
  rfs

Manual alternatives:
  rfs init
  rfs doctor --verbose --format json
"""
ASK_HELP_TEXT = """Ask for one concrete next step in plain language.

Recommended next step:
  rfs ask "옵시디언 볼트를 추가하려면 어떻게 해?"
"""
SHELL_HELP_TEXT = """Open the interactive shell for multi-turn local guidance and commands.

Recommended next step:
  rfs shell
"""

app = typer.Typer(help=APP_HELP_TEXT)
index_app = typer.Typer(help="Index-related commands.")
dev_app = typer.Typer(help="Developer utility commands.")
agent_app = typer.Typer(help="AI-safe commands.")
drive_app = typer.Typer(help="Google Drive commands.")
llm_app = typer.Typer(help="LLM setup and guidance commands.")
research_app = typer.Typer(help="Research workflow commands.")
provider_app = typer.Typer(help="External tool provider commands.")

app.add_typer(index_app, name="index")
app.add_typer(dev_app, name="dev")
app.add_typer(agent_app, name="agent")
app.add_typer(drive_app, name="drive")
app.add_typer(llm_app, name="llm")
app.add_typer(research_app, name="research")
app.add_typer(provider_app, name="provider")


class OutputMode(str, Enum):
    text = "text"
    json = "json"


class NoteKindOption(str, Enum):
    role = "role"
    skill = "skill"


class DriveCacheModeOption(str, Enum):
    disabled = "disabled"
    metadata_only = "metadata-only"


BANNER_LINES = [
    " ____  _____    _    ______   __   _____ ___  ____    ____  _____    _",
    "|  _ \\| ____|  / \\  |  _ \\ \\ / /  |  ___/ _ \\|  _ \\  / ___|| ____|  / \\ ",
    "| |_) |  _|   / _ \\ | | | \\ V /   | |_ | | | | |_) | \\___ \\|  _|   / _ \\ ",
    "|  _ <| |___ / ___ \\| |_| || |    |  _|| |_| |  _ <   ___) | |___ / ___ \\ ",
    "|_| \\_\\_____/_/   \\_\\____/ |_|    |_|   \\___/|_| \\_\\ |____/|_____/_/   \\_\\",
]
WAVE_LINE = "~" * 76
TEXT_GRADIENT_START = (245, 124, 92)
TEXT_GRADIENT_END = (255, 182, 118)
WAVE_GRADIENT_START = (77, 151, 255)
WAVE_GRADIENT_END = (113, 211, 255)
DRIVE_CONTRACT_NOTE = (
    "Drive auth, metadata retrieval, local metadata cache, and metadata-only "
    "`drive search` are implemented."
)
SHELL_PROMPT = "rfs> "
KNOWN_SHELL_COMMANDS = {
    "doctor",
    "init",
    "version",
    "ask",
    "search",
    "show",
    "index",
    "dev",
    "agent",
    "drive",
    "llm",
    "research",
    "provider",
}
STATEFUL_COMMANDS = {
    "ask",
    "doctor",
    "search",
    "show",
    "index",
    "dev",
    "agent",
    "drive",
    "llm",
    "research",
    "provider",
}


def should_use_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return sys.stdout.isatty()


def rgb_escape(red: int, green: int, blue: int) -> str:
    return f"\033[38;2;{red};{green};{blue}m"


def gradient_text(
    text: str,
    start: tuple[int, int, int],
    end: tuple[int, int, int],
) -> str:
    positions = [index for index, char in enumerate(text) if char != " "]
    if not positions:
        return text

    colored_chars: list[str] = list(text)
    total_steps = max(len(positions) - 1, 1)
    for step, position in enumerate(positions):
        ratio = step / total_steps
        red = round(start[0] + (end[0] - start[0]) * ratio)
        green = round(start[1] + (end[1] - start[1]) * ratio)
        blue = round(start[2] + (end[2] - start[2]) * ratio)
        colored_chars[position] = f"{rgb_escape(red, green, blue)}{text[position]}\033[0m"

    return "".join(colored_chars)


def render_banner() -> str:
    lines = BANNER_LINES + ["", WAVE_LINE]
    if not should_use_color():
        return "\n".join(lines)

    colorized = [
        gradient_text(line, TEXT_GRADIENT_START, TEXT_GRADIENT_END) for line in BANNER_LINES
    ]
    colorized.append("")
    colorized.append(gradient_text(WAVE_LINE, WAVE_GRADIENT_START, WAVE_GRADIENT_END))
    return "\n".join(colorized)


def build_dev_data(
    tool: str,
    subject_path: Path,
    summary: str,
    **details: object,
) -> dict[str, object]:
    data: dict[str, object] = {
        "tool": tool,
        "subject_path": str(subject_path.resolve()),
        "summary": summary,
    }
    data.update(details)
    return data


def format_doctor_text_status(label: str, details: dict[str, object]) -> str:
    if not details["exists"]:
        return f"{label}: missing"
    if not details["valid"]:
        error_message = details.get("error") or "invalid"
        return f"{label}: invalid ({error_message})"

    if label == "Config":
        return (
            f'{label}: ok ({details["source_count"]} source(s), '
            f'llm={"yes" if details["llm_configured"] else "no"}, '
            f'drive={"yes" if details["drive_configured"] else "no"})'
        )
    if label == "Index":
        return f'{label}: ok ({details["document_count"]} document(s))'
    if label == "Shell memory":
        return f'{label}: ok ({details["event_count"]} event(s))'
    return f"{label}: ok"


def format_doctor_llm_text_status(details: dict[str, object]) -> str:
    if not details["configured"]:
        return "LLM runtime: not configured"
    if details["reachable"]:
        return f'LLM runtime: reachable ({details["provider"]} / {details["model"]})'
    error_message = details.get("error") or "runtime not reachable"
    return f"LLM runtime: configured but unreachable ({error_message})"


def build_doctor_payload(state_dir: Path, verbose: bool) -> CommandPayload:
    resolved_state_dir = resolve_state_dir(state_dir)
    config_details, app_config = collect_config_diagnostics(resolved_state_dir)
    index_details = collect_index_diagnostics(resolved_state_dir)
    shell_memory_details = collect_shell_memory_diagnostics(resolved_state_dir)
    llm_runtime_details = collect_llm_runtime_diagnostics(app_config)

    return CommandPayload(
        command="doctor",
        ok=True,
        data={
            "version": __version__,
            "verbose": verbose,
            "environment": {
                "cwd": str(Path.cwd().resolve()),
                "state_dir": str(resolved_state_dir),
                "interactive": is_interactive_session(),
                "color_enabled": should_use_color(),
                "python_version": sys.version.split()[0],
                "platform": sys.platform,
            },
            "config": config_details,
            "index": index_details,
            "shell_memory": shell_memory_details,
            "llm_runtime": llm_runtime_details,
            "suggestions": build_doctor_suggestions(
                config_details,
                index_details,
                shell_memory_details,
                llm_runtime_details,
            ),
        },
    )


def build_drive_status_data(app_config: AppConfig, state_dir: Path) -> dict[str, object]:
    if app_config.drive is None or not app_config.drive.enabled:
        return {"configured": False, "note": DRIVE_CONTRACT_NOTE}

    resolved_state_dir = resolve_state_dir(state_dir)
    drive_config = app_config.drive
    auth = drive_config.auth
    cache = drive_config.cache
    token_path = resolve_drive_token_path(state_dir=resolved_state_dir)
    cache_path = resolve_drive_cache_path(state_dir=resolved_state_dir)
    error_message: Optional[str] = None
    credentials = None
    auth_source: Optional[str] = None
    cache_error_message: Optional[str] = None
    cache_entry_count = 0
    cache_valid = False

    try:
        credentials, auth_source, _ = load_drive_credentials(drive_config, resolved_state_dir)
    except ValueError as exc:
        error_message = str(exc)

    try:
        cache_store = load_drive_cache(state_dir=resolved_state_dir)
    except ValueError as exc:
        cache_error_message = str(exc)
    else:
        if cache_store is not None:
            cache_valid = True
            cache_entry_count = len(cache_store.entries)

    refresh_token_present = bool(os.environ.get(auth.refresh_token_env))
    authenticated = credentials is not None and bool(credentials.refresh_token or credentials.token)
    return {
        "configured": True,
        "flow": auth.flow,
        "client_id_env": auth.client_id_env,
        "client_id_present": bool(os.environ.get(auth.client_id_env)),
        "client_secret_env": auth.client_secret_env,
        "client_secret_present": bool(os.environ.get(auth.client_secret_env)),
        "refresh_token_env": auth.refresh_token_env,
        "refresh_token_present": refresh_token_present,
        "scopes": auth.scopes,
        "include_shared_drives": drive_config.include_shared_drives,
        "corpora": drive_config.corpora,
        "metadata_fields": drive_config.metadata_fields,
        "cache_mode": cache.mode,
        "cache_ttl_minutes": cache.ttl_minutes,
        "cache_max_entries": cache.max_entries,
        "cache_path": str(cache_path),
        "cache_file_exists": cache_path.exists(),
        "cache_valid": cache_valid,
        "cache_entry_count": cache_entry_count,
        "token_path": str(token_path),
        "token_file_exists": token_path.exists(),
        "auth_source": auth_source,
        "authenticated": authenticated,
        "credential_refreshable": bool(credentials and credentials.refresh_token),
        "credential_expired": bool(credentials and credentials.expired),
        "credential_scopes": credentials.scopes if credentials is not None else [],
        "metadata_retrieval_ready": True,
        "live_search_available": True,
        "error": error_message,
        "cache_error": cache_error_message,
        "note": DRIVE_CONTRACT_NOTE,
    }


def build_drive_result_contract() -> dict[str, object]:
    return {
        "result_fields": list(DriveFileRecord.model_fields.keys()),
        "search_scope": "metadata-only",
        "live_search_available": True,
        "cache_modes": [option.value for option in DriveCacheModeOption],
    }


def stringify_metadata_value(value: Any) -> str:
    if isinstance(value, dict):
        return ", ".join(
            f"{key}={stringify_metadata_value(nested)}" for key, nested in value.items()
        )
    if isinstance(value, list):
        return ", ".join(stringify_metadata_value(item) for item in value)
    return str(value)


def frontmatter_lines(frontmatter: dict[str, Any], prefix: str = "") -> list[str]:
    lines: list[str] = []

    for key, value in frontmatter.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            lines.extend(frontmatter_lines(value, prefix=full_key))
            continue
        lines.append(f"{full_key}: {stringify_metadata_value(value)}")

    return lines


def emit(payload: CommandPayload, output: OutputMode) -> None:
    if output == OutputMode.json:
        typer.echo(payload.model_dump_json(indent=2))
        return

    if payload.ok:
        data = payload.data
        command = payload.command

        if command == "search":
            typer.echo(f'{data["result_count"]} result(s) for "{data["query"]}"')
            for index, result in enumerate(data["results"], start=1):
                typer.echo(f'{index}. {result["title"]} [{result["source_type"]}]')
                typer.echo(f'   {result["relative_path"]}')
                typer.echo(f'   {result["snippet"]}')
                if result["tags"]:
                    typer.echo(f'   tags: {", ".join(result["tags"])}')
                if result["aliases"]:
                    typer.echo(f'   aliases: {", ".join(result["aliases"])}')
            return

        if command == "show":
            typer.echo(data["path"])
            if data.get("relative_path"):
                typer.echo(f'relative: {data["relative_path"]}')
            if data.get("source_type"):
                typer.echo(f'source: {data["source_type"]}:{data["source_id"]}')
            if data.get("file_type"):
                typer.echo(f'file type: {data["file_type"]}')
            if data.get("tags"):
                typer.echo(f'tags: {", ".join(data["tags"])}')
            if data.get("aliases"):
                typer.echo(f'aliases: {", ".join(data["aliases"])}')
            metadata = data.get("metadata")
            frontmatter = metadata.get("frontmatter") if metadata else None
            if frontmatter:
                typer.echo("frontmatter:")
                for line in frontmatter_lines(frontmatter):
                    typer.echo(f"  {line}")
            if data.get("content_included", True):
                typer.echo("")
                typer.echo(data["preview"])
            return

        if command == "index_add":
            typer.echo(f'Added source {data["source_id"]}')
            typer.echo(f'Root: {data["root_path"]}')
            typer.echo(f'Config: {data["config_path"]}')
            return

        if command == "index_sources":
            typer.echo(f'{data["source_count"]} configured source(s)')
            for source in data["sources"]:
                typer.echo(f'- {source["id"]} [{source["type"]}] {source["root_path"]}')
            return

        if command == "index_run":
            typer.echo(f'Indexed {data["document_count"]} document(s)')
            typer.echo(f'Sources used: {data["source_count"]}')
            typer.echo(f'Index: {data["index_path"]}')
            return

        if command == "dev_project_stats":
            typer.echo(data["summary"])
            for item in data["top_extensions"]:
                typer.echo(f'- {item["extension"]}: {item["count"]}')
            return

        if command == "dev_git_summary":
            typer.echo(data["summary"])
            for line in data["lines"]:
                typer.echo(line)
            return

        if command == "dev_find_todo":
            typer.echo(data["summary"])
            for match in data["matches"]:
                location = (
                    f'{match["relative_path"]}:{match["line"]}:{match["column"]}'
                    f' [{match["kind"]}]'
                )
                typer.echo(f"- {location}")
                typer.echo(f'  {match["text"]}')
            return

        if command == "agent_list_files":
            typer.echo(f'{data["item_count"]} item(s) under {data["root"]}')
            for item in data["items"]:
                typer.echo(f'- {item["kind"]}: {item["path"]}')
            return

        if command == "agent_find_text":
            typer.echo(f'{data["result_count"]} result(s) for "{data["query"]}"')
            for result in data["results"]:
                typer.echo(f'- {result["path"]}')
                typer.echo(f'  {result["snippet"]}')
            return

        if command == "agent_list_notes":
            typer.echo(f'{data["item_count"]} {data["kind"]} note(s)')
            for item in data["items"]:
                typer.echo(f'- {item["name"]}')
                if item.get("purpose"):
                    typer.echo(f'  purpose: {item["purpose"]}')
                typer.echo(f'  path: {item["path"]}')
            return

        if command == "agent_show_note":
            record = data["record"]
            typer.echo(record["name"])
            typer.echo(f'kind: {record["kind"]}')
            if record.get("purpose"):
                typer.echo(f'purpose: {record["purpose"]}')
            if record.get("responsibilities"):
                typer.echo("responsibilities:")
                for responsibility in record["responsibilities"]:
                    typer.echo(f"- {responsibility}")
            if record.get("trigger"):
                typer.echo(f'trigger: {record["trigger"]}')
            if record.get("example"):
                typer.echo(f'example: {record["example"]}')
            typer.echo(f'path: {record["path"]}')
            return

        if command == "version":
            typer.echo(data["version"])
            return

        if command == "doctor":
            environment = data["environment"]
            typer.echo(f'rfs-cli doctor ({data["version"]})')
            typer.echo(f'Python: {environment["python_version"]}')
            typer.echo(f'State dir: {environment["state_dir"]}')
            typer.echo(f'Interactive: {"yes" if environment["interactive"] else "no"}')
            typer.echo(f'Color enabled: {"yes" if environment["color_enabled"] else "no"}')
            typer.echo(format_doctor_text_status("Config", data["config"]))
            typer.echo(format_doctor_text_status("Index", data["index"]))
            typer.echo(format_doctor_text_status("Shell memory", data["shell_memory"]))
            typer.echo(format_doctor_llm_text_status(data["llm_runtime"]))

            suggestions = data.get("suggestions") or []
            if suggestions:
                typer.echo("Suggestions:")
                for suggestion in suggestions:
                    typer.echo(f"- {suggestion}")

            if data.get("verbose"):
                typer.echo("")
                typer.echo("Verbose details:")
                typer.echo(json.dumps(data, indent=2))
            return

        if command == "llm_setup":
            typer.echo(f'Configured {data["provider"]} LLM provider')
            typer.echo(f'Base URL: {data["base_url"]}')
            typer.echo(f'Model: {data["model"]}')
            if data.get("api_key_env"):
                typer.echo(f'API key env: {data["api_key_env"]}')
            typer.echo(f'Config: {data["config_path"]}')
            return

        if command == "llm_status":
            if not data["configured"]:
                typer.echo("LLM 설정이 아직 없습니다.")
                typer.echo("다음 단계: `rfs` 또는 `rfs init`으로 초기 설정을 시작하세요.")
                return
            typer.echo(f'Provider: {data["provider"]}')
            typer.echo(f'Base URL: {data["base_url"]}')
            typer.echo(f'Model: {data["model"]}')
            typer.echo(f'Reachable: {"yes" if data["reachable"] else "no"}')
            if data.get("api_key_env"):
                present = "yes" if data.get("api_key_present") else "no"
                typer.echo(f'API key env: {data["api_key_env"]} (present: {present})')
            available_models = data.get("available_models") or []
            if available_models:
                typer.echo("Available models:")
                for model_name in available_models[:10]:
                    typer.echo(f"- {model_name}")
            if data.get("error"):
                typer.echo(f'Error: {data["error"]}')
            return

        if command == "drive_auth":
            typer.echo("Configured Google Drive auth boundary")
            typer.echo(f'Client ID env: {data["client_id_env"]}')
            typer.echo(f'Client secret env: {data["client_secret_env"]}')
            typer.echo(f'Refresh token env: {data["refresh_token_env"]}')
            typer.echo(f'Cache mode: {data["cache_mode"]}')
            typer.echo(f'Cache path: {data["cache_path"]}')
            typer.echo(f'Cache entries: {data["cache_entry_count"]}')
            typer.echo(f'Token path: {data["token_path"]}')
            typer.echo(f'Authenticated: {"yes" if data["authenticated"] else "no"}')
            typer.echo(
                f'Metadata retrieval adapter: {"yes" if data["metadata_retrieval_ready"] else "no"}'
            )
            typer.echo(f'Config: {data["config_path"]}')
            if data.get("error"):
                typer.echo(f'Error: {data["error"]}')
            if data.get("cache_error"):
                typer.echo(f'Cache error: {data["cache_error"]}')
            typer.echo(data["note"])
            return

        if command == "drive_status":
            if not data["configured"]:
                typer.echo("Google Drive 설정이 아직 없습니다.")
                typer.echo(
                    "다음 단계: `rfs drive auth --configure-only` 또는 "
                    "`rfs drive auth`를 실행하세요."
                )
                typer.echo(data["note"])
                return
            typer.echo(f'Auth flow: {data["flow"]}')
            typer.echo(
                f'Client ID env: {data["client_id_env"]} '
                f'({"yes" if data["client_id_present"] else "no"})'
            )
            typer.echo(
                f'Client secret env: {data["client_secret_env"]} '
                f'({"yes" if data["client_secret_present"] else "no"})'
            )
            typer.echo(
                f'Refresh token env: {data["refresh_token_env"]} '
                f'({"yes" if data["refresh_token_present"] else "no"})'
            )
            typer.echo(f'Cache mode: {data["cache_mode"]}')
            typer.echo(f'Cache path: {data["cache_path"]}')
            typer.echo(f'Cache entries: {data["cache_entry_count"]}')
            typer.echo(f'Shared drives: {"yes" if data["include_shared_drives"] else "no"}')
            typer.echo(f'Authenticated: {"yes" if data["authenticated"] else "no"}')
            typer.echo(
                f'Metadata retrieval adapter: {"yes" if data["metadata_retrieval_ready"] else "no"}'
            )
            typer.echo(f'Live search: {"yes" if data["live_search_available"] else "no"}')
            typer.echo(f'Token path: {data["token_path"]}')
            if data.get("error"):
                typer.echo(f'Error: {data["error"]}')
            if data.get("cache_error"):
                typer.echo(f'Cache error: {data["cache_error"]}')
            typer.echo(data["note"])
            return

        if command == "drive_search":
            cache_label = "hit" if data.get("cache_hit") else "miss"
            typer.echo(f'{data["result_count"]} Drive file(s) for "{data["query"]}"')
            typer.echo(f"Cache: {cache_label}")
            if data.get("next_page_token"):
                typer.echo(f'Next page token: {data["next_page_token"]}')
            for result in data["results"]:
                typer.echo(f'- {result["name"]} [{result["mime_type"]}]')
                typer.echo(f'  id: {result["file_id"]}')
                typer.echo(f'  modified: {result["modified_time"]}')
                if result.get("web_view_link"):
                    typer.echo(f'  link: {result["web_view_link"]}')
            return

        if command == "research_export":
            typer.echo(f'Research export ready for "{data["query"]}"')
            typer.echo(f'Documents: {data["document_count"]}')
            typer.echo(f'Export dir: {data["export_dir"]}')
            typer.echo(f'Manifest: {data["manifest_path"]}')
            return

        if command == "provider_run":
            result = data["provider_result"]
            status = "ok" if result["ok"] else "failed"
            typer.echo(f'{data["provider_id"]}:{data["capability_id"]} {status}')
            typer.echo(result["summary"])
            if result.get("stdout_preview"):
                typer.echo("stdout:")
                typer.echo(result["stdout_preview"])
            if result.get("stderr_preview"):
                typer.echo("stderr:")
                typer.echo(result["stderr_preview"])
            if result.get("truncated"):
                typer.echo("Output truncated.")
            return

        if command == "ask":
            typer.echo(data["answer"])
            return

        typer.echo(json.dumps(payload.data, indent=2))
        return

    error = payload.error or ErrorPayload(code="unknown_error", message="Unknown error.")
    recovery_text = build_recovery_text(payload.command, error.code, error.message)
    if recovery_text is not None:
        typer.echo(recovery_text)
        return
    typer.echo(f"[{error.code}] {error.message}")


def build_recovery_text(command: str, code: str, message: str) -> Optional[str]:
    if code == "missing_llm":
        return (
            "LLM 설정이 아직 없습니다.\n"
            "다음 단계: `rfs` 또는 `rfs init`으로 초기 설정을 시작하세요."
        )

    if code == "missing_index":
        return (
            "인덱스가 아직 없습니다.\n"
            "다음 단계: `rfs index run`으로 먼저 인덱스를 만드세요."
        )

    if code == "missing_source":
        return (
            "연결된 source가 아직 없습니다.\n"
            "다음 단계: `rfs index add <경로> --source local|obsidian`로 source를 추가하세요."
        )

    if code == "missing_drive_config":
        return (
            "Google Drive 설정이 아직 없습니다.\n"
            "다음 단계: `rfs drive auth --configure-only` 또는 "
            "`rfs drive auth`를 실행하세요."
        )

    if code == "not_found":
        if command == "research_export":
            return (
                "내보낼 문서를 찾지 못했습니다.\n"
                "다음 단계: 같은 검색어로 `rfs search \"<검색어>\"` 결과를 먼저 확인하세요."
            )
        return (
            "찾는 항목을 찾지 못했습니다.\n"
            "다음 단계: `rfs search \"<검색어>\"`로 먼저 후보를 확인하세요."
        )

    if code == "llm_error":
        return (
            "LLM 요청 중 문제가 생겼습니다.\n"
            "다음 단계: `rfs llm status`로 연결 상태를 확인하세요.\n"
            f"원인: {message}"
        )

    return None


def fail(command: str, message: str, output: OutputMode, code: str = "runtime_error") -> None:
    payload = CommandPayload(
        command=command,
        ok=False,
        error=ErrorPayload(code=code, message=message),
    )
    emit(payload, output)
    raise typer.Exit(code=1)


def load_config_or_fail(command: str, state_dir: Path, output: OutputMode) -> AppConfig:
    try:
        return load_config(state_dir=state_dir)
    except ValueError as exc:
        fail(command, str(exc), output, code="invalid_config")


def load_agent_config_or_fail(command: str, state_dir: Path, output: OutputMode) -> AppConfig:
    app_config = load_config_or_fail(command, state_dir, output)
    if app_config.llm is None or not app_config.llm.enabled:
        fail(
            command,
            "LLM is required for rfs-cli. Run `rfs init` or `rfs llm setup` first.",
            output,
            code="missing_llm",
        )
    return app_config


def load_provider_config_or_fail(
    app_config: AppConfig,
    provider_id: str,
    output: OutputMode,
) -> ToolProviderRuntimeConfig:
    provider_config = app_config.tool_providers.get(provider_id)
    if provider_config is None:
        fail(
            "provider_run",
            f'Provider "{provider_id}" is not configured in tool_providers.',
            output,
            code="missing_provider_config",
        )
    return provider_config


def load_index_or_fail(command: str, state_dir: Path, output: OutputMode):
    try:
        return load_index(state_dir=state_dir)
    except ValueError as exc:
        fail(command, str(exc), output, code="invalid_index")


def prompt_llm_provider(existing: Optional[LLMConfig]) -> str:
    default_provider = existing.provider if existing is not None else "ollama"
    selected = typer.prompt(
        "LLM provider [ollama/lmstudio/openai-compatible]",
        default=default_provider,
    )
    return normalize_provider(selected)


def configure_llm(
    existing: Optional[LLMConfig],
    provider: Optional[str],
    base_url: Optional[str],
    model: Optional[str],
    api_key_env: Optional[str],
    output: OutputMode,
) -> LLMConfig:
    if provider is None:
        provider_value = prompt_llm_provider(existing)
    else:
        try:
            provider_value = normalize_provider(provider)
        except ValueError as exc:
            fail("llm_setup", str(exc), output, code="invalid_provider")

    default_url = base_url or (existing.base_url if existing is not None else None)
    resolved_base_url = base_url or typer.prompt(
        "Base URL",
        default=default_url or default_base_url(provider_value),
    )

    default_model = model or (
        existing.model if existing is not None and existing.provider == provider_value else None
    )
    resolved_model = model or typer.prompt(
        "Model",
        default=default_model or default_model_hint(provider_value),
    )

    resolved_api_key_env: Optional[str]
    if provider_value == "openai-compatible":
        default_env = (
            api_key_env
            or (
                existing.api_key_env
                if existing is not None and existing.provider == provider_value
                else None
            )
            or default_api_key_env(provider_value)
        )
        resolved_api_key_env = api_key_env or typer.prompt("API key env var", default=default_env)
    else:
        resolved_api_key_env = None

    return LLMConfig(
        provider=provider_value,
        base_url=resolved_base_url.rstrip("/"),
        model=resolved_model,
        api_key_env=resolved_api_key_env,
        enabled=True,
    )


def is_interactive_session() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def run_onboarding_flow(
    state_dir: Path,
    provider: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    api_key_env: Optional[str] = None,
    show_banner: bool = True,
) -> AppConfig:
    resolved_state_dir = resolve_state_dir(state_dir)
    app_config = load_config(state_dir=resolved_state_dir)
    existing = app_config.llm

    if show_banner:
        typer.echo(render_banner())
        typer.echo("")
    typer.echo("Starting rfs onboarding...")

    app_config.llm = configure_llm(
        existing=existing,
        provider=provider,
        base_url=base_url,
        model=model,
        api_key_env=api_key_env,
        output=OutputMode.text,
    )
    config_path = save_config(app_config, state_dir=resolved_state_dir)

    typer.echo("")
    typer.echo(f"LLM configured: {app_config.llm.provider} / {app_config.llm.model}")
    typer.echo(f"Config: {config_path}")
    typer.echo("Onboarding guide loaded for the agent:")
    typer.echo(load_onboarding_document())
    typer.echo("")
    typer.echo("Next steps:")
    typer.echo("- rfs")
    typer.echo("- rfs llm status")
    typer.echo("- rfs shell")
    return app_config


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_shell_memory_or_default(state_dir: Path) -> ShellMemory:
    memory = load_shell_memory(state_dir=state_dir)
    if memory is not None:
        return memory
    now = utc_now_iso()
    return ShellMemory(
        session_id=uuid.uuid4().hex[:12],
        created_at=now,
        updated_at=now,
    )


def append_shell_event(
    memory: ShellMemory,
    kind: str,
    content: str,
    metadata: Optional[dict[str, object]] = None,
) -> None:
    memory.events.append(
        ShellEvent(
            kind=kind,
            content=content,
            timestamp=utc_now_iso(),
            metadata=metadata or {},
        )
    )
    memory.updated_at = utc_now_iso()
    if len(memory.events) > 200:
        memory.events = memory.events[-200:]


def inject_state_dir(args: list[str], state_dir: Path) -> list[str]:
    if "--state-dir" in args or not args:
        return args
    if args[0] not in STATEFUL_COMMANDS:
        return args
    return [*args, "--state-dir", str(state_dir)]


def execute_internal_command(args: list[str], state_dir: Path) -> tuple[int, str]:
    resolved_args = inject_state_dir(args, state_dir)
    if not resolved_args:
        return 0, ""
    if resolved_args[0] == "shell":
        return 1, "Nested `rfs shell` sessions are not supported."

    command = get_command(app)
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    try:
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            command.main(
                args=resolved_args,
                prog_name="rfs",
                standalone_mode=False,
            )
        exit_code = 0
    except click.exceptions.Exit as exc:
        exit_code = exc.exit_code
    except SystemExit as exc:
        exit_code = int(exc.code) if isinstance(exc.code, int) else 1
    except Exception as exc:  # pragma: no cover - defensive path
        exit_code = 1
        stderr_buffer.write(f"{type(exc).__name__}: {exc}\n")

    combined = stdout_buffer.getvalue()
    stderr_output = stderr_buffer.getvalue()
    if stderr_output:
        combined = f"{combined}{stderr_output}"

    return exit_code, combined.rstrip()


def execute_external_command(command_text: str) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            shlex.split(command_text),
            capture_output=True,
            text=True,
            check=False,
        )
    except ValueError as exc:
        return 1, str(exc)
    except FileNotFoundError as exc:
        return 1, f"Command not found: {exc.filename}"

    combined = completed.stdout
    if completed.stderr:
        combined = f"{combined}{completed.stderr}"
    return completed.returncode, combined.rstrip()


@app.callback(invoke_without_command=True)
def root(
    ctx: typer.Context,
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
) -> None:
    if ctx.invoked_subcommand is not None:
        return
    if ctx.resilient_parsing:
        return

    if is_interactive_session():
        resolved_state_dir = resolve_state_dir(state_dir)
        app_config = load_config_or_fail("startup", resolved_state_dir, OutputMode.text)
        if app_config.llm is None or not app_config.llm.enabled:
            run_onboarding_flow(resolved_state_dir)
            typer.echo("")
            typer.echo("Launching rfs shell...")
            run_shell_session(resolved_state_dir, show_banner=False)
            raise typer.Exit()

        run_shell_session(resolved_state_dir)
        raise typer.Exit()

    typer.echo(render_banner())
    typer.echo("")
    typer.echo("Recommended next step:")
    typer.echo("- Run `rfs` in an interactive terminal to start onboarding or the agent shell.")
    typer.echo("Other starting points:")
    typer.echo("- `rfs init` to configure the required LLM flow manually.")
    typer.echo("- `rfs doctor --verbose --format json` to inspect the current workspace state.")
    typer.echo("")
    typer.echo(ctx.get_help())
    raise typer.Exit()


@app.command()
def version(output: OutputMode = typer.Option(OutputMode.text, "--format")) -> None:
    payload = CommandPayload(command="version", ok=True, data={"version": __version__})
    emit(payload, output)


@app.command()
def doctor(
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    verbose: bool = typer.Option(False, "--verbose"),
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
    emit(build_doctor_payload(state_dir, verbose), output)


@app.command()
def init(
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    provider: Optional[str] = typer.Option(None, "--provider"),
    base_url: Optional[str] = typer.Option(None, "--base-url"),
    model: Optional[str] = typer.Option(None, "--model"),
    api_key_env: Optional[str] = typer.Option(None, "--api-key-env"),
) -> None:
    run_onboarding_flow(
        state_dir=state_dir,
        provider=provider,
        base_url=base_url,
        model=model,
        api_key_env=api_key_env,
    )

@app.command(help=ASK_HELP_TEXT)
def ask(
    question: Optional[str] = typer.Argument(None, help="Question about how to use the CLI."),
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
    app_config = load_agent_config_or_fail("ask", state_dir, output)

    prompt = question or typer.prompt("What do you want to do with rfs?")
    intent: UserIntent = interpret_user_intent(prompt)
    suggestion: CommandSuggestion = plan_command_suggestion(intent, app_config, state_dir)
    guidance_response: Optional[GuidanceResponse] = render_guidance_response(
        intent,
        suggestion,
        app_config,
        state_dir,
    )

    if (
        guidance_response is not None
        and suggestion.mode == "follow_up"
        and guidance_response.next_step is not None
    ):
        follow_up_question = guidance_response.next_step
        payload = CommandPayload(
            command="ask",
            ok=True,
            data={
                "question": prompt,
                "provider": app_config.llm.provider,
                "model": app_config.llm.model,
                "answer": follow_up_question,
                "follow_up_required": True,
                "follow_up_question": follow_up_question,
            },
        )
        emit(payload, output)
        return

    if guidance_response is not None and output == OutputMode.text:
        typer.echo(format_guidance_response(guidance_response))
        return

    try:
        answer = ask_llm(
            app_config.llm,
            prompt,
            history=build_guidance_runtime_context(app_config, state_dir),
        )
    except ValueError as exc:
        fail("ask", str(exc), output, code="llm_error")

    payload = CommandPayload(
        command="ask",
        ok=True,
        data={
            "question": prompt,
            "provider": app_config.llm.provider,
            "model": app_config.llm.model,
            "answer": answer,
            "follow_up_required": False,
            "follow_up_question": None,
        },
    )
    emit(payload, output)


def run_shell_session(
    state_dir: Path,
    reset_memory: bool = False,
    show_banner: bool = True,
) -> None:
    resolved_state_dir = resolve_state_dir(state_dir)
    app_config = load_agent_config_or_fail("shell", resolved_state_dir, OutputMode.text)
    if reset_memory:
        now = utc_now_iso()
        memory = ShellMemory(
            session_id=uuid.uuid4().hex[:12],
            created_at=now,
            updated_at=now,
        )
    else:
        memory = load_shell_memory_or_default(resolved_state_dir)

    save_shell_memory(memory, state_dir=resolved_state_dir)

    if show_banner:
        typer.echo(render_banner())
        typer.echo("")
    typer.echo("Interactive shell for rfs-cli")
    typer.echo("Type a supported command without `rfs`, ask a question, or use /help.")
    typer.echo(f"Memory: {resolve_shell_memory_path(state_dir=resolved_state_dir)}")

    while True:
        try:
            raw_input = input(SHELL_PROMPT)
        except EOFError:
            typer.echo("")
            break
        except KeyboardInterrupt:
            typer.echo("")
            continue

        user_input = raw_input.strip()
        if not user_input:
            continue

        append_shell_event(memory, "user", user_input)

        if user_input in {"/exit", "exit", "quit", ":q"}:
            append_shell_event(memory, "system", "Shell session closed by user.")
            save_shell_memory(memory, state_dir=resolved_state_dir)
            typer.echo("Leaving rfs shell.")
            break

        if user_input == "/help":
            help_text = "\n".join(
                [
                    "Shell commands:",
                    "- /help: show shell help",
                    "- /memory: show recent memory items",
                    "- /clear: clear saved shell memory",
                    "- /run <command>: run an rfs command inside the shell",
                    "- !<command>: run an external CLI command and store the result",
                    "- /exit: leave the shell",
                    "You can also type commands directly, for example:",
                    "  doctor --verbose",
                    "  index sources",
                    "  search roadmap",
                    "  dev project-stats --path .",
                    "Or ask a question in natural language if an LLM is configured.",
                ]
            )
            typer.echo(help_text)
            append_shell_event(memory, "assistant", help_text)
            save_shell_memory(memory, state_dir=resolved_state_dir)
            continue

        if user_input == "/memory":
            recent_events = memory.events[:-1][-8:]
            if not recent_events:
                message = "No saved shell memory yet."
            else:
                lines = [
                    f"{event.timestamp} [{event.kind}] {event.content}"
                    for event in recent_events
                ]
                message = "\n".join(lines)
            typer.echo(message)
            append_shell_event(memory, "assistant", message)
            save_shell_memory(memory, state_dir=resolved_state_dir)
            continue

        if user_input == "/clear":
            memory.events = []
            memory.updated_at = utc_now_iso()
            save_shell_memory(memory, state_dir=resolved_state_dir)
            typer.echo("Shell memory cleared.")
            continue

        if user_input.startswith("!"):
            command_text = user_input[1:].strip()
            if not command_text:
                typer.echo("No external command provided.")
                save_shell_memory(memory, state_dir=resolved_state_dir)
                continue

            exit_code, output = execute_external_command(command_text)
            if output:
                typer.echo(output)
            status_text = f"External command exited with code {exit_code}."
            typer.echo(status_text)
            append_shell_event(
                memory,
                "tool",
                output or status_text,
                metadata={
                    "command": command_text,
                    "exit_code": exit_code,
                    "tool_type": "external",
                },
            )
            save_shell_memory(memory, state_dir=resolved_state_dir)
            continue

        command_input = user_input
        if user_input.startswith("/run "):
            command_input = user_input[5:].strip()

        command_tokens = shlex.split(command_input)
        if command_tokens and command_tokens[0] == "rfs":
            command_tokens = command_tokens[1:]

        if command_tokens and command_tokens[0] in KNOWN_SHELL_COMMANDS:
            exit_code, output = execute_internal_command(command_tokens, resolved_state_dir)
            if output:
                typer.echo(output)
            status_text = f"Command exited with code {exit_code}."
            typer.echo(status_text)
            append_shell_event(
                memory,
                "tool",
                output or status_text,
                metadata={"command": " ".join(command_tokens), "exit_code": exit_code},
            )
            save_shell_memory(memory, state_dir=resolved_state_dir)
            continue

        intent = interpret_user_intent(user_input)
        suggestion = plan_command_suggestion(intent, app_config, resolved_state_dir)
        guidance_response = render_guidance_response(
            intent,
            suggestion,
            app_config,
            resolved_state_dir,
        )
        if guidance_response is not None:
            guidance_text = format_guidance_response(guidance_response)
            typer.echo(guidance_text)
            append_shell_event(memory, "assistant", guidance_text)
            save_shell_memory(memory, state_dir=resolved_state_dir)
            continue

        try:
            answer = ask_llm(
                app_config.llm,
                user_input,
                history=build_shell_guidance_history(
                    app_config,
                    resolved_state_dir,
                    memory,
                ),
            )
        except ValueError as exc:
            answer = f"LLM error: {exc}"

        typer.echo(answer)
        append_shell_event(memory, "assistant", answer)
        save_shell_memory(memory, state_dir=resolved_state_dir)


@app.command(help=SHELL_HELP_TEXT)
def shell(
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    reset_memory: bool = typer.Option(False, "--reset-memory"),
) -> None:
    run_shell_session(state_dir=state_dir, reset_memory=reset_memory)


@provider_app.command("run")
def provider_run(
    provider_id: str = typer.Argument(..., help="Provider id, for example qa_claw."),
    capability_id: str = typer.Argument(..., help="Capability id, for example scan_secrets."),
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
    app_config = load_config_or_fail("provider_run", state_dir, output)
    provider_config = load_provider_config_or_fail(app_config, provider_id, output)

    try:
        provider_result = run_tool_provider(provider_id, capability_id, provider_config)
    except ProviderExecutionError as exc:
        fail("provider_run", str(exc), output, code=exc.code)

    payload = CommandPayload(
        command="provider_run",
        ok=True,
        data={
            "provider_id": provider_id,
            "capability_id": capability_id,
            "provider_result": provider_result,
        },
    )
    emit(payload, output)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query."),
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    source: Optional[str] = typer.Option(None, "--source"),
    source_id: Optional[str] = typer.Option(None, "--source-id"),
    tag: Optional[list[str]] = typer.Option(None, "--tag"),
    path_prefix: Optional[str] = typer.Option(None, "--path-prefix"),
    file_type: Optional[str] = typer.Option(None, "--file-type"),
    limit: int = typer.Option(20, min=1, max=100),
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
    load_agent_config_or_fail("search", state_dir, output)
    index_store = load_index_or_fail("search", state_dir, output)
    if index_store is None:
        fail("search", "No index found. Run `rfs index run` first.", output, code="missing_index")

    results = search_index(
        query=query,
        index_store=index_store,
        source_type=source,
        source_id=source_id,
        tag_filters=tag,
        path_prefix=path_prefix,
        file_type=file_type,
        limit=limit,
    )
    payload = CommandPayload(
        command="search",
        ok=True,
        data={
            "query": query,
            "state_dir": str(resolve_state_dir(state_dir)),
            "filters": {
                "source": source,
                "source_id": source_id,
                "tags": tag or [],
                "path_prefix": path_prefix,
                "file_type": file_type,
            },
            "result_count": len(results),
            "results": results,
        },
    )
    emit(payload, output)


@app.command()
def show(
    target: str = typer.Argument(...),
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    metadata_only: bool = typer.Option(False, "--metadata-only"),
    preview_chars: int = typer.Option(500, "--preview-chars", min=0, max=5000),
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
    load_agent_config_or_fail("show", state_dir, output)
    index_store = load_index_or_fail("show", state_dir, output)
    document = resolve_index_document(target, index_store) if index_store is not None else None
    if document is None:
        target_path = Path(target).expanduser()
        if target_path.exists() and target_path.is_file():
            payload = CommandPayload(
                command="show",
                ok=True,
                data=preview_file(target_path, max_chars=0 if metadata_only else preview_chars),
            )
            emit(payload, output)
            return
        if index_store is None:
            fail("show", "No index found. Run `rfs index run` first.", output, code="missing_index")
        fail("show", f'No indexed document matched "{target}".', output, code="not_found")

    payload = CommandPayload(
        command="show",
        ok=True,
        data={
            "path": document.path,
            "relative_path": document.relative_path,
            "size_bytes": len(document.content.encode("utf-8")),
            "preview": "" if metadata_only else document.content[:preview_chars],
            "content_included": not metadata_only,
            "document_id": document.document_id,
            "source_id": document.source_id,
            "source_type": document.source_type,
            "file_type": document.file_type,
            "tags": document.tags,
            "aliases": document.aliases,
            "metadata": document.metadata,
        },
    )
    emit(payload, output)


@index_app.command("add")
def index_add(
    root: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    source: str = typer.Option("local", "--source"),
    source_id: Optional[str] = typer.Option(None, "--id"),
    name: Optional[str] = typer.Option(None, "--name"),
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
    app_config = load_agent_config_or_fail("index_add", state_dir, output)
    resolved_root = root.expanduser().resolve()
    new_source_id = source_id or build_source_id(resolved_root)
    display_name = name or resolved_root.name or new_source_id

    app_config.sources = [
        existing
        for existing in app_config.sources
        if existing.id != new_source_id
        and Path(existing.root_path).expanduser().resolve() != resolved_root
    ]
    app_config.sources.append(
        SourceConfig(
            id=new_source_id,
            type=source,
            root_path=str(resolved_root),
            display_name=display_name,
            enabled=True,
        )
    )

    config_path = save_config(app_config, state_dir=state_dir)
    payload = CommandPayload(
        command="index_add",
        ok=True,
        data={
            "source_id": new_source_id,
            "source_type": source,
            "root_path": str(resolved_root),
            "display_name": display_name,
            "config_path": str(config_path),
        },
    )
    emit(payload, output)


@index_app.command("sources")
def index_sources(
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
    app_config = load_agent_config_or_fail("index_sources", state_dir, output)
    payload = CommandPayload(
        command="index_sources",
        ok=True,
        data={
            "source_count": len(app_config.sources),
            "config_path": str(resolve_config_path(state_dir=state_dir)),
            "sources": [source.model_dump() for source in app_config.sources],
        },
    )
    emit(payload, output)


@index_app.command("run")
def index_run(
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    source: Optional[str] = typer.Option(None, "--source"),
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
    app_config = load_agent_config_or_fail("index_run", state_dir, output)
    sources = [configured for configured in app_config.sources if configured.enabled]
    if source is not None:
        sources = [configured for configured in sources if configured.type == source]

    if not sources:
        fail(
            "index_run",
            "No configured sources matched. Add a source with `rfs index add` first.",
            output,
            code="missing_source",
        )

    index_store = build_index(sources)
    index_path = save_index(index_store, state_dir=state_dir)
    payload = CommandPayload(
        command="index_run",
        ok=True,
        data={
            "state_dir": str(resolve_state_dir(state_dir)),
            "source_count": len(sources),
            "document_count": len(index_store.documents),
            "index_path": str(index_path),
        },
    )
    emit(payload, output)


@dev_app.command("project-stats")
def dev_project_stats(
    path: Path = typer.Option(Path("."), "--path", exists=True, file_okay=False, dir_okay=True),
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
    load_agent_config_or_fail("dev_project_stats", state_dir, output)
    stats = project_stats(path)
    payload = CommandPayload(
        command="dev_project_stats",
        ok=True,
        data=build_dev_data(
            "project-stats",
            path,
            f'Project stats for {stats["root"]}: {stats["total_files"]} file(s)',
            **stats,
        ),
    )
    emit(payload, output)


@dev_app.command("git-summary")
def dev_git_summary(
    path: Path = typer.Option(Path("."), "--path", exists=True, file_okay=False, dir_okay=True),
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
    load_agent_config_or_fail("dev_git_summary", state_dir, output)
    try:
        summary = git_summary(path)
    except ValueError as exc:
        fail("dev_git_summary", str(exc), output, code="git_error")
    payload = CommandPayload(
        command="dev_git_summary",
        ok=True,
        data=build_dev_data(
            "git-summary",
            path,
            f'Git status for {summary["root"]}',
            **summary,
        ),
    )
    emit(payload, output)


@dev_app.command("find-todo")
def dev_find_todo(
    path: Path = typer.Option(Path("."), "--path", exists=True, file_okay=False, dir_okay=True),
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    limit: int = typer.Option(100, min=1, max=500),
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
    load_agent_config_or_fail("dev_find_todo", state_dir, output)
    todo_data = find_todo_markers(path, limit=limit)
    payload = CommandPayload(
        command="dev_find_todo",
        ok=True,
        data=build_dev_data(
            "find-todo",
            path,
            f'Found {todo_data["match_count"]} TODO-like marker(s) under {todo_data["root"]}',
            **todo_data,
        ),
    )
    emit(payload, output)


@agent_app.command("list-files")
def agent_list_files(
    root: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    limit: int = typer.Option(100, min=1, max=200),
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    output: OutputMode = typer.Option(OutputMode.json, "--format"),
) -> None:
    load_agent_config_or_fail("agent_list_files", state_dir, output)
    items = list_files(root, limit=limit)
    payload = CommandPayload(
        command="agent_list_files",
        ok=True,
        data={"root": str(root.resolve()), "item_count": len(items), "items": items},
    )
    emit(payload, output)


@agent_app.command("find-text")
def agent_find_text(
    query: str = typer.Argument(...),
    root: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    limit: int = typer.Option(20, min=1, max=100),
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    output: OutputMode = typer.Option(OutputMode.json, "--format"),
) -> None:
    load_agent_config_or_fail("agent_find_text", state_dir, output)
    results = live_search(query=query, root=root, limit=limit)
    payload = CommandPayload(
        command="agent_find_text",
        ok=True,
        data={
            "query": query,
            "root": str(root.resolve()),
            "result_count": len(results),
            "results": results,
        },
    )
    emit(payload, output)


@agent_app.command("list-notes")
def agent_list_notes(
    kind: NoteKindOption = typer.Option(..., "--kind"),
    limit: int = typer.Option(50, min=1, max=200),
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    output: OutputMode = typer.Option(OutputMode.json, "--format"),
) -> None:
    load_agent_config_or_fail("agent_list_notes", state_dir, output)
    index_store = load_index_or_fail("agent_list_notes", state_dir, output)
    items = list_note_records(index_store, kind=kind.value, limit=limit)
    payload = CommandPayload(
        command="agent_list_notes",
        ok=True,
        data={
            "kind": kind.value,
            "item_count": len(items),
            "items": items,
        },
    )
    emit(payload, output)


@agent_app.command("show-note")
def agent_show_note(
    document_id: str = typer.Argument(...),
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    output: OutputMode = typer.Option(OutputMode.json, "--format"),
) -> None:
    load_agent_config_or_fail("agent_show_note", state_dir, output)
    index_store = load_index_or_fail("agent_show_note", state_dir, output)
    record = get_note_record(index_store, document_id)
    if record is None:
        fail(
            "agent_show_note",
            f"No agent or skill note found for id '{document_id}'.",
            output,
            code="not_found",
        )

    payload = CommandPayload(
        command="agent_show_note",
        ok=True,
        data={"record": record},
    )
    emit(payload, output)


@llm_app.command("setup")
def llm_setup(
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    provider: Optional[str] = typer.Option(None, "--provider"),
    base_url: Optional[str] = typer.Option(None, "--base-url"),
    model: Optional[str] = typer.Option(None, "--model"),
    api_key_env: Optional[str] = typer.Option(None, "--api-key-env"),
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
    app_config = load_config_or_fail("llm_setup", state_dir, output)
    app_config.llm = configure_llm(
        existing=app_config.llm,
        provider=provider,
        base_url=base_url,
        model=model,
        api_key_env=api_key_env,
        output=output,
    )
    config_path = save_config(app_config, state_dir=state_dir)

    payload = CommandPayload(
        command="llm_setup",
        ok=True,
        data={
            "provider": app_config.llm.provider,
            "base_url": app_config.llm.base_url,
            "model": app_config.llm.model,
            "api_key_env": app_config.llm.api_key_env,
            "config_path": str(config_path),
        },
    )
    emit(payload, output)


@llm_app.command("status")
def llm_status(
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
    app_config = load_config_or_fail("llm_status", state_dir, output)
    if app_config.llm is None or not app_config.llm.enabled:
        payload = CommandPayload(
            command="llm_status",
            ok=True,
            data={"configured": False},
        )
        emit(payload, output)
        return

    payload = CommandPayload(
        command="llm_status",
        ok=True,
        data=get_llm_status(app_config.llm),
    )
    emit(payload, output)


@drive_app.command("auth")
def drive_auth(
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    client_id_env: str = typer.Option("GOOGLE_DRIVE_CLIENT_ID", "--client-id-env"),
    client_secret_env: str = typer.Option("GOOGLE_DRIVE_CLIENT_SECRET", "--client-secret-env"),
    refresh_token_env: str = typer.Option("GOOGLE_DRIVE_REFRESH_TOKEN", "--refresh-token-env"),
    include_shared_drives: bool = typer.Option(False, "--include-shared-drives"),
    corpus: Optional[list[str]] = typer.Option(None, "--corpus"),
    metadata_field: Optional[list[str]] = typer.Option(None, "--metadata-field"),
    cache_mode: DriveCacheModeOption = typer.Option(
        DriveCacheModeOption.metadata_only,
        "--cache-mode",
    ),
    cache_ttl_minutes: int = typer.Option(60, "--cache-ttl-minutes", min=1),
    cache_max_entries: int = typer.Option(1000, "--cache-max-entries", min=1),
    configure_only: bool = typer.Option(False, "--configure-only"),
    launch_browser: bool = typer.Option(True, "--launch-browser/--no-launch-browser"),
    auth_port: int = typer.Option(0, "--auth-port", min=0, max=65535),
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
    app_config = load_config_or_fail("drive_auth", state_dir, output)

    try:
        drive_config = DriveConfig(
            enabled=True,
            include_shared_drives=include_shared_drives,
            corpora=corpus or ["user"],
            metadata_fields=metadata_field or DriveConfig().metadata_fields,
            auth=DriveAuthConfig(
                client_id_env=client_id_env,
                client_secret_env=client_secret_env,
                refresh_token_env=refresh_token_env,
            ),
            cache=DriveCacheConfig(
                mode=cache_mode.value,
                ttl_minutes=cache_ttl_minutes,
                max_entries=cache_max_entries,
            ),
        )
    except ValidationError as exc:
        message = exc.errors()[0]["msg"] if exc.errors() else "Invalid Google Drive config."
        fail("drive_auth", message, output, code="invalid_drive_config")

    app_config.drive = drive_config
    config_path = save_config(app_config, state_dir=state_dir)
    token_path = resolve_drive_token_path(state_dir=state_dir)
    if not configure_only:
        try:
            token_path = run_drive_installed_app_auth(
                drive_config,
                state_dir=state_dir,
                open_browser=launch_browser,
                port=auth_port,
            )
        except ValueError as exc:
            fail("drive_auth", str(exc), output, code="drive_auth_error")

    payload = CommandPayload(
        command="drive_auth",
        ok=True,
        data={
            **build_drive_status_data(app_config, state_dir),
            "config_path": str(config_path),
            "configure_only": configure_only,
            "launch_browser": launch_browser,
            "auth_port": auth_port,
            "token_path": str(token_path),
        },
    )
    emit(payload, output)


@drive_app.command("status")
def drive_status(
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
    app_config = load_config_or_fail("drive_status", state_dir, output)
    payload = CommandPayload(
        command="drive_status",
        ok=True,
        data=build_drive_status_data(app_config, state_dir),
    )
    emit(payload, output)


@drive_app.command("search")
def drive_search(
    query: str = typer.Argument(...),
    page_size: int = typer.Option(20, "--page-size", min=1, max=100),
    page_token: Optional[str] = typer.Option(None, "--page-token"),
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
    app_config = load_config_or_fail("drive_search", state_dir, output)
    if app_config.drive is None or not app_config.drive.enabled:
        fail(
            "drive_search",
            "Google Drive is not configured. Run `rfs drive auth` first.",
            output,
            code="missing_drive_config",
        )

    try:
        result = fetch_drive_file_metadata(
            app_config.drive,
            state_dir=state_dir,
            query=query,
            page_size=page_size,
            page_token=page_token,
        )
    except ValueError as exc:
        message = str(exc)
        error_code = "drive_search_error"
        if "not authenticated" in message.lower():
            error_code = "missing_drive_auth"
        fail("drive_search", message, output, code=error_code)

    payload = CommandPayload(
        command="drive_search",
        ok=True,
        data={
            "query": query,
            "page_size": page_size,
            "page_token": page_token,
            "result_count": len(result["records"]),
            "results": [record.model_dump(mode="json") for record in result["records"]],
            "next_page_token": result["next_page_token"],
            "incomplete_search": result["incomplete_search"],
            "auth_source": result["auth_source"],
            "cache_hit": result["cache_hit"],
            "cache_key": result["cache_key"],
            "cache_path": result["cache_path"],
            "fetched_at": result["fetched_at"],
            "expires_at": result["expires_at"],
            "search_scope": "metadata-only",
            "planned_result_contract": build_drive_result_contract(),
            "note": DRIVE_CONTRACT_NOTE,
        },
    )
    emit(payload, output)


@research_app.command("export")
def research_export(
    query: str = typer.Argument(..., help="Search query used to select indexed documents."),
    output_dir: Path = typer.Option(Path("exports/research"), "--output-dir"),
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    source: Optional[str] = typer.Option(None, "--source"),
    source_id: Optional[str] = typer.Option(None, "--source-id"),
    tag: Optional[list[str]] = typer.Option(None, "--tag"),
    path_prefix: Optional[str] = typer.Option(None, "--path-prefix"),
    file_type: Optional[str] = typer.Option(None, "--file-type"),
    limit: int = typer.Option(20, "--limit", min=1, max=100),
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
    load_agent_config_or_fail("research_export", state_dir, output)
    index_store = load_index_or_fail("research_export", state_dir, output)
    if index_store is None:
        fail(
            "research_export",
            "No index found. Run `rfs index run` first.",
            output,
            code="missing_index",
        )

    bundle = export_research_bundle(
        query=query,
        index_store=index_store,
        output_dir=output_dir,
        state_dir=state_dir,
        source=source,
        source_id=source_id,
        tag_filters=tag,
        path_prefix=path_prefix,
        file_type=file_type,
        limit=limit,
    )
    if bundle is None:
        fail(
            "research_export",
            f'No indexed documents matched "{query}".',
            output,
            code="not_found",
        )

    payload = CommandPayload(
        command="research_export",
        ok=True,
        data=bundle,
    )
    emit(payload, output)


def main() -> None:
    app()
