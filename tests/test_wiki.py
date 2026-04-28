import json
from pathlib import Path

from typer.testing import CliRunner

from rfs_cli.main import app

runner = CliRunner()


def assert_command_payload(payload: dict[str, object], command: str, ok: bool) -> None:
    assert payload["schema_version"] == "1"
    assert payload["command"] == command
    assert payload["ok"] is ok
    assert "data" in payload
    assert "error" in payload


def fixture_root(name: str) -> Path:
    return Path("tests/fixtures/wiki_lint").resolve() / name


def test_wiki_lint_healthy_fixture_json() -> None:
    result = runner.invoke(
        app,
        ["wiki", "lint", str(fixture_root("healthy_minimal")), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "wiki_lint", True)
    report = payload["data"]["report"]
    assert report["issue_count"] == 0
    assert report["issues"] == []
    assert report["issues_by_kind"]["missing_page"] == 0


def test_wiki_lint_missing_page_fixture_json() -> None:
    result = runner.invoke(
        app,
        ["wiki", "lint", str(fixture_root("missing_page")), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    report = payload["data"]["report"]
    assert report["issue_count"] == 1
    assert report["issues_by_kind"]["missing_page"] == 1
    assert report["issues"][0]["kind"] == "missing_page"


def test_wiki_lint_orphan_page_fixture_json() -> None:
    result = runner.invoke(
        app,
        ["wiki", "lint", str(fixture_root("orphan_page")), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    report = payload["data"]["report"]
    assert report["issues_by_kind"]["orphan_page"] == 1
    assert any(issue["kind"] == "orphan_page" for issue in report["issues"])


def test_wiki_lint_missing_crosslink_fixture_json() -> None:
    result = runner.invoke(
        app,
        ["wiki", "lint", str(fixture_root("missing_crosslink")), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    report = payload["data"]["report"]
    assert report["issues_by_kind"]["missing_crosslink"] == 1
    assert any(issue["kind"] == "missing_crosslink" for issue in report["issues"])


def test_wiki_lint_invalid_state_fixture_json() -> None:
    result = runner.invoke(
        app,
        ["wiki", "lint", str(fixture_root("invalid_state_missing_log")), "--format", "json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "wiki_lint", False)
    assert payload["error"]["code"] == "invalid_wiki_state"
