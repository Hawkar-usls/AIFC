# Scientific Assurance Lineage v0.5 — Predecessor Semantic Entailment Audit

Status: **DRAFT / three-state predecessor-semantics audit; no authority epoch created**.

This version succeeds `SCIENTIFIC-ASSURANCE-LINEAGE-v0.4.md` without rewriting it. SAL v1.5 established that the exact authoritative predecessor root contains no directly authoritative `AIFC-LINEAGE-TRANSITION-PROFILE-V1`. That result is now interpreted narrowly.

## Corrected bootstrap statement

The current evidence establishes:

```text
DIRECT_PREDECESSOR_TRANSITION_PROFILE_AUTHORITY
= ABSENT_CONFIRMED
```

It does **not** establish:

```text
NO_PREDECESSOR_SEMANTICS_CAN_ENTAIL_TRANSITION_PROFILE
```

The authoritative predecessor release gate `AIFC-RELEASE-GATE-v1.0.9-draft` already contains textual constraints requiring authority-closed proof, gate-definition historical anchoring, gate-atom semantic identity, and explicit prohibitions against theorem-semantics self-selection and descendant-root self-authentication.

Therefore the remaining question is semantic entailment, not direct record membership.

## Central distinction

\[
\boxed{
\text{authoritative text identity}
\neq
\text{authoritative executable semantic identity}
}
\]

Content-addressed authoritative bytes can prove what text was issued. They do not by themselves give every symbolic gate name a machine-executable semantic interpretation.

For this reason SAL v0.5 forbids interpreting a missing semantic interpretation as a proof of non-entailment.

## Three-state entailment audit

The candidate audit method is:

```text
ANCHOR_GATED_FINITE_PROPOSITIONAL_IMPLICATION_V1
```

It has exactly three scientific outcomes:

```text
PROVED
BLOCKED_UNANCHORED_SEMANTICS
REFUTED_BY_COUNTERMODEL
```

### PROVED

Only after every premise symbol has an authoritative semantic anchor may the finite propositional implication engine conclude:

\[
P_{\rm authoritative}\models T.
\]

### BLOCKED_UNANCHORED_SEMANTICS

If any authority-bearing premise symbol lacks authoritative executable semantic identity, the implication question is not yet admissible.

The current exact predecessor is in this state.

The current missing anchor identities are intentionally explicit successor-candidate names:

```text
AIFC-SEMANTIC-ANCHOR-AUTHORITY-CLOSED-PROOF-V1
AIFC-SEMANTIC-ANCHOR-GATE-DEFINITION-HISTORICAL-ANCHOR-V1
AIFC-SEMANTIC-ANCHOR-GATE-ATOM-SEMANTIC-IDENTITY-V1
```

Their absence MUST NOT be converted into `REFUTED`.

### REFUTED_BY_COUNTERMODEL

After anchoring, a non-entailment result requires a concrete finite model `M` such that:

\[
M\models P_{\rm authoritative}
\]

and:

\[
M\not\models T.
\]

The countermodel is machine output, not a prose assertion.

The current predecessor audit does not reach this state.

## Why the target profile is stronger than the old text

The candidate `AIFC-LINEAGE-TRANSITION-PROFILE-V1` requires an exact transition discipline including:

```text
candidate -> attested successor
receipt/content equality
historical workflow-definition identity
historical root membership
exact registry delta
historical artifact semantic replay
successor-registry non-self-promotion
```

The predecessor already carries anti-self-authentication constraints, but no machine proof currently establishes that its authoritative executable semantics imply this complete target profile.

Therefore:

```text
PREDECESSOR_SEMANTIC_ENTAILMENT_OF_FULL_TRANSITION_PROFILE
= BLOCKED_UNANCHORED_SEMANTICS
```

not `PROVED` and not `REFUTED`.

## Epistemic provenance versus normative-authority provenance

SAL v0.5 freezes the distinction:

\[
\boxed{
\textbf{Epistemic provenance}
\neq
\textbf{Normative-authority provenance}
}
\]

Epistemic provenance answers why an assertion is considered supported by evidence or proof.

Normative-authority provenance answers why a particular system of rules has jurisdiction to determine which conclusions are admissible.

A proof may establish:

\[
\pi:T
\]

relative to specified semantics while leaving unresolved:

\[
\operatorname{Jurisdiction}(T).
\]

## Existing bootstrap designation

SAL already contains an historical bootstrap designation:

```text
bootstrap_root_commit
=
908de7afddcf9f72c98c2b3fb696a41be1e438e0
```

Later root registry v1 designates the exact historical `v1.0.8` release gate and admission-authority order as `HISTORICAL_ROOT_AT_BOOTSTRAP_COMMIT`, and their exact blobs are members of that Git tree.

This establishes an existing **designation structure**, not retroactive discovery that the SHA objectively possessed normative authority before the designation.

Current status:

