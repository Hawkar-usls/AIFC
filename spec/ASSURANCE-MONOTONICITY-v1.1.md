# AIFC Assurance Convergence v1.1

Status: **DRAFT HARDENING LAYER — NOT AIFC v1.0 FROZEN**

This document hardens the assurance-convergence law introduced in v1.0 after adversarial review found that a monotonicity checker can itself become a downgrade surface.

The governing principles remain:

> **A newer verifier MUST NOT forget a rejection learned by a mandatory predecessor.**

> **Assurance must be monotone unless the weakening itself carries proof.**

v1.1 adds trust-boundary laws:

> **The monotonicity checker must not trust the successor to define what was inherited.**

> **Proof of strengthening must be replayed by the checker, not asserted to it.**

> **A successor assurance object MUST NOT acquire identity by retroactively extending a predecessor content-hash domain.**

A successor verifier, wrapper, test harness, release script, or claimant MUST NOT provide an authoritative free-form list of predecessor obligations. The inherited obligation set is derived from frozen predecessor/successor release-gate documents plus independently proof-replayed lineage transitions.

Likewise, a caller MUST NOT provide a pre-blessed transition result carrying a claimed `STRENGTHENING_CONFIRMED` status. It may provide only content hashes of proposed transitions plus the resolver domain needed to reproduce them. The monotonicity comparator itself resolves the transition graph and executes the normative strengthening verifier.

## 1. Admission authority is a partial order

Scalar ranks are insufficient because equal rank does not imply equal scientific meaning or admission authority.

The normative machine table is:

`conformance/AIFC-ADMISSION-AUTHORITY-ORDER-v1.json`

For predecessor outcome `R_n` and successor outcome `R_{n+1}`, monotonicity requires:

```text
R_{n+1} in AllowedSuccessors(R_n)
```

The two current admitted forward-null outcomes are intentionally incomparable:

```text
FORWARD_NULL_CONSISTENT_MISS
FORWARD_NULL_INCOMPATIBILITY_CANDIDATE
```

Therefore the transition:

```text
FORWARD_NULL_CONSISTENT_MISS
    -> FORWARD_NULL_INCOMPATIBILITY_CANDIDATE
```

is rejected as:

```text
SAME_RANK_AUTHORITY_ESCALATION
```

The reverse transition is also not silently treated as a weakening; it is an incomparable semantic rewrite.

## 2. Inherited gate obligations are derived, not supplied

Let `G_n` be the mandatory predecessor gate set and `G_{n+1}` the mandatory successor gate set.

For every `g in G_n`:

- if `g in G_{n+1}`, the successor obligation remains `g`;
- if `g` is absent from `G_{n+1}`, there MUST be exactly one independently verified strengthening transition mapping `g` to mandatory successor gate IDs;
- otherwise derivation fails closed.

The resulting obligation map is content-bound together with both release-gate documents and the transition content hashes and is hashed as:

```text
inherited_gate_set_hash = SHA256(canonical derived obligation material)
```

A caller cannot omit `TRIAL_CREATION_POLICY_REPLAY`, `TERMINAL_SUBTYPE_SEMANTICS`, or any other predecessor mandatory gate by simply leaving it out of an input list.

Attack class:

```text
INHERITED_GATE_SET_OMISSION
```

## 3. Gate replacement requires executed proof replay

A structurally plausible `AIFC/gate-lineage-transition/v1` is not sufficient. A pre-blessed in-memory structure is also not sufficient.

The release-gate comparator accepts transition **content hashes**, not claimed verified transition objects. For every removal candidate, it invokes the transition verifier itself. The verifier MUST resolve:

```text
transition hash
previous_gate_definition_hash
successor_definition_hashes[]
equivalence_or_strengthening_evidence_hash
```

v1.1 defines the first executable proof profile:

```text
BOOLEAN_TRUTH_TABLE_IMPLICATION_V1
```

Gate definitions use the restricted `AIFC/gate-definition/v1` Boolean AST. The verifier exhaustively checks the full shared atom space, with at most 16 atoms in this proof profile, and confirms:

```text
AND(successor pass conditions) => predecessor pass condition
```

By contraposition:

```text
predecessor FAIL => at least one successor replacement FAIL
```

Only after this execution may the internal verifier result contain:

```text
STRENGTHENING_CONFIRMED
```

That internal result is not an authoritative caller input to the comparator.

There is deliberately no trusted `PASS` field in `AIFC/gate-strengthening-evidence/v1`.

Attack class:

```text
FAKE_GATE_STRENGTHENING_RECEIPT
```

If a gate cannot be represented by the v1 Boolean definition language, that gate is not removable under this proof profile. A future proof method requires a new versioned evidence profile; unsupported proof methods fail closed.

## 4. Assurance evidence has a new content-hash domain

The first bootstrap run exposed an evolution boundary: the new gate-definition and strengthening objects are not members of the historical v0.2 protocol hash domain. That is intentional and MUST remain true.

