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
from typer.main import get_command

from rfs_cli import __version__
from rfs_cli.config import (
    load_config,
    load_index,
    load_shell_memory,
    resolve_config_path,
    resolve_shell_memory_path,
    resolve_state_dir,
    save_config,
    save_index,
    save_shell_memory,
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
    ErrorPayload,
    LLMConfig,
    ShellEvent,
    ShellMemory,
    SourceConfig,
)
from rfs_cli.services import (
    find_todo_markers,
    git_summary,
    list_files,
    live_search,
    preview_file,
    project_stats,
)

app = typer.Typer(help="Personal knowledge, developer utility, and AI-tool CLI.")
index_app = typer.Typer(help="Index-related commands.")
dev_app = typer.Typer(help="Developer utility commands.")
agent_app = typer.Typer(help="AI-safe commands.")
drive_app = typer.Typer(help="Google Drive placeholder commands.")
llm_app = typer.Typer(help="LLM setup and guidance commands.")

app.add_typer(index_app, name="index")
app.add_typer(dev_app, name="dev")
app.add_typer(agent_app, name="agent")
app.add_typer(drive_app, name="drive")
app.add_typer(llm_app, name="llm")


class OutputMode(str, Enum):
    text = "text"
    json = "json"


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
SHELL_PROMPT = "rfs> "
KNOWN_SHELL_COMMANDS = {
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
}
STATEFUL_COMMANDS = {"ask", "search", "show", "index", "dev", "agent", "drive", "llm"}


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

        if command == "version":
            typer.echo(data["version"])
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
                typer.echo("LLM is not configured. Run `rfs llm setup` first.")
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

        if command == "ask":
            typer.echo(data["answer"])
            return

        typer.echo(json.dumps(payload.data, indent=2))
        return

    error = payload.error or ErrorPayload(code="unknown_error", message="Unknown error.")
    typer.echo(f"[{error.code}] {error.message}")


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


def format_source_summary(sources: list[SourceConfig]) -> list[str]:
    if not sources:
        return ["Configured sources: none."]

    lines = [f"Configured sources: {len(sources)}"]
    for source in sources[:8]:
        status = "enabled" if source.enabled else "disabled"
        lines.append(
            f"- {source.id} [{source.type}] {status} root={source.root_path}"
        )
    if len(sources) > 8:
        lines.append(f"- ... {len(sources) - 8} more source(s)")
    return lines


def build_guidance_runtime_context(app_config: AppConfig, state_dir: Path) -> list[dict[str, str]]:
    resolved_state_dir = resolve_state_dir(state_dir)
    lines = [
        "Workspace guidance context:",
        f"- state_dir: {resolved_state_dir}",
        *format_source_summary(app_config.sources),
    ]

    try:
        index_store = load_index(state_dir=resolved_state_dir)
    except ValueError as exc:
        lines.append("- index_status: invalid")
        lines.append(f"- index_error: {exc}")
        lines.append(
            "- guidance_hint: recommend rebuilding the index with `rfs index run` "
            "after checking configured sources."
        )
        return [{"role": "system", "content": "\n".join(lines)}]

    if index_store is None:
        lines.append("- index_status: missing")
        if app_config.sources:
            lines.append(
                "- guidance_hint: sources exist, so prefer `rfs index run` before "
                "recommending `search` or `show`."
            )
        else:
            lines.append(
                "- guidance_hint: no sources exist, so prefer `rfs index add <root> "
                "--source local|obsidian` before `rfs index run`."
            )
        return [{"role": "system", "content": "\n".join(lines)}]

    source_ids = sorted({document.source_id for document in index_store.documents})
    file_types = sorted({document.file_type for document in index_store.documents})
    lines.extend(
        [
            "- index_status: available",
            f"- indexed_document_count: {len(index_store.documents)}",
            f"- indexed_source_ids: {', '.join(source_ids) if source_ids else 'none'}",
            f"- indexed_file_types: {', '.join(file_types[:10]) if file_types else 'none'}",
            "- guidance_hint: prefer grounded `search`, `show`, and filter suggestions "
            "that match the available sources and indexed content.",
        ]
    )
    return [{"role": "system", "content": "\n".join(lines)}]


def shell_history_messages(
    memory: ShellMemory,
    limit: int = 8,
    include_latest: bool = True,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                "You are answering from inside an already active `rfs shell` session. "
                "The user is already in the shell right now. "
                "Do not tell the user to run `rfs shell` unless they are explicitly "
                "asking how to start a new session."
            ),
        }
    ]
    events = memory.events if include_latest else memory.events[:-1]
    for event in events[-limit:]:
        if event.kind == "user":
            messages.append({"role": "user", "content": event.content})
            continue
        if event.kind == "assistant":
            messages.append({"role": "assistant", "content": event.content})
            continue
        if event.kind == "tool":
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Recent tool execution:\n"
                        f'command: {event.metadata.get("command", "unknown")}\n'
                        f"output:\n{event.content}"
                    ),
                }
            )
    return messages


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
    typer.echo("Run `rfs` in an interactive terminal to start onboarding or the agent shell.")
    typer.echo("Use `rfs init` when you want to configure the required LLM flow manually.")
    typer.echo("")
    typer.echo(ctx.get_help())
    raise typer.Exit()


@app.command()
def version(output: OutputMode = typer.Option(OutputMode.text, "--format")) -> None:
    payload = CommandPayload(command="version", ok=True, data={"version": __version__})
    emit(payload, output)


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


@app.command()
def ask(
    question: Optional[str] = typer.Argument(None, help="Question about how to use the CLI."),
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
    app_config = load_agent_config_or_fail("ask", state_dir, output)

    prompt = question or typer.prompt("What do you want to do with rfs?")

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

        try:
            answer = ask_llm(
                app_config.llm,
                user_input,
                history=shell_history_messages(memory, include_latest=False),
            )
        except ValueError as exc:
            answer = f"LLM error: {exc}"

        typer.echo(answer)
        append_shell_event(memory, "assistant", answer)
        save_shell_memory(memory, state_dir=resolved_state_dir)


@app.command()
def shell(
    state_dir: Path = typer.Option(Path(".rfs"), "--state-dir"),
    reset_memory: bool = typer.Option(False, "--reset-memory"),
) -> None:
    run_shell_session(state_dir=state_dir, reset_memory=reset_memory)


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


@drive_app.command("search")
def drive_search(
    query: str = typer.Argument(...),
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
    fail(
        "drive_search",
        f'Drive integration is scheduled for Phase 4. Query "{query}" was not executed.',
        output,
        code="not_implemented",
    )


def main() -> None:
    app()
