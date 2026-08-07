# AIFC Specification v1.0 — Draft 2

Status: **NORMATIVE DRAFT / NOT FROZEN**

This document supersedes `AIFC-SPEC-v1.0-draft.md` for evaluation of Verifier A replay v0.2. It does not delete or rewrite the earlier draft; the earlier file remains part of the development record.

```text
AIFC_V1_FROZEN = FALSE
IMPLEMENTATION_A_PASS = NOT_ESTABLISHED
IMPLEMENTATION_B_PASS = NOT_ESTABLISHED
PHYSICAL_RETROCAUSALITY = NOT_OBSERVED
```

AIFC specifies an auditable experiment for testing whether an immutable pre-target witness contains exact information about a later independently generated random target beyond a declared forward-causal guessing bound.

AIFC does **not** assume or establish retrocausality, faster-than-light signalling, closed timelike curves, precognition, or any physical mechanism. Its strongest machine verdict is an evidence-admission result under explicitly stated assumptions, never a physical-mechanism verdict.

> **Freeze first. Generate later. Audit everything.**

---

## 1. Normative language

The terms **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are normative.

A missing, contradictory, dangling, noncanonical, cryptographically invalid, causally unresolved, statistically unsupported, or temporally ambiguous required evidence item MUST fail closed.

Human prose, a README badge, a producer-computed boolean, a wall-clock timestamp, a Git tag, a signature without verified semantics, or a claimed SHA string MUST NOT substitute for a required machine-verifiable evidence object.

---

## 2. Threat model

AIFC assumes an adversarial producer/operator may attempt to obtain admission through:

- selective trial initiation;
- silent trial deletion or selective abort;
- hidden candidate pools;
- post-CREATED or post-generation candidate choice;
- target prefetch or pre-generation;
- post-hoc target event selection;
- post-hoc target transformation;
- post-hoc conditioning-view sanitization;
- unsupported or retrospectively chosen entropy arguments;
- shared seeds, latent common causes, side channels, or collider conditioning;
- snapshot rollback, replay, stale checkpoints, or split histories;
- witness/key rebinding, registry forks, fault-model rebinding, or same-failure-domain Sybil counting;
- ambiguous canonicalization or mathematically equivalent but byte-different probability representations;
- optional stopping, hidden multiplicity, or target-derivation multiplicity;
- dangling evidence hashes;
- self-asserted release gates;
- release-manifest / Git commit fixed points.

AIFC does not claim that software can prove the absence of every undisclosed off-system fact. Such residual trust assumptions MUST remain explicit and MUST NOT be silently converted into stronger evidence grades.

---

## 3. Protocol object identity

Every frozen AIFC protocol JSON object MUST:

1. satisfy its versioned JSON Schema;
2. satisfy the AIFC canonicalization profile;
3. be stored as its exact canonical bytes;
4. be identified by its versioned domain-separated SHA-256 content hash.

AIFC v1 MUST NOT use self-hash fields or mutual hash cycles.

Raw non-protocol evidence bytes use:

```text
SHA256(ASCII("AIFC:RAW_EVIDENCE:v1") || 0x00 || exact_bytes)
```

A resolver MUST recover exact bytes and recompute identity before an evidence hash is treated as resolved.

---

## 4. Experiment Plan: the pre-trial contract

Before the first trial slot exists, the experiment MUST freeze an `AIFC/experiment-plan/v1` object.

The plan binds at least:

- protocol version;
- fixed-horizon or anytime mode;
- trial-creation policy;
- declared trial count where applicable;
- initial witness registry;
- candidate-generation policy;
- target-selector policy;
- target-derivation policy;
- entropy-admission policy;
- causal-model hash;
- statistical-plan hash;
- publication policy;
- external-freshness policy;
- pre-target-conditioning-view policy;
- whether witness-registry reconfiguration is allowed;
- strongest-grade rule of exactly one admitted target derivation per trial.

The plan MUST have `frozen_before_first_created = true`.

