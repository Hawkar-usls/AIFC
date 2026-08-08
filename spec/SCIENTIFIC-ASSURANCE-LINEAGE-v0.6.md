# Scientific Assurance Lineage v0.6 — Authoritative Semantic Compilation

Status: **research formalization candidate**. This document does not establish global novelty, AIFC v1 freeze, Implementation A admission, authority-closed finite induction, or a general normative-root lineage theorem.

This successor preserves all earlier SAL claim ceilings and adds a theorem-construction boundary discovered by the v1.6 predecessor semantic-entailment audit.

## Authoritative Theorem Construction Principle

> **A theorem is admissible for normative entailment only if its exact content is deterministically derived from authority-lineage-bound semantic inputs under a content-identified and authority-admissible compilation profile.**

Equivalently:

```text
authoritative symbols != authoritative theorem
compiler identity        != compiler authority
```

A proof or countermodel is admissible only after the machine has established the provenance and authority of the semantics, their complete normative coverage, the authority of the compilation rules, the deterministic derivation of the exact theorem, and the content identity of the resulting formulas.

## Production-path prohibition

A production normative-entailment API MUST NOT accept caller-supplied:

- premise formula;
- target formula;
- semantic anchors;
- semantic compiler implementation;
- preconstructed normative formula objects.

The production input is limited to identities of the predecessor, target profile, and immutable entailment question. All semantic inputs and theorem artifacts are resolved and derived internally.

Conceptually:

```text
audit(predecessor_identity, target_profile_identity, entailment_question_id)
```

## Entailment-question identity

The question is independent of later compilation machinery.

```text
Q = H_D(
  predecessor artifact identity,
  target-profile identity,
  entailment method
)

D = AIFC:ENTAILMENT-QUESTION:v1 || 0x00
```

Compiler/profile/formula identities are evidence about whether an answer to `Q` is admissible. They MUST NOT silently create a different question.

Current exact question:

```text
Q = 994c979c702b81a0940f28b8039ad36cb48060c426f42eb1f333bf1630e473b6
```

It binds exact predecessor `AIFC-RELEASE-GATE-v1.0.9-draft` blob `e46cfee9...`, exact target `AIFC-LINEAGE-TRANSITION-PROFILE-V1` blob `f096dbbb...`, and `ANCHOR_GATED_FINITE_PROPOSITIONAL_IMPLICATION_V1`.

## Historical semantic-anchor provenance

A later interpretation of historical normative text MUST bind:

```text
historical artifact identity
historical commit
historical path
historical Git blob
exact typed semantic locus
hash of the located value
interpretation origin
interpretation status
authority-lineage status
```

The following is forbidden:

```text
RETROACTIVE_DISCOVERY_OF_PREEXISTING_EXECUTABLE_SEMANTICS = TRUE
```

A later formalization may be an `INTERPRETATION_CANDIDATE` or later become an authority-ratified interpretation through a valid authority lineage. It MUST NOT rewrite history by claiming that its executable semantics physically or normatively existed in the historical commit merely because the underlying text did.

## Semantic locator binding

Binding a whole historical blob is insufficient. Every interpretation anchor MUST bind an exact semantic locus.

Current locator classes are deliberately narrow:

```text
REQUIRED_CHECK_ID
FORBIDDEN_SHORTCUT_EXACT
PROFILE_FIELD
```

A locator must resolve with the required cardinality and its located value must match the recorded content hash. Ambiguous resolution blocks compilation.

```text
deterministic ambiguity != semantic authority
AMBIGUITY => BLOCKED
```

## Normative semantic coverage

Individually sound anchors are insufficient if a limiting normative clause is omitted. For each compilation input:

```text
Coverage(CompiledSemantics)
=
RequiredNormativeSemanticSurface
```

Exact set equality is required. Subset acceptance is forbidden.

This is the semantic analogue of inherited-gate omission protection.

## Semantic compilation profile

The semantic compiler has two independent properties:

1. **content identity** — exact implementation and profile bytes are bound;
2. **normative authority** — the profile has authority to define the semantics-to-formula translation.

The first does not imply the second.

Current candidate profile binds:

```text
AIFC-SEMANTIC-COMPILATION-PROFILE-V1
AIFC:SEMANTIC-COMPILATION-PROFILE:v1
FINITE_PROPOSITIONAL_AND_OR_NOT_ATOM_V1
EXACT_TYPED_LOCATOR_PLUS_LOCATED_VALUE_HASH_V1
EXACT_SET_EQUALITY_NO_OMISSION_V1
AMBIGUITY_BLOCKS_COMPILATION
UNSUPPORTED_CONSTRUCT_BLOCKS_COMPILATION
```

and exact source identities for `reference/verifier/semantic_compiler_v1.py`.

Its current authority state is intentionally:

```text
compiler_authority_status = SUCCESSOR_CREATED_COMPILER_IDENTITY_ONLY
profile_authority_status  = SUCCESSOR_CANDIDATE_REQUIRES_PREDECESSOR_AUTHORITY
```

Therefore compiler identity is established as a candidate mechanism while compiler authority is not.

## Formula content identity

Compiled theorem objects use a dedicated domain-separated identity:

```text
AIFC/semantic-formula/v1
AIFC:SEMANTIC-FORMULA:v1 || 0x00
```

The verifier does not merely trust stored hashes. It recompiles the AST and atom bindings from the resolved anchors and candidate profile, then recomputes formula content identities.

Current deterministic candidate products are:

```text
PREDECESSOR_FORMULA_CONTENT_HASH
= b8d4771e7fc598ef3398b6995323fbd8d0b3b9f8b86b1b8b736d990527a88353

TARGET_PROFILE_FORMULA_CONTENT_HASH
= 74f0bac1ee3c2229fff6f1b92e1c02fc4a9439c43ab56bc6d199b261c7def047
```

