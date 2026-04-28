from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from rfs_cli.models import ToolProviderRuntimeConfig


class ProviderExecutionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ScriptCapability:
    command: list[str]
    probe_path: str
    failure_code: str
    success_summary: str
    failure_summary: str


MIN_PROVIDER_PYTHON = (3, 10)


QA_CLAW_SCRIPT_CAPABILITIES: dict[str, ScriptCapability] = {
    "verify_worktrees": ScriptCapability(
        command=["bash", "scripts/verify-worktrees.sh"],
        probe_path="scripts/verify-worktrees.sh",
        failure_code="VERIFY_FAILED",
        success_summary="qa_claw worktree verification passed.",
        failure_summary="qa_claw worktree verification failed.",
    ),
    "check_authz_consistency": ScriptCapability(
        command=["python3", "security/check-authz-matrix-consistency.py", "."],
        probe_path="security/check-authz-matrix-consistency.py",
        failure_code="AUTHZ_MISMATCH",
        success_summary="qa_claw authz consistency check passed.",
        failure_summary="qa_claw authz consistency check failed.",
    ),
    "check_observability_evidence": ScriptCapability(
        command=["bash", "observability/check-telemetry-evidence.sh", "."],
        probe_path="observability/check-telemetry-evidence.sh",
        failure_code="OBSERVABILITY_EVIDENCE_MISSING",
        success_summary="qa_claw observability evidence check passed.",
        failure_summary="qa_claw observability evidence check failed.",
    ),
    "run_backend_regression": ScriptCapability(
        command=["python3", "-m", "unittest", "discover", "-s", "backend/tests", "-p", "test_*.py"],
        probe_path="backend/tests",
        failure_code="TEST_FAILURE",
        success_summary="qa_claw backend regression passed.",
        failure_summary="qa_claw backend regression failed.",
    ),
    "scan_secrets": ScriptCapability(
        command=["bash", "security/scan-secrets.sh", "."],
        probe_path="security/scan-secrets.sh",
        failure_code="SECRET_SCAN_FAILED",
        success_summary="qa_claw secret scan passed.",
        failure_summary="qa_claw secret scan failed.",
    ),
}


def supported_provider_ids() -> list[str]:
    return ["qa_claw"]


def supported_qa_claw_capability_ids() -> list[str]:
    return list(QA_CLAW_SCRIPT_CAPABILITIES.keys())


def ensure_supported_provider(provider_id: str) -> None:
    if provider_id != "qa_claw":
        raise ProviderExecutionError(
            "unsupported_provider",
            f'Provider "{provider_id}" is not supported by the first runtime prototype.',
        )


def ensure_allowed_capability(
    capability_id: str,
    provider_config: ToolProviderRuntimeConfig,
) -> ScriptCapability:
    capability = QA_CLAW_SCRIPT_CAPABILITIES.get(capability_id)
    if capability is None:
        raise ProviderExecutionError(
            "unsupported_capability",
            f'Capability "{capability_id}" is not supported by the qa_claw prototype.',
        )
    if capability_id not in provider_config.capability_allowlist:
        raise ProviderExecutionError(
            "capability_not_allowed",
            f'Capability "{capability_id}" is not enabled in capability_allowlist.',
        )
    return capability


def resolve_repo_root(provider_config: ToolProviderRuntimeConfig) -> Path:
    if provider_config.target_kind != "repo":
        raise ProviderExecutionError(
            "invalid_provider_config",
            'qa_claw requires target_kind="repo".',
        )

    repo_root_value = provider_config.target.get("repo_root")
    if not isinstance(repo_root_value, str) or not repo_root_value.strip():
        raise ProviderExecutionError(
            "invalid_provider_config",
            'qa_claw requires target.repo_root.',
        )

    repo_root = Path(repo_root_value).expanduser().resolve()
    if not repo_root.exists() or not repo_root.is_dir():
        raise ProviderExecutionError(
            "provider_unavailable",
            f"qa_claw repo_root does not exist: {repo_root}",
        )
    return repo_root


