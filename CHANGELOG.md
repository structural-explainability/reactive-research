# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to this project will be documented in this file.

The format is based on **[Keep a Changelog](https://keepachangelog.com/en/1.1.0/)**
and this project adheres to **[Semantic Versioning](https://semver.org/spec/v2.0.0.html)**.

## [Unreleased]

---

## [0.3.0] - 2026-10-06

### Added

- Deterministic versioned observations of working content and selected Git trees,
  including source revisions, declarations, dependency pins and freeze hashes.
- Snapshot-backed identifier resolution and narrow typed impact traversal with
  human-readable revalidation obligations and protected evidence boundaries.
- Mermaid evolution, propagation and impact graphs derived from shared JSON.
- Read-only acceptance examples for SE-100, Transformation and PURL Freeze 01.

### Changed

- Shared source-text extraction with historical observations and distinguished
  additional explicitly typed relationships without inferring scientific agreement.

---

## [0.2.0] - 2026-09-30

### Added

- Repository-local validation for Reactive Research declarations.
- Normalized machine-readable declaration export.
- Cross-repository identifier resolution against local declaration registries.
- Resolution states for `resolved`, `unresolved`, and `duplicate-definition`.
- Validation diagnostics for unsupported relationships and malformed identifiers.
- Package-version discovery shared by the CLI and declaration export.

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

Package versions are derived from Git tags.
Tag `vX.Y.Z` to release.

## Release Procedure (Required)

Follow these steps exactly when creating a new release.

### Task 1. Update release metadata (manual edits)

1.1. CHANGELOG.md: add section, move unreleased entries, update links
1.2. `CITATION.cff` - update `version` and `date-released`
1.3. `pyproject.toml` - update build system `fallback-version`

### Task 2. Validate

Run from the repository root in PowerShell.

```powershell
# Update Python and run repository checks.
.\sit.ps1

# Update GitHub Actions and pin all action references to immutable SHAs.
uvx gha-tools autoupdate --pin=all --write .github/workflows

# Audit the resulting GitHub configuration for security findings.
uvx zizmor@latest .github/
# One informational is fine:
# action functionality is already included by the runner
#  --> .github\workflows\release-pypi.yml

# Validate citation metadata.
uvx cffconvert --validate

# Format Markdown.
npx markdownlint-cli2 --fix

# Verify CLI identity.
uv run reactive-research --help
uv run reactive-research --version

# Extract normalized declarations and exercise file output.
uv run reactive-research extract --format json --output registry\declarations.json

# Exercise repository-local validation.
uv run reactive-research validate --strict --format json

# Exercise registry loading and resolution of all local references.
uv run reactive-research resolve --all --registry registry --format json

# Exercise the complete Reactive Research observation, snapshot,
# impact, graph, and frozen-evidence acceptance workflow against
# the Structural Explainability repository family.
uv run reactive-research generate --root .. --output docs/en/output
# Inspect the generated content.
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

[Unreleased]: https://github.com/structural-explainability/reactive-research/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/structural-explainability/reactive-research/releases/tag/v0.3.0
[0.2.0]: https://github.com/structural-explainability/reactive-research/releases/tag/v0.2.0
[0.1.0]: https://github.com/structural-explainability/reactive-research/releases/tag/v0.1.0

<!-- markdownlint-enable MD024 -->