These hashes establish deterministic candidate construction under the current profile. They do not independently confer normative authority on that construction.

## Solver-admissibility predicate

Normative solver execution is admissible only after semantic closure:

```text
SolverAdmissible(Q) iff
    QuestionIdentity(Q)
  & HistoricalSemanticAnchorProvenance
  & SemanticAnchorAuthority
  & CompilerContentIdentity
  & CompilerAuthority
  & NormativeSemanticCoverage
  & PredecessorFormulaDerivation
  & TargetFormulaDerivation
  & FormulaContentIdentity
```

If semantic closure is not satisfied:

```text
solver_invocation_count = 0
```

This is an executable invariant, not merely a result-label convention.

> **Countermodel search is a privilege earned by semantic closure.**

## External result semantics

The scientific result surface remains three-valued:

```text
PROVED
BLOCKED
REFUTED_BY_COUNTERMODEL
```

`BLOCKED` carries machine-readable subtypes such as:

```text
BLOCKED_UNANCHORED_SEMANTICS
BLOCKED_UNAUTHORIZED_INTERPRETATION
BLOCKED_SEMANTIC_COMPILATION_PROFILE
BLOCKED_SEMANTIC_COVERAGE_AUTHORITY
BLOCKED_AMBIGUOUS_SEMANTIC_COMPILATION
```

A `REFUTED_BY_COUNTERMODEL` result is forbidden until semantic closure authorizes solver execution.

## Current v1.7 intended state

The v1.7 layer is designed to establish candidate provenance, exact locator binding, exact semantic coverage, deterministic formula derivation, question preservation, formula content identity, and the caller-formula prohibition.

It is **not** designed to self-ratify the later interpretations or semantic compiler.

Therefore the current expected result is:

```text
HISTORICAL_SEMANTIC_ANCHOR_PROVENANCE
= PASS_CANDIDATE_PROVENANCE

NORMATIVE_SEMANTIC_COVERAGE
= PASS_CANDIDATE_EXACT_COVERAGE

SEMANTIC_COMPILATION_PROFILE_CONTENT_IDENTITY
= PASS

SEMANTIC_COMPILATION_PROFILE_AUTHORITY
= NOT_ESTABLISHED_SUCCESSOR_CANDIDATE

SEMANTIC_ANCHOR_TO_FORMULA_BINDING
= PASS_DETERMINISTIC_CANDIDATE_DERIVATION

ENTAILMENT_QUESTION_IDENTITY_PRESERVED
= PASS

CALLER_SUPPLIED_NORMATIVE_FORMULA_FORBIDDEN
= PASS

SOLVER_EXECUTION_GATED_BY_SEMANTIC_CLOSURE
= PASS

SOLVER_INVOCATION_COUNT
= 0

PREDECESSOR_SEMANTIC_ENTAILMENT
= BLOCKED_UNAUTHORIZED_INTERPRETATION
```

A green v1.7 conformance run with this `BLOCKED` result is the expected strong outcome. It MUST NOT be relabeled as semantic entailment `PROVED`.

## Attack classes

The v1.7 layer explicitly targets:

```text
SEMANTIC_ANCHOR_TO_FORMULA_REBINDING
PREDECESSOR_SEMANTICS_COMPILATION_REBINDING
TARGET_PROFILE_TO_FORMULA_REBINDING
ENTAILMENT_THEOREM_SUBSTITUTION
RETROACTIVE_SEMANTIC_INTERPRETATION_REBINDING
SEMANTIC_LOCATOR_REBINDING
NORMATIVE_SEMANTIC_COVERAGE_OMISSION
CALLER_SUPPLIED_NORMATIVE_FORMULA
SOLVER_EXECUTION_BEFORE_SEMANTIC_CLOSURE
COMPILER_IDENTITY_AS_AUTHORITY
```

## Claim ceiling

SAL v1.7 does not by itself establish:

```text
GATE_DEFINITION_HISTORICAL_ANCHOR = NOT_ESTABLISHED
GATE_ATOM_SEMANTIC_IDENTITY = NOT_ESTABLISHED
AUTHORITY_CLOSED_PROOF_GENERAL = NOT_ESTABLISHED
SEMANTIC_COMPILATION_PROFILE_AUTHORITY = NOT_ESTABLISHED
AUTHORITY_CLOSED_FINITE_INDUCTION = NOT_YET_ESTABLISHED
FIRST_AUTHORITY_CLOSED_NORMATIVE_INDUCTIVE_STEP = NOT_YET_ESTABLISHED
NORMATIVE_ROOT_LINEAGE_GENERAL = NOT_ESTABLISHED
HISTORICAL_REPLAY_ENVIRONMENT_IDENTITY_GENERAL = NOT_ESTABLISHED
EXOGENOUS_AUTHORITY_EPOCH_NECESSITY = NOT_YET_ESTABLISHED
REAL_SUCCESSOR_WRAPPED_REPLAY = NOT_YET_ESTABLISHED
HISTORICAL_KEY_LIFECYCLE = BLOCKED
IMPLEMENTATION_A_PASS = NOT_ESTABLISHED
AIFC_V1_FROZEN = FALSE
PLATFORM_TRUST_PROVEN = FALSE
SAL_GLOBAL_NOVELTY = NOT_ESTABLISHED
```

No `SAL_AUTHORITY_EPOCH_0` and no external bootstrap ratification are created by this layer.

## Governing distinction

> **A theorem cannot inherit semantic authority merely because its symbols do.**

Authority of meaning is not yet authority of inference. The construction of the exact theorem supplied to a prover must itself have an admissible semantic and authority lineage.
