# AIFC Specification v1.0 — Draft

**Auditable Independent-Future Challenge**  
Status: `DRAFT / NOT YET EXTERNAL-BENCH FROZEN`  
Normative keywords: MUST, MUST NOT, SHOULD, MAY.

## 1. Purpose

AIFC specifies an auditable experiment for testing whether an immutable witness fixed before target generation contains exact information about a later independently generated random target beyond a declared forward-causal guessing bound.

AIFC does not assume or establish retrocausality, faster-than-light signalling, closed timelike curves, precognition, or any other physical mechanism.

## 2. Core objects

For trial `i`:

- `run_id_i`: globally unique trial identifier.
- `R_i`: PRE_RETURN candidate object frozen before target generation.
- `C_i`: canonical set of all admissible exact candidate values frozen for the trial.
- `K_i = |C_i|`: candidate multiplicity.
- `F_{i-1}`: complete pre-target side information available to the candidate process, operator, verifier, witnesses, and admitted adversary before target generation.
- `T_i`: future target generated only after the freeze certificate is complete.
- `p_i`: history-wise upper bound on `max_t P(T_i=t | F_{i-1})`.
- `a_i = min(1, K_i p_i)`: admitted exact-hit probability bound.
- `Q_i`: external witness quorum certificate for the frozen PRE_RETURN state.
- `E_i`: target-generation / entropy evidence.
- `X_i = 1[T_i in C_i]`: exact-hit indicator.

## 3. Canonical hard witness

The strongest AIFC grade MUST use canonical bytes, not semantic similarity.

A recommended hard witness is a canonical JSON object containing at least:

```json
{
  "schema": "AIFC/hard-witness/v1",
  "run_id": "...",
  "payload128": "32 lowercase hex chars",
  "nonce128": "32 lowercase hex chars"
}
```

Canonical serialization MUST be specified before trials. A recommended default is UTF-8 JSON with lexicographically sorted keys, no insignificant whitespace, and no platform-dependent encodings.

The exact identity target MAY be the canonical object itself or a domain-separated cryptographic digest of a canonical target object, provided that choice is frozen before the future target event.

## 4. Temporal order

The following order is normative:

1. construct PRE_RETURN candidate set `C_i`;
2. freeze canonical candidate bytes;
3. obtain external freshness/quorum certificate `Q_i`;
4. only after step 3, make the designated target-producing event eligible;
5. generate target `T_i`;
6. obtain externally verifiable target/entropy evidence `E_i`;
7. run the frozen verifier;
8. publish the complete admitted transcript regardless of hit or miss.

Any evidence that the target, target seed, target-derived commitment, prefetch buffer, deterministic future state, or equivalent hard side information existed before step 3 MUST invalidate the independent-future grade for that trial.

## 5. Future-target requirement

The target-generation mechanism MUST be specified before the run.

The mechanism MUST NOT permit the operator to choose among already observed future outputs after PRE_RETURN inspection.

If a public randomness beacon is used, the future round selection rule MUST be deterministic from information frozen before the selected round output exists.

Example admissible rule:

```text
future_round = first beacon round whose scheduled publication time is
at least DELTA seconds after a valid PRE_RETURN quorum certificate.
```

`DELTA` MUST be fixed before trials.

## 6. Conditional entropy requirement

AIFC requires a history-wise point-probability cap, not merely marginal fairness.

For every admitted trial, the evidence package MUST justify:

`max_t P(T_i=t | F_{i-1}) <= p_i` almost surely under the specified forward null.

The side-information set `F_{i-1}` MUST include all admitted classical information that could improve target guessing, including shared state, previous targets, previous failures, operator actions, public metadata, prefetch state, and any disclosed beacon state.

Average conditional guessing probability or marginal entropy MUST NOT be substituted for this history-wise condition in sequential product or optional-stopping claims unless an independent theorem explicitly justifies the substitution.

## 7. Multiplicity

All candidate values frozen before target generation MUST be counted.

If `K_i` exact candidates are admissible for trial `i`, the per-trial null cap is:

`a_i = min(1, K_i p_i)`.

Hidden candidate multiplicity, alternate decodings, selective hash functions, or operator choice among multiple frozen candidates MUST invalidate the strongest grade unless fully enumerated and charged.

AIFC SHOULD use exactly one hard candidate per trial.

## 8. Causal isolation

The experiment MUST freeze a causal model before the challenge sequence.

The hard target `T_hard` SHOULD be d-separated from the hard PRE_RETURN view `R_pre` conditional only on explicitly allowed public metadata `M_public` in the admitted causal DAG.

The threat model MUST include potential common causes and side channels, not only direct `T -> R` paths.

The audit MUST consider at least:

