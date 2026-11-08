# ============================================================
# src/reactive_research/boundaries.py
# ============================================================

"""Observe declared research boundaries across repositories.

Reads two existing surfaces without editing any repository:

- SE manifests: class, status, dependencies, and scope includes/excludes.
- DOUBTS.md files: doubt entries with their IDs, statuses, and resolutions.

WHY: Doubt status and scope boundaries are the facts most easily lost between
working sessions. A resolved doubt read without its status, or an exclusion
read without its owner, can send research in the wrong direction.

Exact declarations are kept separate from provisional candidates.
Candidates use whitespace- and case-normalized exact text comparison only.
They are suggestions for review, never established relationships.
"""

from pathlib import Path
import re
import tomllib
from typing import Any

from reactive_research.observation import digest, discover_projects, read_project

FORMAT = "reactive-research-boundaries"
FORMAT_VERSION = 1

MANIFEST_NAMES = ("SE_MANIFEST.toml", "MANIFEST.toml", "se-manifest.toml")
DOUBTS_NAME = "DOUBTS.md"

OPEN_STATUSES = ("OPEN", "OPEN CHECK")
RESOLVED_STATUSES = ("RESOLVED",)
STANDING_STATUSES = ("STANDING RULES",)

_HEADING = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.+?)\s*#*\s*$")
_FENCE = re.compile(r"^\s*(?:```|~~~)")
_DOUBT_TITLE = re.compile(
    r"^(?P<id>[A-Z]+-\d+)\.\s+(?:\((?P<status>[^)]+)\)\s+)?(?P<title>.+)$"
)


