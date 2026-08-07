# Target Selector

Status: `NORMATIVE DRAFT SUPPLEMENT`

AIFC separates two different freedoms that must be frozen independently:

```text
Which future event is used?
```

and:

```text
How does that event become exact target bytes?
```

The first question is the **target selector**. The second is the **target derivation profile**.

## Experiment-level policy

`AIFC/target-selector-policy/v1` is frozen by the experiment plan before any trial.

It defines source identity/version, selection algorithm, permitted anchor role and parameters.

## Per-trial selector instance

`AIFC/target-selector-profile/v1` binds the concrete selected event for one trial.

For strongest-grade v1 it must contain exactly one selected event and no alternate event set.

The profile carries:

- policy hash;
- experiment/trial;
- source identity/version;
- selection algorithm;
- anchor role/hash;
- deterministic parameters;
- selected event ID;
- selection-transcript evidence;
- pre-observation freeze flag.

## Current deterministic replay

Verifier A v0.2 currently implements:

```text
FIXED_EVENT_ID_FROM_PLAN
```

For this method:

```text
anchor_role = EXPERIMENT_PLAN
anchor_hash = experiment_plan_hash
selected_event_id = frozen policy.fixed_event_id
```

The verifier therefore derives the event identity rather than trusting a producer string.

Other selector algorithms remain blocked until the source schedule and external anchor semantics are executable and adversarially tested.

## Attack classes

A selector MUST fail admission for:

```text
POST_HOC_TARGET_SELECTION
SELECTOR_POLICY_REBINDING
SELECTOR_ANCHOR_REBINDING
SELECTED_EVENT_RECOMPUTE_MISMATCH
MULTIPLE_TARGET_EVENTS_FORBIDDEN
DANGLING_SELECTION_TRANSCRIPT
```

## Relationship to target derivation

Selector freedom and derivation freedom are different multiplicity sources. Strongest-grade AIFC v1 eliminates hidden target-side multiplicity by requiring one admitted event and one admitted derivation per trial.
