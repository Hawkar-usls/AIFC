# Scientific Assurance Lineage v0.2 — Root Closure

Status: research formalization candidate. This document is an additive successor to `SCIENTIFIC-ASSURANCE-LINEAGE-v0.1.md`; v0.1 remains historical and unchanged.

## Root-closure problem

SAL v0.1 established that conclusion-authorizing semantics require lineage. SAL v0.2 closes the next recursive trust boundary:

```text
normative document
    <- normative resolver
    <- normative registry
    <- registry content identity
    <- predecessor exact-main evidence / lineage
```

Replacing a caller-supplied normative document with a caller-supplied resolver does not remove authority injection.

> A resolver cannot confer authority unless the resolver's own source of authority is itself resolved.

Equivalently:

> A normative resolver is not authoritative merely because it implements the normative-resolver interface.

## Root Closure Law

A normative object `x` is admissible through resolver `R` only if all of the following hold:

1. `R` is selected by the verifier's own versioned semantics, not by the claimant.
2. `R` loads a fixed registry identity `G`, not a caller-selected registry or registry path.
3. the exact bytes of `G` resolve to the content identity bound by `R`;
4. `G` identifies its predecessor registry by content identity and exact predecessor main commit;
5. the record for `x` binds artifact ID, kind, schema, path and exact content identity;
6. the record's authority state is executed, not merely recorded;
7. `HISTORICAL_ROOT_AT_PREDECESSOR_COMMIT` binds to the exact predecessor root;
8. `ATTESTED_SUCCESSOR_AT_COMMIT` resolves a content-identified exact-commit authority receipt;
9. `SUCCESSOR_CANDIDATE_REQUIRES_EXACT_COMMIT_ATTESTATION` is rejected as normative;
10. authority receipts cannot authenticate a different source commit by rebinding metadata.

Therefore:

```text
ValidObjectBytes
AND ValidRegistryRecord
AND ValidResolverImplementation
```

is still insufficient unless:

```text
ValidRootRegistryIdentity
AND ExecutableAuthorityState
AND ValidAuthorityEvidence
```

also hold.

## New attack classes

SAL v0.2 freezes the following attack vocabulary:

```text
NORMATIVE_RESOLVER_INJECTION
CALLER_SUPPLIED_ROOT_REGISTRY
NORMATIVE_ROOT_REGISTRY_REBINDING
SELF_ASSERTED_BOOTSTRAP_ROOT_REGISTRY
UNATTESTED_SUCCESSOR_NORMATIVE_PROMOTION
SAL_ISSUED_SCHEMA_ID_UNREGISTERED
INHERITED_HASH_PROFILE_IMPLEMENTATION_DRIFT
```

## Schema identity closure

An issued SAL protocol schema must not remain outside the versioned schema-identity graph. The v1.3 reference implementation introduces a v3 delta registry that preserves v2 and binds every newly registered SAL schema to:

```text
schema_id
source_path
Git blob SHA-1
raw source SHA-256
JSON Schema dialect
```

Registration does not itself prove global historical first appearance. It prevents future acceptance-language mutation under the same already-issued schema identifier in the tested successor scope.

## Inherited hash implementation closure

The historical hash domain remains unchanged:

```text
AIFC:INHERITED-GATE-OBLIGATION-SET:v1 || 0x00
```

SAL v0.2 does not rewrite `AIFC-INHERITED-GATE-HASH-PROFILE-v1.json`. Instead, an additive implementation-binding object identifies the exact canonicalizer and exact hash implementation source bytes. A change to those source identities requires a new binding/lineage decision; it cannot hide behind the descriptive canonicalization label.

## Authority-state transition

The reference state machine is:

```text
SUCCESSOR_CANDIDATE_REQUIRES_EXACT_COMMIT_ATTESTATION
        | exact receipt resolved and commit-bound
        v
ATTESTED_SUCCESSOR_AT_COMMIT
        | lineage policy accepts use as a normative predecessor
        v
future normative root / historical predecessor
```

The v1.3 branch implements the first executable boundary: an unattested candidate cannot be returned by normative resolution. General normative-root lineage remains a theorem/engineering target and is not claimed established.

## Monotonicity record v4

`AIFC/assurance-monotonicity-record/v4` adds explicit identities for:

```text
normative_root_registry_id
normative_root_registry_git_blob_sha1
predecessor_normative_root_registry_id
predecessor_normative_root_registry_git_blob_sha1
predecessor_exact_main_commit
authority_status_enforced
resolver_provenance_closed
```

This addresses the v3 gap where only a registry name and bootstrap-commit assertion were carried forward.

## Claim ceiling

SAL v0.2 Root Closure does **not** establish:

```text
GENERAL_NORMATIVE_ROOT_LINEAGE
GATE_DEFINITION_HISTORICAL_ANCHOR
GATE_ATOM_SEMANTIC_IDENTITY
AUTHORITY_CLOSED_PROOF_GENERAL
REAL_SUCCESSOR_WRAPPED_REPLAY
HISTORICAL_KEY_LIFECYCLE
IMPLEMENTATION_A_PASS
AIFC_V1_FROZEN
PLATFORM_TRUST_PROVEN
SAL_GLOBAL_NOVELTY
```

The v1.3 release frontier remains `DRAFT_NOT_SATISFIED` until its successor-candidate bytes receive exact post-merge evidence and the remaining inherited release requirements are satisfied.
