# Observation and obligation pilot

Reactive Research now observes existing research surfaces, writes a deterministic
snapshot when explicitly requested, calculates typed obligations, and generates
Mermaid from the same JSON. Observation and analysis do not edit repositories.

## Existing architecture

`extract.py` recognizes source comments and normalizes them through the existing
identifier/declaration models. `declarations.py` exports repository-published
documents. `resolve.py` already aggregated those documents and diagnosed missing
or duplicate definitions. The snapshot, impact and graph modules were CLI stubs.
The specification and registry repositories describe concepts and publication
responsibilities; they are not new databases or lists of participating projects.

This increment retains extraction and local resolution. The text extraction
function is shared with historical observations, and snapshot-backed resolution
now reads the frozen JSON instead of overlaying current filesystem declarations.

## Commands

Run the local checkout with the existing environment and lock file:

```powershell
uv run --no-sync reactive-research snapshot --path .. --format json --output observation.json
uv run --no-sync reactive-research snapshot --path .. --at paper-100-neutral-substrate=v1.0.0 --format json --output before.json
uv run --no-sync reactive-research impact se100.def.FrameworkInvariant --from-snapshot before.json --to-snapshot observation.json --output obligations.md
uv run --no-sync reactive-research graph --snapshot observation.json --view repositories --category evolution --format mermaid --output evolution.mmd
uv run --no-sync reactive-research graph --snapshot observation.json --view repositories --category propagation --format mermaid --output propagation.mmd
uv run --no-sync reactive-research impact se-theory-transformation --snapshot observation.json --format mermaid --output impact.mmd
uv run --no-sync reactive-research resolve se100.def.FrameworkInvariant --snapshot observation.json --format json
```

Keep outputs outside the observed workspace to avoid observing the output of a
previous run as a new input. `--at PROJECT=REV` can be repeated; PROJECT is the
discovered root's relative path (`.` for a single project). Git trees are read
without checkout. `--show FILE` validates a saved snapshot; `--show sha256:HASH
--registry DIR` reads `DIR/HASH.json`. No automatic snapshot store is created.
The explicit `--output` option is the only write in this command pipeline.

The three real acceptance cases can be regenerated with
`uv run --no-sync python examples/acceptance.py --root .. --output EXTERNAL_DIR`.
The example verifies repeated snapshot identity, historical source revisions,
actual downstream edges, freeze bytes at both current and recorded revisions,
documented reconciliation evidence, and unchanged Git HEAD/status across observation.

Without `--from-snapshot`, impact is a caller-selected change scenario. It must
not be reported as an observed new change. With both snapshots, unchanged source
nodes produce no obligations. Missing or ambiguous identities remain diagnostics.

## Observation boundary

Format `reactive-research-observation`, version 1, contains `nodes`, `edges`,
`declarations`, `diagnostics`, and a `sha256:` snapshot identifier. Hashing uses
canonical JSON, deterministic ordering and byte hashes, without run timestamps.
Loading checks both format version and content integrity. The digest includes
the recorded observer version, scope, source states, edges and diagnostics.

Projects are discovered from Git boundaries or existing project markers. Cache
and generated directories are excluded; an independent Git repository named
`site` is still a project. Internal fixtures are not treated as separate projects.
Symlinks are not followed. Git-tracked and eligible untracked working files are
hashed, including non-source artifacts; ignored caches are not research state.

Each project records HEAD, observed source revision, working differences,
working byte identity, source commit time, exact source-revision tags and declared
lifecycle/version where available. `observation: filesystem` is distinguished
from `observation: git-tree`. `observed_revision: working:sha256:…` identifies actual
filesystem bytes, even when a clean checkout also has HEAD provenance. Tags refer
to the committed source revision, never to a dirty working digest. A clean Git
tree or tag is not an assertion that a paper was published or scientifically
validated. Unknown and unborn revisions remain null, not fabricated releases.

Adapters currently read:

