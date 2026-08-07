# AIFC Roadmap

AIFC is being developed as an independently reproducible scientific protocol, not as a claim that an anomalous physical effect has already been observed.

## Phase 0 — Provenance foundation

**Status: COMPLETE**

- standalone public repository;
- Apache-2.0 licensing;
- paper-grade README;
- initial specification draft;
- threat model;
- evidence-grade semantics;
- citation and Zenodo metadata;
- origin/provenance bindings.

## Phase 1 — Freeze machine-readable protocol objects

**Status: NEXT**

Deliverables:

- `AIFC/hard-witness/v1` JSON Schema;
- PRE_RETURN certificate schema;
- target-evidence schema;
- witness receipt schema;
- quorum certificate schema;
- verifier result schema;
- canonical JSON rules;
- domain-separated hashing rules.

Exit criterion: two independent implementations serialize the same test vectors byte-identically.

## Phase 2 — Standalone reference verifier

Deliverables:

- verifier implemented outside Genesis;
- no imports from producer/reference generator;
- deterministic evidence-grade state machine;
- recomputation of candidate multiplicity;
- quorum safety checks;
- freshness bindings;
- target-event binding;
- exact identity check;
- frozen e-process implementation;
- machine-readable terminal verdicts.

Exit criterion: all declared adversarial test vectors are rejected for the expected reason.

## Phase 3 — Adversarial corpus

Deliverables:

- honest null transcript;
- exact chance-hit transcript;
- shared-seed attack;
- RNG prefetch attack;
- target-pregeneration attack;
- target-derived commitment attack;
- hidden multiplicity attack;
- post-selection attack;
- marginal-entropy attack;
- optional-stopping attack;
- rollback attack;
- stale signed-checkpoint attack;
- replay attack;
- split-view attack;
- unsafe-majority quorum attack;
- falsified timestamp attack;
- compromised entropy-authority case.

Exit criterion: no fail-open verifier result in the frozen corpus.

## Phase 4 — External public-randomness bench

Deliverables:

- deterministic future-round selection;
- PRE_RETURN quorum infrastructure;
- target source independent of candidate host;
- complete pre-target side-information transcript;
- public target verification;
- publication of all initiated trials.

Expected scientific outcome: most likely null.

A null result is a successful protocol demonstration.

## Phase 5 — Independent second implementation

Deliverables:

- verifier written by a different implementation team or independent contributor;
- different runtime/language where practical;
- independent witness deployment;
- reproducibility comparison;
- discrepancy ledger.

Exit criterion: identical evidence grades on the same frozen corpus.

## Phase 6 — Prior-art and manuscript freeze

Deliverables:

- broader scholarly review;
- patent review;
- bibliography with closest end-to-end protocols;
- manuscript draft;
- explicit novelty claim narrowed to surviving delta;
- independent technical review.

## Phase 7 — AIFC v1.0 release

Deliverables:

- immutable GitHub release;
- DOI-backed Zenodo archive;
- frozen specification;
- frozen verifier;
- frozen adversarial corpus;
- SHA-256 release manifest;
- citation metadata;
- public paper/preprint.

## Phase 8 — Independent physical replication

Only after the protocol and null model are frozen should extraordinary physical interpretation be discussed.

A replicated anomaly would trigger a new research phase, not an automatic retrocausality claim.

---

## Permanent rules

```text
NEGATIVE_RESULTS_ARE_RESULTS = TRUE
MISSING_EVIDENCE_FAILS_CLOSED = TRUE
SURPRISE_DOES_NOT_OVERRIDE_PROTOCOL = TRUE
SIMULATION_IS_NOT_PHYSICAL_EVIDENCE = TRUE
RETROCAUSALITY_PROVED_BY_VERIFIER = FORBIDDEN
GLOBAL_NOVELTY_WITHOUT_REVIEW = FORBIDDEN
```