def resolve_repo_root_if_present(provider_config: ToolProviderRuntimeConfig) -> Optional[Path]:
    if provider_config.target_kind != "repo":
        return None

    repo_root_value = provider_config.target.get("repo_root")
    if not isinstance(repo_root_value, str) or not repo_root_value.strip():
        return None

    return Path(repo_root_value).expanduser().resolve()


def validate_capability_files(repo_root: Path, capability: ScriptCapability) -> None:
    script_path = repo_root / capability.probe_path
    try:
        script_path.resolve().relative_to(repo_root)
    except ValueError as exc:
        raise ProviderExecutionError(
            "invalid_provider_config",
            "Capability script escapes the configured repo root.",
        ) from exc

    if not script_path.exists() or (not script_path.is_file() and not script_path.is_dir()):
        raise ProviderExecutionError(
            "provider_unavailable",
            f"Required provider script does not exist: {script_path}",
        )


def capability_script_path(repo_root: Path, capability: ScriptCapability) -> Path:
    return (repo_root / capability.probe_path).resolve()


def parse_major_minor(version_text: str) -> Optional[tuple[int, int]]:
    parts = version_text.strip().split(".")
    if len(parts) < 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def candidate_python_executables() -> list[str]:
    candidates: list[str] = [sys.executable]
    for name in ("python3.14", "python3.13", "python3.12", "python3.11", "python3.10", "python3"):
        resolved = shutil.which(name)
        if resolved is not None:
            candidates.append(resolved)

    unique_candidates: list[str] = []
    for candidate in candidates:
        if candidate not in unique_candidates:
            unique_candidates.append(candidate)
    return unique_candidates


