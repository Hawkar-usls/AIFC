# Scientific Assurance Lineage v0.9 — Semantic Bridge Endpoint Identity Closure

Status: **research formalization candidate**. This layer does not establish a non-empty normative bridge, semantic authority, conservative solver-capacity extension, authority-closed finite induction, Implementation A admission, AIFC v1 freeze, platform trust, or global novelty.

SAL v1.7 prohibited theorem substitution. SAL v1.8 prohibited treating a convenient abstraction as normative semantics. SAL v1.9 required the exact bridge relation to be executed by the prover. SAL v1.10 closes the next boundary:

> **Correct execution of a semantic bridge does not prove correct identification of the meanings it connects.**

## Endpoint identity law

A bridge atom is not semantically identified merely because its executable atom ID matches a name used by the prover.

For predecessor endpoints:

```text
role = PREDECESSOR_ATOM
=>
atom in Atoms(P)
and
declared_semantic_identity = CanonicalPredecessorBinding[atom]
```

For target endpoints:

```text
role = TARGET_ATOM
=>
atom in Atoms(T)
and
declared_semantic_identity = CanonicalTargetBinding[atom]
```

Therefore:

> **A semantic bridge must preserve the identity of its endpoints, not merely reuse their executable names.**

Attack classes:

```text
BRIDGE_ATOM_SEMANTIC_IDENTITY_REBINDING
BRIDGE_ATOM_ROLE_REBINDING
```

## Bridge-derived atom isolation

A bridge-derived atom is a new semantic object, not an alias for an existing theorem endpoint.

```text
role = BRIDGE_DERIVED_ATOM
=>
atom not in Atoms(P) union Atoms(T)
```

Every derived atom must resolve a separate content-identified derivation object binding:

```text
entailment question
atom ID
semantic identity
source semantic identities
derivation kind
derivation content hash
authority status
authority-lineage reference
```

Candidate derivations remain non-authoritative. Authority-admissible derived semantics require an independently replayed authority lineage.

Attack classes:

```text
BRIDGE_DERIVED_ATOM_COLLISION
BRIDGE_DERIVED_ATOM_PROVENANCE_OMISSION
BRIDGE_DERIVED_OBJECT_SEMANTIC_IDENTITY_REBINDING
```

## Successor bridge language

SAL v1.10 introduces `AIFC/semantic-bridge-axiom/v2`.

The v1 schema remains historical and immutable. It is not mutated to acquire endpoint-identity semantics.

The successor language keeps the finite executable AST:

```text
ATOM
NOT
AND
OR
```

but binds every executable atom to one of three role-specific semantic forms:

```text
PREDECESSOR_ATOM
TARGET_ATOM
BRIDGE_DERIVED_ATOM
```

The first two must resolve exact canonical formula bindings. The third must be namespace-disjoint and carry a derivation-object reference.

## Endpoint-closed execution

The v1.10 production prover entry is:

```text
bridge_bound_entailment_v2(P, B, T, ...)
```

It first verifies endpoint identity and derived-atom provenance, then constructs:

```text
P_B = P and B_1 and ... and B_n
```

Only `P_B` is eligible for the finite prover.

The production API remains identity-only. Caller-supplied formulas, atom bindings, semantic identities, bridge objects, resolvers, or solvers are not accepted.

Current bridge theory v3 is intentionally empty, so endpoint checking is vacuous on the current scientific theorem. Separate attack vectors establish that the enforcement mechanism rejects endpoint identity rebinding, role rebinding, and derived-atom collision.

## Semantic authority self-assertion

A successor object cannot acquire semantic authority by changing a status string.

Forbidden inference:

```text
successor says AUTHORITY_ADMISSIBLE
=>
successor is authority
```

SAL v1.10 deliberately contains no authority-promotion resolver. Its production path therefore carries an unconditional blocker:

```text
BLOCKED_SEMANTIC_AUTHORITY_STATUS_LINEAGE
```

A later successor may remove that blocker only by replacing it with independently replayed, root-closed authority-lineage resolution.

Attack class:

```text
SEMANTIC_AUTHORITY_STATUS_SELF_ASSERTION
```

Current status:

```text
SEMANTIC_AUTHORITY_STATUS_LINEAGE = NOT_ESTABLISHED
```

## Immutable method capacity

The issued question remains:

```text
Q = 994c979c702b81a0940f28b8039ad36cb48060c426f42eb1f333bf1630e473b6
```

Its logical method label remains:

```text
ANCHOR_GATED_FINITE_PROPOSITIONAL_IMPLICATION_V1
```

The existing content-identified method profile remains immutable with:

```text
max_atoms = 16
```

Current bridge-aware theorem size is:

```text
|Atoms(P) union Atoms(B) union Atoms(T)| = 18
```

The old profile must not be rewritten to `max_atoms = 32` or any other value under the same identity.

## First-class conservative capacity extension

SAL v1.10 introduces the candidate object:

```text
AIFC/entailment-method-capacity-extension/v1
```

