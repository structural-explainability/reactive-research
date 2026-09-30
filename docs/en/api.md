# API

The `reactive-research` package provides the reference executable interface
for Reactive Research.

## Annotation API

The canonical compact namespace is:

```text
RR
```

Annotations use:

```text
RR.<RELATION>: <IDENTIFIER>
```

For example:

```text
RR.DEFINES: SE-210.Definition.4.3
RR.IMPLEMENTS: SE-210.Theorem.5.2
```

The expanded namespace may be used when `RR` conflicts with another local
namespace:

```text
REACTIVE-RESEARCH.DEFINES: SE-210.Definition.4.3
REACTIVE-RESEARCH.IMPLEMENTS: SE-210.Theorem.5.2
```

Namespaces and relationship names are case-insensitive.

For example, these are equivalent:

```text
RR.DEFINES
rr.defines
REACTIVE-RESEARCH.DEFINES
reactive-research.defines
```

## Relationship Types

The Reactive Research relationship vocabulary includes:

```text
RR.DEFINES
RR.IMPLEMENTS
RR.DEPENDS
RR.INFORMS
RR.EVIDENCES
```

Version `0.2.0` currently extracts:

```text
RR.DEFINES
RR.IMPLEMENTS
```

The remaining relationship types are part of the model but are not yet
extracted by the current implementation.

## Source Syntax

Annotations are placed close to the authoritative source.

### Python

```python
# RR.DEFINES: SE-210.Definition.4.3
# RR.IMPLEMENTS: SE-210.Theorem.5.2
```

### TOML

```toml
# RR.DEFINES: SE-210.Definition.4.3
```

### Lean

```lean
-- RR.DEFINES: SE-210.Theorem.5.2
```

### LaTeX

```latex
% RR.DEFINES: SE-210.Definition.4.3
```

### Markdown

```html
<!-- RR.DEFINES: SE-210.Definition.4.3 -->
```

## Command-Line Interface

Show top-level help:

```powershell
uv run reactive-research
uv run reactive-research --help
```

Show the installed version:

```powershell
uv run reactive-research --version
```

Available command surfaces are:

```text
reactive-research
├── extract
├── validate
├── resolve
├── graph
├── impact
├── snapshot
└── inspect
```

## Extract

`extract` is the first command with implemented Reactive Research semantics.

Extract declarations from the current repository:

```powershell
uv run reactive-research extract
```

Machine-readable output:

```powershell
uv run reactive-research extract --format json
```

Extract from another local repository:

```powershell
uv run reactive-research extract --path C:\Repos\some-repository
```

Write output to a file:

```powershell
uv run reactive-research extract --format json --output extraction.json
```

Show command help:

```powershell
uv run reactive-research extract --help
```

Extraction currently:

- discovers eligible source files;
- recognizes `RR.DEFINES` and `RR.IMPLEMENTS`;
- normalizes research identifiers;
- records source path and line number;
- records repository identity;
- records the current Git revision when available;
- detects duplicate local definitions;
- ignores generated, environment, and test directories; and
- emits text or JSON output.

## Validate

```powershell
uv run reactive-research validate --help
uv run reactive-research validate
uv run reactive-research validate --strict
```

The command surface is available.

Full local validation semantics are under implementation.

## Resolve

```powershell
uv run reactive-research resolve --help
uv run reactive-research resolve SE-210.Definition.4.3
uv run reactive-research resolve --all
```

The command surface is available.

Registry-backed identifier resolution is under implementation.

## Graph

```powershell
uv run reactive-research graph --help
uv run reactive-research graph --view objects
uv run reactive-research graph --view repositories
```

The command surface is available.

Typed graph construction is under implementation.

## Impact

```powershell
uv run reactive-research impact --help
uv run reactive-research impact SE-210.Definition.4.3
uv run reactive-research impact SE-210.Definition.4.3 --direct
uv run reactive-research impact SE-210.Definition.4.3 --transitive
```

The command surface is available.

Change-impact traversal and revalidation analysis are under implementation.

An affected downstream result is not automatically invalid.

## Snapshot

```powershell
uv run reactive-research snapshot --help
uv run reactive-research snapshot
```

The command surface is available.

Reproducible graph snapshots are under implementation.

## Inspect

```powershell
uv run reactive-research inspect --help
uv run reactive-research inspect SE-210.Definition.4.3
```

The command surface is available.

Research-object inspection and registry-backed explanation are under
implementation.

## Machine-Readable Output

Commands that support structured output use:

```powershell
--format json
```

For example:

```powershell
uv run reactive-research extract --format json
```

An extraction result includes repository provenance, declarations,
diagnostics, and validity state.

## Development

Run repository checks from the repository root:

```powershell
.\sit.ps1

uvx gha-tools autoupdate --pin=all --write .github/workflows

uvx prek update
git add -A
uvx prek run --all-files

uvx zizmor@latest .github/
uvx cffconvert --validate
npx markdownlint-cli2 --fix
```
