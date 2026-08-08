# Scientific Assurance Lineage v0.3 — Inductive Normative Lineage Activation

Status: **DRAFT / proof-carrying tested-scope candidate**.

This version succeeds SAL v0.2 without rewriting it. It closes the next recursive authority boundary discovered after SAL v1.3 Root Closure.

## New laws

> **Authority over history requires proof of historical membership, not merely a reference to history.**

A historical authority claim is admitted only if the exact declared blob is proven to occur at the exact declared repository path in the Git tree of the claimed authority commit.

> **A later-created receipt is not self-authenticating proof of earlier authority.**

A retroactively formalized authority receipt is admitted only after independent replay of the external evidence it cites, or through an already-authoritative content-addressed provenance object whose own lineage is established.

## Attack classes

- `FALSE_HISTORICAL_TREE_MEMBERSHIP`
- `HISTORICAL_ROOT_COMMIT_MEMBERSHIP_REBINDING`
- `PREDECESSOR_ROOT_REGISTRY_MEMBERSHIP_REBINDING`
- `RETROACTIVE_AUTHORITY_RECEIPT_SELF_ASSERTION`
- `AUTHORITY_RECEIPT_WORKFLOW_PROVENANCE_REBINDING`
- `AUTHORITY_RECEIPT_ARTIFACT_PROVENANCE_REBINDING`
- `ACTIVATED_OBJECT_COMMIT_MEMBERSHIP_REBINDING`
- `LINEAGE_ACTIVATED_SET_REBINDING`
- `SUCCESSOR_REGISTRY_SELF_PROMOTION`
- `NEXT_GENERATION_CANDIDATE_SELF_PROMOTION`

## Inductive transition

Let `R_n` be an already content-identified predecessor authority registry at exact state `C_n`. A candidate successor registry `R_{n+1}` may activate a finite set of predecessor candidates only when a replay proves:

1. `PREDECESSOR_COMMIT_TREE_MEMBERSHIP` — historical authority objects are exact members of their claimed historical Git states;
2. `PREDECESSOR_ROOT_REGISTRY_MEMBERSHIP` — `R_n` itself is an exact member of `GitTree(C_n)`;
3. `AUTHORITY_RECEIPT_PROVENANCE` — cited workflow/artifact evidence is independently replayed and commit-bound;
4. `LINEAGE_TRANSITION_REPLAY` — only preregistered candidates change authority state and their exact object bytes are members of `C_n`;
5. `SUCCESSOR_REGISTRY_NON_SELF_PROMOTION` — `R_{n+1}` is not authorized by the transition it records.

Formally, for the activated subset `S`:

```text
Authoritative(R_n, C_n)
+ HistoricalMembershipProof
+ ReceiptProvenanceReplay
+ ExactTransitionReplay(S)
--------------------------------
Authoritative(S at C_n)
```

but **not**:

```text
Authoritative(R_{n+1})
```

The successor registry remains a candidate for a later independent lineage step.

## Current exact transition

Predecessor exact state:

```text
commit = eeee61c6143cde1bea64c643def6eaec461e7aa2
tree   = 2e939271d22d0a1906c93bd7e0fced77780aa88c
R_n    = AIFC-NORMATIVE-ASSURANCE-ROOTS-V2
blob   = d2bb7f3917f8761836825a4e80f03c1e282fc37d
```

Historical state checked transitively:

```text
commit = 7e58b47398fe585b24db6304ee6122871095d668
R_v1   = 0aec9d6ad0d54ce10d312d28a8cb0def1729f835
```

Activated predecessor candidates are exactly:

```text
AIFC-SCHEMA-IDENTITY-REGISTRY-V3
AIFC-INHERITED-GATE-OBLIGATION-HASH-V1-IMPLEMENTATION-BINDING-V1
AIFC-RELEASE-GATE-v1.0.10-draft
```

The produced `AIFC-NORMATIVE-ASSURANCE-ROOTS-V3` remains `SUCCESSOR_REGISTRY_CANDIDATE_REQUIRES_NEXT_LINEAGE_ATTESTATION`.

## Release frontier

Strict additive extension:

```text
78 -> 83
```

with the five gates listed above. Gate-definition historical anchoring, atom semantic identity, general Authority-Closed Proof, real successor wrapped replay, historical key lifecycle, Implementation A, AIFC v1 freeze, platform trust, general normative-root lineage and global novelty remain outside the established claim.
