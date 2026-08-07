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
- `CGP_i`: proof-carrying candidate-generation profile bounding hidden selection freedom.
- `F_{i-1}`: complete pre-target side information available to the candidate process, operator, verifier, witnesses, and admitted adversary before target generation.
- `T_i`: future target generated only after the freeze certificate is complete.
- `TDP_i`: frozen target-derivation profile mapping a selected future source event to exact target bytes.
- `p_i`: history-wise upper bound on `max_t P(T_i=t | F_{i-1})`.
- `a_i = min(1, K_i p_i)`: admitted exact-hit probability bound.
- `L_e`: experiment-wide append-only trial ledger.
- `Q_i`: external witness quorum certificate for the frozen PRE_RETURN state.
- `EP_i`: proof-carrying entropy profile justifying `p_i`.
- `CM_i`: machine-readable causal model bound to the trial/experiment policy.
- `WR_k`: versioned witness registry at sequence `k`.
- `RTC_k`: joint registry-transition certificate from `WR_k` to `WR_{k+1}`.
- `TE_i`: target-generation evidence.
- `B_i`: complete trial evidence bundle.
- `X_i = 1[T_i in C_i]`: exact-hit indicator.

## 3. Canonical hard witness

The strongest AIFC grade MUST use canonical bytes, not semantic similarity.

The v1 hard witness conforms to [`../schemas/hard-witness.schema.json`](../schemas/hard-witness.schema.json).

Hash-critical AIFC v1 objects MUST follow [`CANONICALIZATION.md`](CANONICALIZATION.md). Canonicalization is normative, not implementation-defined.

The exact identity target MAY be the canonical object itself or a domain-separated cryptographic digest of a canonical target object, provided the exact transformation is frozen in `TDP_i` before the future target event.

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

A trial slot MUST be externally certified as `CREATED` **before candidate production begins**.

The following operational order is normative:

1. create and externally certify the next trial slot in the global ledger;
2. instantiate/bind `CGP_i` and produce candidates only under its admitted process;
3. freeze canonical candidate bytes, multiplicity, `CGP_i`, target selector, and `TDP_i`;
4. obtain external freshness/quorum certificate `Q_i` over the PRE_RETURN state;
5. only after step 4, make the predetermined target-producing event eligible;
6. observe the raw future source object;
7. derive exact `T_i` only by the already-frozen `TDP_i`;
8. obtain externally verifiable target/entropy evidence and `EP_i`;
9. run the frozen verifier;
10. append and externally bind the terminal ledger event;
11. publish the complete evidence bundle regardless of hit, miss, abort, or invalidation.

Any evidence that target data, target-derived commitments, future source output, a hidden candidate pool, or an uncharged post-hoc derivation choice was available outside the declared process MUST fail the strongest independent-future grade.

## 5. Global trial ledger and experiment genesis

AIFC MUST maintain an experiment-wide append-only sequence conforming to [`../schemas/trial-ledger-event.schema.json`](../schemas/trial-ledger-event.schema.json) and [`../docs/TRIAL_LEDGER.md`](../docs/TRIAL_LEDGER.md).

The first ledger event has one deterministic predecessor:

```text
SHA256(ASCII("AIFC:EXPERIMENT_GENESIS:v1") || 0x00 || UTF8(experiment_id))
```

No empty, all-zero, newline-terminated, or implementation-defined first predecessor is permitted.

The ledger MUST expose missing, aborted, invalidated, retried, replayed, and terminal trials. A certified initiated slot can never silently disappear or be renumbered.

A local hash chain is insufficient as the sole proof of continuity; required ledger heads MUST be rooted outside the experiment rollback domain.

## 6. Candidate provenance and shadow-pool control

Certified `CREATED` prevents selective trial initiation after observing a candidate, but it does not alone exclude candidates generated before or outside the visible trial process.

Every strongest-grade trial MUST bind an `AIFC/candidate-generation-profile/v1` object conforming to [`../schemas/candidate-generation-profile.schema.json`](../schemas/candidate-generation-profile.schema.json).

`CGP_i` MUST bind the certified slot, generator identity/version, relevant pre-created state commitment, candidate-set cardinality upper bound, operator selection freedom, external evidence, assumptions, and unresolved assumptions.

If a hidden candidate pool or undeclared off-system selection freedom cannot be excluded or bounded under the admitted threat model, the verifier MUST fail closed or charge the larger defensible multiplicity. It MUST NOT silently accept `K_i=1`.

See [`../docs/CANDIDATE_PROVENANCE.md`](../docs/CANDIDATE_PROVENANCE.md).

## 7. Future-target selection and derivation

The target-generation mechanism MUST be specified before the run.

The mechanism MUST NOT permit the operator to choose among already observed future outputs after PRE_RETURN inspection.

If a public randomness beacon is used, the future round selection rule MUST be deterministic from information frozen before the selected round output exists.

