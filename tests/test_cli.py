import json
import re
import subprocess
from pathlib import Path
from typing import Optional

from typer.testing import CliRunner

from rfs_cli import __version__
from rfs_cli.config import load_config, load_drive_cache, load_shell_memory, save_config
from rfs_cli.drive import fetch_drive_file_metadata
from rfs_cli.guidance import interpret_user_intent, plan_guidance_response
from rfs_cli.llm import extract_message_content, history_to_messages
from rfs_cli.main import app, render_banner
from rfs_cli.models import DriveConfig, DriveFileRecord, LLMConfig

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


def test_pyproject_version_matches_package_version() -> None:
    pyproject_text = Path("pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', pyproject_text, re.MULTILINE)

    assert match is not None
    assert match.group(1) == __version__


def test_doctor_json_reports_workspace_state(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    build_index_with_source(state_dir, fixture_root, "obsidian", source_id="vault")
    rebuild_index(state_dir)

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
        ["doctor", "--state-dir", str(state_dir), "--verbose", "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "doctor", True)
    assert payload["data"]["version"] == __version__
    assert payload["data"]["verbose"] is True
    assert payload["data"]["config"]["valid"] is True
    assert payload["data"]["config"]["source_count"] == 1
    assert payload["data"]["index"]["valid"] is True
    assert payload["data"]["index"]["document_count"] >= 1
    assert payload["data"]["llm_runtime"]["reachable"] is True
    assert payload["data"]["environment"]["state_dir"] == str(state_dir.resolve())


def test_doctor_reports_invalid_state_files_without_failing(tmp_path: Path) -> None:
    state_dir = tmp_path / ".rfs"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "config.json").write_text("{invalid", encoding="utf-8")
    (state_dir / "index.json").write_text("{invalid", encoding="utf-8")

    result = runner.invoke(
        app,
        ["doctor", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "doctor", True)
    assert payload["data"]["config"]["valid"] is False
    assert payload["data"]["index"]["valid"] is False
    assert "Inspect `.rfs/config.json`" in payload["data"]["suggestions"][0]


def test_root_without_args_shows_banner_and_help_when_non_interactive(monkeypatch) -> None:
    monkeypatch.setattr("rfs_cli.main.is_interactive_session", lambda: False)

    result = runner.invoke(app, [])

    assert result.exit_code == 0
    assert " ____  _____    _    ______   __   _____ ___  ____    ____  _____    _" in result.stdout
    assert WAVE_LINE in result.stdout
    assert "Run `rfs` in an interactive terminal" in result.stdout
    assert "Usage:" in result.stdout


def test_render_banner_uses_ansi_when_forced(monkeypatch) -> None:
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.delenv("NO_COLOR", raising=False)

    banner = render_banner()

    assert "\033[38;2;" in banner
    assert "~" in banner


def test_extract_message_content_strips_reasoning_and_control_tokens() -> None:
    content = (
        "<think>internal reasoning</think>\n\n"
        "실행 명령은 `rfs index add ~/vault --source obsidian` 입니다.\n"
        "<|im_end|>"
    )

    assert extract_message_content(content) == (
        "실행 명령은 `rfs index add ~/vault --source obsidian` 입니다."
    )


def test_history_to_messages_merges_extra_system_context() -> None:
    messages = history_to_messages(
        [
            {"role": "system", "content": "shell context"},
            {"role": "user", "content": "search roadmap"},
        ]
    )

    assert messages[0]["role"] == "system"
    assert "shell context" in messages[0]["content"]
    assert messages[1:] == [{"role": "user", "content": "search roadmap"}]


def test_root_without_args_starts_onboarding_then_shell_when_interactive(
    tmp_path: Path,
    monkeypatch,
) -> None:
    state_dir = tmp_path / ".rfs"
    calls: dict[str, object] = {}

    monkeypatch.setattr("rfs_cli.main.is_interactive_session", lambda: True)

    def fake_onboarding_flow(
        state_dir_arg,
        provider=None,
        base_url=None,
        model=None,
        api_key_env=None,
        show_banner=True,
    ):
        calls["onboarding"] = {
            "state_dir": Path(state_dir_arg),
            "show_banner": show_banner,
        }
        return load_config(state_dir=state_dir_arg)

    def fake_shell_session(state_dir_arg, reset_memory=False, show_banner=True):
        calls["shell"] = {
            "state_dir": Path(state_dir_arg),
            "reset_memory": reset_memory,
            "show_banner": show_banner,
        }

    monkeypatch.setattr("rfs_cli.main.run_onboarding_flow", fake_onboarding_flow)
    monkeypatch.setattr("rfs_cli.main.run_shell_session", fake_shell_session)

    result = runner.invoke(app, ["--state-dir", str(state_dir)])

    assert result.exit_code == 0
    assert calls["onboarding"] == {
        "state_dir": state_dir.resolve(),
        "show_banner": True,
    }
    assert calls["shell"] == {
        "state_dir": state_dir.resolve(),
        "reset_memory": False,
        "show_banner": False,
    }
    assert "Launching rfs shell..." in result.stdout


def test_root_without_args_starts_shell_when_interactive_and_llm_exists(
    tmp_path: Path,
    monkeypatch,
) -> None:
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)
    calls: dict[str, object] = {}

    monkeypatch.setattr("rfs_cli.main.is_interactive_session", lambda: True)

    def fake_shell_session(state_dir_arg, reset_memory=False, show_banner=True):
        calls["shell"] = {
            "state_dir": Path(state_dir_arg),
            "reset_memory": reset_memory,
            "show_banner": show_banner,
        }

    monkeypatch.setattr("rfs_cli.main.run_shell_session", fake_shell_session)

    result = runner.invoke(app, ["--state-dir", str(state_dir)])

    assert result.exit_code == 0
    assert calls["shell"] == {
        "state_dir": state_dir.resolve(),
        "reset_memory": False,
        "show_banner": True,
    }


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
    assert "- rfs" in result.stdout
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


def test_drive_auth_persists_drive_config(tmp_path: Path) -> None:
    state_dir = tmp_path / ".rfs"

    result = runner.invoke(
        app,
        [
            "drive",
            "auth",
            "--state-dir",
            str(state_dir),
            "--client-id-env",
            "TEST_DRIVE_CLIENT_ID",
            "--client-secret-env",
            "TEST_DRIVE_CLIENT_SECRET",
            "--refresh-token-env",
            "TEST_DRIVE_REFRESH_TOKEN",
            "--include-shared-drives",
            "--corpus",
            "allDrives",
            "--metadata-field",
            "id",
            "--metadata-field",
            "name",
            "--cache-mode",
            "metadata-only",
            "--cache-ttl-minutes",
            "30",
            "--cache-max-entries",
            "250",
            "--configure-only",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "drive_auth", True)
    assert payload["data"]["configured"] is True
    assert payload["data"]["client_id_env"] == "TEST_DRIVE_CLIENT_ID"
    assert payload["data"]["include_shared_drives"] is True
    assert payload["data"]["corpus"] == "allDrives"
    assert payload["data"]["cache_ttl_minutes"] == 30
    assert payload["data"]["configure_only"] is True
    assert payload["data"]["authenticated"] is False

    config = load_config(state_dir=state_dir)
    assert config.drive is not None
    assert config.drive.auth.client_id_env == "TEST_DRIVE_CLIENT_ID"
    assert config.drive.corpora == ["allDrives"]
    assert config.drive.cache.max_entries == 250


def test_drive_auth_runs_local_oauth_flow_and_saves_token(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    captured: dict[str, object] = {}

    def fake_run_drive_installed_app_auth(drive_config, state_dir, open_browser=True, port=0):
        captured["drive_config"] = drive_config
        captured["state_dir"] = Path(state_dir)
        captured["open_browser"] = open_browser
        captured["port"] = port
        token_path = captured["state_dir"] / "drive-token.json"
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(
            json.dumps(
                {
                    "token": "access-token",
                    "refresh_token": "refresh-token",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "client_id": "client-id",
                    "client_secret": "client-secret",
                    "scopes": ["https://www.googleapis.com/auth/drive.metadata.readonly"],
                }
            ),
            encoding="utf-8",
        )
        return token_path

    monkeypatch.setattr(
        "rfs_cli.main.run_drive_installed_app_auth",
        fake_run_drive_installed_app_auth,
    )

    result = runner.invoke(
        app,
        [
            "drive",
            "auth",
            "--state-dir",
            str(state_dir),
            "--client-id-env",
            "TEST_DRIVE_CLIENT_ID",
            "--client-secret-env",
            "TEST_DRIVE_CLIENT_SECRET",
            "--refresh-token-env",
            "TEST_DRIVE_REFRESH_TOKEN",
            "--no-launch-browser",
            "--auth-port",
            "9090",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "drive_auth", True)
    assert payload["data"]["authenticated"] is True
    assert payload["data"]["token_file_exists"] is True
    assert payload["data"]["auth_source"] == "state_file"
    assert captured["state_dir"] == state_dir.resolve()
    assert captured["open_browser"] is False
    assert captured["port"] == 9090


def test_drive_auth_returns_structured_error_on_auth_failure(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"

    def fail_drive_auth(*args, **kwargs):
        raise ValueError("Missing Google Drive client secret env var(s): TEST_DRIVE_CLIENT_ID")

    monkeypatch.setattr("rfs_cli.main.run_drive_installed_app_auth", fail_drive_auth)

    result = runner.invoke(
        app,
        [
            "drive",
            "auth",
            "--state-dir",
            str(state_dir),
            "--client-id-env",
            "TEST_DRIVE_CLIENT_ID",
            "--client-secret-env",
            "TEST_DRIVE_CLIENT_SECRET",
            "--refresh-token-env",
            "TEST_DRIVE_REFRESH_TOKEN",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "drive_auth", False)
    assert payload["error"]["code"] == "drive_auth_error"


def test_drive_status_reports_env_presence(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    result = runner.invoke(
        app,
        [
            "drive",
            "auth",
            "--state-dir",
            str(state_dir),
            "--configure-only",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0

    monkeypatch.setenv("GOOGLE_DRIVE_CLIENT_ID", "client")
    monkeypatch.setenv("GOOGLE_DRIVE_CLIENT_SECRET", "secret")
    monkeypatch.delenv("GOOGLE_DRIVE_REFRESH_TOKEN", raising=False)

    status_result = runner.invoke(
        app,
        ["drive", "status", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert status_result.exit_code == 0
    payload = json.loads(status_result.stdout)
    assert_command_payload(payload, "drive_status", True)
    assert payload["data"]["configured"] is True
    assert payload["data"]["client_id_present"] is True
    assert payload["data"]["client_secret_present"] is True
    assert payload["data"]["refresh_token_present"] is False
    assert payload["data"]["corpus"] == "user"
    assert payload["data"]["authenticated"] is False
    assert payload["data"]["metadata_retrieval_ready"] is True
    assert payload["data"]["live_search_available"] is True
    assert payload["data"]["cache_file_exists"] is False
    assert payload["data"]["cache_entry_count"] == 0
    assert "drive search` are implemented" in payload["data"]["note"]


def test_drive_status_reports_state_file_auth(tmp_path: Path) -> None:
    state_dir = tmp_path / ".rfs"
    runner.invoke(
        app,
        [
            "drive",
            "auth",
            "--state-dir",
            str(state_dir),
            "--configure-only",
            "--format",
            "json",
        ],
    )
    token_path = state_dir / "drive-token.json"
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(
        json.dumps(
            {
                "token": "access-token",
                "refresh_token": "refresh-token",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": "client-id",
                "client_secret": "client-secret",
                "scopes": ["https://www.googleapis.com/auth/drive.metadata.readonly"],
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["drive", "status", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["data"]["corpus"] == "user"
    assert payload["data"]["authenticated"] is True
    assert payload["data"]["token_file_exists"] is True
    assert payload["data"]["auth_source"] == "state_file"
    assert payload["data"]["metadata_retrieval_ready"] is True
    assert payload["data"]["live_search_available"] is True
    assert payload["data"]["cache_file_exists"] is False


def test_fetch_drive_file_metadata_normalizes_records(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    captured: dict[str, object] = {}

    class FakeCredentials:
        token = "access-token"

    def fake_ensure_drive_credentials(drive_config, state_dir_arg):
        captured["state_dir"] = Path(state_dir_arg)
        return FakeCredentials(), "state_file", Path(state_dir_arg) / "drive-token.json"

    def fake_request_drive_json(url: str, access_token: str, timeout: float = 30.0):
        captured["url"] = url
        captured["access_token"] = access_token
        captured["timeout"] = timeout
        return {
            "nextPageToken": "next-page",
            "incompleteSearch": False,
            "files": [
                {
                    "id": "file-1",
                    "name": "Proposal Draft",
                    "mimeType": "application/pdf",
                    "modifiedTime": "2026-03-14T09:30:00Z",
                    "parents": ["root"],
                    "driveId": "drive-123",
                    "webViewLink": "https://drive.google.com/file/d/file-1/view",
                    "size": "2048",
                }
            ],
        }

    monkeypatch.setattr("rfs_cli.drive.ensure_drive_credentials", fake_ensure_drive_credentials)
    monkeypatch.setattr("rfs_cli.drive.request_drive_json", fake_request_drive_json)

    result = fetch_drive_file_metadata(
        DriveConfig(include_shared_drives=True, corpora=["allDrives"]),
        state_dir=state_dir,
        query="proposal",
        page_size=7,
    )

    assert result["query"] == "proposal"
    assert result["page_size"] == 7
    assert result["next_page_token"] == "next-page"
    assert result["incomplete_search"] is False
    assert result["auth_source"] == "state_file"
    assert result["token_path"] == str(state_dir / "drive-token.json")
    assert result["cache_hit"] is False
    assert result["cache_path"] == str(state_dir / "drive-cache.json")
    assert captured["access_token"] == "access-token"
    assert "name+contains+%27proposal%27" in str(captured["url"])
    assert "pageSize=7" in str(captured["url"])
    assert "includeItemsFromAllDrives=true" in str(captured["url"])
    records = result["records"]
    assert len(records) == 1
    assert records[0].file_id == "file-1"
    assert records[0].name == "Proposal Draft"
    assert records[0].size_bytes == 2048

    cache_store = load_drive_cache(state_dir=state_dir)
    assert cache_store is not None
    assert len(cache_store.entries) == 1
    assert cache_store.entries[0].query == "proposal"


def test_drive_status_rejects_legacy_multi_corpus_config(tmp_path: Path) -> None:
    state_dir = tmp_path / ".rfs"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "config.json").write_text(
        json.dumps(
            {
                "schema_version": "1",
                "sources": [],
                "llm": {
                    "provider": "ollama",
                    "base_url": "http://127.0.0.1:11434",
                    "model": "qwen2.5:7b-instruct",
                    "enabled": True,
                },
                "drive": {
                    "enabled": True,
                    "include_shared_drives": True,
                    "corpora": ["user", "allDrives"],
                    "metadata_fields": ["id", "name"],
                    "auth": {
                        "flow": "oauth-installed-app",
                        "client_id_env": "GOOGLE_DRIVE_CLIENT_ID",
                        "client_secret_env": "GOOGLE_DRIVE_CLIENT_SECRET",
                        "refresh_token_env": "GOOGLE_DRIVE_REFRESH_TOKEN",
                        "scopes": ["https://www.googleapis.com/auth/drive.metadata.readonly"],
                    },
                    "cache": {
                        "mode": "metadata-only",
                        "ttl_minutes": 60,
                        "max_entries": 1000,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["drive", "status", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "drive_status", False)
    assert payload["error"]["code"] == "invalid_config"
    assert "Only one Google Drive corpus is supported" in payload["error"]["message"]


def test_fetch_drive_file_metadata_uses_cache_when_available(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    call_count = {"requests": 0}

    class FakeCredentials:
        token = "access-token"

    def fake_ensure_drive_credentials(drive_config, state_dir_arg):
        return FakeCredentials(), "state_file", Path(state_dir_arg) / "drive-token.json"

    def fake_request_drive_json(url: str, access_token: str, timeout: float = 30.0):
        call_count["requests"] += 1
        return {
            "files": [
                {
                    "id": "file-1",
                    "name": "Cached Proposal",
                    "mimeType": "application/pdf",
                    "modifiedTime": "2026-03-14T09:30:00Z",
                }
            ]
        }

    monkeypatch.setattr("rfs_cli.drive.ensure_drive_credentials", fake_ensure_drive_credentials)
    monkeypatch.setattr("rfs_cli.drive.request_drive_json", fake_request_drive_json)

    first = fetch_drive_file_metadata(DriveConfig(), state_dir=state_dir, query="proposal")
    second = fetch_drive_file_metadata(DriveConfig(), state_dir=state_dir, query="proposal")

    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert call_count["requests"] == 1
    assert second["records"][0].name == "Cached Proposal"

    cache_store = load_drive_cache(state_dir=state_dir)
    assert cache_store is not None
    assert len(cache_store.entries) == 1


def test_fetch_drive_file_metadata_requires_auth(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"

    def fail_auth(*args, **kwargs):
        raise ValueError("Google Drive is not authenticated. Run `rfs drive auth` first.")

    monkeypatch.setattr("rfs_cli.drive.ensure_drive_credentials", fail_auth)

    try:
        fetch_drive_file_metadata(DriveConfig(), state_dir=state_dir, query="proposal")
    except ValueError as exc:
        assert "Google Drive is not authenticated" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("Expected Drive auth failure.")


def test_drive_search_requires_drive_config(tmp_path: Path) -> None:
    state_dir = tmp_path / ".rfs"

    result = runner.invoke(
        app,
        ["drive", "search", "proposal", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "drive_search", False)
    assert payload["error"]["code"] == "missing_drive_config"


def test_drive_search_returns_structured_auth_error(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    runner.invoke(
        app,
        [
            "drive",
            "auth",
            "--state-dir",
            str(state_dir),
            "--configure-only",
            "--format",
            "json",
        ],
    )

    def fail_auth(*args, **kwargs):
        raise ValueError("Google Drive is not authenticated. Run `rfs drive auth` first.")

    monkeypatch.setattr("rfs_cli.main.fetch_drive_file_metadata", fail_auth)

    result = runner.invoke(
        app,
        ["drive", "search", "proposal", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "drive_search", False)
    assert payload["error"]["code"] == "missing_drive_auth"


def test_drive_search_returns_live_results(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    runner.invoke(
        app,
        [
            "drive",
            "auth",
            "--state-dir",
            str(state_dir),
            "--configure-only",
            "--format",
            "json",
        ],
    )

    def fake_fetch_drive_file_metadata(
        drive_config,
        state_dir,
        query,
        page_size=20,
        page_token=None,
    ):
        return {
            "query": query,
            "page_size": page_size,
            "next_page_token": "next-page",
            "incomplete_search": False,
            "auth_source": "state_file",
            "token_path": str(Path(state_dir) / "drive-token.json"),
            "cache_path": str(Path(state_dir) / "drive-cache.json"),
            "cache_key": "drive:test",
            "cache_hit": False,
            "fetched_at": "2026-03-14T10:00:00+00:00",
            "expires_at": "2026-03-14T11:00:00+00:00",
            "records": [
                DriveFileRecord(
                    file_id="file-1",
                    name="Proposal Draft",
                    mime_type="application/pdf",
                    modified_time="2026-03-14T09:30:00Z",
                    web_view_link="https://drive.google.com/file/d/file-1/view",
                    parents=["root"],
                    size_bytes=2048,
                )
            ],
        }

    monkeypatch.setattr("rfs_cli.main.fetch_drive_file_metadata", fake_fetch_drive_file_metadata)

    result = runner.invoke(
        app,
        [
            "drive",
            "search",
            "proposal",
            "--page-size",
            "5",
            "--state-dir",
            str(state_dir),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "drive_search", True)
    assert payload["data"]["query"] == "proposal"
    assert payload["data"]["page_size"] == 5
    assert payload["data"]["result_count"] == 1
    assert payload["data"]["cache_hit"] is False
    assert payload["data"]["next_page_token"] == "next-page"
    assert payload["data"]["planned_result_contract"]["live_search_available"] is True


def test_drive_search_command_uses_cache_end_to_end(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    call_count = {"requests": 0}

    runner.invoke(
        app,
        [
            "drive",
            "auth",
            "--state-dir",
            str(state_dir),
            "--configure-only",
            "--format",
            "json",
        ],
    )

    class FakeCredentials:
        token = "access-token"

    def fake_ensure_drive_credentials(drive_config, state_dir_arg):
        return FakeCredentials(), "state_file", Path(state_dir_arg) / "drive-token.json"

    def fake_request_drive_json(url: str, access_token: str, timeout: float = 30.0):
        call_count["requests"] += 1
        return {
            "files": [
                {
                    "id": "file-1",
                    "name": "Cached Proposal",
                    "mimeType": "application/pdf",
                    "modifiedTime": "2026-03-15T08:00:00Z",
                }
            ]
        }

    monkeypatch.setattr("rfs_cli.drive.ensure_drive_credentials", fake_ensure_drive_credentials)
    monkeypatch.setattr("rfs_cli.drive.request_drive_json", fake_request_drive_json)

    first = runner.invoke(
        app,
        ["drive", "search", "proposal", "--state-dir", str(state_dir), "--format", "json"],
    )
    second = runner.invoke(
        app,
        ["drive", "search", "proposal", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert first.exit_code == 0
    assert second.exit_code == 0
    first_payload = json.loads(first.stdout)
    second_payload = json.loads(second.stdout)
    assert first_payload["data"]["cache_hit"] is False
    assert second_payload["data"]["cache_hit"] is True
    assert second_payload["data"]["results"][0]["name"] == "Cached Proposal"
    assert call_count["requests"] == 1


def test_drive_search_command_refetches_after_cache_expiry(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    call_count = {"requests": 0}

    runner.invoke(
        app,
        [
            "drive",
            "auth",
            "--state-dir",
            str(state_dir),
            "--configure-only",
            "--format",
            "json",
        ],
    )

    class FakeCredentials:
        token = "access-token"

    def fake_ensure_drive_credentials(drive_config, state_dir_arg):
        return FakeCredentials(), "state_file", Path(state_dir_arg) / "drive-token.json"

    def fake_request_drive_json(url: str, access_token: str, timeout: float = 30.0):
        call_count["requests"] += 1
        return {
            "files": [
                {
                    "id": f"file-{call_count['requests']}",
                    "name": f"Proposal {call_count['requests']}",
                    "mimeType": "application/pdf",
                    "modifiedTime": "2026-03-15T08:00:00Z",
                }
            ]
        }

    monkeypatch.setattr("rfs_cli.drive.ensure_drive_credentials", fake_ensure_drive_credentials)
    monkeypatch.setattr("rfs_cli.drive.request_drive_json", fake_request_drive_json)

    first = runner.invoke(
        app,
        ["drive", "search", "proposal", "--state-dir", str(state_dir), "--format", "json"],
    )
    assert first.exit_code == 0

    cache_path = state_dir / "drive-cache.json"
    cache_payload = json.loads(cache_path.read_text(encoding="utf-8"))
    cache_payload["entries"][0]["expires_at"] = "2000-01-01T00:00:00+00:00"
    cache_path.write_text(json.dumps(cache_payload), encoding="utf-8")

    second = runner.invoke(
        app,
        ["drive", "search", "proposal", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert second.exit_code == 0
    second_payload = json.loads(second.stdout)
    assert second_payload["data"]["cache_hit"] is False
    assert second_payload["data"]["results"][0]["name"] == "Proposal 2"
    assert call_count["requests"] == 2


def test_drive_search_command_invalidates_cache_for_different_page_size(
    tmp_path: Path,
    monkeypatch,
) -> None:
    state_dir = tmp_path / ".rfs"
    call_count = {"requests": 0}

    runner.invoke(
        app,
        [
            "drive",
            "auth",
            "--state-dir",
            str(state_dir),
            "--configure-only",
            "--format",
            "json",
        ],
    )

    class FakeCredentials:
        token = "access-token"

    def fake_ensure_drive_credentials(drive_config, state_dir_arg):
        return FakeCredentials(), "state_file", Path(state_dir_arg) / "drive-token.json"

    def fake_request_drive_json(url: str, access_token: str, timeout: float = 30.0):
        call_count["requests"] += 1
        return {
            "files": [
                {
                    "id": f"file-{call_count['requests']}",
                    "name": f"Proposal {call_count['requests']}",
                    "mimeType": "application/pdf",
                    "modifiedTime": "2026-03-15T08:00:00Z",
                }
            ]
        }

    monkeypatch.setattr("rfs_cli.drive.ensure_drive_credentials", fake_ensure_drive_credentials)
    monkeypatch.setattr("rfs_cli.drive.request_drive_json", fake_request_drive_json)

    first = runner.invoke(
        app,
        [
            "drive",
            "search",
            "proposal",
            "--page-size",
            "5",
            "--state-dir",
            str(state_dir),
            "--format",
            "json",
        ],
    )
    second = runner.invoke(
        app,
        [
            "drive",
            "search",
            "proposal",
            "--page-size",
            "10",
            "--state-dir",
            str(state_dir),
            "--format",
            "json",
        ],
    )

    assert first.exit_code == 0
    assert second.exit_code == 0
    first_payload = json.loads(first.stdout)
    second_payload = json.loads(second.stdout)
    assert first_payload["data"]["cache_hit"] is False
    assert second_payload["data"]["cache_hit"] is False
    assert call_count["requests"] == 2


def test_ask_json_uses_configured_llm(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)
    captured: dict[str, object] = {}

    def fake_ask_llm(config, question, history=None):
        captured["history"] = history or []
        return f"Use `rfs search \"{question}\"`."

    monkeypatch.setattr("rfs_cli.main.ask_llm", fake_ask_llm)

    result = runner.invoke(
        app,
        ["ask", "agent memory", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "ask", True)
    assert payload["data"]["provider"] == "ollama"
    assert "rfs search" in payload["data"]["answer"]
    assert payload["data"]["follow_up_required"] is False
    assert payload["data"]["follow_up_question"] is None
    assert captured["history"][0]["role"] == "system"
    assert "Configured sources: none." in captured["history"][0]["content"]
    assert "- index_status: missing" in captured["history"][0]["content"]


def test_ask_includes_source_and_index_context(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    build_index_with_source(state_dir, fixture_root, "obsidian", source_id="vault")
    rebuild_index(state_dir)
    captured: dict[str, object] = {}

    def fake_ask_llm(config, question, history=None):
        captured["history"] = history or []
        return "Use the existing index."

    monkeypatch.setattr("rfs_cli.main.ask_llm", fake_ask_llm)

    result = runner.invoke(
        app,
        [
            "ask",
            "이 워크스페이스의 note 구조를 설명해줘",
            "--state-dir",
            str(state_dir),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "ask", True)
    context = captured["history"][0]["content"]
    assert "Configured sources: 1" in context
    assert "- vault [obsidian] enabled" in context
    assert "- index_status: available" in context
    assert "- indexed_document_count:" in context


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


def test_ask_returns_follow_up_when_no_sources_are_configured(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("LLM should not be called for deterministic follow-up questions.")

    monkeypatch.setattr("rfs_cli.main.ask_llm", fail_if_called)

    result = runner.invoke(
        app,
        ["ask", "검색을 시작하려면 어떻게 해?", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "ask", True)
    assert payload["data"]["follow_up_required"] is True
    assert "어떤 경로를 먼저 연결할까요?" in payload["data"]["follow_up_question"]
    assert payload["data"]["answer"] == payload["data"]["follow_up_question"]


def test_ask_returns_follow_up_when_show_target_is_missing(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    build_index_with_source(state_dir, fixture_root, "obsidian", source_id="vault")
    rebuild_index(state_dir)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("LLM should not be called for deterministic follow-up questions.")

    monkeypatch.setattr("rfs_cli.main.ask_llm", fail_if_called)

    result = runner.invoke(
        app,
        ["ask", "문서 보여줘", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "ask", True)
    assert payload["data"]["follow_up_required"] is True
    assert "어떤 문서를 열어볼까요?" in payload["data"]["follow_up_question"]


def test_interpret_user_intent_classifies_search_goal() -> None:
    intent = interpret_user_intent("roadmap note를 검색하려면?")

    assert intent.goal == "search"
    assert intent.confidence > 0.5
    assert "roadmap" in intent.entities["meaningful_terms"]


def test_interpret_user_intent_classifies_add_source_goal() -> None:
    intent = interpret_user_intent('Obsidian 볼트를 "~/vault"로 연결해줘')

    assert intent.goal == "add_source"
    assert intent.entities["source_type"] == "obsidian"
    assert intent.entities["path_hint"] == "~/vault"


def test_plan_guidance_response_recommends_index_run_when_sources_exist_without_index(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / ".rfs"
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    build_index_with_source(state_dir, fixture_root, "obsidian", source_id="vault")

    app_config = load_config(state_dir=state_dir)
    response = plan_guidance_response("검색하려면 어떻게 해?", app_config, state_dir)

    assert response is not None
    assert response.follow_up_question is None
    assert response.recommended_command == "rfs index run"


def test_plan_guidance_response_recommends_index_add_when_source_type_and_path_exist(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)

    app_config = load_config(state_dir=state_dir)
    response = plan_guidance_response(
        'Obsidian 볼트를 "~/vault"로 연결해줘',
        app_config,
        state_dir,
    )

    assert response is not None
    assert response.follow_up_question is None
    assert response.recommended_command == 'rfs index add "~/vault" --source obsidian'


def test_ask_returns_deterministic_index_run_suggestion(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    build_index_with_source(state_dir, fixture_root, "obsidian", source_id="vault")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("LLM should not be called for deterministic command suggestion.")

    monkeypatch.setattr("rfs_cli.main.ask_llm", fail_if_called)

    result = runner.invoke(
        app,
        ["ask", "검색하려면 어떻게 해?", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "ask", True)
    assert payload["data"]["follow_up_required"] is False
    assert "rfs index run" in payload["data"]["answer"]


def test_ask_returns_grounded_search_suggestion_when_index_exists(
    tmp_path: Path,
    monkeypatch,
) -> None:
    state_dir = tmp_path / ".rfs"
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    build_index_with_source(state_dir, fixture_root, "obsidian", source_id="vault")
    rebuild_index(state_dir)

    def fail_if_called(*args, **kwargs):
        raise AssertionError(
            "LLM should not be called for grounded deterministic search suggestion."
        )

    monkeypatch.setattr("rfs_cli.main.ask_llm", fail_if_called)

    result = runner.invoke(
        app,
        ["ask", "roadmap note를 찾고 싶어", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "ask", True)
    assert payload["data"]["follow_up_required"] is False
    assert 'rfs search "roadmap note"' in payload["data"]["answer"]
    assert "--source-id vault" in payload["data"]["answer"]


def test_ask_recommends_doctor_when_index_state_is_invalid(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "index.json").write_text("{invalid", encoding="utf-8")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("LLM should not be called when doctor-visible state is invalid.")

    monkeypatch.setattr("rfs_cli.main.ask_llm", fail_if_called)

    result = runner.invoke(
        app,
        ["ask", "검색하려면 어떻게 해?", "--state-dir", str(state_dir), "--format", "json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "ask", True)
    assert "rfs doctor --verbose" in payload["data"]["answer"]


def test_shell_returns_deterministic_doctor_suggestion(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("LLM should not be called for deterministic shell suggestion.")

    monkeypatch.setattr("rfs_cli.main.ask_llm", fail_if_called)

    result = runner.invoke(
        app,
        ["shell", "--state-dir", str(state_dir)],
        input="상태를 점검하려면?\n/exit\n",
    )

    assert result.exit_code == 0
    assert "doctor --verbose" in result.stdout


def test_shell_returns_grounded_show_search_path_when_index_exists(
    tmp_path: Path,
    monkeypatch,
) -> None:
    state_dir = tmp_path / ".rfs"
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    build_index_with_source(state_dir, fixture_root, "obsidian", source_id="vault")
    rebuild_index(state_dir)

    def fail_if_called(*args, **kwargs):
        raise AssertionError(
            "LLM should not be called for grounded deterministic inspect suggestion."
        )

    monkeypatch.setattr("rfs_cli.main.ask_llm", fail_if_called)

    result = runner.invoke(
        app,
        ["shell", "--state-dir", str(state_dir)],
        input="roadmap note 보여줘\n/exit\n",
    )

    assert result.exit_code == 0
    assert 'search "roadmap note"' in result.stdout
    assert "--source-id vault" in result.stdout


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
    assert captured["history"][0]["role"] == "system"
    assert "Workspace guidance context:" in captured["history"][0]["content"]
    assert "Configured sources: none." in captured["history"][0]["content"]
    assert captured["history"][1]["role"] == "system"
    assert "already active `rfs shell` session" in captured["history"][1]["content"]

    memory = load_shell_memory(state_dir=state_dir)
    assert memory is not None
    assert any(event.kind == "assistant" for event in memory.events)


def test_shell_includes_source_and_index_context_for_llm(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    build_index_with_source(state_dir, fixture_root, "obsidian", source_id="vault")
    rebuild_index(state_dir)
    captured: dict[str, object] = {}

    def fake_ask_llm(config, question, history=None):
        captured["history"] = history or []
        return "Use `search roadmap --source-id vault`."

    monkeypatch.setattr("rfs_cli.main.ask_llm", fake_ask_llm)

    result = runner.invoke(
        app,
        ["shell", "--state-dir", str(state_dir)],
        input="이 워크스페이스에서 roadmap note 흐름을 설명해줘\n/exit\n",
    )

    assert result.exit_code == 0
    assert "Use `search roadmap --source-id vault`." in result.stdout
    assert "Configured sources: 1" in captured["history"][0]["content"]
    assert "- vault [obsidian] enabled" in captured["history"][0]["content"]
    assert "- index_status: available" in captured["history"][0]["content"]


def test_shell_returns_follow_up_without_calling_llm(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("LLM should not be called for deterministic shell follow-up.")

    monkeypatch.setattr("rfs_cli.main.ask_llm", fail_if_called)

    result = runner.invoke(
        app,
        ["shell", "--state-dir", str(state_dir)],
        input="검색을 시작하려면 어떻게 해?\n/exit\n",
    )

    assert result.exit_code == 0
    assert "어떤 경로를 먼저 연결할까요?" in result.stdout

    memory = load_shell_memory(state_dir=state_dir)
    assert memory is not None
    assert any(
        event.kind == "assistant"
        and "어떤 경로를 먼저 연결할까요?" in event.content
        for event in memory.events
    )


def test_shell_survives_llm_timeout(tmp_path: Path, monkeypatch) -> None:
    state_dir = tmp_path / ".rfs"
    save_llm_config(state_dir)

    def fake_ask_llm(config, question, history=None):
        raise ValueError(
            "Request to http://127.0.0.1:1234/v1/chat/completions timed out after 60.0s."
        )

    monkeypatch.setattr("rfs_cli.main.ask_llm", fake_ask_llm)

    result = runner.invoke(
        app,
        ["shell", "--state-dir", str(state_dir)],
        input="현재 shell로 들어온거지?\n/exit\n",
    )

    assert result.exit_code == 0
    assert "LLM error:" in result.stdout
    assert "Leaving rfs shell." in result.stdout


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


def test_research_export_writes_bundle_manifest_and_documents(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    state_dir = tmp_path / ".rfs"
    output_dir = tmp_path / "exports" / "bundle-a"

    build_index_with_source(state_dir, fixture_root, "obsidian")
    rebuild_index(state_dir)

    result = runner.invoke(
        app,
        [
            "research",
            "export",
            "agent",
            "--state-dir",
            str(state_dir),
            "--output",
            str(output_dir),
            "--limit",
            "2",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "research_export", True)
    assert payload["data"]["query"] == "agent"
    assert payload["data"]["item_count"] >= 1
    manifest_path = Path(payload["data"]["manifest_path"])
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["export_kind"] == "research_bundle"
    assert manifest["query"] == "agent"
    assert manifest["item_count"] >= 1
    first_doc = manifest["documents"][0]
    assert Path(first_doc["export_path"]).exists()
    exported_content = Path(first_doc["export_path"]).read_text(encoding="utf-8")
    assert exported_content


def test_research_export_requires_index(tmp_path: Path) -> None:
    state_dir = tmp_path / ".rfs"

    result = runner.invoke(
        app,
        [
            "research",
            "export",
            "agent",
            "--state-dir",
            str(state_dir),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "research_export", False)
    assert payload["error"]["code"] == "missing_index"


def test_research_export_generates_query_based_default_output_dir(
    tmp_path: Path,
    monkeypatch,
) -> None:
    fixture_root = Path("tests/fixtures/obsidian").resolve()
    state_dir = tmp_path / ".rfs"
    generated_output_dir = tmp_path / "exports" / "research" / "agent-systems-20260315-120000Z"

    build_index_with_source(state_dir, fixture_root, "obsidian")
    rebuild_index(state_dir)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "rfs_cli.main.default_research_output_dir",
        lambda query: Path("exports/research/agent-systems-20260315-120000Z"),
    )

    result = runner.invoke(
        app,
        [
            "research",
            "export",
            "agent systems",
            "--state-dir",
            str(state_dir),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert_command_payload(payload, "research_export", True)
    assert payload["data"]["output_dir"] == str(generated_output_dir.resolve())
    assert Path(payload["data"]["manifest_path"]).exists()


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
