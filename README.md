# Reactive Research: Tools

<!-- [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.x.svg)](https://zenodo.org/records/x) -->
[![PyPI](https://img.shields.io/pypi/v/reactive-research.svg)](https://pypi.org/project/reactive-research/)
[![Python 3.14](https://img.shields.io/badge/python-3.14%2B-blue?logo=python)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![CI Status](https://github.com/structural-explainability/reactive-research/actions/workflows/ci-python-zensical.yml/badge.svg)](https://github.com/structural-explainability/reactive-research/actions/workflows/ci-python-zensical.yml)
[![Docs](https://img.shields.io/badge/docs-Zensical-blue)](https://structural-explainability.github.io/reactive-research/)

> Tools for building, validating, resolving, and querying Reactive Research graphs.

`reactive-research` is the reference command-line implementation for
Reactive Research.

Reactive Research represents addressable research objects and their typed
relationships so changes to upstream research can generate explicit downstream
revalidation obligations.

## Quick Start

From the repository:

```powershell
uv run reactive-research --help
uv run reactive-research extract
uv run reactive-research extract --format json
```

After publication to PyPI:

```powershell
uvx reactive-research --help
```

## Research Annotations

The canonical compact namespace is `RR`.

```text
RR.DEFINES: SE-210.Definition.4.3
RR.IMPLEMENTS: SE-210.Theorem.5.2
```

The expanded namespace is also supported:

```text
REACTIVE-RESEARCH.DEFINES: SE-210.Definition.4.3
REACTIVE-RESEARCH.IMPLEMENTS: SE-210.Theorem.5.2
```

Namespaces and relationship names are case-insensitive.

## Current Implementation

Version `0.2.0` includes:

- the `reactive-research` command-line interface;
- typed research identifiers and declarations;
- repository and Git revision discovery;
- extraction of `RR.DEFINES` and `RR.IMPLEMENTS`;
- source provenance;
- duplicate local definition detection; and
- text and JSON output.

The `validate`, `resolve`, `graph`, `impact`, `snapshot`, and `inspect`
command surfaces are present and are being implemented incrementally.

## Documentation

See the
[Reactive Research documentation](https://structural-explainability.github.io/reactive-research/)
for the model, typed relationships, integration architecture, and command-line API.

## Project Family

Reactive Research currently consists of:

- [reactive-research-spec](https://github.com/structural-explainability/reactive-research-spec) — normative model;
- [reactive-research-registry](https://github.com/structural-explainability/reactive-research-registry) — resolvable graph and snapshots; and
- [reactive-research](https://github.com/structural-explainability/reactive-research) — executable tooling.

## Status

Early development.
The initial implementation is being exercised against an existing
multi-repository research program.

## Annotations

[.annotations/annotations.md](./.annotations/annotations.md)

## Citation

Citation metadata is available in [CITATION.cff](./CITATION.cff).

## License

[MIT](./LICENSE)

## Repository Manifest

The repository's role, scope, and dependencies are declared in
[SE_MANIFEST.toml](./SE_MANIFEST.toml).
