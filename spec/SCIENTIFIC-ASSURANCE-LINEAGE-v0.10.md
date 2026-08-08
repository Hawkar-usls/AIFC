# Scientific Assurance Lineage v0.10 — SAL v1.11 Derived Semantic Lineage Closure

Status: **DRAFT — execution-lineage candidate only. No new normative authority is created by this document.**

## Frozen design law

SAL v1.11 separates four claims that MUST NOT be collapsed:

\[
ObjectIdentity \neq CanonicalResolution \neq DerivationValidity \neq DerivationAuthority.
\]

The implementation has three architectural contours:

1. **Resolution contour** — exact semantic references resolve to canonical semantic loci.
2. **Derivation-execution contour** — a normalized proof is replayed from canonical leaves to a derived output.
3. **Authority contour** — only a separate authority resolver may decide normative admissibility.

The canonical resolver MUST NOT return an authority decision. The derivation replay engine MUST NOT return an authority decision.

## Occurrence provenance and dependency topology

A derivation has two distinct projections:

\[
OccurrenceManifest(\pi_D) \neq CanonicalDependencyGraph(\pi_D).
\]

The occurrence manifest is recomputed only after normalization under the exact derivation profile. It preserves canonical semantic identity, resolved semantic role, canonical source identity, normalized proof-node path, occurrence index, semantic context, and polarity.

Repeated use is not collapsed in occurrence provenance:

\[
[A,A,B] \neq [A,B].
\]

The canonical dependency graph collapses repeated occurrences only after canonical semantic resolution and is used for transitive cycle detection.

## Canonical semantic-locus resolution

The resolution path is:

\[
SourceBytes \to ExactLocator \to ContextClosure \to CanonicalIdentity \to CanonicalRole \to AuthorityScopeEvidence.
\]

`AuthorityScopeEvidence` is evidence only. It is not an authority decision.

The following are forbidden:

- successor-defined canonical identities accepted without replay from exact source bytes and exact locus;
- deterministic tie-breaking of ambiguous semantic resolution;
- promotion of every locus inside an authoritative container to normative authority;
- authority status self-assertion by the resolver profile.

## Derivation replay

The profile binds rule semantics, normalization semantics, leaf extraction semantics, context projection semantics, output semantics, logical fragment, ambiguity policy, unsupported-construct policy, and exact replay-engine implementation identity.

Any derivation-semantics change requires a new profile identity.

The verifier independently requires:

\[
DeclaredOccurrenceManifest = RecomputedOccurrenceManifest(Normalize_R(\pi_D)).
\]

It also requires exact binding of output question, atom, semantic identity, and role.

Dependency acyclicity is checked over resolved canonical semantic identities, not submitted aliases.

## Authority separation

The replay engine has only:

`VALID`, `INVALID`, `BLOCKED`.

The canonical resolver has only:

`RESOLVED`, `AMBIGUOUS`, `UNRESOLVED`.

Only the separate semantic authority contour may return an authority decision.

A valid derivation does not imply authority. Authority must close over the canonical leaves, the canonicalization jurisdiction, the inference rule, and the derived-object authority lineage.

## Frozen laws

**Named sources do not constitute a derivation.**

**A replayable derivation does not constitute authoritative semantics.**

**Semantic authority must close over both the leaves and the inference rule.**

**Canonicalization itself cannot silently acquire semantic jurisdiction.**

**Authority of a semantic container does not automatically confer authority on every locus it contains.**

## Intended v1.11 terminal

A successful v1.11 implementation may establish execution-lineage reconstruction in tested candidate scope while retaining:

`CANONICAL_SEMANTIC_RESOLVER_AUTHORITY = NOT_ESTABLISHED_SUCCESSOR_CANDIDATE`

`BRIDGE_DERIVED_DERIVATION_PROFILE_AUTHORITY = NOT_ESTABLISHED_SUCCESSOR_CANDIDATE`

`DERIVED_SEMANTIC_AUTHORITY = BLOCKED`

`SOLVER_INVOCATION_COUNT = 0`

This asymmetry is intentional and is the claim ceiling of SAL v1.11.
