from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class WikiLintError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


REQUIRED_WIKI_FILES = ("index.md", "log.md", "overview.md")
LINT_KINDS = (
    "contradiction",
    "stale_claim",
    "orphan_page",
    "missing_crosslink",
    "missing_page",
    "coverage_gap",
)
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def resolve_wiki_root(root: Path) -> Path:
    candidate = root.expanduser().resolve()
    if candidate.name == "wiki" and candidate.is_dir():
        return candidate

    wiki_dir = candidate / "wiki"
    if wiki_dir.is_dir():
        return wiki_dir

    raise WikiLintError(
        "wiki_missing",
        f"Could not find a wiki directory under: {candidate}",
    )


def validate_wiki_root(wiki_root: Path) -> None:
    missing_files = [name for name in REQUIRED_WIKI_FILES if not (wiki_root / name).is_file()]
    if missing_files:
        raise WikiLintError(
            "invalid_wiki_state",
            "Missing required wiki file(s): " + ", ".join(f"wiki/{name}" for name in missing_files),
        )


def list_wiki_pages(wiki_root: Path) -> list[Path]:
    return sorted(path for path in wiki_root.rglob("*.md") if path.is_file())


def wiki_label(wiki_root: Path, page_path: Path) -> str:
    return f"wiki/{page_path.relative_to(wiki_root).as_posix()}"


def normalize_link_target(current_page: Path, wiki_root: Path, target: str) -> str | None:
    trimmed = target.strip()
    if not trimmed or trimmed.startswith("#") or "://" in trimmed or trimmed.startswith("mailto:"):
        return None

    target_path = trimmed.split("#", 1)[0].split("?", 1)[0].strip()
    if not target_path:
        return None

    resolved = (current_page.parent / target_path).resolve()
    try:
        relative = resolved.relative_to(wiki_root)
    except ValueError:
        return None
    return relative.as_posix()


def page_links(page_path: Path, wiki_root: Path) -> set[str]:
    text = page_path.read_text(encoding="utf-8")
    links: set[str] = set()
    for target in LINK_PATTERN.findall(text):
        normalized = normalize_link_target(page_path, wiki_root, target)
        if normalized is not None:
            links.add(normalized)
    return links


def severity_rank(severity: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(severity, 3)


def recommended_action_for(kind: str | None) -> str:
    if kind == "missing_page":
        return (
            "Create the missing wiki page or remove the broken link "
            "before expanding wiki workflows."
        )
    if kind == "orphan_page":
        return "Link the orphan page from index.md or another maintained wiki page."
    if kind == "missing_crosslink":
        return "Add at least one outbound wiki link from the isolated page."
    return "No wiki issues detected."


def build_wiki_lint_report(root: Path, max_issues: int = 20) -> dict[str, Any]:
    wiki_root = resolve_wiki_root(root)
    validate_wiki_root(wiki_root)

    pages = list_wiki_pages(wiki_root)
    existing_rel_paths = {page.relative_to(wiki_root).as_posix(): page for page in pages}
    link_map = {
        relative: page_links(page_path, wiki_root)
        for relative, page_path in existing_rel_paths.items()
    }

    inbound_counts = {relative: 0 for relative in existing_rel_paths}
    for links in link_map.values():
        for target in links:
            if target in inbound_counts:
                inbound_counts[target] += 1

    issues: list[dict[str, Any]] = []
    issue_index = 1

    def add_issue(
        kind: str,
        severity: str,
        path: str,
        summary: str,
        details: str,
        related_paths: list[str],
    ) -> None:
        nonlocal issue_index
        issues.append(
            {
                "id": f"lint-{issue_index:03d}",
                "kind": kind,
                "severity": severity,
                "path": path,
                "summary": summary,
                "details": details,
                "related_paths": related_paths,
            }
        )
        issue_index += 1

    for relative, links in link_map.items():
        for target in sorted(links):
            if target not in existing_rel_paths:
                add_issue(
                    "missing_page",
                    "medium",
                    f"wiki/{relative}",
                    "A wiki page links to a target that does not exist.",
                    f"Missing linked page: wiki/{target}",
                    [f"wiki/{target}"],
                )

    maintained_pages = [
        relative
        for relative in existing_rel_paths
        if relative not in REQUIRED_WIKI_FILES
    ]
    for relative in maintained_pages:
        if inbound_counts[relative] == 0:
            add_issue(
                "orphan_page",
                "low",
                f"wiki/{relative}",
                "A maintained wiki page is not linked from the rest of the wiki.",
                "Add a link from index.md, overview.md, or another maintained wiki page.",
                [],
            )

    for relative in maintained_pages:
        outbound = {target for target in link_map[relative] if target in existing_rel_paths}
        if not outbound and len(existing_rel_paths) > 3:
            add_issue(
                "missing_crosslink",
                "low",
                f"wiki/{relative}",
                "A maintained wiki page has no outbound wiki links.",
                "Add at least one outbound wiki link to a related page.",
                [],
            )

    issues.sort(key=lambda item: (severity_rank(item["severity"]), item["path"], item["kind"]))
    trimmed_issues = issues[:max_issues]
    issues_by_kind = {kind: 0 for kind in LINT_KINDS}
    for issue in issues:
        issues_by_kind[issue["kind"]] += 1

    top_kind = trimmed_issues[0]["kind"] if trimmed_issues else None
    return {
        "wiki_root": str(wiki_root),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "page_count": len(existing_rel_paths),
        "issue_count": len(issues),
        "issues_by_kind": issues_by_kind,
        "issues": trimmed_issues,
        "recommended_action": recommended_action_for(top_kind),
    }