@lru_cache(maxsize=1)
def resolve_provider_python_executable() -> str:
    for candidate in candidate_python_executables():
        try:
            version_probe = (
                "import sys; "
                "print(f'{sys.version_info[0]}.{sys.version_info[1]}')"
            )
            completed = subprocess.run(
                [candidate, "-c", version_probe],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            continue

        if completed.returncode != 0:
            continue

        version = parse_major_minor(completed.stdout)
        if version is not None and version >= MIN_PROVIDER_PYTHON:
            return candidate

    return sys.executable


def qa_claw_status(provider_config: Optional[ToolProviderRuntimeConfig]) -> dict[str, Any]:
    supported_capabilities = supported_qa_claw_capability_ids()
    if provider_config is None:
        return {
            "provider_id": "qa_claw",
            "configured": False,
            "enabled": False,
            "provider_kind": "script",
            "target_kind": None,
            "repo_root": None,
            "repo_root_exists": False,
            "worktree_root": None,
            "worktree_root_exists": False,
            "timeout_seconds": None,
            "max_output_bytes": None,
            "supported_capabilities": supported_capabilities,
            "capability_allowlist": [],
            "capabilities": [],
            "issues": ["Provider is not configured."],
        }

    repo_root = resolve_repo_root_if_present(provider_config)
    repo_root_exists = bool(repo_root and repo_root.exists() and repo_root.is_dir())
    worktree_root_value = provider_config.target.get("worktree_root")
    worktree_root = None
    if isinstance(worktree_root_value, str) and worktree_root_value.strip():
        worktree_root = Path(worktree_root_value).expanduser().resolve()
    worktree_root_exists = bool(worktree_root and worktree_root.exists() and worktree_root.is_dir())
    issues: list[str] = []
    if provider_config.target_kind != "repo":
        issues.append('qa_claw requires target_kind="repo".')
    if repo_root is None:
        issues.append("qa_claw requires target.repo_root.")
    elif not repo_root_exists:
        issues.append(f"Configured repo_root does not exist: {repo_root}")
    if worktree_root is not None and not worktree_root_exists:
        issues.append(f"Configured worktree_root does not exist: {worktree_root}")

    unsupported_capabilities = [
        capability_id
        for capability_id in provider_config.capability_allowlist
        if capability_id not in QA_CLAW_SCRIPT_CAPABILITIES
    ]
    for capability_id in unsupported_capabilities:
        issues.append(f"Unsupported capability in allowlist: {capability_id}")

    capabilities: list[dict[str, Any]] = []
    for capability_id in provider_config.capability_allowlist:
        capability = QA_CLAW_SCRIPT_CAPABILITIES.get(capability_id)
        script_path: Optional[Path] = None
        script_exists = False
        if capability is not None and repo_root is not None:
            script_path = capability_script_path(repo_root, capability)
            script_exists = script_path.exists() and (script_path.is_file() or script_path.is_dir())
            if not script_exists:
                issues.append(f"Missing capability script for {capability_id}: {script_path}")
        capabilities.append(
            {
                "capability_id": capability_id,
                "supported": capability is not None,
                "script_path": str(script_path) if script_path is not None else None,
                "script_exists": script_exists,
            }
        )

    return {
        "provider_id": "qa_claw",
        "configured": True,
        "enabled": provider_config.enabled,
        "provider_kind": "script",
        "target_kind": provider_config.target_kind,
        "repo_root": str(repo_root) if repo_root is not None else None,
        "repo_root_exists": repo_root_exists,
        "worktree_root": str(worktree_root) if worktree_root is not None else None,
        "worktree_root_exists": worktree_root_exists,
        "timeout_seconds": provider_config.timeout_seconds,
        "max_output_bytes": provider_config.max_output_bytes,
        "supported_capabilities": supported_capabilities,
        "capability_allowlist": provider_config.capability_allowlist,
        "capabilities": capabilities,
        "issues": issues,
    }


def build_provider_status(
    provider_id: Optional[str],
    provider_configs: dict[str, ToolProviderRuntimeConfig],
) -> dict[str, Any]:
    if provider_id is None:
        providers = [qa_claw_status(provider_configs.get("qa_claw"))]
        configured_count = sum(1 for provider in providers if provider["configured"])
        enabled_count = sum(1 for provider in providers if provider["enabled"])
        return {
            "provider_count": len(providers),
            "configured_count": configured_count,
            "enabled_count": enabled_count,
            "supported_provider_ids": supported_provider_ids(),
            "providers": providers,
        }

    ensure_supported_provider(provider_id)
    return qa_claw_status(provider_configs.get(provider_id))


def build_qa_claw_config(
    repo_root: Path,
    worktree_root: Optional[Path],
    capability_allowlist: list[str],
    enabled: bool,
    timeout_seconds: int,
    max_output_bytes: int,
) -> ToolProviderRuntimeConfig:
    unsupported_capabilities = [
        capability_id
        for capability_id in capability_allowlist
        if capability_id not in QA_CLAW_SCRIPT_CAPABILITIES
    ]
    if unsupported_capabilities:
        raise ProviderExecutionError(
            "invalid_provider_capability",
            "Unsupported qa_claw capability: " + ", ".join(sorted(unsupported_capabilities)),
        )

    if not repo_root.exists() or not repo_root.is_dir():
        raise ProviderExecutionError(
            "invalid_provider_target",
            f"qa_claw repo_root does not exist: {repo_root}",
        )
    if worktree_root is not None and (not worktree_root.exists() or not worktree_root.is_dir()):
        raise ProviderExecutionError(
            "invalid_provider_target",
            f"qa_claw worktree_root does not exist: {worktree_root}",
        )

    target = {"repo_root": str(repo_root)}
    if worktree_root is not None:
        target["worktree_root"] = str(worktree_root)
    config = ToolProviderRuntimeConfig(
        enabled=enabled,
        capability_allowlist=capability_allowlist,
        target_kind="repo",
        target=target,
        timeout_seconds=timeout_seconds,
        max_output_bytes=max_output_bytes,
    )
    for capability_id in capability_allowlist:
        capability = QA_CLAW_SCRIPT_CAPABILITIES[capability_id]
        validate_capability_files(repo_root, capability)
    return config


def build_qa_claw_command(
    capability_id: str,
    capability: ScriptCapability,
    repo_root: Path,
    provider_config: ToolProviderRuntimeConfig,
    arguments: Optional[dict[str, Any]] = None,
) -> list[str]:
    command = list(capability.command)
    if command and command[0] == "python3":
        command[0] = resolve_provider_python_executable()

    if capability_id != "verify_worktrees":
        return command

    resolved_arguments = arguments or {}
    assignments = resolved_arguments.get("assignments") or []
    assignments_file = resolved_arguments.get("assignments_file")
    check_remote = bool(resolved_arguments.get("check_remote"))
    if not assignments and assignments_file is None:
        raise ProviderExecutionError(
            "invalid_provider_arguments",
            "verify_worktrees requires at least one --assignment or --assignments-file.",
        )

    command.extend(["--repo-root", str(repo_root)])
    worktree_root_value = provider_config.target.get("worktree_root")
    if isinstance(worktree_root_value, str) and worktree_root_value.strip():
        command.extend(["--worktree-root", worktree_root_value])

    for assignment in assignments:
        command.extend(["--assignment", assignment])

    if assignments_file is not None:
        assignments_path = Path(assignments_file).expanduser().resolve()
        if not assignments_path.exists() or not assignments_path.is_file():
            raise ProviderExecutionError(
                "invalid_provider_arguments",
                f"Assignments file does not exist: {assignments_path}",
            )
        command.extend(["--assignments-file", str(assignments_path)])

    if check_remote:
        command.append("--check-remote")
    return command


def truncate_to_bytes(value: str, max_bytes: int) -> tuple[str, bool]:
    if max_bytes <= 0:
        return "", bool(value)

    encoded = value.encode("utf-8")
    if len(encoded) <= max_bytes:
        return value, False

    preview = encoded[:max_bytes].decode("utf-8", errors="replace")
    return f"{preview}\n[truncated]", True


def bounded_previews(stdout: str, stderr: str, max_output_bytes: int) -> tuple[str, str, bool]:
    stdout_preview, stdout_truncated = truncate_to_bytes(stdout, max_output_bytes)
    remaining_bytes = max(max_output_bytes - len(stdout_preview.encode("utf-8")), 0)
    stderr_preview, stderr_truncated = truncate_to_bytes(stderr, remaining_bytes)
    return stdout_preview, stderr_preview, stdout_truncated or stderr_truncated


def run_tool_provider(
    provider_id: str,
    capability_id: str,
    provider_config: ToolProviderRuntimeConfig,
    arguments: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    ensure_supported_provider(provider_id)
    if not provider_config.enabled:
        raise ProviderExecutionError(
            "provider_disabled",
            f'Provider "{provider_id}" is configured but disabled.',
        )

    capability = ensure_allowed_capability(capability_id, provider_config)
    repo_root = resolve_repo_root(provider_config)
    validate_capability_files(repo_root, capability)
    command = build_qa_claw_command(
        capability_id,
        capability,
        repo_root,
        provider_config,
        arguments=arguments,
    )

    try:
        completed = subprocess.run(
            command,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=provider_config.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        stdout_preview, stderr_preview, truncated = bounded_previews(
            stdout,
            stderr,
            provider_config.max_output_bytes,
        )
        return {
            "ok": False,
            "summary": f"{provider_id} {capability_id} timed out.",
            "artifacts": [],
            "stdout_preview": stdout_preview,
            "stderr_preview": stderr_preview,
            "truncated": truncated,
            "error_codes": ["TIMEOUT"],
            "exit_code": None,
            "provider_id": provider_id,
            "capability_id": capability_id,
        }

    stdout_preview, stderr_preview, truncated = bounded_previews(
        completed.stdout,
        completed.stderr,
        provider_config.max_output_bytes,
    )
    ok = completed.returncode == 0
    summary = capability.success_summary if ok else capability.failure_summary
    return {
        "ok": ok,
        "summary": summary,
        "artifacts": [],
        "stdout_preview": stdout_preview,
        "stderr_preview": stderr_preview,
        "truncated": truncated,
        "error_codes": [] if ok else [capability.failure_code],
        "exit_code": completed.returncode,
        "provider_id": provider_id,
        "capability_id": capability_id,
    }
