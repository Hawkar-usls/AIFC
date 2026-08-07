# AIFC Specification v1.0 — Draft

**Auditable Independent-Future Challenge**  
Status: `DRAFT / NOT YET EXTERNAL-BENCH FROZEN`  
Normative keywords: MUST, MUST NOT, SHOULD, MAY.

## 1. Purpose

AIFC specifies an auditable experiment for testing whether an immutable witness fixed before target generation contains exact information about a later independently generated random target beyond a declared forward-causal guessing bound.

AIFC does not assume or establish retrocausality, faster-than-light signalling, closed timelike curves, precognition, or any other physical mechanism.

## 2. Core objects

For experiment `e` and trial `i`:

- `experiment_id`: stable experiment identifier.
- `trial_index_i`: monotonically assigned trial slot index.
- `run_id_i`: globally unique trial identifier.
- `R_i`: PRE_RETURN candidate object frozen before target generation.
- `C_i`: canonical set of all admissible exact candidate values frozen for the trial.
- `K_i = |C_i|`: candidate multiplicity.
- `F_{i-1}`: complete pre-target side information available to the candidate process, operator, verifier, witnesses, and admitted adversary before target generation.
- `T_i`: future target generated only after the freeze certificate is complete.
- `p_i`: history-wise upper bound on `max_t P(T_i=t | F_{i-1})`.
- `a_i = min(1, K_i p_i)`: admitted exact-hit probability bound.
- `L_e`: experiment-wide append-only trial ledger.
- `Q_i`: external witness quorum certificate for the frozen PRE_RETURN state.
- `EP_i`: proof-carrying entropy profile justifying `p_i`.
- `CM_i`: machine-readable causal model bound to the trial/experiment policy.
- `WR`: versioned witness registry and key-lifecycle state.
- `TE_i`: target-generation evidence.
- `B_i`: complete trial evidence bundle.
- `X_i = 1[T_i in C_i]`: exact-hit indicator.

## 3. Canonical hard witness

The strongest AIFC grade MUST use canonical bytes, not semantic similarity.

The v1 hard witness conforms to [`../schemas/hard-witness.schema.json`](../schemas/hard-witness.schema.json) and contains at least:

```json
{
  "schema": "AIFC/hard-witness/v1",
  "experiment_id": "...",
  "run_id": "...",
  "trial_index": 1,
  "payload128": "32 lowercase hex chars",
  "nonce128": "32 lowercase hex chars"
}
```

Hash-critical AIFC v1 objects MUST follow [`CANONICALIZATION.md`](CANONICALIZATION.md). Canonicalization is normative, not implementation-defined.

The exact identity target MAY be the canonical object itself or a domain-separated cryptographic digest of a canonical target object, provided that choice is frozen before the future target event.

## 4. Trial state machine and temporal order

The normative state machine is defined in [`STATE_MACHINE.md`](STATE_MACHINE.md) and machine-readable form in [`../conformance/state-machine-v1.json`](../conformance/state-machine-v1.json).

The normal path is:

```text
CREATED
-> PRE_RETURN_FROZEN
-> QUORUM_CERTIFIED
-> TARGET_ARMED
-> TARGET_OBSERVED
-> VERIFIED
-> TERMINAL
```

Crucially, a trial slot MUST be externally certified as `CREATED` **before candidate production begins**. This prevents selective trial initiation after inspecting candidate content.

The following operational order is normative:

1. create and externally certify the next trial slot in the global ledger;
2. construct PRE_RETURN candidate set `C_i`;
3. freeze canonical candidate bytes and multiplicity;
4. obtain external freshness/quorum certificate `Q_i`;
5. only after step 4, make the predetermined target-producing event eligible;
6. generate target `T_i`;
7. obtain externally verifiable target/entropy evidence and `EP_i`;
8. run the frozen verifier;
9. append and externally bind the terminal ledger event;
10. publish the complete evidence bundle regardless of hit, miss, abort, or invalidation.

Any evidence that the target, target seed, target-derived commitment, prefetch buffer, deterministic future state, or equivalent hard side information existed before the freeze MUST invalidate the independent-future grade for that trial.

## 5. Global trial ledger

AIFC MUST maintain an experiment-wide append-only sequence conforming to [`../schemas/trial-ledger-event.schema.json`](../schemas/trial-ledger-event.schema.json) and [`../docs/TRIAL_LEDGER.md`](../docs/TRIAL_LEDGER.md).

The ledger MUST expose missing, aborted, invalidated, retried, replayed, and terminal trials. A certified initiated slot can never silently disappear or be renumbered.

For fixed-horizon experiments, planned trial indices SHOULD be preregistered. For open-ended experiments, each new slot MUST be certified before candidate visibility under a frozen slot-creation rule.

