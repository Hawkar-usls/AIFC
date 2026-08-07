# AIFC Adversarial Test Vectors

Status: **corpus design frozen at the category level; machine-readable vectors not yet imported into this standalone repository.**

The test corpus exists to answer one question:

> Can a malformed, misleading, stale, selectively reported, causally contaminated, ambiguously serialized, or post-hoc derived evidence package make the verifier issue a stronger grade than the specification allows?

## Required vector families

### Honest controls

- `HONEST_NULL_MISS`
- `HONEST_NULL_CHANCE_HIT`
- `VALID_TECHNICAL_INVALIDATION`
- `VALID_POST_FREEZE_ABORT_VISIBLE_IN_LEDGER`

### Trial-ledger / state-machine attacks

- `MISSING_TRIAL_INDEX`
- `SILENT_TRIAL_DELETION`
- `SELECTIVE_INITIATION_AFTER_CANDIDATE_INSPECTION`
- `SELECTIVE_ABORT_AFTER_FREEZE`
- `STATE_SKIP_TARGET_BEFORE_QUORUM`
- `TERMINAL_STATE_RESURRECTION`
- `SAME_EVENT_INDEX_FORK`
- `RETRY_WITH_DIFFERENT_CONTENT_SAME_IDEMPOTENCY_POSITION`
- `WRONG_EXPERIMENT_GENESIS_SENTINEL`

### Candidate provenance / multiplicity attacks

- `SHADOW_CANDIDATE_POOL`
- `UNDECLARED_OPERATOR_CANDIDATE_SELECTION`
- `CANDIDATE_GENERATION_PROFILE_REBINDING`
- `HIDDEN_CANDIDATE_MULTIPLICITY`
- `SEMANTIC_POST_HOC_MAPPING`

### Entropy / dependence attacks

- `SHARED_SEED`
- `RNG_PREFETCH`
- `TARGET_PREGENERATION`
- `TARGET_DERIVED_PRECOMMIT_SIDEINFO`
- `HISTORYWISE_ENTROPY_COLLAPSE`
- `MARGINAL_ENTROPY_SUBSTITUTION`
- `UNSUPPORTED_P_I_ASSERTION`
- `CONDITIONING_VIEW_OMISSION`
- `SIGNED_ENTROPY_ASSERTION_WITHOUT_DERIVATION`
- `RNG_ROLLBACK_REPEATS_PRIOR_KNOWN_TARGET`
- `NONCANONICAL_RATIONAL_BOUND`
- `RATIONAL_NUMERATOR_GT_DENOMINATOR`
- `ZERO_CAP_HIT_DIVISION_BY_ZERO_TRAP`

### Target selection / derivation attacks

- `ADAPTIVE_FUTURE_ROUND_SELECTION`
- `POST_HOC_TARGET_DERIVATION`
- `TARGET_DERIVATION_PROFILE_REBINDING`
- `RAW_SOURCE_OBJECT_SUBSTITUTION`
- `MULTIPLE_UNCHARGED_TARGET_DERIVATIONS`

### Causal-model attacks

- `DIRECTED_PATH_ONLY_FALSE_PASS`
- `LATENT_COMMON_CAUSE_OMITTED`
- `POST_SELECTION_COLLIDER`
- `FORBIDDEN_SELECTION_CONDITIONING`
- `CYCLIC_FORWARD_NULL_DAG`
- `UNKNOWN_EDGE_ENDPOINT`

### Sequential-statistics attacks

- `NAIVE_OPTIONAL_STOPPING`
- `INVALID_EPROCESS_NULL_CAP`
- `POST_HOC_BETTING_PARAMETER`

### Continuity / provenance attacks

- `ROLLBACK_TO_VALID_PREFIX`
- `STALE_SIGNED_CHECKPOINT`
- `REPLAY_OLD_RUN`
- `SPLIT_VIEW_FORK`
- `ROLLBACKABLE_LOCAL_COUNTER`
- `CLOCK_BACKDATE_ONLY`
- `WALL_CLOCK_USED_AS_SOLE_CAUSAL_ROOT`
- `REGISTRY_ROLLBACK_WITH_EXPERIMENT`

### Witness / key-lifecycle / reconfiguration attacks

