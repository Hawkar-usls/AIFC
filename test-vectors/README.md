# AIFC Adversarial Test Vectors

Status: **corpus design frozen at the category level; machine-readable vectors not yet imported into this standalone repository.**

The test corpus exists to answer one question:

> Can a malformed, misleading, stale, selectively reported, or causally contaminated evidence package make the verifier issue a stronger grade than the specification allows?

## Required vector families

### Honest controls

- `HONEST_NULL_MISS`
- `HONEST_NULL_CHANCE_HIT`
- `VALID_TECHNICAL_INVALIDATION`

### Entropy / dependence attacks

- `SHARED_SEED`
- `RNG_PREFETCH`
- `TARGET_PREGENERATION`
- `TARGET_DERIVED_PRECOMMIT_SIDEINFO`
- `HISTORYWISE_ENTROPY_COLLAPSE`
- `MARGINAL_ENTROPY_SUBSTITUTION`

### Selection / multiplicity attacks

- `HIDDEN_CANDIDATE_MULTIPLICITY`
- `SEMANTIC_POST_HOC_MAPPING`
- `POST_SELECTION_COLLIDER`
- `ADAPTIVE_FUTURE_ROUND_SELECTION`

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

### Witness attacks

- `UNSAFE_SIMPLE_MAJORITY`
- `BYZANTINE_OVERLAP_EQUIVOCATION`
- `COLLUDING_WITNESS_ENTROPY_AUTHORITY`
- `STALE_OFFLINE_WITNESS`

### Verifier attacks

- `SELF_ASSERTED_INDEPENDENCE_BOOLEAN`
- `REPAIRED_DIGEST_AFTER_SEMANTIC_TAMPER`
- `TARGET_BINDING_SUBSTITUTION`
- `RUN_ID_REBINDING`
- `MISSING_REQUIRED_EVIDENCE`
- `FALSE_GRADE_PROMOTION`

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

Before AIFC v1.0, the frozen verifier should satisfy:

```text
ALL_HONEST_CONTROL_EXPECTATIONS = PASS
ALL_DECLARED_ATTACKS_REJECTED_AS_EXPECTED = PASS
FAIL_OPEN_CASES = 0
DETERMINISTIC_REPLAY = PASS
```

If a test vector produces an unexpected stronger grade, the verifier or specification must be treated as unresolved until the discrepancy is explained.

## Negative results

An attack that fails to break AIFC is still preserved.

AIFC should maintain the attack lineage rather than delete unsuccessful attacks, because repeated failed attack classes are part of the evidence about protocol hardening.
