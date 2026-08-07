# AIFC Trial State Machine — v1.0 Draft

Status: `NORMATIVE DRAFT`

The AIFC state machine exists to make selective aborts, crash recovery, retries, and hidden post-selection visible to an external auditor.

## 1. Trial creation precedes candidate production

A trial slot is an AIFC trial only after a `CREATED` ledger event has been appended to the experiment-wide ledger and externally certified under the declared witness policy.

Candidate production for that slot **MUST NOT begin before `CREATED` is certified**. This prevents an operator from inspecting a candidate and deciding afterward whether the attempt should count.

For a fixed-horizon experiment, all planned trial slots SHOULD be predeclared in the experiment plan. For an open-ended anytime-valid experiment, each new slot MUST be certified before candidate visibility and the slot-creation rule MUST be frozen in advance.

## 2. States

```text
CREATED
  |
  v
PRE_RETURN_FROZEN
  |
  v
QUORUM_CERTIFIED
  |
  v
TARGET_ARMED
  |
  v
TARGET_OBSERVED
  |
  v
VERIFIED
  |
  v
TERMINAL
```

Permitted terminal subtypes:

- `COMPLETED_HIT`
- `COMPLETED_MISS`
- `INVALIDATED_EVIDENCE`
- `ABORTED_PRE_FREEZE`
- `ABORTED_POST_FREEZE_PRE_TARGET`
- `ABORTED_POST_TARGET_PRE_VERIFY`
- `ABORTED_RECOVERY_FAILURE`

An abort is a result. It MUST remain in the global ledger and MUST NOT be deleted or renumbered.

## 3. Permitted transitions

| From | To | Required evidence |
|---|---|---|
| none | `CREATED` | externally certified trial-slot creation |
| `CREATED` | `PRE_RETURN_FROZEN` | canonical candidate-set digest and multiplicity |
| `PRE_RETURN_FROZEN` | `QUORUM_CERTIFIED` | valid freeze quorum certificate |
| `QUORUM_CERTIFIED` | `TARGET_ARMED` | deterministic target selector bound to the frozen state |
| `TARGET_ARMED` | `TARGET_OBSERVED` | target-generation evidence and entropy profile |
| `TARGET_OBSERVED` | `VERIFIED` | frozen verifier result |
| `VERIFIED` | `TERMINAL` | published evidence-bundle hash and terminal subtype |
| any nonterminal state | `TERMINAL` | explicit abort/invalidation reason and available evidence |

All other transitions are forbidden.

## 4. Crash and retry semantics

### Crash before PRE_RETURN freeze

The slot remains `CREATED`. Recovery may continue the same slot only if the ledger head and slot identity reconcile with the external witnesses. Otherwise it terminates as `ABORTED_PRE_FREEZE`.

### Crash after freeze but before quorum certification

The trial MUST NOT arm a target. Recovery may finish certification only if the exact frozen candidate bytes are recovered and externally reconciled; otherwise terminate as `ABORTED_POST_FREEZE_PRE_TARGET`.

### Crash after quorum certification but before target observation

The trial remains counted. It may recover and continue only under the frozen target-selection rule. It MUST NOT silently disappear because the candidate appears unpromising.

### Crash after target observation

The observed target and all available source receipts MUST be preserved. Failure to complete verification terminates as `ABORTED_POST_TARGET_PRE_VERIFY`; it cannot be reclassified as an uninitiated attempt.

## 5. Idempotency

Every state transition MUST carry an idempotency key derived from `(experiment_id, trial_index, transition_ordinal, prior_event_hash)`.

A repeated identical request MAY return the previously issued receipt. A request using the same logical position with different content is an equivocation/fork and MUST be rejected or exposed as conflict evidence.

## 6. Selective-abort rule

AIFC treats abort behavior as part of the observed process. The verifier MUST account for every certified `CREATED` slot regardless of whether it reaches target generation.

A protocol that discards failed, interrupted, inconvenient, or non-impressive initiated trials is not eligible for an AIFC independent-future evidence grade.

## 7. Wall-clock boundary

State-machine order is established by certified event order and ledger continuity. Wall-clock timestamps are metadata unless a separately declared external timing assumption is required. See [`TIME_AND_ORDERING.md`](TIME_AND_ORDERING.md).