```text
EXISTING_BOOTSTRAP_ROOT_DESIGNATION
= 908de7afddcf9f72c98c2b3fb696a41be1e438e0

BOOTSTRAP_ROOT_EXTERNAL_AUTHORITY_BASIS
= IMPLICIT_NOT_YET_FIRST_CLASS

RETROACTIVE_DISCOVERY_OF_PREEXISTING_AUTHORITY
= FALSE

EXTERNAL_BOOTSTRAP_RATIFICATION
= NOT_PERFORMED
```

SAL v0.5 does not create `SAL_AUTHORITY_EPOCH_0`.

## NO_NORMATIVE_AUTHORITY_EX_NIHILO

For a finite acyclic authority-dependency graph, if the authoritative set is nonempty and every authoritative non-root node must derive authority from an authoritative predecessor, at least one authoritative source node is required.

Operational name:

```text
NO_NORMATIVE_AUTHORITY_EX_NIHILO
```

Status:

```text
BOOTSTRAP_LEMMA_UNDER_DECLARED_DAG_ASSUMPTIONS
```

This is not claimed as new graph theory. It is the explicit SAL base-case consequence of forbidding self/descendant authentication.

Human statement:

> Verification can establish what follows from authority; it cannot by itself establish where authority begins.

## Historical replay environment boundary

SAL v1.5 replays historical verifier/checker source from detached worktrees. The current tested lineage also uses one exact hash-locked dependency file blob across:

```text
7e58b473...
eeee61c...
56370d60...
5afc09e9...
```

with:

```text
requirements.lock.txt
Git blob = 1fb5b20d71b3eac742573fb3b4885537e6c512b7
```

This supports the current 9/9 historical artifact replay result and is useful continuity evidence.

It does not establish general historical execution-environment identity.

\[
\boxed{
\text{historical source replay}
\not\Rightarrow
\text{historical execution replay}
}
\]

without adequate identity for interpreter/runtime, installed dependencies, action/runtime semantics, runner state, and relevant platform behavior.

Current status:

```text
HISTORICAL_DEPENDENCY_LOCK_IDENTITY
= SAME_BLOB_CONFIRMED_IN_CURRENT_TESTED_LINEAGE

HISTORICAL_REPLAY_ENVIRONMENT_IDENTITY_GENERAL
= NOT_ESTABLISHED
```

## Release frontier

The next draft frontier is a strict additive extension:

```text
88 -> 92
```

New mandatory classes:

```text
PREDECESSOR_SEMANTIC_ENTAILMENT_AUDIT
PREDECESSOR_SEMANTIC_ANCHOR_COVERAGE
BOOTSTRAP_AUTHORITY_BASE_CASE_EXPLICITNESS
HISTORICAL_REPLAY_ENVIRONMENT_IDENTITY
```

The audit mechanism may PASS while its scientific result is `BLOCKED_UNANCHORED_SEMANTICS`. The other unresolved gates remain mandatory and must not be silently converted to PASS.

## Next route

SAL v0.5 does not introduce a new authority epoch. The route is:

```text
Predecessor Semantic Entailment Audit
        ↓
identify missing historical semantic anchors
        ↓
Gate-definition historical anchoring
        ↓
Atom / executable semantic identity
        ↓
rerun the same audit
        ↓
PROVED
or
REFUTED_BY_COUNTERMODEL
```

Only an anchored countermodel would justify concluding that the predecessor semantics cannot entail the target profile. Only then does explicit external bootstrap ratification become a demonstrated necessity for this transition path.

## Claim ceiling

```text
DIRECT_PREDECESSOR_TRANSITION_PROFILE_AUTHORITY
= ABSENT_CONFIRMED

PREDECESSOR_ANTI_SELF_AUTHENTICATION_CONSTRAINTS
= PRESENT_CONFIRMED

PREDECESSOR_SEMANTIC_ENTAILMENT_OF_FULL_TRANSITION_PROFILE
= BLOCKED_UNANCHORED_SEMANTICS

EXOGENOUS_AUTHORITY_EPOCH_NECESSITY
= NOT_YET_ESTABLISHED

EXISTING_BOOTSTRAP_ROOT_DESIGNATION
= 908de7afddcf9f72c98c2b3fb696a41be1e438e0

BOOTSTRAP_ROOT_EXTERNAL_AUTHORITY_BASIS
= IMPLICIT_NOT_YET_FIRST_CLASS

NO_NORMATIVE_AUTHORITY_EX_NIHILO
= LEMMA_CANDIDATE_UNDER_EXPLICIT_DAG_ASSUMPTIONS

HISTORICAL_REPLAY_ENVIRONMENT_IDENTITY_GENERAL
= NOT_ESTABLISHED

AUTHORITY_CLOSED_FINITE_INDUCTION
= NOT_YET_ESTABLISHED

FIRST_AUTHORITY_CLOSED_NORMATIVE_INDUCTIVE_STEP
= NOT_YET_ESTABLISHED

NORMATIVE_ROOT_LINEAGE_GENERAL
= NOT_ESTABLISHED

SAL_GLOBAL_NOVELTY
= NOT_ESTABLISHED
```
