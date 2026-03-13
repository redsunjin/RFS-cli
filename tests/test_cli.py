import json
import subprocess
from pathlib import Path
from typing import Optional

from typer.testing import CliRunner

from rfs_cli.config import load_config, load_shell_memory, save_config
from rfs_cli.main import app, render_banner
from rfs_cli.models import LLMConfig

runner = CliRunner()
WAVE_LINE = "~" * 76


def save_llm_config(state_dir: Path) -> None:
    config = load_config(state_dir=state_dir)
    config.llm = LLMConfig(
        provider="ollama",
        base_url="http://127.0.0.1:11434",
        model="qwen2.5:7b-instruct",
    )
    save_config(config, state_dir=state_dir)


def assert_command_payload(payload: dict[str, object], command: str, ok: bool) -> None:
    assert payload["schema_version"] == "1"
    assert payload["command"] == command
    assert payload["ok"] is ok
    assert "data" in payload
    assert "error" in payload


def build_index_with_source(
    state_dir: Path,
    root: Path,
    source_type: str,
    source_id: Optional[str] = None,
) -> None:
    save_llm_config(state_dir)
    command = ["index", "add", str(root), "--source", source_type, "--state-dir", str(state_dir)]
    if source_id is not None:
        command.extend(["--id", source_id])
    runner.invoke(app, command)


def rebuild_index(state_dir: Path) -> None:
    runner.invoke(app, ["index", "run", "--state-dir", str(state_dir)])


