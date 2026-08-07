# Global Trial Ledger

Status: `NORMATIVE DRAFT`

The experiment-wide ledger makes missing, renumbered, selectively aborted, replayed, or rewritten trials externally auditable.

## Core rule

Every AIFC trial slot is assigned a monotonically increasing `trial_index`. Every protocol transition is assigned a monotonically increasing experiment-wide `event_index` and is linked to the previous ledger event by hash.

```text
E_0 -> E_1 -> E_2 -> ... -> E_n
```

Each event binds at least:

```text
experiment_id
trial_index
run_id
event_index
transition_ordinal
state_from
state_to
previous_event_hash
payload_hash
evidence_bundle_hash
reason_code
```

The canonical event hash is domain separated:

```text
SHA256("AIFC:TRIAL_LEDGER_EVENT:v1\0" || canonical_event_bytes)
```

## Experiment genesis predecessor

Independent implementations MUST NOT invent their own predecessor convention for the first event.

For event `E_0`, `previous_event_hash` is the lowercase hexadecimal SHA-256 digest of:

```text
ASCII("AIFC:EXPERIMENT_GENESIS:v1") || 0x00 || UTF8(experiment_id)
```

No trailing newline, NUL after `experiment_id`, all-zero digest, empty string, or implementation-defined sentinel is admissible.

The verifier MUST recompute this value. For all events after `E_0`, `previous_event_hash` MUST equal the domain-separated canonical hash of the immediately preceding event.

## No-gap rule

For fixed-horizon experiments, the experiment plan MUST declare the intended trial count and indices before execution.

For open-ended experiments, new trial indices MUST be issued sequentially and externally certified before candidate production for the new slot begins.

An auditor MUST reject an unexplained sequence such as:

```text
trial 001
trial 002
trial 003
trial 005
```

The only admissible explanation is a visible ledger record for trial 004 with a terminal state, including an abort or invalidation state.

## External anti-rewrite root

A local hash chain alone does not prove that an earlier valid history was not replaced. Therefore ledger heads MUST be periodically or transition-wise certified by the declared external witness policy.

At minimum, the following positions MUST receive externally rooted evidence:

1. trial-slot creation (`CREATED`), before candidate production;
2. PRE_RETURN freeze / quorum certification;
3. terminal publication.

A stronger deployment MAY certify every ledger transition.

## Selective initiation

Candidate production MUST NOT precede certified trial creation. Otherwise an operator could inspect candidate output and create a ledger entry only for desirable guesses.

If the experiment uses a schedule, participant action, sensor trigger, or other eligibility rule to decide when a new trial starts, that rule MUST be frozen before outcomes and included in the experiment plan.

## Shadow-candidate rule

Certified `CREATED` prevents selective trial creation after observing a candidate, but does not by itself exclude a hidden pool produced before or outside the visible trial process.

Every strongest-grade trial MUST therefore bind an `AIFC/candidate-generation-profile/v1` object. The profile MUST declare the candidate-generation implementation/state, the externally certified `CREATED` slot it follows, the upper bound on candidate-set cardinality, any operator selection freedom, external evidence, and unresolved assumptions.

The verifier MUST fail closed if a shadow pool or undeclared candidate-selection freedom cannot be excluded under the admitted model. Software provenance cannot prove the absence of arbitrary undisclosed human/off-system information; such trust assumptions MUST remain explicit rather than being silently converted into `K_i=1`.

## Selective abort

After `CREATED` is certified, the slot can never disappear. Crash, timeout, refusal to arm the target, source outage, or operator abort all terminate visibly and remain in multiplicity/reporting accounting as specified by the statistical protocol.

## Fork rule

Two different events at the same `(experiment_id, event_index)` or the same `(experiment_id, trial_index, transition_ordinal)` constitute ledger equivocation. The verifier MUST fail closed and retain both conflicting objects as evidence.

## Publication rule

A release MUST include:

- complete ledger from experiment genesis through the release head;
- external certificates needed to establish continuity;
- every terminal trial bundle;
- explicit entries for every aborted or invalidated slot;
- the final ledger-head digest.

No summary table is a substitute for the underlying ledger.

Schemas:

- [`../schemas/trial-ledger-event.schema.json`](../schemas/trial-ledger-event.schema.json)
- [`../schemas/candidate-generation-profile.schema.json`](../schemas/candidate-generation-profile.schema.json)
