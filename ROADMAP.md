# AIFC Roadmap

AIFC is being developed as an independently reproducible scientific protocol, not as a claim that an anomalous physical effect has already been observed.

## Current internal terminal handoff

The scientific-assurance lineage has reached an explicit internally authored boundary on exact post-merge verified SAL v1.17 main:

```text
CURRENT_TESTED_MAIN = 1eaf6ea1d6874b85cd7e85fba87cfc167bd4441d
CURRENT_TESTED_TREE = a03273fc39e6310934258539e7e4f81fc98fffb9
POST_MERGE_UNIT_TESTS = 425 / 425 PASS
POST_MERGE_PR_TRIGGERED_WORKFLOWS = 21 / 21 SUCCESS
```

SAL v1.16 established in its declared root-relative descendant-closure model:

```text
InternalAuthorityClosure != BootstrapLegitimacy
```

SAL v1.17 preserves that boundary and establishes in its current tested scope:

```text
StructuralIndependence + Authentication != AuthorityAdmissibility
```

The current handoff classification is therefore:

```text
AIFC_INTERNAL_ASSURANCE_LINEAGE_TERMINAL = ESTABLISHED_IN_CURRENT_TESTED_SCOPE
AIFC_ARTICLE_PUBLICATION_READINESS = READY_WITH_EXPLICIT_DRAFT_AND_CLAIM_CEILING
AIFC_V1_FROZEN = FALSE
IMPLEMENTATION_A_PASS = NOT_ESTABLISHED
IMPLEMENTATION_B = NOT_ESTABLISHED
EXTERNAL_RATIFICATION_CANDIDATE = NOT_PRESENT_AT_DESIGNATED_INTAKE_PATH
EXTERNAL_RATIFIER_AUTHORITY_ADMISSIBILITY = NOT_ESTABLISHED
EXTERNAL_BOOTSTRAP_RATIFICATION = NOT_PERFORMED
BOOTSTRAP_AUTHORITY_LEGITIMACY = NOT_ESTABLISHED
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

**Status: INTERNAL REFERENCE / SELF-AUDIT LINE COMPLETE TO CURRENT CLAIM CEILING; EXTERNAL INDEPENDENCE STILL OPEN**

The current repository contains a standalone verifier family, deterministic evidence-grade semantics, extensive fail-closed replay, exact-main CI attestation, platform-receipt binding, and scientific-assurance lineage hardening through SAL v1.17. This does not promote `IMPLEMENTATION_A_PASS` to an AIFC v1.0 release-gate PASS because authority legitimacy and the full frozen release evidence basis remain unresolved.

External/frozen-v1 work remains responsible for independent implementation and release-grade authority/evidence closure.

## Phase 3 — Adversarial corpus

**Status: DEEP INTERNAL CORPUS IMPLEMENTED / FROZEN CROSS-IMPLEMENTATION CORPUS PENDING**

Current internal tests cover honest controls plus attacks against trial omission/selective abort/state skipping, shadow candidates, entropy/conditioning claims, post-hoc derivation, hidden multiplicity, optional-stopping misuse, rollback/replay, key lifecycle, registry reconfiguration, canonicalization ambiguity, release-manifest self-assertion, semantic promotion, authority laundering, lineage incompleteness, self-ratification, and external-ratifier authority promotion.

Frozen-v1 exit criterion remains:

```text
ALL_HONEST_VECTORS = PASS
ALL_ATTACK_VECTORS = EXPECTED_REJECTION
FAIL_OPEN = 0
```

under the final independently reproducible release corpus.

## Phase 4 — External public-randomness bench

**Status: EXTERNAL — NOT YET ESTABLISHED**

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

Expected scientific outcome: most likely null. A null result is a successful protocol demonstration.

## Phase 5 — Independent second implementation

**Status: EXTERNAL / INDEPENDENT CONTRIBUTOR REQUIRED**

Deliverables:

- verifier written by a different implementation team or independent contributor;
- different runtime/language where practical;
- independent witness deployment;
- reproducibility comparison;
- discrepancy ledger.

Exit criterion: identical evidence grades on the same frozen corpus and byte-identical canonicalization outputs.

## Phase 6 — Prior-art and manuscript freeze

**Status: PUBLIC COMMUNICATION MAY BEGIN; FINAL NOVELTY/MANUSCRIPT FREEZE REMAINS EXTERNAL-REVIEW DEPENDENT**

Deliverables:

- broader scholarly review;
- patent review;
- bibliography with closest end-to-end protocols;
- manuscript draft;
- explicit novelty claim narrowed to surviving delta;
- independent technical review.

A public technical article may precede this freeze if it obeys `docs/PUBLICATION_READY_STATUS.md` and does not claim frozen v1.0, global novelty, or observed retrocausality.

## Phase 7 — AIFC v1.0 release

**Status: BLOCKED — DO NOT TAG FROZEN**

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

**Status: EXTERNAL — NOT YET RUN**

Only after the protocol and null model are frozen should extraordinary physical interpretation be discussed. A replicated anomaly would trigger a new research phase, not an automatic retrocausality claim.

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