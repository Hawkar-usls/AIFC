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

**Status: DRAFT OBJECT SET IMPLEMENTED / CROSS-IMPLEMENTATION FREEZE PENDING**

Draft deliverables now present:

- `AIFC/hard-witness/v1` JSON Schema;
- PRE_RETURN certificate schema;
- experiment-wide trial-ledger event schema;
- entropy-profile schema;
- machine-readable causal-model schema;
- witness-registry/key-lifecycle schema;
- individual witness-receipt schema;
- quorum-certificate schema;
- target-evidence schema;
- complete evidence-bundle schema;
- verifier-result schema;
- normative canonicalization/domain-separation profile;
- normative trial state machine;
- wall-clock/causal-order boundary;
- machine-readable draft release gate;
- repository-level draft conformance CI.

Still required for Phase-1 freeze:

- canonicalization machine vectors;
- schema-positive and schema-negative vectors;
- independent implementation B of canonicalization/object parsing;
- byte-identical output across implementations;
- review and version freeze of every draft schema.

Exit criterion:

```text
BYTE_IDENTICAL_CANONICALIZATION = PASS
IMPLEMENTATION_A_SCHEMA_SUITE = PASS
IMPLEMENTATION_B_SCHEMA_SUITE = PASS
PHASE_1_OBJECTS_FROZEN = TRUE
```

## Phase 2 — Standalone reference verifier

**Status: NEXT MAJOR ENGINEERING GATE**

Deliverables:

- verifier implemented outside Genesis;
- no imports from producer/reference generator;
- deterministic evidence-grade state machine;
- global trial-ledger continuity/gap/fork checks;
- recomputation of candidate multiplicity;
- proof-carrying entropy-profile verification;
- independent d-separation evaluation over frozen causal DAG;
- witness registry/key-lifecycle verification;
- quorum safety checks;
- freshness bindings;
- target-event binding;
- exact identity check;
- frozen e-process implementation;
- machine-readable terminal verdicts.

Exit criterion: all declared adversarial test vectors are rejected for the expected reason.

## Phase 3 — Adversarial corpus

Deliverables include honest controls plus attacks against:

- trial omission/selective abort/state skipping;
- entropy claims and conditioning-view omissions;
- shared seed/prefetch/target pregeneration;
- causal common causes/collider selection;
- hidden multiplicity;
- optional stopping/e-process misuse;
- rollback/replay/split views;
- wall-clock trust misuse;
- witness/key rotation/revocation/compromise;
- canonicalization ambiguity;
- semantic verifier promotion.

Exit criterion:

```text
ALL_HONEST_VECTORS = PASS
ALL_ATTACK_VECTORS = EXPECTED_REJECTION
FAIL_OPEN = 0
```

## Phase 4 — External public-randomness bench

Deliverables:

- deterministic future-round selection;
- PRE_RETURN quorum infrastructure;
- target source independent of candidate host;
- complete pre-target side-information transcript;
- proof-carrying entropy profile;
- machine-readable causal model;
- global externally rooted trial ledger;
- public target verification;
- publication of all certified initiated trials, including aborts/invalidations.

Expected scientific outcome: most likely null.

A null result is a successful protocol demonstration.

## Phase 5 — Independent second implementation

Deliverables:

- verifier written by a different implementation team or independent contributor;
- different runtime/language where practical;
- independent witness deployment;
- reproducibility comparison;
- discrepancy ledger.

Exit criterion: identical evidence grades on the same frozen corpus and byte-identical canonicalization outputs.

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

- every machine-readable release gate at PASS;
- immutable GitHub release;
- DOI-backed Zenodo archive;
- frozen specification;
- frozen verifier;
- frozen adversarial corpus;
- SHA-256 release manifest;
- synchronized `.zenodo.json` and `CITATION.cff` metadata;
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
SILENT_TRIAL_DELETION = FORBIDDEN
UNSUPPORTED_ENTROPY_BOUND = FORBIDDEN
WALL_CLOCK_AS_SOLE_CAUSAL_ROOT = FORBIDDEN
PREMATURE_V1_FROZEN_TAG = FORBIDDEN
```