### 4.1 Plan certification precedes trial creation

A plan hash existing somewhere is insufficient. Before the first `CREATED` event, independent witnesses MUST certify the exact plan hash using experiment-scoped objects:

```text
AIFC/experiment-plan-receipt/v1
AIFC/experiment-plan-quorum/v1
```

These objects MUST NOT contain a `trial_index`, because they exist before any trial slot.

The plan quorum MUST:

- bind `logical_position = EXPERIMENT_PLAN_FROZEN`;
- bind the exact experiment ID and plan content hash;
- bind the initial witness-registry hash;
- use the registry's exact `(n,f,q)` fault model;
- satisfy `2q > n + f`;
- count at least `q` distinct active witness identities;
- count at least `q` distinct admitted failure domains;
- use keys valid at registry sequence 0;
- cryptographically verify all signatures before frozen admission.

Verifier A v0.2 currently replays all listed structural/failure-domain conditions but keeps Ed25519 cryptographic verification as a blocked gate.

---

## 5. Trial creation and global ledger

For fixed-horizon experiments, the trial plan MUST declare every intended trial index before execution.

The first global ledger predecessor is:

```text
SHA256(ASCII("AIFC:EXPERIMENT_GENESIS:v1") || 0x00 || UTF8(experiment_id))
```

For the first event:

```text
state_from = null
state_to   = CREATED
payload_hash = experiment_plan_hash
prerequisite_certificate_hash = experiment_plan_quorum_hash
```

Thus the causal/preregistration chain is:

```text
EXPERIMENT_PLAN
        ↓
experiment-scoped quorum(plan hash)
        ↓
CREATED event references plan-quorum hash
        ↓
trial-scoped quorum(CREATED event hash)
        ↓
candidate production becomes eligible
```

Candidate production before both plan certification and trial-slot certification is forbidden for the strongest grade.

Every initiated slot MUST remain permanently visible. Abort, crash, timeout, source outage, invalid evidence, or refusal to continue MUST produce a visible terminal outcome rather than deletion.

The global event sequence MUST have contiguous `event_index`; each trial MUST have contiguous `transition_ordinal`; every event MUST bind the immediately preceding global event hash.

---

## 6. Trial state machine

Normal completed-trial lifecycle:

```text
CREATED
  -> PRE_RETURN_FROZEN
  -> QUORUM_CERTIFIED
  -> TARGET_ARMED
  -> TARGET_OBSERVED
  -> VERIFIED
  -> TERMINAL
```

A terminal abort MAY occur from a nonterminal state only through an allowed terminal subtype. `TERMINAL -> nonterminal` is forbidden.

Wall-clock timestamps are metadata by default. Causal eligibility is established by certified event/order relationships. If a protocol requires an actual elapsed-time constraint, that requirement MUST be carried by a separate externally justified timing profile with uncertainty semantics.

---

## 7. Candidate generation and multiplicity

A `CREATED` certificate prevents selective initiation after observing a candidate. It does not exclude a hidden precomputed pool.

The experiment plan therefore freezes an `AIFC/candidate-generation-policy/v1`.

For strongest-grade v1:

```text
operator_choice_after_created    = forbidden
operator_choice_after_generation = forbidden
```

Each trial carries an `AIFC/candidate-generation-profile/v1` bound to that policy and to the certified `CREATED` slot.

The verifier MUST resolve the candidate-generation evidence. Merely containing a 64-hex-character string is insufficient.

### 7.1 Frozen candidate set

The exact candidate opportunity set is an `AIFC/candidate-set/v1` object containing the unique canonical hashes of every admitted `AIFC/hard-witness/v1` member.

The verifier MUST independently resolve every member and recompute:

```text
K_i = len(resolved unique candidate members)
```

It MUST NOT trust a producer-supplied `candidate_multiplicity` when the set itself is available for replay.

For strongest-grade v1, unexplained candidate-selection freedom invalidates admission rather than being silently treated as `K_i = 1`.

