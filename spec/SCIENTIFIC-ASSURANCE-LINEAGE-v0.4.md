# Scientific Assurance Lineage v0.4 — Authority-Closure Hardening

Status: **DRAFT / proof-carrying tested-scope hardening with a preserved authority obstruction**.

This version succeeds `SCIENTIFIC-ASSURANCE-LINEAGE-v0.3.md` without rewriting it. SAL v1.4 established an executable finite lineage transition for an exact predecessor candidate set. SAL v1.5 closes three concrete implementation gaps in that transition machinery and makes the remaining authority bootstrap gap machine-visible rather than silently promoting it.

## Authority Inheritance Law

> **A transition cannot inherit authority from a predecessor unless the rules of transition are themselves inherited from authority.**

Equivalently:

> Successor-created transition semantics cannot, by their own execution, make the transition relation they define authoritative.

A valid finite replay can establish that a candidate set satisfies a successor rule. It cannot establish that the successor rule itself carries predecessor authority unless that rule, or a sufficiently strong rule that entails it, is already anchored in the authoritative predecessor lineage.

## New attack classes

SAL v0.4 freezes the following attack vocabulary:

```text
PROVENANCE_RECEIPT_CONTENT_DISCONNECT
AUTHORITY_RECEIPT_PROVENANCE_CONTENT_REBINDING
HISTORICAL_WORKFLOW_DEFINITION_REBINDING
SUCCESSOR_REGISTRY_EXTRA_RECORD_INJECTION
UNANCHORED_LINEAGE_TRANSITION_SEMANTICS
SUCCESSOR_DEFINED_ACTIVATION_AUTHORITY
ARTIFACT_BYTES_WITHOUT_SEMANTIC_REPLAY
```

## 1. Receipt ↔ provenance content binding

A later-created provenance object may not cite an arbitrary live-valid evidence set under the identifier of an authority receipt.

For every receipt `Q`, the verifier opens the exact content-identified receipt bytes and requires:

```text
receipt_id(Q) = provenance.receipt_id
source_commit(Q) = provenance.source_commit
tree(Q) = provenance.tree
WorkflowEvidence(Q) = WorkflowEvidence(provenance)
ArtifactEvidence(Q) = ArtifactEvidence(provenance)
```

The equality is schema-aware. Historical receipt v1 named workflow roles and run IDs; receipt v2 additionally named workflow names and expected conclusions. The successor provenance may add stronger identity metadata, but it cannot replace the evidence set named by the receipt.

Therefore:

```text
replay(valid evidence B) under receipt A
```

is rejected when `B != EvidenceNamedBy(A)`.

## 2. Historical workflow-definition identity

A GitHub Actions run is not identified strongly enough by a run ID and a human-readable name alone.

SAL v0.4 binds each historical workflow run to:

```text
run_id
workflow_id
workflow_path
workflow_definition_git_blob_sha1
event
head_sha
conclusion
```

and proves:

```text
GitTree(head_sha, workflow_path) = workflow_definition_git_blob_sha1
```

The live GitHub API replay must agree with the declared `workflow_id`, `workflow_path`, event, source commit and conclusion. The historical Git tree independently binds the actual workflow-definition bytes.

## 3. Exact successor-registry delta

A successor registry is not admitted merely because all predecessor records remain present and the intended activated set is correct. The complete successor record set is constrained.

For the v2 → v3 transition:

```text
RecordIDs(R_v3)
=
RecordIDs(R_v2)
∪
{
  AIFC-SCHEMA-IDENTITY-REGISTRY-V4,
  AIFC-RELEASE-GATE-v1.0.11-draft
}
```

The equality is exact. Any undeclared additional record, including an extra `ATTESTED_SUCCESSOR_AT_COMMIT` record, is a failure.

The inherited record identities remain immutable, the exact three v1.4 candidates receive only their declared authority transition, and the two new records remain exact successor candidates.

## 4. Historical artifact semantic replay

Artifact ZIP digest equality proves byte provenance but not the semantics of the evidence inside the ZIP.

SAL v0.4 therefore downloads the exact historical artifacts, creates a detached Git worktree at each artifact's attested source commit, and replays the appropriate historical verifier/checker from that exact source state.

For verifier CI attestation artifacts it executes the historical CI-attestation verifier against the extracted evidence bundle.

For platform-receipt artifacts it executes the historical platform-receipt verifier, including its GitHub/API checks.

For SAL v1.2, v1.3 and v1.4 report artifacts it verifies the archived report hash, executes the corresponding historical SAL checker from the attested source worktree, and requires byte-for-byte equality between replayed checker output and the archived report.

Thus the tested v1.5 path distinguishes:

```text
ARTIFACT_BYTES_PROVENANCE
```

from the stronger:

```text
HISTORICAL_ARTIFACT_SEMANTIC_REPLAY
```

## 5. Transition-profile authority obstruction

SAL v0.4 introduces a candidate transition profile:

```text
AIFC-LINEAGE-TRANSITION-PROFILE-V1
```

