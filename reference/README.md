# AIFC Reference Implementation

Status: **Verifier A frontier core v0.1 executable / full Implementation A not yet established**.

This directory contains the first standalone AIFC evidence-admission code. The normative draft schemas live at repository root under [`../schemas/`](../schemas/).

The reference implementation does not depend on Genesis for scientific admission.

## Current executable frontier

`reference/verifier/frontier.py` implements deterministic checks for the first four verifier-grade attack surfaces:

```text
SHADOW_CANDIDATE_POOL
        ↓
REGISTRY_RECONFIGURATION_FORK
        ↓
POST_HOC_TARGET_DERIVATION
        ↓
NONCANONICAL_RATIONAL_BOUND
```

It also implements the deterministic experiment-genesis hash, multiplicity-scaled exact-hit cap, explicit zero-cap branch, structural proof-carrying release-manifest checks, and joint old/new registry-transition structural admission.

Executable tests live in [`tests/test_frontier.py`](tests/test_frontier.py). Machine-readable scope/status is recorded in [`../conformance/VERIFIER-A-FRONTIER-v0.1.json`](../conformance/VERIFIER-A-FRONTIER-v0.1.json).

A green frontier test run means only:

```text
VERIFIER_A_FRONTIER_CORE = PASS
IMPLEMENTATION_A_PASS = NOT_ESTABLISHED
AIFC_V1_FROZEN = FALSE
```

## Design requirements for full Implementation A

The frozen verifier must independently:

- parse only versioned machine-readable evidence;
- enforce RFC 8785/JCS plus the AIFC canonicalization profile;
- recompute all domain-separated hashes and the deterministic experiment-genesis predecessor;
- validate the complete experiment-wide trial ledger and reject gaps/forks/selective deletion;
- enforce the trial state machine and abort semantics;
- validate candidate-generation provenance and fail closed on unbounded shadow-candidate selection freedom;
- enumerate/charge candidate multiplicity rather than trust a declared count;
- validate the proof-carrying entropy profile and canonical exact-rational `p_i` bound;
- explicitly handle `a_i = 0` without division-by-zero behavior;
- bind the entropy claim to the complete conditioning-view hash and target-derivation profile;
- recompute target derivation from the preserved raw source object;
- parse the causal DAG and independently evaluate required d-separation queries;
- reject forbidden collider/post-selection conditioning;
- verify witness registry state, Ed25519 signatures, key validity, rotation/revocation/compromise handling;
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
├── registry-transition-body.schema.json
├── registry-transition-receipt.schema.json
├── registry-transition-quorum.schema.json
├── registry-transition-certificate.schema.json
├── target-evidence.schema.json
├── evidence-bundle.schema.json
├── verifier-result.schema.json
└── release-manifest.schema.json
```

These schemas are draft interfaces. Their existence or partial implementation is not evidence that full standalone verification has already been achieved.

## Current v0.1 limitations

Verifier A frontier v0.1 intentionally does **not** yet claim:

- full JSON Schema validation;
- full RFC 8785 cross-implementation canonicalization;
- Ed25519 signature verification;
- registry key-interval/revocation replay;
- complete trial-ledger replay;
- d-separation computation;
- cryptographic verification of the future randomness source;
- the full e-process/statistical engine;
- a frozen machine-readable adversarial corpus;
- independent Implementation B agreement.

In particular, registry-transition v0.1 checks structural joint quorum/fork semantics but does not yet treat placeholder signatures in unit tests as cryptographically valid evidence.

## Independence requirement

Implementation B must be written without importing Verifier A decision logic. Before `AIFC v1.0 FROZEN`, two independent implementations must agree on schema admission, byte-identical canonicalization, ledger/genesis verdicts, candidate provenance/multiplicity, entropy bounds, target derivation, d-separation, witness/registry transitions, honest/attack corpus grades, and terminal results.

## Current scientific boundary

AIFC remains a **draft executable evidence-admission project**, not a complete frozen external bench. No physical retrocausal effect is reported or inferred by Verifier A v0.1.
