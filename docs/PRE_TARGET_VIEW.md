# Pre-Target Conditioning View

Status: `NORMATIVE DRAFT SUPPLEMENT`

AIFC statistical claims are conditional claims. The relevant object is not merely the candidate but the complete admitted information state available before target observation.

Let that information be denoted by:

```text
F_{i-1}
```

AIFC represents the auditable part of this state using `AIFC/pre-target-conditioning-view/v1`.

## Why PRE_RETURN is too early

The PRE_RETURN freeze occurs before several pieces of pre-target information exist, including:

- PRE_RETURN quorum state;
- current registry state;
- target selector instance;
- target derivation instance;
- operator actions after freeze;
- source metadata available before target observation.

Therefore a PRE_RETURN-only conditioning hash can omit genuine side information.

## Capture boundary

The strongest-grade v1 view is constructed after PRE_RETURN quorum certification and before target observation.

The current choreography is:

```text
QUORUM_CERTIFIED ledger head
        ↓
construct complete PRE_TARGET_CONDITIONING_VIEW
        ↓
hash(view)
        ↓
independent quorum certifies view hash
        ↓
TARGET_ARMED event binds view-quorum hash
        ↓
target may be observed
```

The view MUST NOT contain the hash of the quorum that signs it; doing so would create a hash cycle.

## Required bindings

Under the frozen conditioning-view policy, the view may be required to bind:

- experiment plan;
- current ledger head;
- candidate set/profile;
- PRE_RETURN certificate/quorum;
- witness registry;
- target selector profile;
- target derivation profile;
- causal model;
- operator-state evidence;
- source-state evidence;
- additional explicitly declared pre-target evidence.

## Fail-closed rule

A verifier MUST reject strongest-grade admission if required evidence is missing or if critical unresolved assumptions remain under a policy that requires their resolution.

The attack class is:

```text
POST_HOC_CONDITIONING_VIEW_SANITIZATION
```

A clean-looking history reconstructed after target observation is not equivalent to a conditioning view externally frozen before the target became known.

## Scientific boundary

The view is an auditable representation of the admitted side information. It cannot prove that no undisclosed human/off-system fact existed. Residual assumptions about off-system information must remain explicit rather than being silently treated as entropy.