---

## 8. PRE_RETURN freeze

The `PRE_RETURN_FROZEN` ledger event binds the candidate-set hash.

The `AIFC/pre-return-certificate/v1` MUST bind:

- experiment plan;
- candidate set;
- recomputed multiplicity;
- candidate-generation profile;
- exact freeze-event hash;
- freeze ledger head;
- PRE_RETURN quorum certificate;
- target-selector **policy** hash;
- target-derivation **policy** hash.

PRE_RETURN MUST NOT bind a concrete later derivation instance that is defined only after the trial reaches its subsequent certified state. This temporal distinction prevents a future-derived object from being smuggled into an earlier certificate.

---

## 9. Target selector: which future event?

AIFC separates:

```text
Which future event defines the challenge?
```

from:

```text
How are exact target bytes derived from that event?
```

The experiment plan freezes `AIFC/target-selector-policy/v1` before any trial.

A per-trial `AIFC/target-selector-profile/v1` MUST bind:

- selector-policy hash;
- source identity/version;
- deterministic selection algorithm;
- exact anchor role/hash;
- exact parameters;
- one selected future event ID;
- selection-transcript evidence;
- `frozen_before_target_observed = true`.

Strongest-grade v1 admits exactly one selected event per trial.

Verifier A v0.2 currently replays `FIXED_EVENT_ID_FROM_PLAN`. Other selector algorithms remain blocked until their deterministic scheduling/anchor semantics are implemented and tested.

---

## 10. Target derivation: how event bytes become T_i

The experiment plan freezes an `AIFC/target-derivation-policy/v1`.

A concrete `AIFC/target-derivation-profile/v1` MUST bind:

- policy hash;
- experiment/trial/run;
- source identity/version;
- concrete target-selector-profile hash;
- exact extraction method;
- exact transformation algorithm;
- exact typed framing;
- ordered input tokens;
- domain separator;
- output length;
- `frozen_before_target = true`.

Strongest-grade v1 permits only the frozen deterministic DSL. Current transformations are `IDENTITY` and `SHA-256`; free-text algorithms are forbidden.

The current typed framing is:

```text
uint16_be(len(ASCII(token_name)))
|| ASCII(token_name)
|| uint64_be(len(token_bytes))
|| token_bytes
```

for each frozen token in exact `input_order`.

The verifier MUST execute the derivation from resolved raw source bytes. A producer-supplied final target string is not sufficient.

If multiple target derivations are ever admitted in a later version, their opportunity multiplicity MUST be charged explicitly. Strongest-grade v1 avoids this by requiring exactly one derivation.

---

## 11. Pre-target conditioning view F_{i-1}

The point-probability claim

```text
max_t P(T_i=t | F_{i-1}) <= p_i
```

is meaningful only if `F_{i-1}` is represented and frozen before target observation.

AIFC therefore uses `AIFC/pre-target-conditioning-view/v1`.

The view MUST bind the relevant pre-target information available by the `TARGET_ARMED` boundary, including:

- experiment plan;
- replayed ledger head;
- candidate set/profile;
- PRE_RETURN certificate/quorum;
- current witness registry;
- target selector profile;
- target derivation profile;
- causal-model hash;
- required operator-state evidence;
- required source-state evidence;
- any additional declared pre-target evidence;
- unresolved assumptions.

For strongest-grade admission, unresolved assumptions forbidden by the plan's conditioning-view policy MUST block admission.

### 11.1 View certification choreography

To avoid a self-certification hash cycle:

```text
QUORUM_CERTIFIED ledger head
        ↓
build PRE_TARGET_CONDITIONING_VIEW
        ↓
hash(view)
        ↓
trial quorum certifies view hash
        ↓
TARGET_ARMED.payload_hash = hash(view quorum)
        ↓
target observation becomes eligible
```

The view MUST NOT contain the hash of the quorum that signs it.

---

## 12. Entropy admission policy and trial-specific p_i evidence

