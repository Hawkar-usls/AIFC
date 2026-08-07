# AIFC Threat Model

This document defines the adversarial conditions AIFC is designed to detect, reject, or explicitly leave unresolved.

AIFC assumes that extraordinary claims about future information are especially vulnerable to ordinary explanations that can survive superficial timestamp, signature, or randomness checks.

## 1. Security objective

An admitted AIFC trial should make the following statement auditable:

> The exact candidate bytes were frozen before the target-producing event; the target retained a justified history-wise unpredictability bound relative to the complete pre-target information set; and no admitted forward-causal leakage, post-selection, rollback, multiplicity, or witness-equivocation path explains the exact match within the stated null model.

AIFC does not claim that this objective is equivalent to proving a physical retrocausal mechanism.

## 2. Adversary classes

### A. Direct information leakage

Examples:

- target bytes copied into PRE_RETURN memory;
- shared filesystem or cache;
- network side channel;
- IPC/shared memory;
- operator disclosure;
- beacon response cached before freeze.

**Required response:** invalidate causal isolation.

### B. Hidden common cause

A target and PRE_RETURN may be statistically dependent without any direct `target -> PRE_RETURN` path.

Examples:

```text
shared_seed ──> PRE_RETURN
     └────────> target
```

or a shared deterministic state, synchronized entropy pool, restored VM snapshot, or common orchestration process.

**Required response:** model latent/common causes; directed-path-only checks are insufficient.

### C. RNG pre-generation / prefetch

The target is generated early and merely revealed later.

Examples:

- operating-system random buffer filled before freeze;
- PRNG future stream fixed by a shared state already accessible;
- future beacon value mirrored into a cache;
- hardware entropy samples pre-collected before PRE_RETURN.

**Required response:** the independent-future grade fails unless the target-generation claim is redefined and its entropy premise remains valid relative to all pre-target state.

### D. Target-derived precommit side information

A commitment or digest of the future target is available before freeze.

Even if cryptographically hard to invert, such a commitment is still target-derived side information and must be represented in the causal/entropy model.

**Required response:** strongest independent-future grade fails unless the protocol explicitly proves that the side information cannot reduce the admitted guessing entropy to an unacceptable level.

### E. Candidate multiplicity

The experiment presents one apparent prediction but actually froze many candidates, encodings, hashes, semantic interpretations, or selection rules.

**Required response:** count all exact candidate values using `K_i`; hidden multiplicity invalidates the grade.

### F. Post-selection / selective reporting

A trial enters the dataset only because its outcome looks impressive.

Causal pattern:

```text
target ──> selected_for_analysis <── PRE_RETURN
```

Conditioning on the collider can create apparent dependence from independent variables.

**Required response:** preregister inclusion and publish all initiated valid trials.

### G. Optional stopping / repeated peeking

The researcher monitors ordinary p-values or coincidence counts and stops when a threshold looks impressive.

**Required response:** preregister a fixed horizon or use an anytime-valid e-process / equivalent sequential method.

### H. Entropy overclaim

The source is called "256-bit random" because its output has 256 bits, while conditional predictability is much higher.

Examples:

- biased source;
- correlated rounds;
- state compromise;
- history-dependent entropy collapse;
- average min-entropy used where a worst-history cap is required.

**Required response:** require a history-wise point-probability bound relative to the complete pre-target information set.

### I. Snapshot rollback

The experiment is restored to an earlier valid state after a later state existed.

A local hash chain and valid signatures may still verify because the old state is genuinely authentic.

**Required response:** require freshness rooted outside the rollback domain.

### J. Replay

An old valid PRE_RETURN, target, receipt, or certificate is replayed as if it belonged to the current trial.

**Required response:** bind every artifact to unique `run_id`, logical position, witness state, target event, and freshness context.

### K. Fork / split history

Two conflicting histories share a valid prefix and each receives apparently valid local evidence.

**Required response:** external head comparison, transparency/gossip, or a Byzantine-safe witness quorum.

### L. Witness collusion

Some external witnesses certify conflicting states.

**Required response:** explicit fault model `(n,f,q)` satisfying `2q > n+f` for conflicting-certificate safety under the stated honest-witness rule.

### M. Timestamp-only attack

A clock is changed, backdated, or desynchronized.

A clock attack may falsify event ordering without leaking target bits.

**Required response:** treat ordering/provenance evidence separately from information-isolation evidence. A clock anomaly is not automatically a future-information channel.

### N. Adaptive future-round selection

After viewing PRE_RETURN or early beacon outputs, the operator chooses which later round counts.

**Required response:** future event/round selection must be deterministic from pre-outcome frozen information.

### O. Semantic degrees of freedom

A vague prediction is mapped after the fact to whichever outcome looks closest.

**Required response:** strongest grade uses canonical exact bytes. Semantic experiments require separate preregistered scoring and cannot inherit exact-bit evidence grades.

### P. Verifier self-certification

A producer writes metadata such as `independent=true` and the verifier trusts it.

**Required response:** independent reconstruction; assertions cannot promote evidence without externally checkable support.

### Q. Compromised entropy authority

The randomness service or its signing key is compromised, or the service can choose outputs after seeing PRE_RETURN.

**Required response:** degrade or reject the entropy premise. A valid signature proves provenance, not unpredictability.

## 3. Trust boundaries

AIFC distinguishes at least four failure domains:

1. **Candidate domain** — creates PRE_RETURN.
2. **Witness domain** — certifies freeze/freshness.
3. **Entropy domain** — produces future target.
4. **Verification/publication domain** — independently validates and preserves evidence.

For the strongest experiment, these should not collapse onto one rollbackable host, one administrator, one seed state, or one storage substrate.

## 4. What AIFC cannot prove internally

Software alone cannot prove that the physical causal DAG is complete.

AIFC therefore treats claims such as the following as external scientific premises that require evidence:

- true physical isolation;
- hardware entropy quality;
- absence of undocumented shared state;
- integrity of external witnesses;
- correctness of time-source calibration;
- absence of undisclosed operator information.

The protocol's purpose is to expose these assumptions rather than hide them.

## 5. Failure semantics

A failed threat-model gate does not mean fraud and does not prove leakage occurred.

It means only:

```text
THE CLAIM IS NOT ADMITTED AT THE REQUESTED AIFC EVIDENCE GRADE
```

This fail-closed distinction is fundamental to AIFC.