- shared seed or deterministic state;
- RNG prefetch;
- shared memory;
- filesystem/cache state;
- network side channels;
- shared entropy pools;
- colluding witness/entropy services;
- VM snapshots and restored process state;
- target-derived commitments;
- operator knowledge and adaptive scheduling;
- selection/reporting variables.

D-connection means structural independence is not certified. It does not itself prove that leakage occurred.

## 9. No post-selection

The rule deciding whether a trial enters analysis MUST be frozen before target outcomes are observed.

All valid initiated trials MUST produce one of:

- admitted hit;
- admitted miss;
- invalid / excluded for a preregistered technical reason;
- unresolved evidence failure.

A run MUST NOT disappear merely because its outcome is inconvenient.

## 10. External freshness and rollback resistance

A local hash chain or valid local signature authenticates presented content but does not by itself prove that the content is the latest state.

At least one freshness root MUST remain outside the experiment rollback domain.

Acceptable patterns include:

- independent append-only remote witnesses;
- non-rollbackable monotonic hardware state;
- transparency logs with independently compared heads;
- an equivalent externally rooted continuity mechanism.

If the entire trusted state can be restored by the same snapshot, that state MUST NOT serve as the sole anti-rollback root.

## 11. Witness quorum

Let:

- `n`: number of witnesses;
- `f`: maximum Byzantine witnesses admitted by the fault model;
- `q`: signatures required for a certificate.

If honest witnesses refuse to certify conflicting heads at the same logical position, conflicting certificates are excluded when:

`2q > n + f`.

Equivalent minimum quorum:

`q_min = floor((n+f)/2) + 1`.

The first external AIFC bench SHOULD use multiple genuinely independent failure domains. Multiple containers, processes, or VMs sharing one rollback root MUST NOT be counted as independent witnesses.

## 12. Sequential / anytime-valid inference

For bounded preregistered trials:

`P(exists i<=N: T_i in C_i) <= 1 - product_i (1-a_i)`.

For continuous monitoring, AIFC SHOULD use an anytime-valid e-process or another preregistered sequential method with equivalent type-I control.

One admissible factor is:

`L_i = (1-lambda_i) + lambda_i X_i/a_i`,

where `lambda_i in [0,1]` is predictable from `F_{i-1}`.

Then:

`E_n = product_i L_i`

is a nonnegative supermartingale under the admitted null, and Ville's inequality yields:

`P_0(sup_n E_n >= 1/alpha) <= alpha`.

The betting strategy, mixture, or adaptation rule MUST be specified so that all parameters used at trial `i` are predictable from the pre-target history.

## 13. Evidence admission gates

The strongest AIFC grade requires all of the following to pass:

1. exact pre-target candidate freeze;
2. post-freeze target-generation order;
3. externally supported history-wise entropy bound;
4. causal-isolation audit;
5. explicit multiplicity accounting;
6. preregistered inclusion/no-post-selection rule;
7. valid stopping/statistical method;
8. external freshness/anti-rollback continuity;
9. Byzantine-safe witness quorum under an explicit fault model;
10. verifier integrity and deterministic replay.

A missing gate MUST fail closed.

## 14. Verifier semantics

The verifier MUST distinguish asserted metadata from independently recomputed evidence.

The verifier MUST NOT promote a result merely because a transcript contains booleans such as:

```text
rng_independent=true
causal_isolation=true
external=true
```

unless the protocol defines externally checkable evidence supporting those assertions.

The verifier SHOULD reconstruct canonical hashes, candidate multiplicity, target bindings, quorum rules, evidence-grade transitions, and all deterministic predicates independently from the producer.

## 15. Verdicts

The verifier MUST NOT output `RETROCAUSALITY_PROVED`.

Normative result classes include:

- `NOT_ADMITTED`
- `STRUCTURAL_MATCH_ONLY`
- `FORWARD_NULL_COMPATIBLE`
- `FORWARD_NULL_INCOMPATIBILITY_CANDIDATE`
- `EXTERNAL_REPLICATION_REQUIRED`
- `PHYSICAL_MECHANISM_UNRESOLVED`

A threshold crossing means that the observed record is incompatible with the specified forward null **or with at least one evidence premise used to instantiate that null**. It does not identify the failed premise or a physical mechanism by itself.

## 16. Publication rule

All preregistered trials, including misses and invalidations, SHOULD be published with machine-readable evidence.

AIFC treats negative results, failed attacks, discovered leakage, and verifier counterexamples as first-class scientific outputs.

## 17. Current draft boundary

This draft is not yet the final externally frozen AIFC v1.0 protocol.

Before v1.0 release, the project requires at least:

- a standalone reference verifier;
- frozen machine-readable schemas;
- adversarial test vectors;
- one external public-randomness implementation path;
- a complete provenance manifest;
- independent review of the threat model;
- a broader scholarly/patent prior-art audit;
- a DOI-backed release.

No physical anomalous result is reported by this specification.
