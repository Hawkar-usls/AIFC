# Scientific Assurance Lineage v0.13 — Lineage Vertex Universe Reference Closure

Status: **SAL v1.12 successor-candidate hardening specification**.

This layer preserves the exact SAL v1.11u milestone at
`b71ee1d6606dd41fcf24346e324c56e4407fd537`. It does not reinterpret or
invalidate the v1.11u machine-derived edge universe. It asks the next question:

> How was the set of vertices over which edge completeness was derived obtained?

## Frozen laws

**A lineage vertex universe is reference-closed only when every resolvable
reference is recursively expanded to an exact identified vertex until a
machine-verified fixed point is reached.**

**A fixed point of reference closure is not proof that the seed or the
reference semantics exhaust global lineage relevance.**

Equivalently:

```text
EdgeUniverseCompleteness(V) != VertexUniverseReferenceClosure(V)
ReferenceClosure(V0)        != GlobalLineageCompleteness
```

## Mathematical target

Let `C` be the exact predecessor commit and `T = ExactTree(C)`. Let `Pi_I` be a
content-identified candidate object-index/reference-classification profile.

```text
I       = Index(T, Pi_I)
V0      = vertices recovered from the inherited v1.11h binding receipt
F_I(V)  = V union UniqueResolve_I(ReferenceCandidates(V))
V*      = lfp(F_I)
```

Required postconditions are:

```text
V0 subseteq V* subseteq I
UniqueResolve_I(ReferenceCandidates(V*)) subseteq V*
```

The second condition is replayed after the worklist terminates. An empty
worklist alone is not accepted as proof of fixed point.

## Exact-tree object index

Production code does not accept `AVAILABLE_OBJECTS`, `VERTEX_SPECS`,
`REQUIRED_VERTICES`, `MAX_DEPTH`, `MAX_ROUNDS`, or `MAX_RECURSION`.

The candidate index implementation:

1. verifies the exact predecessor tree SHA;
2. recursively enumerates `conformance/` from that exact Git tree;
3. reads exact blobs with Git object identity;
4. strict-parses JSON;
5. recognizes only schemas named by the content-bound object-index profile;
6. recomputes each recognized type's whole-object content identity where the
   type defines one;
7. builds target identity channels from the indexed exact objects.

This establishes only:

```text
REPOSITORY_OBJECT_INDEX_COMPLETENESS
= ESTABLISHED_ONLY_RELATIVE_TO_EXACT_TREE_AND_RECOGNIZED_OBJECT_PROFILE
```

It does **not** establish global adequacy of `Pi_I`.

## Reference classification

Reference classification is fixed before resolution outcome. Current classes:

```text
REQUIRED_INTERNAL_OBJECT_REFERENCE
OPTIONAL_INTERNAL_OBJECT_REFERENCE
EXTERNAL_REFERENCE
NON_OBJECT_IDENTITY_OCCURRENCE
```

For a required internal reference:

```text
0 exact targets  -> BLOCKED_UNRESOLVED_LINEAGE_VERTEX_REFERENCE
>1 exact targets -> BLOCKED_AMBIGUOUS_LINEAGE_VERTEX_REFERENCE
```

No deterministic tie-break is authority.

The current candidate reference semantics intentionally cover exact repository
object references used by the v1.11 derived-lineage machinery. They do not
claim to recognize every possible semantic relation.

## Fixed point and monotonicity

The implementation is monotone: discovered vertices are never removed.
With finite exact-tree index `I`, productive expansion terminates without a
magic recursion/depth bound.

BFS and DFS must yield the same canonical final vertex universe and canonical
discovery-occurrence manifest. Traversal order may differ; semantic identity of
the result may not.

## Current exact-instance witness

From the inherited six v1.11h vertices, the current candidate is expected to
recursively discover, among others:

```text
AIFC-CANONICAL-SEMANTIC-RESOLVER-PROFILE-v1.json
AIFC-CANONICAL-SEMANTIC-REFERENCE-A-v1.json
AIFC-CANONICAL-SEMANTIC-REFERENCE-B-v1.json
AIFC-PREDECESSOR-SEMANTIC-FORMULA-v1.json
AIFC-TARGET-SEMANTIC-FORMULA-v1.json
```

These values are not a successor-provided required-vertex list. They are
expected current-instance witnesses and must be rediscovered by production
closure from exact predecessor bytes.

## Attack corpus

```text
LINEAGE_REQUIRED_VERTEX_UNIVERSE_OMISSION
LINEAGE_VERTEX_REFERENCE_TARGET_REBINDING
LINEAGE_VERTEX_REFERENCE_TARGET_AMBIGUITY
LINEAGE_VERTEX_REFERENCE_TARGET_UNRESOLVED
LINEAGE_VERTEX_DISCOVERY_SUPPRESSION
LINEAGE_VERTEX_DISCOVERY_INDEX_INJECTION
LINEAGE_VERTEX_DISCOVERY_INDEX_OMISSION
LINEAGE_VERTEX_FIXED_POINT_FALSE_TERMINATION
LINEAGE_VERTEX_CONTENT_IDENTITY_REBINDING
LINEAGE_VERTEX_QUESTION_CONTEXT_REBINDING
REPOSITORY_OBJECT_INDEX_PROFILE_REBINDING
REPOSITORY_OBJECT_RECOGNITION_SUPPRESSION
REPOSITORY_OBJECT_INDEX_TREE_OMISSION
REPOSITORY_OBJECT_INDEX_TREE_INJECTION
REPOSITORY_OBJECT_INDEX_PATH_REBINDING
REPOSITORY_OBJECT_INDEX_OBJECT_ID_REBINDING
REPOSITORY_OBJECT_INDEX_CONTENT_IDENTITY_REBINDING
LINEAGE_VERTEX_CLOSURE_NONMONOTONE_REMOVAL
UNRESOLVED_INTERNAL_REFERENCE_TO_EXTERNAL_RECLASSIFICATION
LINEAGE_VERTEX_DISCOVERY_ORDER_DEPENDENCE
LINEAGE_VERTEX_DISCOVERY_OCCURRENCE_OMISSION
LINEAGE_VERTEX_DISCOVERY_OCCURRENCE_REBINDING
```

## Claim ceiling

Even a successful v1.12 result establishes only reference closure from the
inherited seed under the candidate recognized-object/reference profile.

It does not establish:

```text
GLOBAL_LINEAGE_SEED_COMPLETENESS
OBJECT_INDEX_PROFILE_GLOBAL_ADEQUACY
GLOBAL_REPOSITORY_OBJECT_UNIVERSE_COMPLETENESS
LINEAGE_SEMANTIC_RELATION_UNIVERSE_COMPLETENESS
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

This is a hardening layer over the existing 122 -> 143 execution-lineage
frontier. The release gate remains inherited unchanged; no decorative
renumbering is introduced.