A local hash chain is insufficient as the sole proof of continuity; required ledger heads MUST be rooted outside the experiment rollback domain.

## 6. Future-target requirement

The target-generation mechanism MUST be specified before the run.

The mechanism MUST NOT permit the operator to choose among already observed future outputs after PRE_RETURN inspection.

If a public randomness beacon is used, the future round selection rule MUST be deterministic from information frozen before the selected round output exists.

AIFC SHOULD prefer externally verifiable event/round ordering over local wall-clock timing. If actual elapsed time is part of the requirement, the experiment MUST satisfy [`TIME_AND_ORDERING.md`](TIME_AND_ORDERING.md), including external timing evidence and uncertainty bounds.

## 7. Conditional entropy evidence

AIFC requires a history-wise point-probability cap, not merely marginal fairness.

For every admitted trial, an `AIFC/entropy-profile/v1` object conforming to [`../schemas/entropy-profile.schema.json`](../schemas/entropy-profile.schema.json) MUST justify:

`max_t P(T_i=t | F_{i-1}) <= p_i` almost surely under the specified forward null.

The entropy profile MUST bind the source/version, deterministic target selector, complete conditioning-view hash, exact rational point-probability upper bound, derivation method, supporting evidence, assumptions, and unresolved assumptions.

The side-information set `F_{i-1}` MUST include all admitted classical information that could improve target guessing, including shared state, previous targets, previous failures, operator actions, public metadata, prefetch state, disclosed beacon state, and known history relevant to RNG rollback/reuse.

A signature can prove provenance of an entropy claim; it does not by itself prove unpredictability. See [`../docs/ENTROPY_EVIDENCE.md`](../docs/ENTROPY_EVIDENCE.md).

Average conditional guessing probability or marginal entropy MUST NOT be substituted for this history-wise condition in sequential product or optional-stopping claims unless an independent theorem explicitly justifies the substitution.

## 8. Multiplicity

All candidate values frozen before target generation MUST be counted.

If `K_i` exact candidates are admissible for trial `i`, the per-trial null cap is:

`a_i = min(1, K_i p_i)`.

Hidden candidate multiplicity, alternate decodings, selective hash functions, or operator choice among multiple frozen candidates MUST invalidate the strongest grade unless fully enumerated and charged.

AIFC SHOULD use exactly one hard candidate per trial.

## 9. Machine-readable causal isolation

The experiment MUST freeze a machine-readable causal model before the challenge sequence or bind a versioned model policy applicable to the trial.

The model MUST conform to [`../schemas/causal-model.schema.json`](../schemas/causal-model.schema.json) and the rules in [`../docs/CAUSAL_MODEL.md`](../docs/CAUSAL_MODEL.md).

The strongest grade requires a structural query equivalent to:

`T_hard ⟂d R_pre | M_public`

under the declared forward-causal DAG.

The threat model MUST include potential common causes and side channels, not only direct `T -> R` paths. It MUST consider at least:

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

The verifier MUST independently evaluate the declared d-separation query and reject forbidden collider/post-selection conditioning.

D-separation success certifies structure only under the declared model. It does not prove physical causal-model completeness.

## 10. No post-selection / selective abort

The rule deciding whether a trial enters analysis MUST be frozen before target outcomes are observed.

Every externally certified `CREATED` slot MUST reach a visible terminal state, including explicit abort/invalidation states from the state machine.

A run MUST NOT disappear because its outcome is inconvenient, because target arming was selectively refused, or because a crash happened after candidate visibility.

The complete global trial ledger is the proof-carrying mechanism for this rule; a prose declaration of `all trials were reported` is insufficient.

## 11. External freshness and rollback resistance

A local hash chain or valid local signature authenticates presented content but does not by itself prove that the content is the latest state.

At least one freshness root MUST remain outside the experiment rollback domain.

Acceptable patterns include:

- independent append-only remote witnesses;
- non-rollbackable monotonic hardware state;
- transparency logs with independently compared heads;
- an equivalent externally rooted continuity mechanism.

If the entire trusted state can be restored by the same snapshot, that state MUST NOT serve as the sole anti-rollback root.

## 12. Witness registry, quorum, and key lifecycle

Witness identity and key validity MUST conform to [`../schemas/witness-registry.schema.json`](../schemas/witness-registry.schema.json) and [`WITNESS_LIFECYCLE.md`](WITNESS_LIFECYCLE.md).

Individual receipts and quorum certificates MUST conform to:

- [`../schemas/witness-receipt.schema.json`](../schemas/witness-receipt.schema.json)
- [`../schemas/quorum-certificate.schema.json`](../schemas/quorum-certificate.schema.json)