The scientific burden of AIFC is not the phrase “256-bit RNG.” It is the justified history-wise bound:

```text
max_t P(T_i=t | F_{i-1}) <= p_i.
```

The experiment plan MUST freeze an `AIFC/entropy-policy/v1` before any trial.

The policy defines:

- admissible source identity/version;
- allowed derivation/security methods for the bound;
- required external evidence classes;
- conditioning-view role;
- unresolved-assumption rule;
- optional derivation-spec evidence;
- prohibition on choosing the entropy/security justification after target observation.

Each trial then carries an `AIFC/entropy-profile/v1`.

For strongest-grade admission, the verifier MUST establish that the profile:

1. matches the frozen source/version;
2. uses a preregistered allowed derivation method;
3. binds the concrete target-selector profile;
4. binds the concrete target-derivation profile;
5. binds the frozen pre-target conditioning-view hash;
6. carries the exact canonical rational point-probability upper bound;
7. resolves every required external evidence class;
8. contains no unresolved assumptions prohibited by policy.

A signature proves provenance/attestation. It does not by itself prove unpredictability.

---

## 13. Canonical rational p_i

Probability bounds MUST be represented as exact reduced decimal rationals.

Examples:

```text
1/2  valid
2/4  invalid
01/02 invalid
0/1  canonical zero
1/1  canonical one
```

The verifier MUST require no leading zeroes, positive denominator, reduced GCD, and the unique zero/one forms.

No binary floating-point value may silently replace the exact protocol rational.

---

## 14. Causal model

The causal DAG is a formal statement of the admitted model; it is not proof that physical reality contains no omitted common cause.

Every declared causal edge MUST carry evidence references.

Every critical no-edge claim MUST either:

- carry evidence references supporting its exclusion under the admitted model; or
- be represented explicitly as an unresolved assumption.

Strongest-grade admission blocks unresolved critical no-edge assumptions.

The verifier MUST independently compute required d-separation queries over the machine-readable graph. Verifier A replay v0.2 currently resolves edge/no-edge evidence but keeps the d-separation engine blocked.

---

## 15. Witness registry and quorum

For a fixed registry with `n` witnesses, at most `f` Byzantine witnesses and quorum size `q`, conflicting same-position certificates are excluded under the stated honest-signing model when:

```text
2q > n + f.
```

AIFC additionally defines independence by **failure domain**, not process count.

An admitted quorum MUST contain at least `q` distinct admitted witness identities in at least `q` distinct failure domains.

Four containers on one rollbackable host do not constitute four independent failure domains.

The verifier MUST bind certificate `(n,f,q)` to the resolved registry rather than trusting certificate-local values.

Keys MUST be replayed against registry sequence, status, rotation, revocation and compromise semantics.

Verifier A v0.2 performs membership/key-status/failure-domain structural replay, but Ed25519 signature verification remains blocked.

---

## 16. Registry reconfiguration

A hash-linked new registry alone does not prove legitimate membership transition.

Every allowed transition MUST be experiment-scoped and jointly establish:

```text
old registry quorum authorizes transition body
new registry quorum accepts transition body
```

The verifier MUST independently recompute the transition-body hash, require connected registry sequence/hash history, bind all experiment IDs, bind each quorum's `(n,f,q)` to its signing registry, verify membership/failure domains/keys and verify signatures.

A disjoint locally safe registry configuration MUST NOT be accepted without a valid connected transition certificate.

---

## 17. Target evidence and source proof

`AIFC/target-evidence/v1` binds:

- source identity;
- target-selector profile;
- target-derivation profile;
- conditioning-view hash;
- selected event ID;
- raw source-object hash;
- derived target bytes/hash;
- entropy-profile hash;
- source evidence hashes.

The resolver MUST recover exact raw source bytes. The verifier MUST execute the frozen selector/derivation and compare the result to target evidence.