def test_version_json() -> None:
    result = runner.invoke(app, ["version", "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "version", True)
    assert payload["data"]["version"] == "0.1.0"


def test_root_without_args_shows_banner_and_help() -> None:
    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert " ____  _____    _    ______   __   _____ ___  ____    ____  _____    _" in result.stdout
    assert WAVE_LINE in result.stdout
    assert "Start with `rfs init`" in result.stdout
    assert "Usage:" in result.stdout


def test_render_banner_uses_ansi_when_forced(monkeypatch) -> None:
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)

    banner = render_banner()

    assert "\033[38;2;" in banner
    assert "~" in banner


def test_llm_setup_interactive_saves_config(tmp_path: Path) -> None:
    state_dir = tmp_path / ".rfs"

    result = runner.invoke(
        app,
        ["llm", "setup", "--state-dir", str(state_dir), "--format", "json"],
        input="ollama\n\n\n",
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    assert_command_payload(payload, "llm_setup", True)
    assert payload["data"]["provider"] == "ollama"
    assert payload["data"]["base_url"] == "http://127.0.0.1:11434"
    assert payload["data"]["model"] == "qwen2.5:7b-instruct"

    config = json.loads((state_dir / "config.json").read_text(encoding="utf-8"))
    assert config["llm"]["provider"] == "ollama"


def test_init_interactive_writes_llm_config_and_prints_onboarding(tmp_path: Path) -> None:
    state_dir = tmp_path / ".rfs"

    result = runner.invoke(
        app,
        ["init", "--state-dir", str(state_dir)],
        input="ollama\n\n\n",
    )

    assert result.exit_code == 0
    assert "Starting rfs onboarding..." in result.stdout
    assert "R2-D2-inspired persona" in result.stdout
    assert "rfs shell" in result.stdout

    config = json.loads((state_dir / "config.json").read_text(encoding="utf-8"))
    assert config["llm"]["provider"] == "ollama"


def test_llm_status_json_reports_configured_state(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)

    monkeypatch.setattr(
        "rfs_cli.main.get_llm_status",
        lambda config: {
            "configured": True,
            "provider": config.provider,
            "base_url": config.base_url,
            "model": config.model,
            "api_key_env": None,
            "api_key_present": None,
            "reachable": True,
            "available_models": [config.model],
            "default_model_available": True,
            "error": None,
        },
    )

    result = runner.invoke(
        app,
        ["llm", "status", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "llm_status", True)
    assert payload["data"]["configured"] is True
    assert payload["data"]["reachable"] is True


def test_ask_json_uses_configured_llm(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)

    monkeypatch.setattr(
        "rfs_cli.main.ask_llm",
        lambda config, question: f"Use `rfs search \"{question}\"`.",
    )

    result = runner.invoke(
        app,
        ["ask", "agent memory", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "ask", True)
    assert payload["data"]["provider"] == "ollama"
    assert "rfs search" in payload["data"]["answer"]


def test_ask_fails_without_llm_config(tmp_path: Path) -> None:
    state_dir = tmp_path / ".rfs"

    result = runner.invoke(
        app,
        ["ask", "how do I search?", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "ask", False)
    assert payload["error"]["code"] == "missing_llm"


def test_shell_runs_internal_command_and_saves_memory(tmp_path: Path) -> None:
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)

    result = runner.invoke(
        app,
        ["shell", "--state-dir", str(state_dir)],
        input="version\n/exit\n",
    )

    assert result.exit_code == 0
    assert "Interactive shell for rfs-cli" in result.stdout
    assert "0.1.0" in result.stdout
    assert "Command exited with code 0." in result.stdout

    memory = load_shell_memory(state_dir=state_dir)
    assert memory is not None
    assert any(event.kind == "tool" for event in memory.events)
    assert any(event.metadata.get("command") == "version" for event in memory.events)


def test_shell_uses_llm_and_persists_conversation(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)

    captured: dict[str, object] = {}

    def fake_ask_llm(config, question, history=None):
        captured["question"] = question
        captured["history"] = history or []
        return "Use `rfs search \"roadmap\"`."

    monkeypatch.setattr("rfs_cli.main.ask_llm", fake_ask_llm)

    result = runner.invoke(
        app,
        ["shell", "--state-dir", str(state_dir)],
        input="How do I search roadmap notes?\n/exit\n",
    )

    assert result.exit_code == 0
    assert 'Use `rfs search "roadmap"`.' in result.stdout
    assert captured["question"] == "How do I search roadmap notes?"
    assert captured["history"] == []

    memory = load_shell_memory(state_dir=state_dir)
    assert memory is not None
    assert any(event.kind == "assistant" for event in memory.events)


def test_shell_memory_commands_work(tmp_path: Path) -> None:
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)

    result = runner.invoke(
        app,
        ["shell", "--state-dir", str(state_dir)],
        input="/memory\n/clear\n/memory\n/exit\n",
    )

    assert result.exit_code == 0
    assert "No saved shell memory yet." in result.stdout
    assert "Shell memory cleared." in result.stdout


def test_shell_runs_external_command_and_records_it(tmp_path: Path) -> None:
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)

    result = runner.invoke(
        app,
        ["shell", "--state-dir", str(state_dir)],
        input="!/bin/echo hello\n/exit\n",
    )

    assert result.exit_code == 0
    assert "hello" in result.stdout
    assert "External command exited with code 0." in result.stdout

    memory = load_shell_memory(state_dir=state_dir)
    assert memory is not None
    assert any(event.metadata.get("tool_type") == "external" for event in memory.events)


def test_index_add_writes_source_config(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)

    result = runner.invoke(
        app,
        [
            "index",
            "add",
            str(fixture_root),
            "--source",
            "obsidian",
            "--state-dir",
            str(state_dir),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "index_add", True)
    assert payload["data"]["source_id"] == "obsidian"

    config_data = json.loads((state_dir / "config.json").read_text(encoding="utf-8"))
    assert config_data["sources"][0]["type"] == "obsidian"


def test_index_run_builds_index(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    state_dir = tmp_path / ".rfs"

    build_index_with_source(state_dir, fixture_root, "obsidian")

    result = runner.invoke(
        app,
        ["index", "run", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "index_run", True)
    assert payload["data"]["document_count"] == 3
    assert (state_dir / "index.json").exists()


def test_search_uses_indexed_content(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    state_dir = tmp_path / ".rfs"

    build_index_with_source(state_dir, fixture_root, "obsidian")
    rebuild_index(state_dir)

    result = runner.invoke(
        app,
        ["search", "roadmap", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "search", True)
    assert payload["data"]["result_count"] == 1
    assert payload["data"]["results"][0]["title"] == "Project Roadmap"
    assert payload["data"]["results"][0]["relative_path"] == "project-roadmap.md"


def test_show_json_resolves_document_id(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    state_dir = tmp_path / ".rfs"

    build_index_with_source(state_dir, fixture_root, "obsidian")
    rebuild_index(state_dir)

    index_data = json.loads((state_dir / "index.json").read_text(encoding="utf-8"))
    document_id = index_data["documents"][0]["document_id"]

    result = runner.invoke(
        app,
        ["show", document_id, "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "show", True)
    assert payload["data"]["document_id"] == document_id
    assert "metadata" in payload["data"]


def test_obsidian_frontmatter_and_alias_search(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    state_dir = tmp_path / ".rfs"

    build_index_with_source(state_dir, fixture_root, "obsidian")
    rebuild_index(state_dir)

    result = runner.invoke(
        app,
        ["search", "toolkit", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "search", True)
    assert payload["data"]["result_count"] == 1
    result_doc = payload["data"]["results"][0]
    assert result_doc["title"] == "Agent Systems"
    assert result_doc["aliases"] == ["Agent Toolkit", "Tooling Notes"]
    assert result_doc["tags"] == ["agents", "search"]
    assert result_doc["metadata"]["frontmatter"]["priority"] == 3
    assert result_doc["metadata"]["frontmatter"]["context"]["owner"] == "red"


def test_search_supports_tag_path_prefix_and_file_type_filters(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    state_dir = tmp_path / ".rfs"

    build_index_with_source(state_dir, fixture_root, "obsidian")
    rebuild_index(state_dir)

    result = runner.invoke(
        app,
        [
            "search",
            "agent",
            "--state-dir",
            str(state_dir),
            "--tag",
            "agents",
            "--path-prefix",
            "ideas",
            "--file-type",
            "md",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "search", True)
    assert payload["data"]["result_count"] == 1
    assert payload["data"]["results"][0]["relative_path"] == "ideas/agent-systems.md"


def test_show_by_path_returns_indexed_metadata_when_available(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    state_dir = tmp_path / ".rfs"

    build_index_with_source(state_dir, fixture_root, "obsidian")
    rebuild_index(state_dir)

    indexed_path = fixture_root / "ideas" / "agent-systems.md"
    result = runner.invoke(
        app,
        ["show", str(indexed_path), "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "show", True)
    assert payload["data"]["relative_path"] == "ideas/agent-systems.md"
    assert payload["data"]["metadata"]["frontmatter"]["status"] == "active"
    assert payload["data"]["metadata"]["aliases"] == ["Agent Toolkit", "Tooling Notes"]
    assert payload["data"]["metadata"]["frontmatter"]["context"]["team"] == "cli"


def test_show_metadata_only_omits_preview_content(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    state_dir = tmp_path / ".rfs"

    build_index_with_source(state_dir, fixture_root, "obsidian")
    rebuild_index(state_dir)

    indexed_path = fixture_root / "ideas" / "agent-systems.md"
    result = runner.invoke(
        app,
        [
            "show",
            str(indexed_path),
            "--state-dir",
            str(state_dir),
            "--metadata-only",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "show", True)
    assert payload["data"]["content_included"] is False
    assert payload["data"]["preview"] == ""


def test_show_text_mode_renders_frontmatter_details(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    state_dir = tmp_path / ".rfs"

    build_index_with_source(state_dir, fixture_root, "obsidian")
    rebuild_index(state_dir)

    indexed_path = fixture_root / "ideas" / "agent-systems.md"
    result = runner.invoke(
        app,
        ["show", str(indexed_path), "--state-dir", str(state_dir)],
    )

    assert result.exit_code == 0
    assert "source: obsidian:obsidian" in result.stdout
    assert "frontmatter:" in result.stdout
    assert "status: active" in result.stdout
    assert "context.owner: red" in result.stdout
    assert "context.team: cli" in result.stdout


def test_multi_source_search_prefers_obsidian_note_for_exact_title(tmp_path: Path) -> None:
    obsidian_root = Path("tests/fixtures/obsidian").resolve()
    local_root = Path("tests/fixtures/local").resolve()
    state_dir = tmp_path / ".rfs"

    build_index_with_source(state_dir, obsidian_root, "obsidian", source_id="obsidian-main")
    build_index_with_source(state_dir, local_root, "local", source_id="local-docs")
    rebuild_index(state_dir)

    result = runner.invoke(
        app,
        ["search", "agent systems", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "search", True)
    assert payload["data"]["result_count"] >= 2
    assert payload["data"]["results"][0]["source_id"] == "obsidian-main"
    assert payload["data"]["results"][0]["title"] == "Agent Systems"


def test_search_supports_source_id_filter(tmp_path: Path) -> None:
    obsidian_root = Path("tests/fixtures/obsidian").resolve()
    local_root = Path("tests/fixtures/local").resolve()
    state_dir = tmp_path / ".rfs"

    build_index_with_source(state_dir, obsidian_root, "obsidian", source_id="obsidian-main")
    build_index_with_source(state_dir, local_root, "local", source_id="local-docs")
    rebuild_index(state_dir)

    result = runner.invoke(
        app,
        [
            "search",
            "agent",
            "--state-dir",
            str(state_dir),
            "--source-id",
            "local-docs",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "search", True)
    assert payload["data"]["result_count"] == 1
    assert payload["data"]["results"][0]["source_id"] == "local-docs"


def test_agent_find_text_ignores_virtualenv_directories(tmp_path: Path) -> None:
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)
    ignored_root = tmp_path / ".venv"
    ignored_root.mkdir()
    (ignored_root / "ignore.md").write_text("agent should not be found here", encoding="utf-8")

    visible_root = tmp_path / "notes"
    visible_root.mkdir()
    (visible_root / "keep.md").write_text("agent should be found here", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "agent",
            "find-text",
            "agent",
            str(tmp_path),
            "--state-dir",
            str(state_dir),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "agent_find_text", True)
    assert payload["data"]["result_count"] == 1
    assert payload["data"]["results"][0]["title"] == "keep"


def test_dev_project_stats_json_contract(tmp_path: Path) -> None:
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "ignore.py").write_text("print('ignore')\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "dev",
            "project-stats",
            "--path",
            str(tmp_path),
            "--state-dir",
            str(state_dir),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "dev_project_stats", True)
    assert payload["data"]["tool"] == "project-stats"
    assert payload["data"]["subject_path"] == str(tmp_path.resolve())
    assert payload["data"]["total_files"] == 1


def test_dev_find_todo_json_contract(tmp_path: Path) -> None:
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "plan.md").write_text(
        "# Plan\n- TODO: implement search\n- FIXME: normalize schema\n",
        encoding="utf-8",
    )
    (tmp_path / "notes.txt").write_text("XXX revisit ranking\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "dev",
            "find-todo",
            "--path",
            str(tmp_path),
            "--state-dir",
            str(state_dir),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "dev_find_todo", True)
    assert payload["data"]["tool"] == "find-todo"
    assert payload["data"]["match_count"] == 3
    assert payload["data"]["counts"] == {"TODO": 1, "FIXME": 1, "XXX": 1}
    assert payload["data"]["matches"][0]["relative_path"] in {"docs/plan.md", "notes.txt"}


def test_dev_git_summary_json_contract(tmp_path: Path) -> None:
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)
    subprocess.run(["git", "init", "-b", "main"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)

    tracked = tmp_path / "tracked.txt"
    tracked.write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    tracked.write_text("hello\nworld\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "dev",
            "git-summary",
            "--path",
            str(tmp_path),
            "--state-dir",
            str(state_dir),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "dev_git_summary", True)
    assert payload["data"]["tool"] == "git-summary"
    assert payload["data"]["subject_path"] == str(tmp_path.resolve())
    assert any(line.startswith("## main") for line in payload["data"]["lines"])
    assert any("tracked.txt" in line for line in payload["data"]["lines"])


def test_search_missing_index_returns_structured_error(tmp_path: Path) -> None:
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)
    result = runner.invoke(
        app,
        ["search", "agent", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "search", False)
    assert payload["error"]["code"] == "missing_index"


def test_search_requires_llm_configuration(tmp_path: Path) -> None:
    state_dir = tmp_path / ".rfs"
    result = runner.invoke(
        app,
        ["search", "agent", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "search", False)
    assert payload["error"]["code"] == "missing_llm"


def test_show_invalid_index_returns_structured_error(tmp_path: Path) -> None:
    state_dir = tmp_path / ".rfs"
    state_dir.mkdir()
    save_llm_config(state_dir)
    (state_dir / "index.json").write_text('{"documents": "broken"}', encoding="utf-8")

    result = runner.invoke(
        app,
        ["show", "missing-doc", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "show", False)
    assert payload["error"]["code"] == "invalid_index"


def test_dev_git_summary_non_repo_returns_structured_error(tmp_path: Path) -> None:
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)
    result = runner.invoke(
        app,
        [
            "dev",
            "git-summary",
            "--path",
            str(tmp_path),
            "--state-dir",
            str(state_dir),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "dev_git_summary", False)
    assert payload["error"]["code"] == "git_error"


def test_documented_quickstart_flow_is_valid(tmp_path: Path) -> None:
    obsidian_root = Path("tests/fixtures/obsidian").resolve()
    local_root = Path("tests/fixtures/local").resolve()
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)

    for command in [
        ["index", "add", str(obsidian_root), "--source", "obsidian", "--state-dir", str(state_dir)],
        ["index", "add", str(local_root), "--source", "local", "--state-dir", str(state_dir)],
        ["index", "run", "--state-dir", str(state_dir)],
    ]:
        result = runner.invoke(app, command)
        assert result.exit_code == 0

    for command in [
        ["index", "sources", "--state-dir", str(state_dir), "--format", "json"],
        ["search", "agent memory", "--state-dir", str(state_dir), "--format", "json"],
        [
            "dev",
            "find-todo",
            "--path",
            str(local_root),
            "--state-dir",
            str(state_dir),
            "--format",
            "json",
        ],
        ["agent", "list-files", str(local_root), "--state-dir", str(state_dir), "--format", "json"],
        [
            "agent",
            "find-text",
            "TODO",
            str(local_root),
            "--state-dir",
            str(state_dir),
            "--format",
            "json",
        ],
    ]:
        result = runner.invoke(app, command)
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["ok"] is True

    search_result = runner.invoke(
        app,
        ["search", "agent systems", "--state-dir", str(state_dir), "--format", "json"],
    )
    search_payload = json.loads(search_result.stdout)
    document_id = search_payload["data"]["results"][0]["document_id"]

    show_result = runner.invoke(
        app,
        ["show", document_id, "--state-dir", str(state_dir), "--format", "json"],
    )
    assert show_result.exit_code == 0
    show_payload = json.loads(show_result.stdout)
    assert_command_payload(show_payload, "show", True)
