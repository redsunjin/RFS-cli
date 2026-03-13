from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List

TEXT_EXTENSIONS = {
    ".md",
    ".markdown",
    ".txt",
    ".py",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
}

IGNORED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}


def iter_files(root: Path) -> Iterable[Path]:
    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in IGNORED_DIRS)
        for filename in sorted(filenames):
            yield Path(current_root, filename)


def iter_text_files(root: Path) -> Iterable[Path]:
    for path in iter_files(root):
        if path.suffix.lower() in TEXT_EXTENSIONS:
            yield path


def build_snippet(content: str, query: str, radius: int = 70) -> str:
    lowered = content.lower()
    index = lowered.find(query.lower())
    if index == -1:
        return content[: radius * 2].replace("\n", " ").strip()

    start = max(index - radius, 0)
    end = min(index + len(query) + radius, len(content))
    return content[start:end].replace("\n", " ").strip()


def live_search(query: str, root: Path, limit: int = 20) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []

    for path in iter_text_files(root):
        content = path.read_text(encoding="utf-8", errors="ignore")
        if query.lower() not in content.lower():
            continue

        result = {
            "path": str(path.resolve()),
            "title": path.stem,
            "source_type": "obsidian" if ".obsidian" in str(path.parent) else "local",
            "score": 1.0,
            "snippet": build_snippet(content, query),
        }
        results.append(result)

        if len(results) >= limit:
            break

    return results


def list_files(root: Path, limit: int = 100) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []

    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in IGNORED_DIRS)

        for dirname in dirnames:
            if len(records) >= limit:
                return records
            path = Path(current_root, dirname)
            records.append(
                {
                    "path": str(path.resolve()),
                    "kind": "dir",
                    "size_bytes": 0,
                }
            )

        for filename in sorted(filenames):
            if len(records) >= limit:
                return records
            path = Path(current_root, filename)
            if not path.exists():
                continue
            records.append(
                {
                    "path": str(path.resolve()),
                    "kind": "file",
                    "size_bytes": path.stat().st_size,
                }
            )

    return records


def project_stats(root: Path) -> Dict[str, object]:
    total_files = 0
    counts: Dict[str, int] = {}

    for path in iter_files(root):
        total_files += 1
        suffix = path.suffix.lower() or "<no_ext>"
        counts[suffix] = counts.get(suffix, 0) + 1

    top_extensions = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:10]

    return {
        "root": str(root.resolve()),
        "total_files": total_files,
        "top_extensions": [{"extension": ext, "count": count} for ext, count in top_extensions],
    }


def preview_file(target: Path, max_chars: int = 500) -> Dict[str, object]:
    content = target.read_text(encoding="utf-8", errors="ignore")

    return {
        "path": str(target.resolve()),
        "size_bytes": target.stat().st_size,
        "preview": content[:max_chars],
    }


def git_summary(root: Path) -> Dict[str, object]:
    process = subprocess.run(
        ["git", "-C", str(root), "status", "--short", "--branch"],
        capture_output=True,
        text=True,
        check=False,
    )

    if process.returncode != 0:
        raise ValueError(process.stderr.strip() or "Git status failed.")

    lines = [line for line in process.stdout.splitlines() if line.strip()]
    return {"root": str(root.resolve()), "lines": lines}
