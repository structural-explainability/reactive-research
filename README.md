# Reactive Research Tools

> Tools for building, validating, resolving, and querying Reactive Research graphs.

`reactive-research` is the reference command-line implementation for Reactive Research.

It extracts research-object declarations, validates relationships, resolves identifiers against registries, builds typed research graphs, and identifies downstream research affected by upstream changes.

## Quick Start

Run directly from PyPI with `uvx`:

```shell
uvx reactive-research --help
```

The distribution and command name intentionally match the repository name:

```text
reactive-research
```

The Python package name is:

```text
reactive_research
```

## What It Does

Reactive Research Tools is intended to support workflows such as:

```text
source annotations
      ↓
extract
      ↓
research-object contract
      ↓
resolve identifiers
      ↓
typed research graph
      ↓
validate
      ↓
snapshot
      ↓
change-impact analysis
```

The tools should make cross-repository research relationships machine-checkable without requiring each repository to clone every other repository.

## Research Object Extraction

Repositories may declare addressable objects and relationships close to their authoritative source.

Examples include:

```text
DEFINES: SE-210.Definition.4.3
IMPLEMENTS: SE-210.Theorem.5.2
```

The extractor converts supported annotations into normalized machine-readable declarations.

Humans declare the relationship once.

Generated manifests, registry records, and graph edges should be derived from that authoritative declaration rather than manually duplicated.

## Typed Relationships

Reactive Research preserves the meaning of different relationships.

Initial relationship classes include:

```text
DEFINES
IMPLEMENTS
DEPENDS
INFORMS
EVIDENCES
```

Build dependencies, semantic implementation dependencies, and informal intellectual relationships must not be collapsed into one ambiguous dependency list.

## Resolution

The resolver checks references against a versioned Reactive Research Registry snapshot.

For example:

```text
repository B
IMPLEMENTS SE-210.Definition.4.3
```

should resolve to the authoritative definition record for that identifier.

Resolution should verify provenance including the relevant repository and revision information.

## Validation

Validation can detect conditions such as:

- unresolved identifiers;
- duplicate authoritative definitions;
- stale generated declarations;
- invalid relationship types;
- incompatible schema versions;
- malformed research identifiers;
- missing provenance;
- forbidden graph structures; and
- relationships requiring revalidation.

Validation rules should remain relationship-specific.

Not every graph is required to be acyclic.

## Graph Construction

The tool builds a typed graph in which research objects remain first-class nodes.

Example:

```text
repo: specification
        |
        | DEFINES
        v
Definition.4.3
        ^
        | IMPLEMENTS
        |
repo: verifier
```

Repository dependency graphs are derived views over this richer graph.

## Change Impact

Given a changed research object, the tool can identify directly and transitively affected downstream objects.

Conceptually:

```shell
uvx reactive-research impact SE-210.Definition.4.3
```

A future impact report may distinguish:

```text
changed
affected
revalidation-required
revalidated
unresolved
superseded
```

Being affected does not mean a downstream result is false.

It means its current status against the changed upstream object has not yet been established.

## Graph Snapshots

The tool should support reproducible graph snapshots containing:

- participating objects;
- repository revisions;
- relationship edges;
- registry version;
- extractor version;
- validation results; and
- a stable snapshot identifier or hash.

This allows a research artifact to record the graph state against which it was established.

## Repository Integration

Reactive Research Tools is designed to work with existing research infrastructure rather than replacing it.

Within Structural Explainability this includes:

- `se-manifest-schema`;
- `se-theory-reference-kit`;
- `se-contract-kit`;
- `accountable-surface-spec`; and
- participating research repositories.

Each existing tool remains authoritative for its own contract surface.

Reactive Research Tools composes those declarations into a broader research graph.

## Automation and Authority

Automation must not silently convert technical capability into authority.

Repository-local automation may operate in modes such as:

```text
check
propose
write
```

The permitted mode should come from the repository's authority declarations where such governance metadata exists.

For Structural Explainability repositories, protected-surface decisions should remain governed by `accountable-surface-spec`.

## Beyond Software Research

Reactive Research Tools is intended for structured research relationships generally.

Examples include:

### Science

```text
hypothesis
→ experimental design
→ dataset
→ analysis
→ evidence
→ claim
```

### Law

```text
constitution / statute / regulation
→ case
→ holding
→ interpretation
→ legal claim
→ decision
```

### Policy

```text
evidence
→ assumptions
→ policy analysis
→ recommendation
→ decision
→ evaluation
```

### Engineering

```text
requirement
→ design
→ implementation
→ verification
→ evidence
→ assurance claim
```

The graph does not decide what is true or what decision should be made.

It makes the dependencies and effects of change visible.

## Project Family

Reactive Research consists initially of:

- `reactive-research-spec` — normative model;
- `reactive-research-registry` — resolvable graph and snapshots;
- `reactive-research` — executable tooling.

## Status

Early development.

The initial implementation is being exercised against an existing multi-repository research program before broader interoperability claims are made.

## License

See [LICENSE](./LICENSE).
