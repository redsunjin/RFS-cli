from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import typer

from rfs_cli import __version__
from rfs_cli.config import (
    load_config,
    load_index,
    resolve_config_path,
    resolve_state_dir,
    save_config,
    save_index,
)
from rfs_cli.indexing import build_index, build_source_id, resolve_index_document, search_index
from rfs_cli.models import AppConfig, CommandPayload, ErrorPayload, SourceConfig
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

app.add_typer(index_app, name="index")
app.add_typer(dev_app, name="dev")
app.add_typer(agent_app, name="agent")
app.add_typer(drive_app, name="drive")


class OutputMode(str, Enum):
    text = "text"
    json = "json"


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


def load_index_or_fail(command: str, state_dir: Path, output: OutputMode):
    try:
        return load_index(state_dir=state_dir)
    except ValueError as exc:
        fail(command, str(exc), output, code="invalid_index")


@app.command()
def version(output: OutputMode = typer.Option(OutputMode.text, "--format")) -> None:
    payload = CommandPayload(command="version", ok=True, data={"version": __version__})
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
    app_config = load_config_or_fail("index_add", state_dir, output)
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
    app_config = load_config_or_fail("index_sources", state_dir, output)
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
    app_config = load_config_or_fail("index_run", state_dir, output)
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
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
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
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
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
    limit: int = typer.Option(100, min=1, max=500),
    output: OutputMode = typer.Option(OutputMode.text, "--format"),
) -> None:
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
    output: OutputMode = typer.Option(OutputMode.json, "--format"),
) -> None:
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
    output: OutputMode = typer.Option(OutputMode.json, "--format"),
) -> None:
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
