# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to this project will be documented in this file.

The format is based on **[Keep a Changelog](https://keepachangelog.com/en/1.1.0/)**
and this project adheres to **[Semantic Versioning](https://semver.org/spec/v2.0.0.html)**.

## [Unreleased]

---

## [0.1.0] - 2026-09-30

### Added

- initial release
- Reactive Research command-line interface with `extract`, `validate`, `resolve`, `graph`, `impact`, `snapshot`, and `inspect` command surfaces.
- Typed models for research identifiers, relationships, source locations, repository context, extraction results, and diagnostics.
- Research identifier parsing and validation.
- Repository identity and Git revision discovery.
- Source extraction for `RR.DEFINES` and `RR.IMPLEMENTS` annotations.
- Support for the expanded `REACTIVE-RESEARCH` annotation namespace.
- Source-specific annotation syntax for Python, TOML, Lean, LaTeX, and Markdown.
- Detection of duplicate local research-object definitions.
- Deterministic filtering of generated, environment, and test directories during extraction.
- JSON and human-readable command output.

---

## Notes on versioning and releases

We use **SemVer**:

- **MAJOR** - Breaking changes to artifact structure or validation semantics.
- **MINOR** - Backward-compatible additions to schema or validation rules.
- **PATCH** - Fixes, documentation, and tooling.

Package versions are derived from Git tags. Tag `vX.Y.Z` to release.

## Release Procedure (Required)

Follow these steps exactly when creating a new release.

### Task 1. Update release metadata (manual edits)

1.1. CHANGELOG.md: add section, move unreleased entries, update links
1.2. `CITATION.cff` - update `version` and `date-released`
1.3. `pyproject.toml` - update build system `fallback-version`

### Task 2. Validate

Run from the repository root in PowerShell.

```powershell
# Run repository checks.
.\sit.ps1

# Update GitHub Actions and pin all action references to immutable SHAs.
uvx gha-tools autoupdate --pin=all --write .github/workflows

# Update hooks.
uvx prek update
git add -A
uvx prek run --all-files

# Audit the resulting GitHub configuration for security findings.
uvx zizmor@latest .github/

# Validate citation metadata.
uvx cffconvert --validate

# Format Markdown.
npx markdownlint-cli2 --fix

# ============================================================
# REACTIVE RESEARCH CLI
# ============================================================

# Show top-level help and version.
uv run reactive-research
uv run reactive-research --help
uv run reactive-research --version

# Show command help.
uv run reactive-research extract --help
uv run reactive-research validate --help
uv run reactive-research resolve --help
uv run reactive-research graph --help
uv run reactive-research impact --help
uv run reactive-research snapshot --help
uv run reactive-research inspect --help

# ============================================================
# IMPLEMENTED
# ============================================================

# Extract RR.DEFINES and RR.IMPLEMENTS annotations from this repository.
uv run reactive-research extract

# Extract as JSON.
uv run reactive-research extract --format json

# Extract from another local repository.
uv run reactive-research extract --path C:\Repos\some-repository

# Write extraction output to a file.
uv run reactive-research extract --format json --output extraction.json

# The --check option is accepted.
# NOTE: It currently records check=true but does not yet compare/write artifacts.
uv run reactive-research extract --check

# ============================================================
# SCAFFOLDED - COMMANDS RUN, CORE SEMANTICS NOT YET IMPLEMENTED
# ============================================================

# Local validation scaffold.
uv run reactive-research validate
uv run reactive-research validate --strict

# Identifier-resolution scaffold.
uv run reactive-research resolve SE-210.Definition.4.3
uv run reactive-research resolve --all

# Graph scaffold.
uv run reactive-research graph
uv run reactive-research graph --view objects
uv run reactive-research graph --view repositories

# Impact-analysis scaffold.
uv run reactive-research impact SE-210.Definition.4.3
uv run reactive-research impact SE-210.Definition.4.3 --direct
uv run reactive-research impact SE-210.Definition.4.3 --transitive

# Snapshot scaffold.
uv run reactive-research snapshot

# Inspection scaffold.
uv run reactive-research inspect SE-210.Definition.4.3

# All scaffolded commands also support structured JSON output.
uv run reactive-research validate --format json
uv run reactive-research resolve SE-210.Definition.4.3 --format json
uv run reactive-research graph --format json
uv run reactive-research impact SE-210.Definition.4.3 --format json
uv run reactive-research snapshot --format json
uv run reactive-research inspect SE-210.Definition.4.3 --format json
```

### Task 4. Commit, push, tag

```shell
git add -A
git commit -m "Prepare X.Y.Z"
git push -u origin main
```

Verify actions run on GitHub. After success:

```shell
git tag vX.Y.Z -m "X.Y.Z"
git push origin vX.Y.Z
```

## Only As Needed (delete a tag)

```shell
git tag -d vX.Z.Y
git push origin :refs/tags/vX.Z.Y
```

## Links

[Unreleased]: https://github.com/structural-explainability/reactive-research/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/structural-explainability/reactive-research/releases/tag/v0.1.0

<!-- markdownlint-enable MD024 -->