Separately, the verifier MUST cryptographically validate source-specific proof that the raw object actually belongs to the claimed external future source/event. Verifier A v0.2 performs byte derivation replay but keeps source-specific beacon proof verification blocked.

---

## 18. Exact identity and multiplicity

Let `C_i` be the verified frozen candidate set with `|C_i| = K_i`.

Let the admitted history-wise point-probability cap be `p_i`.

The per-trial exact-hit cap is:

```text
a_i = min(1, K_i p_i).
```

The exact hit indicator is:

```text
X_i = 1[T_i in C_i].
```

Semantic similarity, human interpretation, nearest-neighbour distance, partial prefix matches or post-hoc decoding MUST NOT be substituted for the strongest-grade exact-byte comparison.

---

## 19. Statistical plan

The statistical rule MUST be frozen before the first `CREATED` slot in `AIFC/statistical-plan/v1`.

### 19.1 Fixed-horizon experiments

The bound

```text
P(exists i <= N : X_i = 1)
<= 1 - product_i (1 - a_i)
```

MUST be used only under the exact theorem conditions declared by the frozen plan, including a deterministic or preregistered admissible cap sequence as specified by the AIFC v1 draft policy.

A second implementation MUST NOT infer broader adaptive validity from the formula merely because each marginal cap looks small.

### 19.2 Adaptive / anytime experiments

For history-dependent predictable operation or continuous monitoring, AIFC uses an anytime-valid e-process or another explicitly frozen sequential method whose assumptions are independently verified.

One supported mathematical template is:

```text
L_i = (1-lambda_i) + lambda_i X_i/a_i
E_n = product_i L_i
```

with predictable `lambda_i` and history-wise valid `a_i`, yielding the Ville threshold bound under its assumptions.

If `a_i = 0`, the verifier MUST take an explicit zero-cap branch and MUST NOT evaluate `X_i/a_i`.

Verifier A v0.2 validates the fixed statistical-plan structure and per-trial `a_i` construction but keeps full experiment-wide statistical/e-process replay blocked.

---

## 20. Evidence resolver

A content hash is not self-authenticating merely because it has 64 hexadecimal characters.

The scientific verifier MUST expose the conceptual operation:

```text
resolve(content_hash)
  -> exact preserved bytes
  -> declared/verified content type
  -> strict parse where applicable
  -> canonical-byte equality where applicable
  -> independent domain-separated identity recomputation
  -> resolved evidence object
```

A dangling hash, path escape, type rebinding, noncanonical stored protocol JSON, malformed UTF-8 or content-hash mismatch MUST fail closed.

Locators/URLs are metadata only until bytes are retrieved and verified.

---

## 21. Evidence bundle and terminal choreography

A completed trial deliberately avoids a bundle/terminal fixed point.

The directed order is:

```text
TARGET_OBSERVED
   -> VERIFIED event
   -> per-trial EVIDENCE_BUNDLE binds VERIFIED head
   -> TERMINAL event binds evidence-bundle hash
```

The evidence bundle MUST NOT point forward to the experiment-level publication manifest.

For a completed exact miss, terminal subtype is `COMPLETED_MISS`.

For a completed exact hit, terminal subtype is `COMPLETED_HIT`.

Invalid/aborted trials use the explicit terminal subtypes defined by the state machine and remain published.

---

## 22. Publication manifest

After relevant trials terminate, an `AIFC/publication-manifest/v1` MUST enumerate every declared/created trial required by the frozen publication policy.

It binds:

- experiment plan;
- publication policy;
- declared trial count;
- final global ledger head;
- each trial index;
- terminal event hash;
- terminal subtype;
- evidence-bundle hash where applicable;
- external publication root;
- external publication receipts.

The publication manifest points backward to terminal/bundle evidence. Trial bundles do not point forward to it.

`COMPLETE_TRIAL_PUBLICATION` is therefore intended to become a machine-verifiable property, not an author promise.

---

## 23. Release choreography

A final source commit cannot safely contain a manifest field equal to that same commit's SHA without defining a fixed-point convention.

