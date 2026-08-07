# Experiment Plan and Pre-Trial Certification

Status: `NORMATIVE DRAFT SUPPLEMENT`

The `AIFC/experiment-plan/v1` object is the machine-readable contract that exists before any trial slot.

Its purpose is to prevent a protocol from becoming stricter only after the experimenter already knows which choices were favorable.

## Why a plan hash is not enough

A plan can be perfectly immutable and still be created too late.

Therefore AIFC distinguishes:

```text
plan identity
```

from:

```text
proof that this exact plan was externally certified before the first trial existed.
```

The directed preregistration chain is:

```text
AIFC/experiment-plan/v1
        ↓ content hash
AIFC/experiment-plan-quorum/v1
        ↓ certificate hash
first AIFC/trial-ledger-event/v1 with state_to=CREATED
        ↓
trial-scoped CREATED quorum
        ↓
candidate production eligibility
```

The first `CREATED` event MUST bind:

```text
payload_hash = experiment_plan_hash
prerequisite_certificate_hash = experiment_plan_quorum_hash
```

Thus a verifier can reject a plan that is valid but was not part of the certified causal history before trial creation.

## Why the plan quorum is experiment-scoped

The ordinary AIFC quorum certificate is trial-scoped and requires `trial_index`.

That type is intentionally **not** used for plan freeze, because the plan must be certified before the first trial exists.

AIFC therefore defines:

```text
AIFC/experiment-plan-receipt/v1
AIFC/experiment-plan-quorum/v1
```

These objects have no `trial_index`.

This separation prevents an implementation from inventing a dummy trial merely to authenticate pre-trial evidence.

## Frozen policy graph

The experiment plan references the exact policies governing:

- trial-slot creation;
- candidate generation;
- target event selection;
- target byte derivation;
- entropy-bound admission;
- causal model;
- statistical method;
- publication/completeness;
- external freshness;
- pre-target conditioning-view capture;
- initial witness registry;
- registry reconfiguration permission.

Any trial-specific evidence profile MUST conform to the relevant pre-experiment policy.

## Scientific boundary

Plan certification establishes provenance/order under the admitted witness model. It does not establish that every scientific assumption in the plan is true.

For example, freezing an entropy policy proves which entropy argument was chosen before the trial; it does not prove that the entropy argument itself is valid. The latter remains an independent evidence gate.
