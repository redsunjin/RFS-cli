import json
from pathlib import Path

from typer.testing import CliRunner

from rfs_cli.main import app

runner = CliRunner()


def test_version_json() -> None:
    result = runner.invoke(app, ["version", "--format", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["data"]["version"] == "0.1.0"


def test_index_add_writes_source_config(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    state_dir = tmp_path / ".rfs"

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
    assert payload["ok"] is True
    assert payload["data"]["source_id"] == "obsidian"

    config_data = json.loads((state_dir / "config.json").read_text(encoding="utf-8"))
    assert config_data["sources"][0]["type"] == "obsidian"


def test_index_run_builds_index(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    state_dir = tmp_path / ".rfs"

    runner.invoke(
        app,
        ["index", "add", str(fixture_root), "--source", "obsidian", "--state-dir", str(state_dir)],
    )

    result = runner.invoke(
        app,
        ["index", "run", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["data"]["document_count"] == 2
    assert (state_dir / "index.json").exists()


def test_search_uses_indexed_content(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    state_dir = tmp_path / ".rfs"

    runner.invoke(
        app,
        ["index", "add", str(fixture_root), "--source", "obsidian", "--state-dir", str(state_dir)],
    )
    runner.invoke(app, ["index", "run", "--state-dir", str(state_dir)])

    result = runner.invoke(
        app,
        ["search", "roadmap", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["data"]["result_count"] == 1
    assert payload["data"]["results"][0]["title"] == "Project Roadmap"


def test_show_json_resolves_document_id(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    state_dir = tmp_path / ".rfs"

    runner.invoke(
        app,
        ["index", "add", str(fixture_root), "--source", "obsidian", "--state-dir", str(state_dir)],
    )
    runner.invoke(app, ["index", "run", "--state-dir", str(state_dir)])

    index_data = json.loads((state_dir / "index.json").read_text(encoding="utf-8"))
    document_id = index_data["documents"][0]["document_id"]

    result = runner.invoke(
        app,
        ["show", document_id, "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["data"]["document_id"] == document_id


def test_agent_find_text_ignores_virtualenv_directories(tmp_path: Path) -> None:
    ignored_root = tmp_path / ".venv"
    ignored_root.mkdir()
    (ignored_root / "ignore.md").write_text("agent should not be found here", encoding="utf-8")

    visible_root = tmp_path / "notes"
    visible_root.mkdir()
    (visible_root / "keep.md").write_text("agent should be found here", encoding="utf-8")

    result = runner.invoke(
        app,
        ["agent", "find-text", "agent", str(tmp_path), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["data"]["result_count"] == 1
    assert payload["data"]["results"][0]["title"] == "keep"
