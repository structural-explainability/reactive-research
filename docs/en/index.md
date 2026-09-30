# Reactive Research

Reactive Research is a research coordination model in which
addressable research objects declare typed semantic relationships,
those relationships form a resolvable versioned graph,
and changes to graph objects generate explicit downstream
revalidation obligations.

The graph makes research relationships, provenance,
and the effects of change visible.

## Core Model

Research objects are first-class graph nodes.

For example:

```text
repository: specification
        |
        | DEFINES
        v
SE-210.Definition.4.3
        ^
        | IMPLEMENTS
        |
repository: verifier
```

Repository-to-repository dependency graphs can be derived from this richer
research-object graph.

## Typed Relationships

Reactive Research preserves the meaning of different relationships.

Initial relationship classes include:

```text
RR.DEFINES
RR.IMPLEMENTS
RR.DEPENDS
RR.INFORMS
RR.EVIDENCES
```

The expanded namespace is also supported:

```text
REACTIVE-RESEARCH.DEFINES
REACTIVE-RESEARCH.IMPLEMENTS
REACTIVE-RESEARCH.DEPENDS
REACTIVE-RESEARCH.INFORMS
REACTIVE-RESEARCH.EVIDENCES
```

Namespaces and relationship names are case-insensitive.

Build dependencies, semantic implementation dependencies,
and informal intellectual relationships must not be collapsed
into one ambiguous dependency list.

## Reactive Research Workflow

Conceptually:

```text
authoritative research source
        ↓
typed declarations
        ↓
research-object contract
        ↓
identifier resolution
        ↓
typed research graph
        ↓
validation
        ↓
versioned snapshot
        ↓
change-impact analysis
        ↓
explicit revalidation obligations
```

An affected downstream result is **not** automatically invalid.
It means its status relative to a changed upstream research object
may need to be established again.

## Command-Line API

The `reactive-research` package provides the reference command-line
implementation.

See [API](api.md) for:

- annotation syntax;
- supported source formats;
- command-line commands;
- machine-readable output; and
- current implementation status.

## Structured Research

Reactive Research is intended for structured research relationships generally.

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

## Structural Explainability Integration

Reactive Research originated within the Structural Explainability research
ecosystem but is intended to remain usable independently.

Related Structural Explainability repositories include:

1. [se-manifest-schema](https://github.com/structural-explainability/se-manifest-schema) — repository manifests and existing graph semantics.
2. [se-theory-reference-kit](https://github.com/structural-explainability/se-theory-reference-kit) — authoritative-source to stable-reference to generated-artifact validation.
3. [se-contract-kit](https://github.com/structural-explainability/se-contract-kit) — declaration, resolution, and validation architecture.
4. [accountable-surface-spec](https://github.com/structural-explainability/accountable-surface-spec) — authority over automated repository changes.
5. [paper-210-operational-identity](https://github.com/structural-explainability/paper-210-operational-identity) — initial `RR.DEFINES` source fixture.
6. [se-verification-operational-identity](https://github.com/structural-explainability/se-verification-operational-identity) — initial `RR.IMPLEMENTS` consumer fixture.
7. [se-theory-structural-assurability](https://github.com/structural-explainability/se-theory-structural-assurability) — formal-theory and reference-surface fixture.

Each existing tool remains authoritative for its own contract surface.

Reactive Research composes those declarations into a broader research graph.

## Project Family

Reactive Research currently consists of:

- [reactive-research-spec](https://github.com/structural-explainability/reactive-research-spec) — normative model;
- [reactive-research-registry](https://github.com/structural-explainability/reactive-research-registry) — resolvable graph and snapshots; and
- [reactive-research](https://github.com/structural-explainability/reactive-research) — executable tooling.
