from __future__ import annotations

from pathlib import Path

from rfs_cli.models import ToolProviderRuntimeConfig
from rfs_cli.providers import (
    build_qa_claw_command,
    candidate_python_executables,
    resolve_provider_python_executable,
)


def test_candidate_python_executables_start_with_current_interpreter() -> None:
    candidates = candidate_python_executables()

    assert candidates
    assert Path(candidates[0]).exists()


def test_resolve_provider_python_executable_prefers_compatible_candidate(monkeypatch) -> None:
    monkeypatch.setattr(
        "rfs_cli.providers.candidate_python_executables",
        lambda: ["/tmp/current-python", "/tmp/python3.14"],
    )

    class Completed:
        def __init__(self, returncode: int, stdout: str) -> None:
            self.returncode = returncode
            self.stdout = stdout

    def fake_run(command: list[str], capture_output: bool, text: bool, check: bool) -> Completed:
        executable = command[0]
        if executable == "/tmp/current-python":
            return Completed(0, "3.9\n")
        if executable == "/tmp/python3.14":
            return Completed(0, "3.14\n")
        raise AssertionError(f"Unexpected executable: {executable}")

    monkeypatch.setattr("rfs_cli.providers.subprocess.run", fake_run)
    resolve_provider_python_executable.cache_clear()
    try:
        assert resolve_provider_python_executable() == "/tmp/python3.14"
    finally:
        resolve_provider_python_executable.cache_clear()


def test_build_qa_claw_command_uses_resolved_python_interpreter(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        "rfs_cli.providers.resolve_provider_python_executable",
        lambda: "/tmp/python3.14",
    )

    provider_config = ToolProviderRuntimeConfig(
        enabled=True,
        capability_allowlist=["run_backend_regression"],
        target_kind="repo",
        target={"repo_root": str(tmp_path)},
        timeout_seconds=30,
        max_output_bytes=32768,
    )
    capability = {
        "command": [
            "python3",
            "-m",
            "unittest",
            "discover",
            "-s",
            "backend/tests",
            "-p",
            "test_*.py",
        ],
        "probe_path": "backend/tests",
        "failure_code": "TEST_FAILURE",
        "success_summary": "ok",
        "failure_summary": "fail",
    }

    from rfs_cli.providers import ScriptCapability

    command = build_qa_claw_command(
        "run_backend_regression",
        ScriptCapability(**capability),
        tmp_path,
        provider_config,
    )

    assert command[0] == "/tmp/python3.14"
    assert command[1:] == ["-m", "unittest", "discover", "-s", "backend/tests", "-p", "test_*.py"]
