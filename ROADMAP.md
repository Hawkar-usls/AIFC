# AIFC Roadmap

AIFC is being developed as an independently reproducible scientific protocol, not as a claim that an anomalous physical effect has already been observed.

## Current internal terminal handoff

The scientific-assurance lineage has reached an explicit internal boundary on exact post-merge verified SAL v1.16 main `b8a1f3acf9d8444affccdb6b0b754f19e6a08949` (tree `9534c147ba29cc53f7f321b4101907a04818c3bc`). In the declared root-relative descendant-closure model, SAL v1.16 establishes that the internal authority closure cannot independently ratify the bootstrap root from which its own normative jurisdiction descends.

```text
AIFC_INTERNAL_ASSURANCE_LINEAGE_TERMINAL = ESTABLISHED_IN_CURRENT_TESTED_SCOPE
CURRENT_INTERNAL_VERIFICATION_PATH_TO_BOOTSTRAP_LEGITIMACY = ABSENT
BOOTSTRAP_AUTHORITY_LEGITIMACY = NOT_ESTABLISHED
EXTERNAL_BOOTSTRAP_RATIFICATION = NOT_PERFORMED
AIFC_V1_FROZEN = FALSE
AIFC_ARTICLE_PUBLICATION_READINESS = READY_WITH_EXPLICIT_DRAFT_AND_CLAIM_CEILING
NEXT_PHASE = PUBLIC_COMMUNICATION_AND_EXTERNAL_FALSIFICATION
```

This terminal handoff does **not** complete the v1.0 release gate. The remaining blockers include genuinely external or cross-implementation evidence and must not be manufactured by another internally self-authorized successor layer. See `docs/PUBLICATION_READY_STATUS.md`.

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

**Status: DEEP DRAFT OBJECT SET IMPLEMENTED / CROSS-IMPLEMENTATION FREEZE PENDING**

Draft deliverables now present:

- `AIFC/hard-witness/v1` schema;
- PRE_RETURN certificate schema;
- experiment-wide trial-ledger event schema and deterministic genesis predecessor;
- candidate-generation provenance profile for shadow-pool control;
- proof-carrying entropy profile with canonical exact-rational bound;
- frozen target-derivation profile;
- machine-readable causal-model schema;
- witness registry/key-lifecycle schema;
- typed individual witness-receipt and quorum-certificate schemas;
- joint witness-registry transition certificate;
- target-evidence schema binding raw source object and frozen derivation;
- complete evidence-bundle schema;
- verifier-result schema;
- proof-carrying release-manifest schema;
- normative canonicalization/domain-separation profile;
- normative trial state machine;
- wall-clock/causal-order boundary;
- machine-readable draft release gate;
- repository-level draft conformance CI.

Still required for Phase-1 freeze:

- canonicalization machine vectors, including rational/genesis cases;
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
- deterministic ledger-genesis and continuity/gap/fork checks;
- candidate-generation provenance / hidden-selection-freedom admission;
- recomputation of candidate multiplicity;
- proof-carrying entropy-profile and canonical-rational verification;
- exact zero-cap statistical branch;
- frozen target-selector and target-derivation replay from raw source evidence;
- independent d-separation evaluation over frozen causal DAG;
- witness registry/key-lifecycle verification;
- joint old/new quorum verification for registry reconfiguration;
- quorum safety checks;
- freshness bindings;
- exact identity check;
- frozen e-process implementation;
- proof-carrying release-manifest verification;
- machine-readable terminal verdicts.

First red-team order:

```text
SHADOW_CANDIDATE_POOL
-> REGISTRY_RECONFIGURATION_FORK
-> POST_HOC_TARGET_DERIVATION
-> NONCANONICAL_RATIONAL_BOUND
```

Exit criterion: all declared adversarial test vectors are rejected for the expected reason.

## Phase 3 — Adversarial corpus

Deliverables include honest controls plus attacks against:

- trial omission/selective abort/state skipping/genesis ambiguity;
- shadow candidate pools and undeclared candidate selection;
- entropy claims, rational canonicality and conditioning-view omissions;
- shared seed/prefetch/target pregeneration;
- post-hoc target derivation;
- causal common causes/collider selection;
- hidden multiplicity;
- optional stopping/e-process misuse;
- rollback/replay/split views;
- wall-clock trust misuse;
- witness/key rotation/revocation/compromise;
- unauthorized/disjoint registry reconfiguration;
- canonicalization ambiguity;
- release-manifest self-assertion;
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
- frozen target-derivation profile;
- PRE_RETURN quorum infrastructure;
- target source independent of candidate host;
- complete pre-target side-information transcript;
- proof-carrying candidate-generation profile;
- proof-carrying entropy profile;
- machine-readable causal model;
- global externally rooted trial ledger;
- public raw-source and target verification;
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
- proof-carrying `AIFC/release-manifest/v1` with per-gate evidence hashes;
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
SHADOW_CANDIDATE_MULTIPLICITY = FORBIDDEN
POST_HOC_TARGET_DERIVATION = FORBIDDEN
UNAUTHORIZED_REGISTRY_RECONFIGURATION = FORBIDDEN
NONCANONICAL_RATIONAL_BOUND = FORBIDDEN
UNSUPPORTED_ENTROPY_BOUND = FORBIDDEN
WALL_CLOCK_AS_SOLE_CAUSAL_ROOT = FORBIDDEN
FROZEN_PASS_WITHOUT_GATE_EVIDENCE = FORBIDDEN
PREMATURE_V1_FROZEN_TAG = FORBIDDEN
```