Its rules bind receipt content, workflow definitions, exact registry delta, artifact semantic replay and successor-registry non-self-promotion.

However, the authoritative predecessor root used by v1.4 is:

```text
AIFC-NORMATIVE-ASSURANCE-ROOTS-V2
blob = d2bb7f3917f8761836825a4e80f03c1e282fc37d
commit = eeee61c6143cde1bea64c643def6eaec461e7aa2
```

That exact authoritative registry contains **zero authoritative records** for:

```text
AIFC-LINEAGE-TRANSITION-PROFILE-V1
LINEAGE_TRANSITION_PROFILE
AIFC/lineage-transition-profile/v1
```

The new profile is successor-created and explicitly remains:

```text
SUCCESSOR_CANDIDATE_REQUIRES_PREDECESSOR_PROFILE_ATTESTATION
```

Therefore SAL v0.4 freezes the negative result:

```text
LINEAGE_TRANSITION_PROFILE_AUTHORITY_ANCHOR
= BLOCKED_NO_PREDECESSOR_TRANSITION_PROFILE_AUTHORITY

AUTHORITY_CLOSED_FINITE_INDUCTION
= FALSE
```

This is not treated as a failed engineering run. It is the correct fail-closed result for the current authority graph.

## Corrected interpretation of SAL v1.4

SAL v1.4 remains established as an executable finite transition in its exact tested scope:

```text
NORMATIVE_ROOT_LINEAGE_FIRST_EXECUTABLE_INDUCTIVE_STEP
= ESTABLISHED_IN_EXACT_TESTED_SCOPE

EXACT_EEEE61C_ACTIVATION_TRANSITION_REPLAY
= CONFIRMED

EXACT_ACTIVATED_SET_SATISFIES_V14_RULES
= CONFIRMED
```

But SAL v0.4 does not promote that to:

```text
FIRST_AUTHORITY_CLOSED_NORMATIVE_INDUCTIVE_STEP
```

because the transition semantics themselves are not inherited from the authoritative predecessor root.

## Release frontier

The draft release frontier is a strict additive extension:

```text
83 -> 88
```

with the five new required gates:

```text
PROVENANCE_RECEIPT_CONTENT_BINDING
HISTORICAL_WORKFLOW_DEFINITION_IDENTITY
SUCCESSOR_REGISTRY_EXACT_DELTA
LINEAGE_TRANSITION_PROFILE_AUTHORITY_ANCHOR
HISTORICAL_ARTIFACT_SEMANTIC_REPLAY
```

The first, second, third and fifth gates may be established by the v1.5 tested mechanism. The fourth remains blocked until transition semantics genuinely descend from authority.

## Bootstrap consequence

A future authority-closed lineage cannot solve the missing predecessor transition-profile authority by merely adding a stronger successor profile and then running it. That would reproduce `SUCCESSOR_DEFINED_ACTIVATION_AUTHORITY`.

A later design must instead provide a non-circular authority source for transition semantics, for example an explicitly established authority epoch/genesis that includes the transition profile from its authoritative beginning, or an already-authoritative predecessor artifact whose semantics can be shown to entail the required transition relation.

No such bootstrap is claimed in SAL v0.4.

## Claim ceiling

```text
SAL_V1_5_AUTHORITY_CLOSURE_HARDENING = TESTED_SCOPE_CANDIDATE
PROVENANCE_RECEIPT_CONTENT_BINDING = IMPLEMENTED_CANDIDATE
HISTORICAL_WORKFLOW_DEFINITION_IDENTITY = IMPLEMENTED_CANDIDATE
SUCCESSOR_REGISTRY_EXACT_DELTA = IMPLEMENTED_CANDIDATE
HISTORICAL_ARTIFACT_SEMANTIC_REPLAY = IMPLEMENTED_CANDIDATE
LINEAGE_TRANSITION_PROFILE_AUTHORITY_ANCHOR = BLOCKED_NO_PREDECESSOR_PROFILE
AUTHORITY_CLOSED_FINITE_INDUCTION = NOT_YET_ESTABLISHED
FIRST_AUTHORITY_CLOSED_NORMATIVE_INDUCTIVE_STEP = NOT_YET_ESTABLISHED
NORMATIVE_ROOT_LINEAGE_GENERAL = NOT_ESTABLISHED
GATE_DEFINITION_HISTORICAL_ANCHOR = NOT_ESTABLISHED
GATE_ATOM_SEMANTIC_IDENTITY = NOT_ESTABLISHED
AUTHORITY_CLOSED_PROOF_GENERAL = NOT_ESTABLISHED
REAL_SUCCESSOR_WRAPPED_REPLAY = NOT_YET_ESTABLISHED
HISTORICAL_KEY_LIFECYCLE = BLOCKED
IMPLEMENTATION_A_PASS = NOT_ESTABLISHED
AIFC_V1_FROZEN = FALSE
PLATFORM_TRUST_PROVEN = FALSE
SAL_GLOBAL_NOVELTY = NOT_ESTABLISHED
```
