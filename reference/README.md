# AIFC Reference Implementation

Status: **planned / not yet frozen**.

This directory will contain the standalone AIFC verifier and supporting schema/canonicalization code.

The reference implementation must not depend on Genesis for scientific admission.

## Design requirements

The verifier should:

- parse only versioned machine-readable evidence;
- canonicalize independently of the producer;
- recompute hashes and target bindings;
- enumerate candidate multiplicity rather than trust a declared count;
- verify witness quorum safety under the declared `(n,f,q)` model;
- verify freshness/continuity bindings;
- distinguish provenance from unpredictability;
- bind every target to a post-freeze event-selection rule;
- verify the history-wise null cap interface;
- compute the preregistered e-process or fixed-horizon statistic;
- emit deterministic failure codes;
- fail closed on missing or contradictory evidence;
- never emit `RETROCAUSALITY_PROVED`.

## Planned layout

```text
reference/
├── README.md
├── verifier/
│   ├── aifc_verify.py
│   └── evidence_state_machine.py
├── schemas/
│   ├── hard-witness.schema.json
│   ├── pre-return-certificate.schema.json
│   ├── witness-receipt.schema.json
│   ├── target-evidence.schema.json
│   └── verifier-result.schema.json
└── canonical/
    └── canonical_json.py
```

Exact names may change before the first frozen implementation.

## Independence requirement

A second implementation should be written without importing the reference verifier's decision logic. Agreement between independently implemented verifiers is a stronger result than replay by copies of the same code.

## Current scientific boundary

The absence of a frozen standalone verifier means the repository is currently a **protocol/specification project**, not yet a complete turnkey external bench.
