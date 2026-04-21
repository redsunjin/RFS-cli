from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rfs_cli.models import ToolProviderRuntimeConfig


class ProviderExecutionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ScriptCapability:
    command: list[str]
    failure_code: str
    success_summary: str
    failure_summary: str


QA_CLAW_SCRIPT_CAPABILITIES: dict[str, ScriptCapability] = {
    "scan_secrets": ScriptCapability(
        command=["bash", "security/scan-secrets.sh", "."],
        failure_code="SECRET_SCAN_FAILED",
        success_summary="qa_claw secret scan passed.",
        failure_summary="qa_claw secret scan failed.",
    ),
}


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


def validate_capability_files(repo_root: Path, capability: ScriptCapability) -> None:
    script_path = repo_root / capability.command[1]
    try:
        script_path.resolve().relative_to(repo_root)
    except ValueError as exc:
        raise ProviderExecutionError(
            "invalid_provider_config",
            "Capability script escapes the configured repo root.",
        ) from exc

    if not script_path.exists() or not script_path.is_file():
        raise ProviderExecutionError(
            "provider_unavailable",
            f"Required provider script does not exist: {script_path}",
        )


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

    try:
        completed = subprocess.run(
            capability.command,
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
