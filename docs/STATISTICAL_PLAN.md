# Statistical Plan

Status: `NORMATIVE DRAFT SUPPLEMENT`

AIFC separates the validity of a probability bound from the validity of the sequential analysis that consumes that bound.

For trial `i`, let the verified candidate set have cardinality `K_i`, and suppose the admitted pre-target history-wise bound is:

```text
max_t P(T_i=t | F_{i-1}) <= p_i.
```

Then the exact-hit cap is:

```text
a_i = min(1, K_i p_i).
```

Both `K_i` and `p_i` are evidence-bearing quantities: `K_i` is recomputed from the resolved frozen candidate set; `p_i` is admitted only through the frozen entropy policy/profile and conditioning view.

## Fixed horizon

For the strongest fixed-horizon v1 path, the experiment plan/statistical plan must freeze the horizon and the conditions under which the product bound is invoked.

The current policy string is:

```text
ONLY_FOR_DETERMINISTIC_OR_PREREGISTERED_CAP_SEQUENCE
```

Under the corresponding theorem conditions, AIFC may use:

```text
P(exists i <= N : X_i = 1)
<= 1 - product_i (1 - a_i).
```

A verifier MUST NOT generalize this formula to an arbitrary adaptively selected cap sequence merely because every realized `a_i` appears small after the fact.

## Anytime / adaptive operation

For continuous monitoring or history-dependent predictable operation, the statistical plan must preregister an anytime-valid method.

One supported mathematical template is:

```text
L_i = (1-lambda_i) + lambda_i X_i/a_i
E_n = product_i L_i
```

where `lambda_i` is predictable from allowed past information and `a_i` is history-wise valid under the admitted null.

Under the relevant supermartingale conditions, Ville's inequality gives:

```text
P_0(sup_n E_n >= 1/alpha) <= alpha.
```

## Zero-cap branch

If `a_i = 0`, the verifier MUST NOT evaluate `X_i/a_i`.

It must branch explicitly:

```text
X_i = 0 -> zero-cap miss is structurally consistent
X_i = 1 -> contradiction with the instantiated null/premises
```

The latter is not automatically a physical-mechanism verdict; it means the observed record and admitted premises cannot all be true simultaneously.

## Multiplicity

Strongest-grade v1 uses exactly one admitted target selector and exactly one admitted target derivation per trial. Candidate multiplicity remains explicitly charged through `K_i`.

Any future protocol version that admits multiple selectors or derivations must define and charge the resulting opportunity set explicitly.

## Current implementation boundary

Verifier A v0.2 validates canonical rational structure, candidate multiplicity, `a_i` construction, zero-cap behavior and the fixed-horizon statistical-plan contract.

It does **not** yet establish:

```text
FULL_EXPERIMENT_STATISTICAL_REPLAY
ANYTIME_EPROCESS_REPLAY
```

Those remain frozen-release blockers.