Separately, the exact mapping from the raw future source object to `T_i` MUST be frozen in an `AIFC/target-derivation-profile/v1` object conforming to [`../schemas/target-derivation-profile.schema.json`](../schemas/target-derivation-profile.schema.json).

`TDP_i` MUST specify raw source-object schema, extraction rule, transformation algorithm/input order, domain separator and output length. `PRE_RETURN`, `EP_i`, and `TE_i` MUST bind the same derivation-profile hash.

A transformation chosen or modified after target observation is post-hoc multiplicity and invalidates the strongest grade unless all alternatives were preregistered and statistically charged.

See [`../docs/TARGET_DERIVATION.md`](../docs/TARGET_DERIVATION.md).

AIFC SHOULD prefer externally verifiable event/round ordering over local wall-clock timing. If elapsed time is part of the requirement, the experiment MUST satisfy [`TIME_AND_ORDERING.md`](TIME_AND_ORDERING.md).

## 8. Conditional entropy evidence and canonical rational bounds

AIFC requires a history-wise point-probability cap, not merely marginal fairness.

For every admitted trial, an `AIFC/entropy-profile/v1` object conforming to [`../schemas/entropy-profile.schema.json`](../schemas/entropy-profile.schema.json) MUST justify:

`max_t P(T_i=t | F_{i-1}) <= p_i` almost surely under the specified forward null.

The entropy profile MUST bind the source/version, deterministic target selector, `TDP_i`, complete conditioning-view hash, exact rational point-probability upper bound, derivation method, supporting evidence, assumptions, and unresolved assumptions.

Rational probability bounds MUST use the unique reduced representation in [`CANONICALIZATION.md`](CANONICALIZATION.md): no leading zeros, positive denominator, `0 <= numerator <= denominator`, gcd equal to one, zero exactly `0/1`, and one exactly `1/1`.

A signature can prove provenance of an entropy claim; it does not by itself prove unpredictability. See [`../docs/ENTROPY_EVIDENCE.md`](../docs/ENTROPY_EVIDENCE.md).

Average conditional guessing probability or marginal entropy MUST NOT be substituted for the history-wise condition unless an independent theorem explicitly justifies the substitution.

## 9. Multiplicity

All candidate values and all admissible target derivations frozen for a trial MUST be accounted for.

If `K_i` exact candidates are admissible for trial `i`, the per-trial null cap is:

`a_i = min(1, K_i p_i)`.

Hidden candidate multiplicity, alternate decodings, selective hash functions, operator choice, or multiple uncharged target transformations MUST invalidate the strongest grade unless fully enumerated and charged.

AIFC SHOULD use exactly one hard candidate and one target derivation per trial.

## 10. Machine-readable causal isolation

The experiment MUST freeze a machine-readable causal model before the challenge sequence or bind a versioned model policy applicable to the trial.

The model MUST conform to [`../schemas/causal-model.schema.json`](../schemas/causal-model.schema.json) and [`../docs/CAUSAL_MODEL.md`](../docs/CAUSAL_MODEL.md).

The strongest grade requires the declared d-separation query under the forward-causal DAG. The threat model MUST include common causes, prefetch, shared state, operator knowledge, target-derived commitments and selection variables.

D-separation success certifies structure only under the declared model. It does not prove physical causal-model completeness.

## 11. No post-selection / selective abort

Every externally certified `CREATED` slot MUST reach a visible terminal state, including explicit abort/invalidation states.

A run MUST NOT disappear because its outcome is inconvenient, target arming was selectively refused, or a crash occurred after candidate visibility.

The complete global trial ledger is the proof-carrying mechanism for this rule.

## 12. External freshness and rollback resistance

A local hash chain or valid local signature authenticates presented content but does not by itself prove that the content is the latest state.

At least one freshness root MUST remain outside the experiment rollback domain. If the entire trusted state can be restored by the same snapshot, it MUST NOT serve as the sole anti-rollback root.

## 13. Witness registry, quorum, keys, and reconfiguration

Witness identity and key validity MUST conform to [`../schemas/witness-registry.schema.json`](../schemas/witness-registry.schema.json) and [`WITNESS_LIFECYCLE.md`](WITNESS_LIFECYCLE.md).

Individual receipts and quorum certificates MUST conform to their typed schemas. Quorum receipt items MUST resolve through `witness-receipt.schema.json`; untyped receipt objects are not admissible.

For a fixed registry, safety requires:

`2q > n + f`.

Every registry transition after sequence `0` MUST resolve to an `AIFC/registry-transition-certificate/v1` object conforming to [`../schemas/registry-transition-certificate.schema.json`](../schemas/registry-transition-certificate.schema.json).

The transition MUST be jointly certified: the old registry quorum authorizes the exact new registry hash, and the new registry quorum accepts the exact old registry/transition. A hash link alone is not authorization.

The verifier MUST reject unauthorized reconfiguration, disjoint configuration forks, sequence jumps, stale-registry extensions, and replayed transition certificates.

## 14. Sequential / anytime-valid inference

