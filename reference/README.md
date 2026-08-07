# AIFC Reference Implementation

Status: **planned / not yet frozen**.

This directory will contain the standalone AIFC verifier and supporting implementation code. The normative draft schemas now live at repository root under [`../schemas/`](../schemas/).

The reference implementation must not depend on Genesis for scientific admission.

## Design requirements

The verifier must independently:

- parse only versioned machine-readable evidence;
- enforce the frozen canonicalization profile;
- recompute domain-separated hashes and target bindings;
- validate the experiment-wide trial ledger and reject gaps/forks/selective deletion;
- enforce the trial state machine and abort semantics;
- enumerate candidate multiplicity rather than trust a declared count;
- validate the proof-carrying entropy profile and exact rational `p_i` bound;
- bind the entropy claim to the complete conditioning-view hash;
- parse the causal DAG and independently evaluate required d-separation queries;
- reject forbidden collider/post-selection conditioning;
- verify witness registry state, key validity, rotation/revocation/compromise handling;
- verify individual witness receipts and quorum safety under the declared `(n,f,q)` model;
- verify freshness/continuity bindings outside the experiment rollback domain;
- distinguish provenance from unpredictability;
- bind every target to a post-freeze event-selection rule;
- treat wall-clock timestamps as metadata unless a valid external timing profile applies;
- compute the preregistered e-process or fixed-horizon statistic;
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
├── entropy-profile.schema.json
├── causal-model.schema.json
├── witness-registry.schema.json
├── witness-receipt.schema.json
├── quorum-certificate.schema.json
├── target-evidence.schema.json
├── evidence-bundle.schema.json
└── verifier-result.schema.json
```

These schemas are draft interfaces. Their existence is not evidence that the standalone verifier has already implemented them correctly.

## Planned implementation layout

```text
reference/
├── README.md
└── verifier/
    ├── aifc_verify.py
    ├── canonicalization.py
    ├── ledger.py
    ├── entropy.py
    ├── causal.py
    ├── witnesses.py
    └── statistics.py
```

Exact implementation filenames may change before the first frozen implementation; protocol object names and semantics require versioned changes.

## Independence requirement

A second implementation should be written without importing the reference verifier's decision logic. Agreement between independently implemented verifiers is a stronger result than replay by copies of the same code.

Before `AIFC v1.0 FROZEN`, two implementations must agree on:

- schema admission;
- byte-identical canonicalization vectors;
- ledger/state-machine verdicts;
- entropy-profile bounds;
- d-separation queries;
- witness/quorum validity;
- all honest/attack corpus grades;
- terminal verifier results.

## Current scientific boundary

The absence of a frozen standalone verifier means the repository remains a **protocol/specification project**, not yet a complete turnkey external bench.
