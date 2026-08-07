# Candidate Provenance and Shadow-Pool Control

Status: `NORMATIVE DRAFT`

A certified `CREATED` slot prevents a producer from seeing a candidate and only then deciding to open a trial. It does **not** by itself prove that the candidate was not selected from a hidden pool generated earlier or elsewhere.

## Threat

A producer could precompute or privately inspect many candidate values before trial creation, then after `CREATED` publish only one and claim `K_i = 1`.

This is a multiplicity attack even if every visible state transition is temporally correct.

## Candidate Generation Profile

Strongest-grade trials MUST bind an `AIFC/candidate-generation-profile/v1` object before PRE_RETURN freeze.

The profile records:

- the certified `CREATED` slot it follows;
- generator implementation/version and code/image hash;
- a commitment to relevant pre-created generator state;
- the admitted candidate-set cardinality upper bound;
- operator choice after creation/generation;
- the evidence basis for excluding or accounting for a hidden candidate pool;
- external evidence and unresolved assumptions.

Schema: [`../schemas/candidate-generation-profile.schema.json`](../schemas/candidate-generation-profile.schema.json).

## Admission boundary

Candidate provenance is necessarily an evidence claim under a declared trust/adversary model. A software log cannot prove that an operator had no undisclosed notebook, second machine, prior simulation, or human-selected pool.

Therefore AIFC MUST NOT translate unexplained off-system selection freedom into `K_i=1`. If the strongest grade cannot exclude or bound a shadow pool, the trial fails closed or charges the larger multiplicity.

## Preferred strongest-grade design

Prefer a single-shot generator whose relevant state is committed after externally certified `CREATED`, with no operator choice over outputs and with external evidence that binds the execution instance.

The reference verifier MUST include a dedicated `SHADOW_CANDIDATE_POOL` rejection path.