A future capacity extension is admissible only if it establishes all of:

```text
old-domain result equivalence
same-question logical-semantics preservation
capacity for the exact resolved bridge-aware theorem
authority lineage
```

Conceptually, if `M_16` is the frozen supported domain and `M_N` is the extension:

```text
M_16 subset M_N
```

and for every formula pair in the old supported domain:

```text
Result_old(F) = Result_extended(F)
```

The extension must also bind the exact resolved theorem size:

```text
N >= |Atoms(P) union Atoms(B) union Atoms(T)|
```

It is not sufficient to preserve the historical count `18`, because a future non-empty bridge may add atoms.

Current extension state:

```text
resolved_bridge_aware_atom_count = null
extended_max_atoms = null
old_domain_result_equivalence_status = NOT_ESTABLISHED
same_question_method_semantics_preservation_status = NOT_ESTABLISHED
bridge_aware_extended_capacity_status = NOT_ESTABLISHED
extension_authority_status = SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE
authority_lineage_status = NOT_ESTABLISHED
```

Therefore the effective production limit remains exactly `16`.

## Release frontier

The v1.10 draft release gate is a strict additive extension:

```text
115 -> 122
```

New obligations:

```text
BRIDGE_ENDPOINT_SEMANTIC_IDENTITY
BRIDGE_ATOM_ROLE_IDENTITY_BINDING
BRIDGE_DERIVED_ATOM_PROVENANCE
SEMANTIC_AUTHORITY_STATUS_LINEAGE
ENTAILMENT_METHOD_CONSERVATIVE_CAPACITY_EXTENSION
SAME_QUESTION_METHOD_SEMANTICS_PRESERVATION
BRIDGE_AWARE_EXTENDED_CAPACITY
```

## Current expected production state

```text
BRIDGE_ENDPOINT_SEMANTIC_IDENTITY
= PASS_ENFORCEMENT_IMPLEMENTED_CURRENT_BRIDGE_EMPTY

BRIDGE_ATOM_ROLE_IDENTITY_BINDING
= PASS_STRICT_ROLE_LOOKUP_IMPLEMENTED_CURRENT_BRIDGE_EMPTY

BRIDGE_DERIVED_ATOM_PROVENANCE
= PASS_REQUIRED_BY_V2_LANGUAGE_CURRENT_BRIDGE_EMPTY

SEMANTIC_AUTHORITY_STATUS_LINEAGE
= NOT_ESTABLISHED_SELF_ASSERTION_BLOCKED

ENTAILMENT_METHOD_CONSERVATIVE_CAPACITY_EXTENSION
= NOT_ESTABLISHED_CANDIDATE_OBJECT_ONLY

SAME_QUESTION_METHOD_SEMANTICS_PRESERVATION
= NOT_ESTABLISHED

BRIDGE_AWARE_EXTENDED_CAPACITY
= BLOCKED_NO_AUTHORIZED_EXTENSION_18_GT_16

SOLVER_INVOCATION_COUNT
= 0

PREDECESSOR_SEMANTIC_ENTAILMENT
= BLOCKED_UNAUTHORIZED_INTERPRETATION
```

A green v1.10 run with this blocked scientific result is the intended strong outcome.

## Claim ceiling

SAL v1.10 does not establish:

```text
CROSS_FORMULA_SEMANTIC_BRIDGE = ABSENT
CROSS_FORMULA_SEMANTIC_BRIDGE_AUTHORITY = NOT_ESTABLISHED
SEMANTIC_ABSTRACTION_ADEQUACY = NOT_ESTABLISHED
BRIDGE_ENDPOINT_IDENTITY_PROFILE_AUTHORITY = NOT_ESTABLISHED
SEMANTIC_BRIDGE_EXECUTION_PROFILE_AUTHORITY = NOT_ESTABLISHED
SEMANTIC_AUTHORITY_STATUS_LINEAGE = NOT_ESTABLISHED
ENTAILMENT_METHOD_CONSERVATIVE_CAPACITY_EXTENSION = NOT_ESTABLISHED
SAME_QUESTION_METHOD_SEMANTICS_PRESERVATION = NOT_ESTABLISHED
BRIDGE_AWARE_EXTENDED_CAPACITY = NOT_ESTABLISHED
ENTAILMENT_QUESTION_SOURCE_DUAL_IDENTITY = NOT_ESTABLISHED
AUTHORITY_CLOSED_FINITE_INDUCTION = NOT_YET_ESTABLISHED
FIRST_AUTHORITY_CLOSED_NORMATIVE_INDUCTIVE_STEP = NOT_YET_ESTABLISHED
IMPLEMENTATION_A_PASS = NOT_ESTABLISHED
AIFC_V1_FROZEN = FALSE
PLATFORM_TRUST_PROVEN = FALSE
SAL_GLOBAL_NOVELTY = NOT_ESTABLISHED
```

## Governing law

> **A semantic bridge must prove what its endpoints mean, not merely execute over the same variable names.**
