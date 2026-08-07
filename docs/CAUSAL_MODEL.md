# Machine-Readable Causal Model

Status: `NORMATIVE DRAFT`

AIFC uses causal isolation as an evidence gate, so the causal model cannot remain only prose or a diagram.

Every independent-future experiment MUST publish a versioned `AIFC/causal-model/v1` object conforming to [`../schemas/causal-model.schema.json`](../schemas/causal-model.schema.json).

## Required content

The model declares:

- all named causal nodes relevant to PRE_RETURN and target generation;
- observed and latent/common-cause nodes admitted by the threat model;
- directed edges and mechanism classes;
- which variables are available before target generation;
- variables conditioned on by the analysis;
- required d-separation statements;
- variables on which conditioning is forbidden because it would create selection/collider bias;
- explicit assumptions and model-completeness status.

## Core structural query

The strongest AIFC causal-isolation grade requires a declared query equivalent to:

```text
PRE_RETURN_HARD ⟂d TARGET_HARD | ALLOWED_PUBLIC_METADATA
```

inside the frozen DAG.

A direct-path-only test is insufficient. A shared latent parent can create dependence without a directed path from target to PRE_RETURN or from PRE_RETURN to target.

## Selection variables

Any variable influenced by both PRE_RETURN and target/outcome status — for example `selected_for_analysis` — MUST be marked as a selection variable and MUST NOT be conditioned on unless the protocol explicitly proves that doing so cannot manufacture dependence.

## Machine checks required before v1.0 FROZEN

The independent verifier MUST:

1. reject duplicate node identifiers and unknown edge endpoints;
2. verify the graph is acyclic for the declared forward-causal null model;
3. independently evaluate every required d-separation query;
4. reject conditioning on forbidden selection variables;
5. bind the exact causal-model digest into the PRE_RETURN/evidence bundle;
6. report `BLOCKED_INCOMPLETE` when the declared model omits a required threat-model state;
7. never translate d-separation success into a claim that the physical causal graph is proven complete.

## Physical completeness boundary

A DAG is a declared causal model, not direct proof that no unmodeled physical or procedural channel exists.

Passing the structural gate therefore means:

```text
INDEPENDENCE_IS_STRUCTURALLY_SUPPORTED_UNDER_DECLARED_MODEL
```

not:

```text
ALL_POSSIBLE_PHYSICAL_COMMON_CAUSES_HAVE_BEEN_PROVEN_ABSENT
```

External audit, hardware/process isolation, and entropy evidence remain separate gates.
