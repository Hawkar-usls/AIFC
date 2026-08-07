# AIFC Current Draft Status — Verifier A v0.2

Status date: 2026-08-07

This file is a development status map, not a frozen scientific result.

## Draft precedence

For PR #5 evaluation, use the following order:

1. [`spec/AIFC-SPEC-v1.0-draft.2.md`](../spec/AIFC-SPEC-v1.0-draft.2.md) — current normative draft for preregistration/replay semantics;
2. [`conformance/AIFC-RELEASE-GATE-v1.0.2-draft.json`](../conformance/AIFC-RELEASE-GATE-v1.0.2-draft.json) — current superseding draft frozen-gate profile;
3. earlier `AIFC-SPEC-v1.0-draft.md` and `AIFC-RELEASE-GATE-v1.json` remain preserved as development history and MUST NOT be interpreted as silently rewritten records.

The duplicate/superseding draft files are intentional while PR #5 is under review. A later cleanup PR may consolidate names only after executable semantics and CI are stable.

## Current architectural transition

```text
SPECIFICATION
    ↓
EXECUTABLE EVIDENCE-ADMISSION FRONTIER  (Verifier A v0.1, merged)
    ↓
CONTENT-ADDRESSED REPLAY CORE           (Verifier A v0.2 candidate)
    ↓
EXPERIMENT-PLAN PREREGISTRATION GATE    (v0.2 candidate)
```

The phrase **full executable evidence-admission system** remains premature until the blocked cryptographic, causal, source-proof, statistical and cross-implementation gates are implemented.

## Current top-level v0.2 intended order

```text
EXPERIMENT_PLAN
    ↓
experiment-scoped plan-freeze quorum
    ↓
first CREATED references plan-quorum hash
    ↓
trial-scoped CREATED quorum
    ↓
candidate production / frozen candidate set
    ↓
PRE_RETURN + quorum
    ↓
target selector + target derivation profile
    ↓
PRE_TARGET_CONDITIONING_VIEW + quorum
    ↓
TARGET_ARMED
    ↓
TARGET_OBSERVED from resolved raw source evidence
    ↓
VERIFIED
    ↓
EVIDENCE_BUNDLE
    ↓
TERMINAL
    ↓
PUBLICATION_MANIFEST
```

## Verifier entry points during PR #5

The newest preregistration-aware development entry point is:

```text
reference/verifier/aifc_verify_v02.py
```

Composition:

```text
EvidenceResolverV02
    ↓
verify_plan_preregistration
    ↓
entropy-policy admission
    ↓
resolver-driven replay engine
    ↓
AIFC/verifier-result/v1
```

Older `aifc_verify.py`, `canonical.py`, `resolver.py` and helper modules remain for compatibility with the already-tested frontier/replay corpus during the draft migration. Their presence is not a second independent implementation.

## Evidence currently expected from CI

A fresh PR #5 CI run after the preregistration changes must establish only repository/executable development claims such as:

```text
BASE_REPOSITORY_CONFORMANCE = PASS
PREREGISTRATION_SUPPLEMENTAL_CONFORMANCE = PASS
VERIFIER_A_TEST_SUITE = PASS
IMPLEMENTATION_A_PASS = NOT_ESTABLISHED
AIFC_V1_FROZEN = FALSE
```

Any older `25/25` replay result predating experiment-plan preregistration and entropy-policy integration is historical evidence, not the current branch verdict.

## Explicit blockers

```text
ED25519_SIGNATURE_CRYPTO = BLOCKED
CAUSAL_D_SEPARATION = BLOCKED
TARGET_SOURCE_CRYPTOGRAPHIC_PROOF = BLOCKED
FULL_EXPERIMENT_STATISTICAL_REPLAY = BLOCKED
ANYTIME_EPROCESS_REPLAY = BLOCKED
BYTE_IDENTICAL_CANONICALIZATION_WITH_IMPLEMENTATION_B = BLOCKED
FROZEN_MACHINE_READABLE_CORPUS = BLOCKED
INDEPENDENT_IMPLEMENTATION_B = BLOCKED
FULL_RELEASE_MANIFEST_EVIDENCE_RESOLUTION = BLOCKED
EXTERNAL_PUBLIC_BEACON_BENCH = NOT_RUN
```

Therefore:

```text
IMPLEMENTATION_A_PASS = NOT_ESTABLISHED
IMPLEMENTATION_B_PASS = NOT_ESTABLISHED
AIFC_V1_FROZEN = FALSE
PHYSICAL_RETROCAUSALITY = NOT_OBSERVED
GLOBAL_NOVELTY = NOT_ESTABLISHED
```
