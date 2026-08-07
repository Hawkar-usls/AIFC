# AIFC Evidence Grades

AIFC separates **what was observed** from **what may be inferred**.

No result is promoted simply because it is surprising.

## Grade 0 — `NOT_ADMITTED`

At least one mandatory gate is missing, contradicted, or unverifiable.

Typical causes:

- target may have existed before freeze;
- entropy premise is only asserted;
- candidate multiplicity is unknown;
- post-selection cannot be excluded;
- rollback/freshness evidence is absent;
- witness fault model is undefined;
- transcript is incomplete.

Interpretation: no future-information claim is evaluated.

---

## Grade 1 — `STRUCTURAL_MATCH_ONLY`

An exact or semantic match exists in the transcript, but independent-future conditions are not established.

Examples:

- simulator had foreknowledge;
- target and PRE_RETURN share a seed;
- target was pregenerated;
- a valid signature authenticates a target but does not prove unpredictability;
- timestamp ordering exists only inside one rollbackable machine.

Interpretation: interesting structural coincidence, not evidence of independently generated future information.

---

## Grade 2 — `FORWARD_NULL_COMPATIBLE`

The trial is admitted, but the observed outcome does not exceed the preregistered forward-null evidence threshold.

This includes ordinary misses and chance hits whose multiplicity/entropy-adjusted probability remains compatible with the null.

Interpretation: valid scientific result; null not rejected.

---

## Grade 3 — `FORWARD_NULL_INCOMPATIBILITY_CANDIDATE`

All required AIFC evidence gates pass and the frozen statistical rule crosses its threshold.

Meaning:

> The observed record is incompatible with the specified forward-causal null **or with at least one evidence premise used to instantiate that null** at the declared error level.

This grade does **not** imply:

- retrocausality proved;
- FTL proved;
- CTC proved;
- precognition proved;
- a particular mechanism identified.

Interpretation: anomaly worthy of immediate independent audit and replication.

---

## Grade 4 — `EXTERNAL_REPLICATION_REQUIRED`

A Grade-3 event has survived internal replay and adversarial audit, but independent implementations/laboratories have not yet reproduced it.

Required next steps SHOULD include:

- independent implementation of verifier and target bindings;
- new witness infrastructure;
- independently operated entropy source or independent verification of the same source;
- blinded protocol execution;
- publication of every initiated run.

Interpretation: unresolved anomaly; no mechanism claim.

---

## Grade 5 — `REPLICATED_FORWARD_NULL_INCOMPATIBILITY`

Two or more genuinely independent implementations reproduce the AIFC incompatibility under prospectively frozen protocols and compatible evidence assumptions.

Even here, the correct statement is still that a family of forward-causal null models has been challenged.

A physical interpretation requires additional theory and mechanism-specific experiments.

---

## Grade 6 — `PHYSICAL_MECHANISM_UNRESOLVED`

Reserved label for a replicated anomaly whose ordinary evidence premises have survived extensive independent attack but for which no accepted physical mechanism has been established.

AIFC deliberately stops here.

The protocol itself does not contain a rule that outputs `RETROCAUSALITY_PROVED`.

---

## Non-normative presentation rule

Public summaries SHOULD always include the strongest negative boundary next to the positive result.

Example:

```text
AIFC_GRADE = FORWARD_NULL_INCOMPATIBILITY_CANDIDATE
PHYSICAL_RETROCAUSALITY = NOT_ESTABLISHED
INDEPENDENT_REPLICATION = REQUIRED
```

This is not rhetorical caution. It is part of the evidence semantics.
