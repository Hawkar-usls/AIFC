# AIFC Reference Implementation

Status: **planned / not yet frozen**.

This directory will contain the standalone AIFC verifier and supporting implementation code. The normative draft schemas live at repository root under [`../schemas/`](../schemas/).

The reference implementation must not depend on Genesis for scientific admission.

## Design requirements

The verifier must independently:

- parse only versioned machine-readable evidence;
- enforce the frozen canonicalization profile;
- recompute domain-separated hashes and the deterministic experiment-genesis predecessor;
- validate the experiment-wide trial ledger and reject gaps/forks/selective deletion;
- enforce the trial state machine and abort semantics;
- validate candidate-generation provenance and fail closed on unbounded shadow-candidate selection freedom;
- enumerate/charge candidate multiplicity rather than trust a declared count;
- validate the proof-carrying entropy profile and canonical exact-rational `p_i` bound;
- explicitly handle `a_i = 0` without division-by-zero behavior;
- bind the entropy claim to the complete conditioning-view hash and target-derivation profile;
- freeze and recompute target derivation from the raw source object, not from producer-supplied final bytes alone;
- parse the causal DAG and independently evaluate required d-separation queries;
- reject forbidden collider/post-selection conditioning;
- verify witness registry state, key validity, rotation/revocation/compromise handling;
- verify typed individual witness receipts and quorum safety under the declared `(n,f,q)` model;
- validate every witness-registry reconfiguration by joint old-quorum authorization and new-quorum acceptance;
- verify freshness/continuity bindings outside the experiment rollback domain;
- distinguish provenance from unpredictability;
- treat wall-clock timestamps as metadata unless a valid external timing profile applies;
- compute the preregistered e-process or fixed-horizon statistic;
- verify proof-carrying release manifests before any frozen-release admission;
- emit deterministic failure codes;
- fail closed on missing or contradictory evidence;
- never emit `RETROCAUSALITY_PROVED`.

## Draft protocol objects

Current draft schemas include:

```text
schemas/
├── hard-witness.schema.json
├── pre-return-certificate.schema.json
├── trial-ledger-event.schema.json
├── candidate-generation-profile.schema.json
├── entropy-profile.schema.json
├── target-derivation-profile.schema.json
├── causal-model.schema.json
├── witness-registry.schema.json
├── witness-receipt.schema.json
├── quorum-certificate.schema.json
├── registry-transition-certificate.schema.json
├── target-evidence.schema.json
├── evidence-bundle.schema.json
├── verifier-result.schema.json
└── release-manifest.schema.json
```

These schemas are draft interfaces. Their existence is not evidence that the standalone verifier has already implemented them correctly.

## First red-team frontier

The first executable verifier should be attacked in this order:

```text
SHADOW_CANDIDATE_POOL
        ↓
REGISTRY_RECONFIGURATION_FORK
        ↓
POST_HOC_TARGET_DERIVATION
        ↓
NONCANONICAL_RATIONAL_BOUND
```

A verifier that cannot reject these four classes is not ready to claim end-to-end evidence admission.

## Planned implementation layout

```text
reference/
├── README.md
└── verifier/
    ├── aifc_verify.py
    ├── canonicalization.py
    ├── ledger.py
    ├── candidate_provenance.py
    ├── entropy.py
    ├── target_derivation.py
    ├── causal.py
    ├── witnesses.py
    ├── release_manifest.py
    └── statistics.py
```

## Independence requirement

A second implementation should be written without importing the reference verifier's decision logic. Agreement between independently implemented verifiers is a stronger result than replay by copies of the same code.

Before `AIFC v1.0 FROZEN`, two implementations must agree on schema admission, byte-identical canonicalization, ledger/genesis verdicts, candidate-provenance/multiplicity decisions, entropy bounds, target derivation, d-separation, witness/registry transitions, honest/attack corpus grades, and terminal verifier results.

## Current scientific boundary

The absence of a frozen standalone verifier means the repository remains a **protocol/specification project**, not yet a complete turnkey external bench.
