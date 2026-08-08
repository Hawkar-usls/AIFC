# Scientific Assurance Lineage v0.7 — Semantic Abstraction Closure

Status: research formalization candidate. This document does not freeze AIFC v1, establish Implementation A, prove general authority-closed induction, or establish global novelty.

Supersedes for SAL research drafting: `spec/SCIENTIFIC-ASSURANCE-LINEAGE-v0.6.md`.

## Central law

> A proof about a model inherits normative force only after the model's relation to the norm has itself been justified.

Equivalently:

\[
\text{authoritative theorem construction}
\not\Rightarrow
\text{authority of the logical abstraction}.
\]

SAL v1.7 established a tested identity-only theorem-construction path. SAL v1.8 adds a fail-closed layer before solver execution for the semantic universe, abstraction relation, cross-formula bridge, entailment-method semantics, solver capacity, and stronger source identity of the already-issued question.

## 1. Required semantic surface is authority-bearing

Let \(U_P\) and \(U_T\) denote the required predecessor and target semantic surfaces.

Exact coverage proves only:

\[
Covered = U.
\]

It does not prove:

\[
U = CompleteNormativeSurface(Q).
\]

Therefore the object selecting \(U\) is itself authority-bearing. A successor-created surface definition may be content-identified while remaining non-authoritative.

Attack classes:

- `NORMATIVE_SEMANTIC_SURFACE_SELECTION_REBINDING`
- `REQUIRED_SEMANTIC_SURFACE_OMISSION`
- `SEMANTIC_COVERAGE_UNIVERSE_INJECTION`

## 2. Abstraction adequacy precedes normative countermodels

The current v1.7 predecessor formula is a conjunction of five `SEMANTIC_ATOM_*` atoms. The target formula is a conjunction of thirteen `TARGET_ATOM_*` atoms. Their vocabularies are disjoint.

As a proposition of classical Boolean logic, a countervaluation is therefore constructible: make every predecessor atom true and at least one target atom false.

That fact alone does **not** establish a countermodel to the normative semantics. It establishes only a countermodel to the current propositional encoding.

Frozen boundary:

```text
DISJOINT_SEMANTIC_VOCABULARY_TRIVIAL_REFUTATION
= LATENT_IF_SOLVER_PREMATURELY_ENABLED

SEMANTIC_ABSTRACTION_ADEQUACY
= NOT_ESTABLISHED
```

A model-level countervaluation may acquire normative force only after the abstraction relation is justified.

## 3. Semantic bridge theory

A cross-formula bridge is first-class:

```text
AIFC/semantic-bridge-theory/v1
```

It binds the issued question, predecessor formula identity, target formula identity, logical fragment, bridge axioms, theory identity, and authority state.

Identity is distinct from authority:

\[
BridgeIdentity \neq BridgeAuthority.
\]

The v1.8 object intentionally contains no authority-admissible bridge axioms. It records absence rather than inventing a relation.

## 4. Entailment method binding

The v1 question retains the historical method label:

```text
ANCHOR_GATED_FINITE_PROPOSITIONAL_IMPLICATION_V1
```

The question identity is not mutated.

A separate object:

```text
AIFC/entailment-method-profile/v1
```

binds that label to exact executable source identity and formal semantics, including:

- model class;
- entailment relation;
- countermodel meaning;
- normalized formula operators;
- atom bound;
- issued-question atom count;
- method authority state.

Thus:

\[
MethodIdentity \neq MethodAuthority.
\]

## 5. Capacity is a separate executable prerequisite

The current finite solver defaults to `max_atoms = 16`.

The current issued formula pair contains:

\[
5 + 13 = 18
\]

distinct atoms.

Therefore the present executable method cannot evaluate the issued formula pair under its frozen limit. The logical abstraction has a latent trivial countervaluation, but the current implementation would first fail closed on the atom limit.

Frozen boundary:

```text
ENTAILMENT_METHOD_CAPACITY_FOR_ISSUED_QUESTION
= BLOCKED_ATOM_LIMIT_18_GT_16
```

Changing `16` to a larger bound is a semantic change to the method profile and cannot occur silently under the same authority claim.

## 6. Preserve the issued question

The v1 question remains:

```text
994c979c702b81a0940f28b8039ad36cb48060c426f42eb1f333bf1630e473b6
```

It is not rewritten to add later compiler, bridge, method-profile, or SHA-256 fields.

A separate non-retroactive binding object records whether the historical Git-blob identities have also been strengthened with raw SHA-256 identities.

Current state:

```text
ENTAILMENT_QUESTION_SOURCE_DUAL_IDENTITY
= NOT_ESTABLISHED
```

Later strengthening must answer the same \(Q\), not issue a replacement question.

## 7. Solver admissibility

For SAL v1.8 the intended admissibility condition is:

\[
\begin{aligned}
SolverAdmissible(Q) \iff{}&
InterpretationAuthority\\
&\land CompilerAuthority\\
&\land CoverageAuthority\\
&\land SurfaceSelectionAuthority\\
&\land AbstractionAdequacy\\
&\land BridgeTheoryAuthority\\
&\land EntailmentMethodAuthority\\
&\land MethodCapacity(Q)\\
&\land QuestionSourceIdentity(Q).
\end{aligned}
\]

Only after all terms are authority-admissible may normative entailment evaluation execute.

The current production path therefore requires:

```text
SOLVER_INVOCATION_COUNT = 0
```

## 8. Claim ceiling

SAL v1.8 may establish tested content identity and fail-closed behavior. It does not establish:

```text
NORMATIVE_SEMANTIC_SURFACE_AUTHORITY
SEMANTIC_ABSTRACTION_ADEQUACY
CROSS_FORMULA_SEMANTIC_BRIDGE_AUTHORITY
ENTAILMENT_METHOD_AUTHORITY
ENTAILMENT_QUESTION_SOURCE_DUAL_IDENTITY
AUTHORITY_CLOSED_FINITE_INDUCTION
IMPLEMENTATION_A_PASS
AIFC_V1_FROZEN
SAL_GLOBAL_NOVELTY
```

The purpose of this layer is to prevent a formally valid proof or countermodel from answering a different, weaker abstraction-level question while being reported as a normative semantic result.
