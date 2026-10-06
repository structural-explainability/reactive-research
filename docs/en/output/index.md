# Generated Research Views

These views are generated from the current Reactive Research observation of the
research family.

The full detailed research graphs and structured observation are retained.
The smaller views below provide focused entry points for inspection.

## Transformation Neighborhood

This diagram depicts the repositories directly connected to
`se-theory-transformation` in the current Reactive Research observation.

Reactive Research first observes supported relationship evidence across the
research family and builds a repository-level graph.
The evidence may come from sources such as repository declarations,
dependency information, formalization references, and Reactive Research annotations.

For this view, the generator selects `se-theory-transformation` and every
repository connected to it by one recorded relationship in either direction.
All recorded relationship types are eligible for this view.

The diagram therefore shows the immediate context around Transformation:
which repositories are directly related to it and the type of each recorded
relationship.

Only one level of connections is included.
Relationships beyond direct neighbors are not included.

```mermaid
flowchart LR
  %% Typed arrows read source --relation--> target. Dependency impact follows reverse arrows; influence/protection follows forward arrows.
  n0["se-theory-identity-regimes [working e8daf211] / declared 0.3.1 / commit 2026-10-03"]
  class n0 ordinary
  n1["se-theory-interpretive-kernel [working ] / declared 0.4.0"]
  class n1 ordinary
  n2["se-theory-operational-identity [working ] / declared 0.4.0"]
  class n2 ordinary
  n3["se-theory-persistence [working 00faac87] / declared 0.1.0 / commit 2026-10-03"]
  class n3 ordinary
  n4["se-theory-transformation [working 350c7ff0] / declared 0.5.1 / commit 2026-10-05"]
  class n4 ordinary
  n5["mathlib [observed ]"]
  class n5 unresolved
  n0 -->|"depends-on / build / v0.5.1"| n4
  n1 -->|"depends-on / build / v0.5.1"| n4
  n2 -->|"depends-on / build / v0.5.1"| n4
  n3 -->|"depends-on / build / v0.5.1"| n4
  n3 -->|"depends-on / semantic / main"| n4
  n3 -->|"depends-on / build / v4.34.0 / unresolved"| n5
  n4 -->|"depends-on / build / v4.34.0 / unresolved"| n5
  classDef changed fill:#fde68a,stroke:#92400e,stroke-width:3px
  classDef protected fill:#fecaca,stroke:#991b1b,stroke-width:3px
  classDef mechanical fill:#bfdbfe,stroke:#1d4ed8
  classDef semantic fill:#e9d5ff,stroke:#7e22ce
  classDef verification fill:#bbf7d0,stroke:#166534
  classDef unresolved fill:#e5e7eb,stroke:#4b5563,stroke-dasharray:5 5
  classDef ordinary fill:#f8fafc,stroke:#64748b
```

Generated artifacts:

- [Transformation neighborhood Mermaid](transformation-neighborhood.mmd)
- [Transformation neighborhood JSON](transformation-neighborhood.json)

## Transformation Downstream

This diagram depicts repositories that rely on
`se-theory-transformation`, either directly or through another repository.

It is generated from the same repository-level graph as the Transformation
Neighborhood view, but it selects only relationships that indicate downstream
use or dependency.

The included relationship types are:

- `depends-on`
- `implements`
- `formalizes`
- `specifies`
- `tests`
- `pilots`
- `evaluates`
- `derives-from`

The first level contains repositories with one of these recorded relationships
to Transformation.

The second level contains repositories with one of these relationships to a
repository in the first level.

The traversal stops after two levels to keep the diagram limited in scope.

Unlike the Transformation Neighborhood view, this diagram does not include
every recorded relationship around Transformation.
It depicts only the selected relationships
used to trace **downstream reliance**.

```mermaid
flowchart LR
  %% Typed arrows read source --relation--> target. Dependency impact follows reverse arrows; influence/protection follows forward arrows.
  n0["AccountableEntities [working 7cd1bc0f] / declared 0.2.0 / commit 2026-05-30"]
  class n0 ordinary
  n1["accountable-record-py [working bee8c0bd] / commit 2026-05-29"]
  class n1 ordinary
  n2["se-formal-contract [working a93c2eea] / declared 0.2.0 / commit 2026-05-30"]
  class n2 ordinary
  n3["se-theory-identity-regimes [working e8daf211] / declared 0.3.1 / commit 2026-10-03"]
  class n3 ordinary
  n4["se-theory-interpretive-kernel [working ] / declared 0.4.0"]
  class n4 ordinary
  n5["se-theory-operational-identity [working ] / declared 0.4.0"]
  class n5 ordinary
  n6["se-theory-persistence [working 00faac87] / declared 0.1.0 / commit 2026-10-03"]
  class n6 ordinary
  n7["se-theory-structural-explainability [working 6c1d88e9] / declared 0.3.0 / commit 2026-07-25"]
  class n7 ordinary
  n8["se-theory-transformation [working 350c7ff0] / declared 0.5.1 / commit 2026-10-05"]
  class n8 ordinary
  n0 -->|"depends-on / semantic / v1"| n3
  n1 -->|"depends-on / semantic / main"| n2
  n1 -->|"depends-on / semantic / main"| n3
  n2 -->|"depends-on / semantic"| n3
  n2 -->|"depends-on / semantic"| n7
  n3 -->|"depends-on / build / v0.5.1"| n8
  n4 -->|"depends-on / build / v0.5.1"| n8
  n5 -->|"depends-on / build / v0.5.1"| n8
  n6 -->|"depends-on / build / v0.5.1"| n8
  n6 -->|"depends-on / semantic / main"| n8
  n7 -->|"depends-on / build / main"| n3
  n7 -->|"depends-on / semantic"| n3
  classDef changed fill:#fde68a,stroke:#92400e,stroke-width:3px
  classDef protected fill:#fecaca,stroke:#991b1b,stroke-width:3px
  classDef mechanical fill:#bfdbfe,stroke:#1d4ed8
  classDef semantic fill:#e9d5ff,stroke:#7e22ce
  classDef verification fill:#bbf7d0,stroke:#166534
  classDef unresolved fill:#e5e7eb,stroke:#4b5563,stroke-dasharray:5 5
  classDef ordinary fill:#f8fafc,stroke:#64748b
```

Generated artifacts:

- [Transformation downstream Mermaid](transformation-downstream.mmd)
- [Transformation downstream JSON](transformation-downstream.json)

## Full Detailed Research Graphs

The complete drawings are retained for detailed inspection.

- [Full research evolution](evolution.mmd)
- [Full research propagation](propagation.mmd)

## Full Structured Research Data

- [Full observation](observation.json)
- [Repository graph](repository-graph.json)

Regenerate these artifacts from the `reactive-research` repository root:

```powershell
uv run reactive-research generate --root .. --output docs/en/output
```
