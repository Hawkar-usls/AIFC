# AIFC Assurance Monotonicity and Protocol Lineage v1

Status: **normative convergence draft / not frozen**.

This document defines a meta-invariant for evolution of AIFC verifiers, release gates, protocol schemas, and normative profiles.

> **A newer verifier MUST NOT forget a rejection learned by a mandatory predecessor.**

More generally:

> **Assurance must be monotone unless the weakening itself carries proof.**

This is an evolution rule for evidence admission. It is not a physical claim and does not establish `IMPLEMENTATION_A_PASS` or `AIFC_V1_FROZEN`.

---

## 1. Inherited admission semantics

Let `V_n` be a mandatory predecessor verifier and `V_{n+1}` its successor. Let `D_inherited` be the domain on which the successor claims to inherit the predecessor's admission semantics after all genuinely new prerequisite gates have been satisfied.

For evidence `E` in that inherited domain:

```text
E in D_inherited
and
V_n(E) = R

implies

V_{n+1}(Wrap_valid_new_gates(E)) <=_A R
```

where `<=_A` means **no stronger by admission authority**.

The current terminal-grade ceiling order is:

```text
INVALIDATED_EVIDENCE        rank 0
NOT_ADMITTED                rank 1
STRUCTURAL_MATCH_ONLY       rank 2
FORWARD_NULL_CONSISTENT_MISS             rank 3
FORWARD_NULL_INCOMPATIBILITY_CANDIDATE   rank 3
```

A successor result with a numerically larger rank is an assurance regression.

The ordering is deliberately coarse. Two grades at the same rank are not thereby declared scientifically equivalent.

### 1.1 Mandatory gate preservation

Terminal rank alone is insufficient.

For every inherited mandatory gate that is `FAIL` under the predecessor on a frozen fixture, the successor MUST preserve that gate failure or an explicitly registered strengthening/supersession. It MUST NOT silently omit the gate and return a weaker reject-like outcome.

A predecessor `BLOCKED` gate MAY become `PASS` when the successor actually implements the missing assurance. That is strengthening, not regression.

### 1.2 Operational corpus rule

Monotonicity MUST be tested using real frozen fixtures and real verifier entry points, not mocks that merely assert one Python function called another.

Each monotonicity record SHOULD bind:

```text
predecessor_verifier
successor_verifier
fixture_hash
wrapped_fixture_hash
predecessor_outcome
successor_outcome
inherited_gate_set_hash
monotonicity_result
```

Required attack class:

```text
INHERITED_HARDENING_LAYER_OMISSION
```

Known motivating examples include:

```text
V05_DOWNGRADE_BYPASSES_TRIAL_CREATION_POLICY
V05_DOWNGRADE_BYPASSES_TERMINAL_SUBTYPE_SEMANTICS
V05_DOWNGRADE_BYPASSES_PUBLICATION_GATE_CORRECTION
```

---

## 2. Release-gate monotonicity

Let `G_n` be the semantic set of mandatory frozen-release gate IDs in release-gate generation `n`.

Default evolution law:

```text
G_n subseteq G_{n+1}
```

A later draft MAY add requirements. It MUST NOT silently delete a mandatory gate merely because that gate remains blocked.

A blocked mandatory gate is often precisely what prevents premature `FROZEN` status.

### 2.1 Explicit gate lineage transition

Removing or replacing a gate requires an `AIFC/gate-lineage-transition/v1` object containing at least:

```text
removed_gate_id
successor_gate_ids[]
previous_gate_definition_hash
successor_definition_hashes[]
equivalence_or_strengthening_evidence_hash
migration_reason
approved_protocol_version
```

`successor_gate_ids` is an array because one previous assurance may validly split into several stricter requirements.

The transition MUST provide machine-verifiable evidence that the replacement is equivalent or stronger for the inherited assurance obligation. A human migration note alone is insufficient.

Required attack class:

```text
RELEASE_GATE_REGRESSION
```

---

## 3. Immutable issued schema identity

Once evidence has been issued under a protocol schema identifier, that identifier MUST NOT acquire a different acceptance language.

The immutable identity is modeled as:

```text
(
  schema_id,
  dialect,
  exact_schema_source_content_identity,
  admission_semantics_version
)
```

The source-content identity binds exact schema bytes. The admission-semantics version binds the validator semantics used to interpret those bytes.

A strongest-grade verifier MUST bind both.

### 3.1 Semantic changes require a new identifier

If a change alters which JSON instances are admitted, a new schema identifier is required.

Examples of acceptance-language changes include:

- adding a previously forbidden property under `additionalProperties:false`;
- changing a field from optional to required or vice versa;
- changing accepted key/signature encodings;
- tightening or widening numeric/string ranges;
- changing referenced schema families;
- changing validator semantics in a way that changes accepted instances.

Required attack class:

```text
SAME_SCHEMA_ID_LANGUAGE_MUTATION
```

Historical evidence MUST remain replayable under the schema identity that actually governed it.

---

## 4. Normative profile lineage

A better design does not permit rewriting an already issued profile identifier.

```text
better design != permission to rewrite provenance
```

If a signature-preimage framing/profile has already been issued and independently replayed, an incompatible framing requires a new profile/version identifier.

The existing v0.5 direct typed preimage profile is therefore historically established **only in its tested v0.5/v0.6 scope**. A future resolver-derived or differently framed profile must use a new identifier and an explicit lineage mapping.

The version boundary SHOULD extend through the connected schema graph. If a new receipt family changes normative receipt semantics, enclosing quorum/certificate schemas must either receive new IDs or carry an explicit frozen polymorphic mapping.

Required gate:

```text
NORMATIVE_PROFILE_LINEAGE_VALID
```

---

## 5. Resolver-derived signature semantics

The cleanest future signature-preimage replay derives semantic metadata from exact resolved protocol evidence rather than accepting it as claimant-controlled input.

At minimum, a future successor profile SHOULD derive:

```text
protocol_version      <- resolved experiment plan
content_schema        <- resolved signed content object
registry_sequence     <- resolved signing registry
```

A new profile implementing this rule requires a new versioned profile/schema family if adopting it would alter already issued v1 receipt/profile acceptance semantics.

Required gate:

```text
SIGNATURE_PREIMAGE_RESOLVER_DERIVED_REPLAY
```

This gate is an evolution target and MUST NOT be retroactively claimed for the already issued v1 profile merely by rewriting its schema.

---

## 6. Current convergence boundary

At the time this invariant was introduced:

```text
v0.6 Ed25519 crypto main        = established in tested scope
historical key lifecycle        = blocked
external freshness              = blocked/incomplete
Implementation A                = not established
AIFC v1.0 frozen                = false
physical retrocausality         = not observed
```

The convergence layer does not weaken any of those ceilings.

A future key-lifecycle verifier must first preserve all mandatory v0.6/v0.3 inherited rejection semantics and all mandatory release-gate obligations.