- `UNSAFE_SIMPLE_MAJORITY`
- `BYZANTINE_OVERLAP_EQUIVOCATION`
- `COLLUDING_WITNESS_ENTROPY_AUTHORITY`
- `STALE_OFFLINE_WITNESS`
- `REVOKED_KEY_ACCEPTED`
- `OLD_KEY_SIGNS_AFTER_ROTATION_INTERVAL`
- `DUPLICATE_KEYS_COUNTED_AS_DISTINCT_WITNESSES`
- `MULTIPLE_PROCESSES_SAME_FAILURE_DOMAIN_COUNTED_SEPARATELY`
- `COMPROMISED_KEY_INTERVAL_IGNORED`
- `UNAUTHORIZED_REGISTRY_RECONFIGURATION`
- `DISJOINT_CONFIG_FORK`
- `OLD_QUORUM_ONLY_WITHOUT_NEW_ACCEPTANCE`
- `NEW_QUORUM_ONLY_WITHOUT_OLD_AUTHORIZATION`
- `REGISTRY_SEQUENCE_JUMP`
- `REGISTRY_TRANSITION_REPLAY`

### Canonicalization attacks

- `NON_NFC_UNICODE`
- `DUPLICATE_JSON_KEYS`
- `FLOATING_POINT_HASH_AMBIGUITY`
- `KEY_ORDER_VARIATION`
- `TRAILING_NEWLINE_IN_HASH_INPUT`
- `WRONG_DOMAIN_SEPARATOR`
- `RAW_SHA256_WITHOUT_DOMAIN_SEPARATOR`
- `PLATFORM_ENDIAN_BINARY_ENCODING`
- `NONCANONICAL_RATIONAL_BOUND`
- `WRONG_GENESIS_PREDECESSOR`

### Verifier / release attacks

- `SELF_ASSERTED_INDEPENDENCE_BOOLEAN`
- `REPAIRED_DIGEST_AFTER_SEMANTIC_TAMPER`
- `TARGET_BINDING_SUBSTITUTION`
- `RUN_ID_REBINDING`
- `MISSING_REQUIRED_EVIDENCE`
- `FALSE_GRADE_PROMOTION`
- `RETROCAUSALITY_PROVED_OUTPUT_ATTEMPT`
- `UNTYPED_QUORUM_RECEIPT`
- `FROZEN_PASS_WITH_MISSING_GATE_EVIDENCE`
- `RELEASE_MANIFEST_DUPLICATE_GATE`
- `RELEASE_MANIFEST_EVIDENCE_HASH_MISMATCH`

## First standalone-verifier red-team order

The first executable verifier MUST prioritize these four attack surfaces before broader corpus freeze:

```text
SHADOW_CANDIDATE_POOL
        ↓
REGISTRY_RECONFIGURATION_FORK
        ↓
POST_HOC_TARGET_DERIVATION
        ↓
NONCANONICAL_RATIONAL_BOUND
```

These attacks target hidden choice, cross-configuration continuity, post-target degrees of freedom, and byte-level uniqueness respectively.

## Vector contract

Every machine-readable vector should eventually contain:

```json
{
  "vector_id": "...",
  "protocol_version": "...",
  "expected_admission": false,
  "expected_grade": "NOT_ADMITTED",
  "expected_failure_code": "...",
  "attack_class": "...",
  "evidence": {}
}
```

Where practical, tamper vectors should repair superficial hashes/signatures that an attacker could legitimately recompute after mutation. The verifier should reject the semantic inconsistency, not merely notice an intentionally broken checksum.

## Acceptance rule for the corpus

Before AIFC v1.0, the frozen verifier must satisfy:

```text
ALL_HONEST_VECTORS = PASS
ALL_ATTACK_VECTORS = EXPECTED_REJECTION
IMPLEMENTATION_A = PASS
IMPLEMENTATION_B = PASS
BYTE_IDENTICAL_CANONICALIZATION = PASS
FAIL_OPEN = 0
DETERMINISTIC_REPLAY = PASS
```

If a test vector produces an unexpected stronger grade, the verifier or specification must be treated as unresolved until the discrepancy is explained.

## Negative results

An attack that fails to break AIFC is still preserved.

AIFC should maintain the attack lineage rather than delete unsuccessful attacks, because repeated failed attack classes are part of the evidence about protocol hardening.