def parse_doubts(text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Parse DOUBTS.md text into doubt entries and diagnostics.

    A doubt entry is a level-3 heading such as
    ``### UM-002. (RESOLVED) Joint Satisfiability``.
    The status is optional because some files use another convention.
    """
    entries: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    first_line_by_id: dict[str, int] = {}
    fields_by_entry: list[dict[str, str]] = []

    section: str | None = None
    current: dict[str, Any] | None = None
    current_fields: dict[str, str] = {}
    field: str | None = None
    in_fence = False

    for number, line in enumerate(text.splitlines(), start=1):
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        heading = _HEADING.match(line)
        if heading is None:
            # WHY: The first non-empty line under a level-4 heading is the
            # short statement used for a criterion or a one-line resolution.
            if (
                current is not None
                and field is not None
                and line.strip()
                and field not in current_fields
            ):
                current_fields[field] = line.strip()
            continue

        level = len(heading.group("hashes"))
        title = heading.group("text")

        if level <= 3:
            current = None
            field = None
            if level == 2:
                section = title
            if level == 3:
                match = _DOUBT_TITLE.match(title)
                if match is not None:
                    status = match.group("status")
                    current_fields = {}
                    current = {
                        "id": match.group("id"),
                        "status": status.strip().upper() if status else None,
                        "title": match.group("title").strip(),
                        "section": section,
                        "line": number,
                    }
                    entries.append(current)
                    fields_by_entry.append(current_fields)
            continue

        if level == 4 and current is not None:
            field = title.strip().lower()

    for entry, fields in zip(entries, fields_by_entry, strict=True):
        entry["criterion"] = fields.get("research criterion")
        entry["resolution"] = fields.get("resolution")

        identifier = entry["id"]
        if entry["status"] is None:
            diagnostics.append(
                {
                    "code": "RR.DOUBT_STATUS_MISSING",
                    "severity": "info",
                    "line": entry["line"],
                    "id": identifier,
                    "message": f"{identifier} has no status in its heading.",
                }
            )
        if identifier in first_line_by_id:
            diagnostics.append(
                {
                    "code": "RR.DUPLICATE_DOUBT_ID",
                    "severity": "warning",
                    "line": entry["line"],
                    "id": identifier,
                    "message": (
                        f"{identifier} also appears at line "
                        f"{first_line_by_id[identifier]}."
                    ),
                }
            )
        else:
            first_line_by_id[identifier] = entry["line"]

    return entries, diagnostics


def read_manifest(
    data: dict[str, bytes],
) -> tuple[str | None, dict[str, Any], list[dict[str, Any]]]:
    """Read the repository manifest, preserving parse failure as a diagnostic."""
    name = next((candidate for candidate in MANIFEST_NAMES if candidate in data), None)
    if name is None:
        return None, {}, []
    try:
        manifest = tomllib.loads(data[name].decode("utf-8", errors="replace"))
    except tomllib.TOMLDecodeError as error:
        return (
            name,
            {},
            [
                {
                    "code": "RR.SURFACE_PARSE",
                    "severity": "warning",
                    "path": name,
                    "message": str(error),
                }
            ],
        )
    return name, manifest, []


def manifest_boundaries(
    manifest: dict[str, Any],
    manifest_name: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Extract identity, dependencies, and scope from one parsed manifest."""
    diagnostics: list[dict[str, Any]] = []

    identity = manifest.get("repository", manifest.get("repo", {}))
    if not isinstance(identity, dict):
        identity = {}

    depends = manifest.get("depends", {})
    if not isinstance(depends, dict):
        depends = {}
    dependencies: dict[str, list[str]] = {}
    for kind in ("required", "optional"):
        dependencies[kind] = _dependency_names(
            depends.get(kind, []), kind, manifest_name, diagnostics
        )

    scope = manifest.get("scope", {})
    if not isinstance(scope, dict):
        scope = {}
    includes = _string_list(
        scope.get("includes", []), "includes", manifest_name, diagnostics
    )
    excludes = _string_list(
        scope.get("excludes", []), "excludes", manifest_name, diagnostics
    )

    return (
        {
            "name": identity.get("name"),
            "organization": identity.get("organization"),
            "class": identity.get("class"),
            "kind": identity.get("kind"),
            "status": identity.get("status"),
            "schema_version": manifest.get("schema_version"),
            "depends": dependencies,
            "includes": includes,
            "excludes": excludes,
        },
        diagnostics,
    )


def observe_boundaries(
    path: Path, extra_diagnostics: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Observe manifests and DOUBTS files in every discovered project."""
    root = path.resolve()
    repositories: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = list(extra_diagnostics or [])

    for project_root in discover_projects(root):
        relative = project_root.relative_to(root).as_posix()
        data, state = read_project(project_root)

        manifest_name, manifest, manifest_errors = read_manifest(data)
        diagnostics.extend({**error, "project": relative} for error in manifest_errors)

        declared: dict[str, Any] = {
            "name": None,
            "organization": None,
            "class": None,
            "kind": None,
            "status": None,
            "schema_version": None,
            "depends": {"required": [], "optional": []},
            "includes": [],
            "excludes": [],
        }
        if manifest_name is None:
            diagnostics.append(
                {
                    "code": "RR.MANIFEST_NOT_FOUND",
                    "severity": "info",
                    "project": relative,
                    "message": "No supported manifest was found; the data is missing, not defective.",
                }
            )
        elif manifest:
            declared, scope_errors = manifest_boundaries(manifest, manifest_name)
            diagnostics.extend({**error, "project": relative} for error in scope_errors)

        doubts: list[dict[str, Any]] = []
        if DOUBTS_NAME in data:
            doubts, doubt_errors = parse_doubts(
                data[DOUBTS_NAME].decode("utf-8", errors="replace")
            )
            diagnostics.extend(
                {**error, "project": relative, "path": DOUBTS_NAME}
                for error in doubt_errors
            )

        repositories.append(
            {
                "path": relative,
                **declared,
                "name": declared["name"] or project_root.name,
                "manifest": manifest_name,
                "doubts": doubts,
                "source": {
                    "revision": state["source_revision"],
                    "mode": state["mode"],
                    "observed_revision": state["observed_revision"],
                    "manifest_sha256": state["files"].get(manifest_name or ""),
                    "doubts_sha256": state["files"].get(DOUBTS_NAME),
                },
            }
        )

    repositories.sort(key=lambda repository: repository["path"])
    payload: dict[str, Any] = {
        "format": FORMAT,
        "format_version": FORMAT_VERSION,
        "scope": (
            "Discovered Git/project roots. Exact declarations from manifests and "
            "DOUBTS.md; no scientific validation inferred."
        ),
        "repositories": repositories,
        "diagnostics": sorted(
            diagnostics,
            key=lambda item: (
                str(item.get("project")),
                str(item.get("code")),
                int(item.get("line") or 0),
                str(item.get("id")),
            ),
        ),
        "provisional": provisional_candidates(repositories),
    }
    return {**payload, "snapshot_id": "sha256:" + digest(payload)}


def provisional_candidates(repositories: list[dict[str, Any]]) -> dict[str, Any]:
    """Return suggested overlaps from normalized exact text comparison only."""
    includes_by_text: dict[str, dict[str, Any]] = {}
    for repository in repositories:
        for text in repository["includes"]:
            record = includes_by_text.setdefault(
                _normalize(text), {"text": text, "repositories": set()}
            )
            record["repositories"].add(repository["name"])

    repeated_includes: list[dict[str, Any]] = [
        {"text": record["text"], "repositories": sorted(record["repositories"])}
        for record in includes_by_text.values()
        if len(record["repositories"]) > 1
    ]

    excludes_without_include: list[dict[str, str]] = []
    for repository in repositories:
        for text in repository["excludes"]:
            owners = includes_by_text.get(_normalize(text), {}).get(
                "repositories", set()
            )
            if not owners - {repository["name"]}:
                excludes_without_include.append(
                    {"text": text, "repository": repository["name"]}
                )

    scopes: dict[tuple[tuple[str, ...], tuple[str, ...]], list[str]] = {}
    for repository in repositories:
        if not repository["includes"]:
            continue
        key = (
            tuple(sorted(_normalize(text) for text in repository["includes"])),
            tuple(sorted(_normalize(text) for text in repository["excludes"])),
        )
        scopes.setdefault(key, []).append(repository["name"])
    identical_scope = [
        {
            "repositories": sorted(names),
            "includes": len(key[0]),
            "excludes": len(key[1]),
        }
        for key, names in scopes.items()
        if len(names) > 1
    ]

    return {
        "status": "provisional",
        "note": [
            "Whitespace- and case-normalized exact text comparison only.",
            "These are suggestions for review, not established relationships.",
            "An exclusion without a matching inclusion may name work outside the observed set.",
            "It may also name work nobody currently owns.",
        ],
        "repeated_includes": sorted(
            repeated_includes, key=lambda item: _normalize(item["text"])
        ),
        "excludes_without_exact_include": sorted(
            excludes_without_include,
            key=lambda item: (item["repository"], _normalize(item["text"])),
        ),
        "identical_scope": sorted(
            identical_scope, key=lambda item: item["repositories"]
        ),
    }


def boundaries_report(document: dict[str, Any], *, view: str = "index") -> str:
    """Render the observation as Markdown, one sentence per line.

    View ``index`` lists doubts with statuses and diagnostics.
    View ``scope`` lists each repository's includes and excludes.
    View ``all`` renders both.
    """
    repositories: list[dict[str, Any]] = document["repositories"]
    lines: list[str] = ["# Boundaries Index", ""]
    lines += [
        f"Observed {len(repositories)} repositories.",
        "This report is an observation, not a decision.",
        "Statuses are copied from the source headings.",
        f"Snapshot: `{document['snapshot_id']}`",
        "",
    ]

    if view in ("index", "all"):
        lines += _doubts_sections(repositories)
        lines += _diagnostics_section(document["diagnostics"])
        lines += _provisional_section(document["provisional"])
    if view in ("scope", "all"):
        lines += _scope_sections(repositories)

    return "\n".join(lines).rstrip() + "\n"


def _doubts_sections(repositories: list[dict[str, Any]]) -> list[str]:
    """Render summary counts and doubts grouped by status class."""
    counts: dict[str, int] = {}
    for repository in repositories:
        for doubt in repository["doubts"]:
            label = doubt["status"] or "NO STATUS"
            counts[label] = counts.get(label, 0) + 1

    with_manifest = sum(1 for repository in repositories if repository["manifest"])
    with_doubts = sum(1 for repository in repositories if repository["doubts"])
    lines = [
        "## Summary",
        "",
        f"- Repositories observed: {len(repositories)}",
        f"- With a manifest: {with_manifest}",
        f"- With doubt entries: {with_doubts}",
    ]
    for label in sorted(counts):
        lines.append(f"- {label}: {counts[label]}")
    lines.append("")

    for heading in ("Open", "Resolved", "Standing Rules", "Other"):
        lines += _doubt_group(heading, repositories)
    return lines


def _status_group(status: str | None) -> str:
    """Return the report group for one doubt status."""
    if status in OPEN_STATUSES:
        return "Open"
    if status in RESOLVED_STATUSES:
        return "Resolved"
    if status in STANDING_STATUSES:
        return "Standing Rules"
    return "Other"


def _doubt_group(heading: str, repositories: list[dict[str, Any]]) -> list[str]:
    """Render the doubts that belong to one report group."""
    lines: list[str] = []
    for repository in repositories:
        selected = [
            doubt
            for doubt in repository["doubts"]
            if _status_group(doubt["status"]) == heading
        ]
        if not selected:
            continue
        if not lines:
            lines += [f"## {heading}", ""]
        lines += [f"### {repository['name']}", ""]
        for doubt in selected:
            status = doubt["status"] or "no status"
            lines.append(f"- {doubt['id']} ({status}): {doubt['title']}")
            if doubt["resolution"]:
                lines.append(f"  Resolution: {doubt['resolution']}")
            lines.append(f"  See: {_link(repository, DOUBTS_NAME, doubt['line'])}")
        lines.append("")
    return lines


def _diagnostics_section(diagnostics: list[dict[str, Any]]) -> list[str]:
    """Render diagnostics, keeping missing data distinct from defects."""
    if not diagnostics:
        return []
    lines = ["## Diagnostics", ""]
    for item in diagnostics:
        location = item.get("project", "")
        if item.get("path"):
            location += f"/{item['path']}"
        if item.get("line"):
            location += f":{item['line']}"
        lines.append(
            f"- [{item.get('severity', 'info')}] {item['code']} "
            f"at {location}: {item.get('message', '')}".rstrip()
        )
    lines.append("")
    return lines


def _provisional_section(provisional: dict[str, Any]) -> list[str]:
    """Render counts of provisional candidates with their caveat."""
    lines = [
        "## Provisional Candidates",
        "",
        *provisional["note"],
        "",
        f"- Includes repeated in more than one repository: {len(provisional['repeated_includes'])}",
        f"- Excludes with no exact include elsewhere: {len(provisional['excludes_without_exact_include'])}",
        f"- Groups of repositories with identical scope: {len(provisional['identical_scope'])}",
    ]
    for group in provisional["identical_scope"]:
        lines.append(f"  - {', '.join(group['repositories'])}")
    lines.append("")
    return lines


def _scope_sections(repositories: list[dict[str, Any]]) -> list[str]:
    """Render includes and excludes per repository."""
    lines: list[str] = ["## Scope", ""]
    for repository in repositories:
        if not repository["includes"] and not repository["excludes"]:
            continue
        lines += [f"### {repository['name']}", ""]
        for label, key in (("Includes", "includes"), ("Excludes", "excludes")):
            if repository[key]:
                lines.append(f"{label}:")
                lines += [f"- {text}" for text in repository[key]]
        lines.append(
            f"See: {_link(repository, repository['manifest'] or 'SE_MANIFEST.toml')}"
        )
        lines.append("")
    return lines


def _link(repository: dict[str, Any], file_name: str, line: int | None = None) -> str:
    """Return a revision-pinned link when organization and revision are known."""
    label = file_name if line is None else f"{file_name}#L{line}"
    organization = repository.get("organization")
    revision = repository["source"]["revision"]
    if not organization or not revision:
        return label
    anchor = "" if line is None else f"#L{line}"
    return (
        f"[{label}](https://github.com/{organization}/{repository['name']}"
        f"/blob/{revision}/{file_name}{anchor})"
    )


def _normalize(text: str) -> str:
    """Normalize whitespace and case for provisional comparison only."""
    return " ".join(text.lower().split())


def _string_list(
    value: Any,
    key: str,
    manifest_name: str,
    diagnostics: list[dict[str, Any]],
) -> list[str]:
    """Return a list of strings or record a malformed-scope diagnostic."""
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return list(value)
    diagnostics.append(
        {
            "code": "RR.MALFORMED_SCOPE",
            "severity": "warning",
            "path": manifest_name,
            "message": f"scope.{key} is not a list of strings.",
        }
    )
    return []


def _dependency_names(
    items: Any,
    kind: str,
    manifest_name: str,
    diagnostics: list[dict[str, Any]],
) -> list[str]:
    """Return dependency repository names from string or table entries."""
    if not isinstance(items, list):
        diagnostics.append(
            {
                "code": "RR.MALFORMED_DEPENDENCIES",
                "severity": "warning",
                "path": manifest_name,
                "message": f"depends.{kind} is not a list.",
            }
        )
        return []
    names: list[str] = []
    for item in items:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, dict) and isinstance(
            item.get("repository", item.get("repo")), str
        ):
            names.append(item.get("repository", item.get("repo")))
        else:
            diagnostics.append(
                {
                    "code": "RR.UNRESOLVED_DEPENDENCY",
                    "severity": "warning",
                    "path": manifest_name,
                    "message": f"depends.{kind} contains an unreadable entry.",
                }
            )
    return names
