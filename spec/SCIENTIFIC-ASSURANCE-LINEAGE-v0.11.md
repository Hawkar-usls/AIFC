# Scientific Assurance Lineage v0.11 — v1.11h Derived Semantic Lineage Edge Binding

Status: **draft hardening supplement**.

This layer does not change the v1.11 semantic-authority ceiling. It hardens the
execution lineage by proving that the exact content-identified vertices
`P, π, M, G, D, Q` are connected by the exact relations actually traversed by
replay.

## Frozen law

> **A proof-carrying lineage must bind its edges, not only its vertices.**

Equivalently:

\[
\text{Vertex identity} \neq \text{Edge identity},
\qquad
\text{Verified vertices} \neq \text{Verified graph}.
\]

A semantic projection hash is not a whole-object identity:

\[
SemanticProjectionIdentity(X)\neq WholeObjectIdentity(X).
\]

For v1.11h, an exact vertex is bound by schema ID, object ID, Git blob SHA-1,
raw SHA-256, whole-object protocol content hash when one exists, and a separate
semantic-projection hash when one exists.

## Required lineage edge universe

The edge universe is exact and non-successor-selectable:

1. proof → derivation profile;
2. proof → canonical leaf manifest;
3. proof → canonical dependency graph;
4. manifest → derivation profile;
5. dependency graph → issued entailment question;
6. derived object → derivation profile;
7. derived object → derivation proof;
8. derived object → canonical leaf manifest;
9. derived object → canonical dependency graph.

Omission or injection of an edge is blocking.

## Edge binding

For every edge the verifier resolves the target to its exact whole-object byte
identity and independently checks every reference field already present in the
source object. Where the source declares only a semantic projection hash, the
edge receipt additionally binds the full resolved target object.

Thus a correct leaf-manifest projection cannot be used as a substitute for a
different full manifest object, and a correct full object cannot be attached
through a false semantic-projection reference.

The dependency graph is additionally bound directly to the exact issued
question:

\[
G.entailmentQuestionID=\pi.entailmentQuestionID=D.entailmentQuestionID=Q.
\]

## Content-addressed lineage graph

The verifier deterministically recomputes the required ordered edge evidence
and hashes it under:

`AIFC:DERIVED-SEMANTIC-LINEAGE-EDGES:v1`.

It then hashes the exact vertex identities together with those exact edges
under:

`AIFC:DERIVED-SEMANTIC-LINEAGE-GRAPH:v1`.

This establishes a content-addressed execution lineage graph `(V,E)` in the
tested scope.

## Authority ceiling

v1.11h is an execution-lineage hardening only.

It does **not** establish canonical-resolver authority, source semantic
authority, derivation-profile authority, derived semantic authority,
authority-closed finite induction, Implementation A PASS, AIFC v1 freeze,
platform trust, or global novelty.

The entailment solver remains uninvoked while inherited semantic-authority
blockers remain present.

Current v1.11 release-gate numbering `122 → 143` is inherited unchanged by this
hardening supplement; the new edge attacks are part of the proof-carrying
test corpus and must remain closed before any future freeze.
