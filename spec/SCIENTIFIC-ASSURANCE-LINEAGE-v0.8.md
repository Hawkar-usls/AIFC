# Scientific Assurance Lineage v0.8 — Semantic Bridge Execution Closure

Status: SAL v1.9 successor candidate. This document does not freeze AIFC v1,
does not establish Implementation A, and does not authorize any currently absent
semantic bridge.

## Governing law

> **Authority over a semantic relation is not enough; the proof must demonstrably use that relation.**

An authority-admissible relation `B` between predecessor semantics `P` and target
semantics `T` has no effect if the prover actually solves `P |= T`. The admissible
question after a bridge is authorized is:

\[
P \land B \models T.
\]

Therefore bridge authority and bridge execution are separate assurance obligations.

## Bridge execution closure

Let:

- `P` be the deterministically compiled predecessor formula;
- `T` be the deterministically compiled target formula;
- `B = (B_1, ..., B_k)` be the ordered bridge theory;
- `Compose(P,B)` be the exact executable composition rule bound by
  `AIFC/semantic-bridge-execution-profile/v1`.

For v1 the composition rule is:

\[
Compose(P,()) = P,
\]

and for non-empty `B`:

\[
Compose(P,B) = AND(P,B_1,\ldots,B_k).
\]

The prover is admissible only if it consumes `Compose(P,B)`. A PASS showing that
`B` has authority while the prover consumes bare `P` is a protocol failure.

## Executable bridge-axiom language

A future non-empty bridge axiom must be an
`AIFC/semantic-bridge-axiom/v1` object. Its normalized formula is restricted to
the finite classical propositional AST:

- `ATOM`
- `NOT`
- `AND`
- `OR`

Every atom in the AST must have exactly one explicit semantic binding. Unknown
operators, missing atom bindings, extra atom bindings, duplicate axiom IDs,
content-hash mismatch, source-byte mismatch, or authority mismatch fail closed.

The bridge theory references each axiom by source path, Git blob SHA-1, raw
SHA-256, and domain-separated axiom content hash.

\[
BridgeAxiomIdentity \neq BridgeAxiomAuthority.
\]

## Demonstrable semantic effect

The execution implementation contains a non-normative regression vector:

\[
A \not\models C
\]

but:

\[
A \land (\neg A \lor C) \models C.
\]

The vector exists only to prove that the bridge-bound execution path feeds the
composed premise to the finite prover. It does not create any normative bridge
axiom for the issued AIFC question.

## Bridge-aware method capacity

The relevant atom count after bridge introduction is not the historical
`Atoms(P) union Atoms(T)` count. It is recomputed from the exact composed theorem:

\[
|Atoms(P) \cup Atoms(B) \cup Atoms(T)|.
\]

Thus the current 18-atom count remains correct only while the bridge is empty.
If a future bridge introduces new atoms, those atoms increase the capacity
requirement before solver execution.

## Question source raw-SHA256 recomputation

The issued entailment question v1 remains unchanged.

A successor binding may claim `DUAL_IDENTITY_ESTABLISHED` only if:

1. the predecessor path is proven to be the expected Git blob at the exact
   historical predecessor commit;
2. the target profile path is proven to be the expected Git blob at the exact
   historical target commit;
3. SHA-256 is recomputed over the bytes of those exact bound blobs;
4. the recomputed values equal the declared raw-SHA256 values.

Two syntactically valid 64-hex strings are not proof of dual identity.

## Solver admissibility

The v1.9 production solver path is admissible only after all inherited v1.7/v1.8
closure conditions and all of the following hold:

\[
\begin{aligned}
SolverAdmissible \iff{}&
InterpretationAuthority\\
&\land CompilerAuthority\\
&\land CoverageAuthority\\
&\land SurfaceSelectionAuthority\\
&\land AbstractionAdequacy\\
&\land BridgeTheoryAuthority\\
&\land BridgeAxiomExecutableSemantics\\
&\land BridgeAxiomAuthority\\
&\land BridgeExecutionProfileAuthority\\
&\land BridgeCompositionReplay\\
&\land EntailmentMethodAuthority\\
&\land BridgeAwareMethodCapacity\\
&\land QuestionSourceDualIdentity.
\end{aligned}
\]

The only v1.9 prover entry point composes the bridge before invoking the finite
propositional solver.

## Current successor-candidate ceiling

The current bridge remains empty and non-authoritative. The new execution profile
is content-identified but successor-candidate. Exact historical raw-SHA256 values
are recomputed during the v1.9 audit, but the issued v1 question is not
retroactively mutated and the v2 source binding remains non-authoritative.

Therefore:

- `SOLVER_INVOCATION_COUNT = 0`
- `PREDECESSOR_SEMANTIC_ENTAILMENT = BLOCKED_UNAUTHORIZED_INTERPRETATION`
- `NORMATIVE_COUNTERMODEL = NOT_CLAIMED`
- `AUTHORITY_CLOSED_FINITE_INDUCTION = NOT_YET_ESTABLISHED`
- `IMPLEMENTATION_A_PASS = NOT_ESTABLISHED`
- `AIFC_V1_FROZEN = FALSE`
- `SAL_GLOBAL_NOVELTY = NOT_ESTABLISHED`