For bounded preregistered trials:

`P(exists i<=N: T_i in C_i) <= 1 - product_i (1-a_i)`.

For continuous monitoring, AIFC SHOULD use an anytime-valid e-process or another preregistered sequential method with equivalent type-I control.

For positive `a_i`, one admissible factor is:

`L_i = (1-lambda_i) + lambda_i X_i/a_i`,

where `lambda_i in [0,1]` is predictable from `F_{i-1}`.

If `a_i = 0`, the verifier MUST take an explicit zero-cap branch and MUST NOT evaluate division by zero. An observed hit at zero admitted probability is a contradiction of the instantiated null/premises, not an invitation to implementation-defined arithmetic.

## 15. Evidence bundle

A complete trial bundle MUST bind the exact hashes of the ledger state, PRE_RETURN certificate, `CGP_i`, `TDP_i`, entropy profile, causal model, witness registry/transition state, target evidence, candidate set/multiplicity, statistical state where applicable, and publication manifest.

The bundle MUST conform to [`../schemas/evidence-bundle.schema.json`](../schemas/evidence-bundle.schema.json).

## 16. Evidence admission gates

The strongest AIFC grade requires all applicable gates to pass, including:

1. certified trial creation before candidate production;
2. deterministic ledger genesis and continuous trial ledger;
3. admitted candidate-generation provenance / shadow-pool control;
4. exact pre-target candidate freeze;
5. frozen target selector and target-derivation profile;
6. post-freeze target-generation order;
7. externally supported history-wise entropy profile with canonical rational bound;
8. machine-readable causal-isolation audit;
9. explicit multiplicity accounting;
10. valid stopping/statistical method;
11. external freshness/anti-rollback continuity;
12. Byzantine-safe witness quorum, key lifecycle, and authorized registry transitions;
13. canonicalization conformance;
14. verifier integrity and deterministic replay.

A missing or contradictory gate MUST fail closed.

## 17. Verifier semantics

The verifier MUST distinguish asserted metadata from independently recomputed evidence and MUST NOT promote a result merely because a transcript contains self-asserted booleans.

The verifier SHOULD reconstruct canonical hashes, ledger continuity/genesis, candidate provenance, candidate multiplicity, target selector/derivation, entropy bounds/rational canonicality, d-separation, registry transitions, quorum/key rules, evidence-grade transitions, and all deterministic predicates independently from the producer.

Verifier output MUST conform to [`../schemas/verifier-result.schema.json`](../schemas/verifier-result.schema.json).

## 18. Verdicts

The verifier MUST NOT output `RETROCAUSALITY_PROVED`.

Normative machine result classes are constrained by the verifier-result schema and include `NOT_ADMITTED`, `STRUCTURAL_MATCH_ONLY`, `FORWARD_NULL_CONSISTENT_MISS`, `FORWARD_NULL_INCOMPATIBILITY_CANDIDATE`, and `INVALIDATED_EVIDENCE`.

A threshold crossing means that the observed record is incompatible with the specified forward null **or with at least one evidence premise used to instantiate that null**. It does not identify a physical mechanism by itself.

## 19. Publication rule

Every externally certified `CREATED` trial MUST be represented in the published global ledger with a terminal state.

All completed trial evidence bundles, misses, hits, aborts, invalidations, discovered leakage, failed attacks, and verifier counterexamples MUST be preserved under the frozen publication policy.

## 20. Conformance and proof-carrying v1.0 freeze

Repository-level draft conformance is checked by `tools/check_repo_conformance.py` and `.github/workflows/draft-conformance.yml`.

The machine-readable release gate is [`../conformance/AIFC-RELEASE-GATE-v1.json`](../conformance/AIFC-RELEASE-GATE-v1.json).

A release MUST NOT be labeled `AIFC v1.0 FROZEN` merely because a status field, tag, badge, or CI job says so.

The release MUST carry an `AIFC/release-manifest/v1` object conforming to [`../schemas/release-manifest.schema.json`](../schemas/release-manifest.schema.json). Every required release gate MUST appear exactly once with machine-verifiable result, evidence hash, verifier identity/version, and run/commit binding. `FROZEN_PASS` is admissible only if every required gate is `PASS` and every evidence binding verifies.

See [`../docs/RELEASE_MANIFEST.md`](../docs/RELEASE_MANIFEST.md).

## 21. Current draft boundary

This draft is not yet the final externally frozen AIFC v1.0 protocol.

The machine-readable object set and deeper provenance/derivation rules exist as draft, but are not frozen and have not yet been cross-implemented.

Before v1.0 release, the project still requires at least:

- standalone reference verifier implementation;
- independent second implementation;
- frozen adversarial and canonicalization test vectors;
- one external public-randomness implementation path;
- proof-carrying release manifest with per-gate PASS evidence;
- independent review of the threat model and entropy assumptions;
- broader scholarly/patent prior-art audit;
- DOI-backed release.

No physical anomalous result is reported by this specification.