- existing `RR.*` annotations using the original extraction rules;
- supported SE manifests and diagnosed legacy variants;
- direct Lake requirements with requested revisions and lock-resolved commits;
- Python runtime requirement strings (installed environments are not observed);
- explicit paper `seN.*` LaTeX labels and theory-reference citation mappings;
- Lean headers explicitly stating which paper identifiers they formalize;
- README motivation paragraphs with explicit repository links, as `informs`;
- established freeze records with exact SHA-256 member commitments.

Labels observed at several locations remain ambiguous. They may be quoted or
inherited paper material; diagnostics do not classify them as research defects.
Lake `.lean` configurations, conditional dependency resolution, transitive Python
locks, publications and arbitrary prose are outside this pilot's adapters.

## Relation direction and impact policy

Arrows read `source --relation--> target`. Thus a consumer `depends-on` its
upstream, a formalization `formalizes` a paper object, and an upstream `informs`
its informed consumer. The motivation adapter reverses the prose's "motivated by"
wording into that natural `informs` direction.

| Relation class | Impact direction | Default | Result |
| --- | --- | --- | --- |
| depends-on, implements, formalizes, specifies, tests, pilots, evaluates, derives-from | reverse | selected | Typed review or verification; may traverse |
| should-revalidate | forward | selected | Verification; may traverse |
| informs, contributes-to, evidences | forward | opt-in | Context notice; terminal |
| cites, revises, supersedes | reverse | opt-in | Provenance review; terminal |
| freezes | forward | opt-in | Protected member; terminal |
| defines | none | excluded | Ownership is not a semantic dependency |

Use repeated `--relation` arguments to select an explicit subset. A build edge
creates verification and separate semantic-review obligations. A pin discrepancy
or an observed SE/Lake visibility omission can add a mechanical candidate.
Intentional historical pins remain valid possibilities; no edit is proposed as
scientifically compulsory. Optional requirements retain their optional status.

Traversal is deterministic, cycle-safe, and records the edge evidence and a
path for each reached obligation. Direct queries do not continue past consumers.
Transitive queries conservatively traverse declared repository-level edges;
this is possible attention, not proof that every downstream claim changed.
Changing an implementation does not automatically mean all objects it defines
changed: ownership edges are deliberately excluded from impact propagation.

Freeze hash members generate protection-boundary notices whenever their owner
is reached. These notices are distinct from traversed dependencies, including
when the owner is reached through an opt-in context edge. They state:

### DO NOT MODIFY FROZEN EVIDENCE

Hash mismatches are recorded while preserving the protection boundary. Analysis
never repairs a freeze, updates theory, runs a study, or marks obligations
scientifically discharged. A newer implementation may require successor work
under a new explicit freeze; it cannot silently rewrite the old commitment.

## Reporting and visualization

Text impact output is a Markdown obligation report. JSON retains changed source
and prior state, consumer state, relation, evidence, constraints, disposition,
distance and path. It distinguishes semantic review, verification required,
mechanical candidate, unresolved and frozen/protected dispositions.

The same `nodes` and `edges` are the D3 boundary: nodes have stable string `id`s;
edges carry string `source`/`target` IDs plus relation, kind, constraints, evidence
and resolution. Give D3 a copy of these records if a force simulation mutates
endpoints. No frontend or external dependency is required for this pilot.

Mermaid evolution and propagation views select relation classes. The repository
projection retains frozen artifact nodes rather than hiding the protection
boundary. Rendering groups identical projected arrows with evidence counts;
the JSON retains every individual evidence edge. Impact colors show source,
protection, mechanical candidates, semantic review and verification, and labels
retain multiple dispositions when a consumer needs several kinds of attention.

## Next increment

Add a small human-authored reconciliation attestation referencing the existing
upstream/consumer content identities and evidence, using the existing declaration
publication model. It should distinguish a documented later response from an
obligation reviewed and discharged against an exact source version. Avoid a new
master registry or automatically inferring scientific agreement from changelogs.
