# Scientific Assurance Lineage v0.12 — Derived Semantic Lineage Edge Universe Closure

Status: **SAL v1.11u successor-candidate hardening specification**.

This document preserves the exact SAL v1.11h milestone. It does not reinterpret
or invalidate the v1.11h nine-edge receipt. It adds a stricter question:

> How was the set of edges that must be checked obtained?

## Frozen law

**A verified graph is not a complete lineage until the required edge universe is
itself independently derived.**

Equivalently:

```text
DeclaredEdgeSetExactness != RequiredEdgeUniverseCompleteness
VerifiedVertices          != CompleteLineage
```

A successor cannot establish that no required edge was omitted merely by
declaring an edge list and then proving that its receipt contains every member
of that same list.

## Scope

SAL v1.11u deliberately freezes a narrow theorem. It derives the complete
**cross-vertex exact-identity-reference universe relative to the already bound
six-vertex v1.11h scope**:

```text
PROFILE
PROOF
MANIFEST
GRAPH
DERIVED
QUESTION
```

This is not a proof that those six vertices are the complete global lineage
vertex universe. The v1.11 derivation profile itself references a resolver
profile, and proof/derived objects reference semantic-reference objects outside
this six-vertex set. Therefore:

```text
LINEAGE_VERTEX_UNIVERSE_COMPLETENESS
= NOT_ESTABLISHED
```

The theorem also does not claim completeness of every possible semantic
relation that may be represented by transformations rather than exact identity
references:

```text
LINEAGE_SEMANTIC_RELATION_UNIVERSE_COMPLETENESS
= NOT_ESTABLISHED
```

## Machine derivation

The production derivation accepts no `EDGE_SPECS`, `REQUIRED_EDGE_IDS`, or
caller-supplied edge list.

1. Rebuild the exact v1.11h vertices from their bytes.
2. Use each vertex's already-bound identity channels:
   object ID, whole-object content hash where present, and semantic-projection
   hash where present.
3. If a vertex has a top-level `semantic_identity`, include that value as its
   semantic identity alias. In the current scope this is the v1.11 derived
   output identity.
4. Recursively traverse every string leaf of every bound source vertex.
5. Whenever a source string equals an exact identity channel of a different
   bound vertex, emit a relation occurrence with its JSON pointer and matched
   target identity channel(s).
6. Group occurrences by source/target vertex pair and sort canonically.
7. Hash the machine-derived universe and the resulting whole lineage graph.
8. Compare the receipt to the recomputed result.

The required universe is therefore an output of the verifier, not an input
chosen by the receipt.

## Current exact-instance consequence

For the exact v1.11h six-vertex instance, machine derivation yields 15 distinct
source/target pairs. The historical v1.11h nine declared pairs are a strict
subset. Six additional relations are discovered:

```text
PROFILE_TO_QUESTION
PROOF_TO_QUESTION
MANIFEST_TO_QUESTION
DERIVED_TO_QUESTION
GRAPH_TO_DERIVED
PROOF_TO_DERIVED
```

`PROOF_TO_QUESTION` carries two independent source occurrences: the proof's
top-level question context and the derivation conclusion question context.

`PROOF_TO_DERIVED` is not manually declared. It is discovered because the
derivation conclusion's `semantic_identity` equals the exact derived object's
top-level `semantic_identity`.

## Question-context closure

SAL v1.11h's exact current receipt was content-bound and correct, but its
generic edge verifier did not explicitly compare the binding object's
top-level `entailment_question_id` to the exact QUESTION vertex. The old audit
had the analogous generic omission.

SAL v1.11u adds explicit fail-closed invariants:

```text
source_binding.entailment_question_id == QUESTION.object_id
source_audit.entailment_question_id   == QUESTION.object_id
universe_receipt.entailment_question_id == QUESTION.object_id
universe_audit.entailment_question_id   == QUESTION.object_id
```

These checks do not mutate the v1.11h schemas or historical objects.

## Attack corpus

The following are distinct attacks:

```text
LINEAGE_REQUIRED_EDGE_UNIVERSE_OMISSION
LINEAGE_REQUIRED_EDGE_UNIVERSE_INJECTION
LINEAGE_BINDING_QUESTION_CONTEXT_REBINDING
LINEAGE_AUDIT_QUESTION_CONTEXT_REBINDING
LINEAGE_UNIVERSE_QUESTION_CONTEXT_REBINDING
LINEAGE_UNIVERSE_AUDIT_QUESTION_CONTEXT_REBINDING
SUCCESSOR_DEFINED_REQUIRED_EDGE_UNIVERSE_REBINDING
```

The first attack differs from the v1.11h receipt-omission attack. Here the
attacker attempts to make a self-consistent receipt whose *definition of the
required universe* has silently forgotten an otherwise discoverable relation.
The verifier rejects it because the universe is recomputed from exact vertex
content.

## Authority ceiling

Edge-universe derivation is an execution-lineage identity result only.

It does not establish:

```text
CANONICAL_SEMANTIC_RESOLVER_AUTHORITY
BRIDGE_DERIVED_SOURCE_AUTHORITY_RESOLUTION
BRIDGE_DERIVED_DERIVATION_PROFILE_AUTHORITY
BRIDGE_DERIVED_AUTHORITY_LINEAGE_REPLAY
DERIVED_SEMANTIC_AUTHORITY
AUTHORITY_CLOSED_FINITE_INDUCTION
IMPLEMENTATION_A_PASS
AIFC_V1_FROZEN
PLATFORM_TRUST_PROVEN
SAL_GLOBAL_NOVELTY
```

The entailment solver remains uninvoked.

## Release-gate integration

SAL v1.11u is a hardening layer over the existing execution-lineage boundary.
The 122 -> 143 release frontier remains inherited unchanged. This cycle does not
renumber the release gate merely to create a milestone.
