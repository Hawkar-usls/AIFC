# Entropy Admission Policy

Status: `NORMATIVE DRAFT SUPPLEMENT`

The central statistical premise of AIFC is a history-wise point-probability bound:

```text
max_t P(T_i=t | F_{i-1}) <= p_i.
```

The number `p_i` is not accepted merely because a target has a nominal bit length.

A second, subtler problem is that the **method used to justify `p_i` can itself become a post-target degree of freedom**. For example, after observing the target, an operator could choose whichever source model, security argument, empirical estimate or side-information interpretation yields the most favorable bound.

AIFC therefore separates:

```text
AIFC/entropy-policy/v1       experiment-level admissible method
AIFC/entropy-profile/v1      trial-specific proof object
```

## Experiment-level entropy policy

The experiment plan freezes the entropy policy before the first `CREATED` slot.

It binds:

- source identity;
- source protocol version;
- allowed derivation/security methods;
- conditioning-view role;
- required external evidence classes;
- optional derivation-spec evidence;
- treatment of unresolved assumptions;
- explicit prohibition on post-target method selection.

For strongest-grade v1:

```text
post_target_method_selection_forbidden = true
unresolved_assumptions_policy = BLOCK_STRONGEST_GRADE
```

## Trial-specific entropy profile

After the concrete target selector, derivation profile and frozen pre-target conditioning view exist, the trial entropy profile binds all of them.

The verifier must establish that the profile:

1. matches the preregistered source and version;
2. uses one of the preregistered derivation methods;
3. binds the exact frozen conditioning-view hash;
4. binds the exact selector and derivation profile;
5. carries a canonical exact-rational bound;
6. resolves every required external evidence class;
7. has no disallowed unresolved assumptions.

## What policy freeze proves

Policy freeze proves **which argument was allowed before the result was known**.

It does not prove that the argument is scientifically correct.

For example, a preregistered `PUBLIC_BEACON_SPECIFICATION` method may still fail because:

- the source security assumption is invalid;
- a precommitment leaked target-derived side information;
- the conditioning view omitted source/operator knowledge;
- the selected target event was not generated according to the claimed process;
- the cryptographic source proof is invalid;
- common infrastructure violates the declared independence model.

Those remain separate evidence gates.

## Attack class

```text
POST_TARGET_ENTROPY_METHOD_SUBSTITUTION
```

A trial that changes the entropy/security justification after target observation is not strongest-grade AIFC evidence even if the replacement bound is mathematically well formed.
