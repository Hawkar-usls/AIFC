# Entropy Evidence Interface

Status: `NORMATIVE DRAFT`

AIFC does not accept statements such as `this is a 256-bit RNG` as evidence for a point-probability bound.

The verifier must be able to answer:

> **Why is the declared history-wise bound `p_i` admissible relative to the complete pre-target view?**

## 1. Required object

Every target event used for an independent-future grade MUST carry an `AIFC/entropy-profile/v1` object.

The profile binds:

- exact source identity and protocol version;
- deterministic target-selection rule;
- the hash of the complete conditioning view used for the claim;
- an exact rational upper bound on point guessing probability;
- derivation method;
- supporting external evidence;
- assumptions;
- unresolved assumptions;
- an explicit admission status.

Schema: [`../schemas/entropy-profile.schema.json`](../schemas/entropy-profile.schema.json).

## 2. Exact arithmetic

The authoritative point-probability upper bound is represented as an exact rational:

```json
"point_probability_upper_bound": {
  "numerator_dec": "1",
  "denominator_dec": "115792089237316195423570985008687907853269984665640564039457584007913129639936"
}
```

This represents `2^-256` without floating-point ambiguity.

A human-readable min-entropy value MAY also be supplied, but it is not a substitute for the exact verifier input.

## 3. Conditioning view

The `conditioning_view_hash` MUST bind the complete freeze-time side-information object relevant to the entropy claim.

This includes, as applicable:

- public metadata;
- previous targets and receipts;
- prior ledger history;
- source-health data;
- target-selection state;
- operator-visible information;
- known shared state;
- any prior target values that could become relevant after RNG rollback or replay.

A bound conditioned only on a convenient subset of available history MUST NOT be promoted to the AIFC independent-future grade.

## 4. Derivation methods

Examples of admissible derivation classes include:

- a formally specified uniform-bit source with externally supported certification;
- a public randomness beacon whose security/unpredictability assumption is explicitly cited and whose future round was fixed before publication;
- an external proof or security reduction yielding a conservative point-probability cap;
- a deliberately conservative analytic bound;
- an empirical model only when its assumptions and limitations are explicit and the requested evidence grade permits that model.

AIFC does not equate computational difficulty with information-theoretic min-entropy unless the experiment explicitly declares a computational null model.

## 5. Unresolved assumptions fail closed

For the strongest exact independent-future grade:

```text
unresolved_assumptions == []
admission_status == ADMITTED
```

If the source may have reused state, rolled back, leaked a seed, exposed target-derived information, or otherwise lost the stated history-wise bound, the profile MUST be blocked or replaced with a weaker conservative bound.

## 6. RNG rollback consequence

If a target generator repeats a previously revealed target after state rollback, and that prior target belongs to the pre-target history, the history-wise point probability for that branch may become `1`.

AIFC therefore treats entropy-state continuity as part of evidence, not as an implementation detail.

## 7. Separation from provenance

A signed entropy receipt can establish provenance and integrity of a claim. A signature alone does not prove unpredictability.

The entropy profile MUST distinguish:

```text
WHO SAID IT
from
WHY THE BOUND IS VALID
```

The verifier checks both.