The historical `protocol_hash_v02()` domain map is not extended to recognize v1.1 assurance objects.

New assurance-only protocol metadata is content-addressed under:

```text
AIFC/assurance-evidence-hash/v1
```

with the dedicated domain prefix:

```text
AIFC:ASSURANCE-EVIDENCE:v1 || 0x00
```

and explicit schema-ID separation before canonical object bytes. `AssuranceEvidenceResolverV1` independently recomputes this identity and then performs strict runtime schema admission.

Current members are exactly:

```text
AIFC/gate-definition/v1
AIFC/gate-strengthening-evidence/v1
AIFC/gate-lineage-transition/v1
```

A conformance test requires the old v0.2 hash profile to continue rejecting these objects. Adding them to the old domain map would be a historical-semantics mutation rather than a valid successor extension.

## 5. Validator semantics are content-addressed

A human-readable semantics label is not a cryptographic identity.

The registered acceptance-language identity now binds:

```text
schema_id
schema dialect
schema Git blob SHA-1
raw schema SHA-256
validator semantics ID
validator semantics manifest raw SHA-256
```

`conformance/AIFC-VALIDATOR-SEMANTICS-MANIFEST-v1.json` binds the tested schema runtime source, exact CPython version, Draft 2020-12 implementation choice, format-checker policy, local/no-network reference policy, duplicate-key behavior, Unicode/source parsing policy, error-selection policy, and the exact hash-locked Python dependency set.

Thus:

```text
different validator implementation
+ same semantics label
```

is rejected as:

```text
VALIDATOR_IMPLEMENTATION_CHANGED_WITH_SAME_SEMANTICS_ID
```

## 6. Dual schema content identity

For registered schema source bytes:

```text
git_blob_sha1
```

is retained as the Git provenance locator, while:

```text
raw_schema_sha256
```

is the protocol cryptographic source identity.

Neither replaces the other.

The v2 registry preserves the same 11 critical registered schema IDs as the convergence v1 registry and binds the exact runner-recomputed raw SHA-256 for each current source file.

## 7. Registration point is not historical first appearance

`registered_immutable_at_commit` means:

> the convergence point at which this exact acceptance-language identity became registered and protected against forward mutation.

It MUST NOT be interpreted as:

> the first historical appearance of this schema ID.

Historical pre-convergence variants, if reconstructed, require separate records with status:

```text
HISTORICAL_PRE_CONVERGENCE_ONLY
```

and MUST NOT be silently substituted into strongest-grade current admission.

The current v2 registry deliberately records:

```text
first_historical_appearance_status = NOT_ESTABLISHED
```

for all 11 registered identities.

## 8. Real successor test remains mandatory

This hardening layer does not establish successor monotonicity merely by testing synthetic result dictionaries.

A future clean key-lifecycle successor must preserve the exact predecessor evidence bytes:

```text
E --V0.6--> R6
Wrap(E, L) --V0.7--> R7
```

and then prove:

```text
R7 <=_A R6
```

under the machine partial order while preserving every derived inherited rejection obligation.

The proposed architecture:

```text
AIFC/key-lifecycle-replay-envelope/v1
```

is currently **REQUIRED ARCHITECTURE / NOT YET IMPLEMENTED**. It is not established by this convergence hardening layer.

## 9. Release frontier

v1.1 extends the mandatory draft release-gate set by ID from 61 to 65 with exactly:

```text
ADMISSION_AUTHORITY_PARTIAL_ORDER_VALID
INHERITED_GATE_SET_DERIVATION
GATE_LINEAGE_EVIDENCE_RESOLUTION
VALIDATOR_SEMANTICS_CONTENT_BINDING
```

No predecessor mandatory gate is removed.

The dedicated assurance hash domain is an implementation requirement of resolver-backed gate-lineage proof replay, not a fifth independent release-gate class.

## Claim ceiling

```text
ASSURANCE_CONVERGENCE_V1_0_POST_MERGE_RECEIPT = CONFIRMED
ASSURANCE_CONVERGENCE_V1_1 = CANDIDATE_UNTIL_EXACT_HEAD_AND_POST_MERGE_ATTESTATION
REAL_SUCCESSOR_WRAPPED_REPLAY = NOT_YET_ESTABLISHED
FULL_NORMATIVE_SCHEMA_GRAPH_COVERAGE = NOT_ESTABLISHED
FULL_HISTORICAL_SCHEMA_LANGUAGE_LINEAGE = NOT_ESTABLISHED
CLEAN_V0_7_VERSIONED_ENVELOPE = REQUIRED_NOT_IMPLEMENTED
HISTORICAL_KEY_LIFECYCLE = BLOCKED
EXTERNAL_FRESHNESS_REPLAY = INCOMPLETE
IMPLEMENTATION_A_PASS = NOT_ESTABLISHED
AIFC_V1_FROZEN = FALSE
PLATFORM_TRUST_PROVEN = FALSE
PHYSICAL_RETROCAUSALITY = NOT_OBSERVED
```