AIFC v1 therefore uses two stages:

```text
1. Freeze immutable source commit S.
2. Build out-of-tree AIFC/release-manifest/v1 referring to source_commit = S.
3. Resolve and verify every required gate evidence hash.
4. Compute external domain-separated release-manifest content identity.
5. Publish GitHub Release / archive record that binds S and the manifest identity.
```

The source tree MUST NOT be modified after creating the manifest and still be called the same frozen source release.

A future frozen workflow MUST execute the release-manifest verifier. It MUST NOT authorize a release solely because `conformance/AIFC-RELEASE-GATE*.json` contains `status = FROZEN_PASS`.

---

## 24. Machine verdicts versus research-program grades

A trial verifier result and the maturity of an entire research program are different objects.

Machine trial verdicts MAY include classes such as:

```text
INVALIDATED_EVIDENCE
NOT_ADMITTED
STRUCTURAL_MATCH_ONLY
FORWARD_NULL_CONSISTENT_MISS
FORWARD_NULL_INCOMPATIBILITY_CANDIDATE
```

A machine trial verdict MUST NOT emit `RETROCAUSALITY_PROVED`.

Separate human/research-program grades MAY summarize replication maturity, physical calibration, independent implementations, external benches or cross-laboratory evidence. Such grades MUST NOT be encoded as if they were a single-trial statistical verdict.

---

## 25. Current Verifier A v0.2 boundary

The v0.2 development path is intended to replay increasingly more evidence from exact bytes rather than producer declarations.

Candidate/implemented structural replay includes:

- experiment-plan preregistration chain;
- content-addressed resolver;
- fixed-horizon ledger continuity;
- candidate set and multiplicity;
- candidate provenance;
- fixed-event selector;
- pre-target conditioning view;
- frozen entropy-policy admission;
- target derivation from raw source bytes;
- causal evidence resolution;
- registry membership/fault/failure-domain structure;
- publication completeness;
- bundle/terminal choreography.

The following remain explicit blockers for full Implementation A:

```text
ED25519_SIGNATURE_CRYPTO
CAUSAL_D_SEPARATION
TARGET_SOURCE_CRYPTOGRAPHIC_PROOF
FULL_EXPERIMENT_STATISTICAL_REPLAY
ANYTIME_EPROCESS_REPLAY
BYTE_IDENTICAL_CANONICALIZATION_WITH_IMPLEMENTATION_B
FROZEN_MACHINE_READABLE_CORPUS
FULL_RELEASE_MANIFEST_EVIDENCE_RESOLUTION
```

A green v0.2 replay is therefore evidence of implemented admission/rejection logic, not evidence of a physical future-information effect.

---

## 26. Frozen-release rule

`AIFC v1.0 FROZEN` MUST remain false until every required frozen release-gate class has machine-verifiable PASS evidence, including at least:

- experiment plan certified before CREATED;
- full ledger/publication continuity;
- candidate provenance/multiplicity;
- conditioning-view admission;
- target selector/derivation replay;
- entropy policy/profile admission;
- causal admission and d-separation;
- witness signatures/key lifecycle/failure-domain quorum;
- source-specific cryptographic target proof;
- full statistical replay;
- two independent implementations;
- byte-identical canonicalization;
- fail-open zero;
- external bench evidence outside Genesis;
- resolved proof-carrying release manifest.

Until then:

```text
AIFC_V1_FROZEN = FALSE
```

---

## 27. Scientific interpretation

A fully admitted threshold crossing would establish only that the observed record is incompatible with the specified forward-causal null **or with at least one of the premises used to admit that null**.

It would not by itself identify retrocausality, FTL, CTCs, precognition or any physical mechanism.

AIFC remains scientifically useful if every external experiment returns null: it can still expose leakage, multiplicity, weak entropy, rollback, post-selection, causal-model defects, witness failures, source-proof failures or statistical misuse.

Negative results and protocol failures are first-class outputs.
