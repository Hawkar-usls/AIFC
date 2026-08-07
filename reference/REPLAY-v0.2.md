# Verifier A Replay v0.2

Status: **development replay implementation / not full Implementation A**

This document maps the PR #5 code paths while the draft implementation is being hardened.

## Authoritative development entry point

```text
reference/verifier/aifc_verify_v02.py
```

Intended composition:

```text
strict JSON input
    ↓
EvidenceResolverV02
    ↓
experiment-plan preregistration gate
    ↓
entropy-policy admission gate
    ↓
resolver-driven replay engine
    ↓
AIFC/verifier-result/v1
```

## What v0.2 is designed to recompute

The current codebase contains executable logic for:

- exact evidence-byte resolution and domain-separated rehashing;
- experiment-plan identity and experiment-scoped preregistration quorum structure;
- first-CREATED prerequisite binding;
- deterministic ledger genesis and fixed-horizon ledger replay;
- candidate-set members and multiplicity;
- candidate-generation provenance and post-CREATED choice rejection;
- pre-return bindings;
- target-selector fixed-event replay;
- pre-target conditioning-view bindings;
- entropy-policy/profile source/method/evidence binding;
- canonical rational probability structure;
- raw-source target derivation using a strict typed framing DSL;
- registry fault-model and failure-domain structural checks;
- connected registry-transition structure;
- causal edge/no-edge evidence resolution;
- per-trial bundle / terminal choreography;
- publication-manifest completeness structure.

## What v0.2 explicitly does not establish

```text
ED25519_SIGNATURE_CRYPTO
CAUSAL_D_SEPARATION
TARGET_SOURCE_CRYPTOGRAPHIC_PROOF
FULL_EXPERIMENT_STATISTICAL_REPLAY
ANYTIME_EPROCESS_REPLAY
BYTE_IDENTICAL_CANONICALIZATION_WITH_IMPLEMENTATION_B
FROZEN_MACHINE_READABLE_CORPUS
INDEPENDENT_IMPLEMENTATION_B
FULL_RELEASE_MANIFEST_EVIDENCE_RESOLUTION
EXTERNAL_PUBLIC_BEACON_BENCH
```

Therefore a green v0.2 replay means that the implemented evidence-admission logic survived the declared development tests. It is **not** `IMPLEMENTATION_A_PASS` and is not physical evidence.

## Compatibility modules during PR #5

Because protocol-object schemas are still moving under review, PR #5 temporarily preserves earlier tested modules and adds versioned compatibility layers (`canonical_v02`, `resolver_v02`, preregistration composition) rather than silently changing the semantics beneath old tests.

This duplication is intentional during the draft review. A later cleanup PR should consolidate the authoritative path after the v0.2 semantics are stable and the test corpus has been frozen.

Copies or wrappers around the same decision logic do not count as Implementation B.

## Fail-closed principle

For each new protocol field, the engineering question is:

> What is the smallest false statement in one JSON object that could still cause the verifier to accept something it should have recomputed?

Every such case should become a deterministic rejection path and a frozen adversarial vector before v1.0.