Let:

- `n`: number of witnesses;
- `f`: maximum Byzantine witnesses admitted by the fault model;
- `q`: signatures required for a certificate.

If honest witnesses refuse to certify conflicting heads at the same logical position, conflicting certificates are excluded when:

`2q > n + f`.

Equivalent minimum quorum:

`q_min = floor((n+f)/2) + 1`.

Witnesses are counted by stable identity/failure domain, not by process or key count. Key rotation, revocation, compromise intervals, stale-witness reconciliation, and same-position equivocation MUST be auditable.

## 13. Sequential / anytime-valid inference

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

## 14. Evidence bundle

A complete trial bundle MUST bind the exact hashes of the ledger state, PRE_RETURN certificate, entropy profile, causal model, witness registry, target evidence, candidate set/multiplicity, statistical state where applicable, and publication manifest.

The bundle MUST conform to [`../schemas/evidence-bundle.schema.json`](../schemas/evidence-bundle.schema.json).

Target evidence MUST conform to [`../schemas/target-evidence.schema.json`](../schemas/target-evidence.schema.json).

## 15. Evidence admission gates

The strongest AIFC grade requires all of the following to pass:

1. certified trial creation before candidate production;
2. exact pre-target candidate freeze;
3. post-freeze target-generation order;
4. externally supported history-wise entropy profile;
5. machine-readable causal-isolation audit;
6. explicit multiplicity accounting;
7. complete global trial-ledger continuity/no-post-selection evidence;
8. valid stopping/statistical method;
9. external freshness/anti-rollback continuity;
10. Byzantine-safe witness quorum and key lifecycle under an explicit fault model;
11. verifier integrity and deterministic replay;
12. canonicalization conformance.

A missing gate MUST fail closed.

## 16. Verifier semantics

The verifier MUST distinguish asserted metadata from independently recomputed evidence.

The verifier MUST NOT promote a result merely because a transcript contains booleans such as:

```text
rng_independent=true
causal_isolation=true
external=true
```

unless the protocol defines externally checkable evidence supporting those assertions.

The verifier SHOULD reconstruct canonical hashes, ledger continuity, candidate multiplicity, target bindings, entropy bounds, d-separation, quorum/key rules, evidence-grade transitions, and all deterministic predicates independently from the producer.

Verifier output MUST conform to [`../schemas/verifier-result.schema.json`](../schemas/verifier-result.schema.json).

## 17. Verdicts

The verifier MUST NOT output `RETROCAUSALITY_PROVED`.

Normative machine result classes are constrained by the verifier-result schema and include:

- `NOT_ADMITTED`
- `STRUCTURAL_MATCH_ONLY`
- `FORWARD_NULL_CONSISTENT_MISS`
- `FORWARD_NULL_INCOMPATIBILITY_CANDIDATE`
- `INVALIDATED_EVIDENCE`

A threshold crossing means that the observed record is incompatible with the specified forward null **or with at least one evidence premise used to instantiate that null**. It does not identify the failed premise or a physical mechanism by itself.

## 18. Publication rule

Every externally certified `CREATED` trial MUST be represented in the published global ledger with a terminal state.

All completed trial evidence bundles, misses, hits, aborts, invalidations, discovered leakage, failed attacks, and verifier counterexamples MUST be preserved under the frozen publication policy.

AIFC treats negative results as first-class scientific outputs.

## 19. Conformance and v1.0 freeze

Repository-level draft conformance is checked by `tools/check_repo_conformance.py` and `.github/workflows/draft-conformance.yml`.

The machine-readable release gate is [`../conformance/AIFC-RELEASE-GATE-v1.json`](../conformance/AIFC-RELEASE-GATE-v1.json).

A release MUST NOT be labeled `AIFC v1.0 FROZEN` unless every required release gate is backed by machine-verifiable PASS evidence, including:

- honest-vector acceptance;
- attack-vector expected rejection;
- zero fail-open cases;
- two independent verifier implementations;
- byte-identical canonicalization test vectors;
- complete trial publication proof;
- externally rooted bench evidence.

## 20. Current draft boundary

This draft is not yet the final externally frozen AIFC v1.0 protocol.

The Phase-1 machine-readable schema set now exists as draft, but it is not frozen and has not yet been cross-implemented.

Before v1.0 release, the project still requires at least:

- standalone reference verifier implementation;
- independent second implementation;
- frozen adversarial and canonicalization test vectors;
- one external public-randomness implementation path;
- complete release/provenance manifest;
- independent review of the threat model and entropy assumptions;
- broader scholarly/patent prior-art audit;
- DOI-backed release.

No physical anomalous result is reported by this specification.
