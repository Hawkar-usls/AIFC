# AIFC Roadmap — Verifier A v0.2 Draft Track

This file supplements `ROADMAP.md` during PR #5. It does not retroactively rewrite earlier milestones.

## Phase 1 — Protocol object surface

Status: **DEEP DRAFT / MACHINE-READABLE OBJECT SET EXPANDED**

Current object families include experiment plan/policies, candidate set/provenance, selector/derivation, pre-target conditioning view, entropy policy/profile, causal model, witness registry/transitions, statistics, publication, resolver index, replay manifest and release manifest.

Exit remains blocked until cross-implementation canonicalization and schema corpus freeze.

## Phase 2 — Standalone Verifier A

Status: **STARTED — CONTENT-ADDRESSED REPLAY v0.2 UNDER REVIEW**

Already implemented/candidate-tested areas:

```text
frontier attacks
content-addressed evidence resolution
fixed-horizon ledger replay
candidate multiplicity replay
target selector/derivation replay
pre-target conditioning-view bindings
entropy-policy admission
failure-domain quorum structure
publication completeness structure
experiment-plan preregistration structure
```

Still required before `IMPLEMENTATION_A_PASS`:

```text
full JSON Schema runtime validation
Ed25519 verification with frozen signature preimage rules
complete key rotation/revocation/compromise replay
independent d-separation engine
source-specific beacon proof verification
full fixed-horizon experiment statistics
anytime e-process implementation
frozen adversarial/honest corpus
full release-manifest evidence resolution
```

## Phase 3 — Canonicalization crucible

Status: **PENDING**

Requirements:

- freeze canonicalization corpus;
- independent second language implementation;
- byte-for-byte equality for admitted vectors;
- identical domain-separated hashes;
- identical rejection of duplicate keys, invalid UTF-8, non-NFC, forbidden floats, out-of-range integers and noncanonical rationals;
- typed target-framing agreement;
- genesis-sentinel agreement.

Exit:

```text
BYTE_IDENTICAL_CANONICALIZATION = PASS
```

## Phase 4 — Frozen machine-readable adversarial corpus

Status: **PENDING; DEVELOPMENT TESTS EXIST**

The final corpus must preserve expected results for honest controls and every declared attack class. Attacks cannot be removed after failures are observed.

Priority frontier:

```text
POST_CREATED_OPERATOR_CHOICE
POST_HOC_CONDITIONING_VIEW_SANITIZATION
PLAN_PREREGISTRATION_REBINDING
REGISTRY_EXPERIMENT_REBINDING
FAULT_MODEL_REBINDING
SAME_FAILURE_DOMAIN_SYBIL
DISCONNECTED_REGISTRY_CHAIN
AMBIGUOUS_DERIVATION_ENCODING
POST_TARGET_ENTROPY_METHOD_SUBSTITUTION
FAKE_FROZEN_PASS_WITH_DANGLING_EVIDENCE
NONCANONICAL_STORED_PROTOCOL_BYTES
```

## Phase 5 — Implementation B

Status: **NOT STARTED**

Implementation B must not import Verifier A decision logic or canonicalization code.

Exit requires identical verdict/failure semantics on the frozen corpus and byte-identical canonicalization.

## Phase 6 — Public null bench

Status: **NOT RUN**

Requirements include:

- externally certified experiment plan before first trial;
- genuinely distinct witness failure domains;
- certified CREATED slots;
- real future public randomness source outside the candidate host;
- frozen selector/derivation/conditioning view;
- source-specific cryptographic verification;
- all misses/aborts/timeouts/invalidations preserved;
- final publication manifest externally rooted.

Expected scientific outcome: most likely null.

## Phase 7 — Manuscript / prior-art freeze

Status: **PENDING**

Before novelty language is strengthened:

- scholarly database search;
- patent search;
- exact-claim matrix;
- reproducible citation set;
- independent expert review where possible.

Global novelty remains `NOT_ESTABLISHED` until then.

## Phase 8 — v1.0 frozen release

Status: **FORBIDDEN UNTIL ALL GATES PASS**

Current superseding draft gate contains 39 required evidence classes.

Frozen release choreography:

```text
immutable source commit
    ↓
out-of-tree proof-carrying release manifest
    ↓
resolve every required gate evidence hash
    ↓
independent verifier agreement
    ↓
GitHub Release / archive record binds source + manifest hash
```

No README edit, CI badge, human approval or status-field change can substitute for missing evidence.

```text
AIFC_V1_FROZEN = FALSE
```
