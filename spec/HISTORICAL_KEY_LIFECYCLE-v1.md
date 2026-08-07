# AIFC Historical Key Lifecycle v1

Status: **NORMATIVE DRAFT / VERIFIER A v0.7**

This profile addresses a problem deliberately left open by registry-local Ed25519 verification:

```text
valid signature under an ACTIVE key in the signing registry snapshot
!=
proof that the key was historically uncompromised at that position
```

A later incident may establish that a key was already compromised when an older receipt was produced. AIFC therefore treats later key-lifecycle evidence as potentially retroactive evidence against already-verified certificates.

## 1. Frozen policy

Before the first trial, the experiment plan may bind:

```text
key_lifecycle_policy_hash
```

which resolves to:

```text
AIFC/key-lifecycle-policy/v1
```

Strongest v0.7 admission requires the policy even though the draft schema keeps the field optional for historical fixture readability.

The normative v1 policy uses:

```text
boundary unit = REGISTRY_SEQUENCE
compromise = invalidate signatures at or after earliest untrusted sequence
unknown compromise boundary = invalidate from registry sequence zero
revocation/retirement declaration = prospective unless represented as compromise
quorum re-evaluation = remove historically untrusted signatures and recompute q + failure domains
external completeness = mandatory
wall clock alone = insufficient
```

## 2. Lifecycle events

Known key-history changes are represented by:

```text
AIFC/key-lifecycle-event/v1
```

Event types:

```text
COMPROMISE_DISCOVERED
REVOCATION_DECLARED
RETIREMENT_DECLARED
```

Every event binds:

- experiment ID;
- global lifecycle event index;
- previous lifecycle event hash;
- witness ID and key ID;
- subject registry where the key identity is resolved;
- registry snapshot against which the event was recorded;
- recorded registry sequence;
- effective registry sequence;
- boundary basis;
- one or more resolved evidence hashes;
- reason code;
- optional wall-clock metadata.

## 3. Compromise boundary semantics

For `COMPROMISE_DISCOVERED`, the event states the earliest registry sequence from which the key can no longer be trusted.

Allowed bases:

```text
EXACT_KNOWN
CONSERVATIVE_LOWER_BOUND
UNKNOWN_FROM_GENESIS
```

Rules:

```text
effective_from_registry_sequence <= recorded_against_registry_sequence
```

and:

```text
UNKNOWN_FROM_GENESIS
=> effective_from_registry_sequence = 0
```

If several compromise/lifecycle events concern the same `(witness_id, key_id)`, the verifier uses the **minimum** effective boundary.

A later event therefore cannot relax an earlier conservative boundary.

## 4. Revocation and retirement are not retroactive compromise by default

`REVOCATION_DECLARED` and `RETIREMENT_DECLARED` use:

```text
boundary_basis = PROSPECTIVE_DECLARATION
```

and MUST satisfy:

```text
effective_from_registry_sequence >= recorded_against_registry_sequence
```

An operator cannot retroactively invalidate or reinterpret old signatures by labelling a prospective revocation as if it had always applied.

If evidence indicates earlier misuse or exposure, that evidence must be represented as `COMPROMISE_DISCOVERED` with an explicit uncertainty boundary.

## 5. Hash-chained local lifecycle ledger

Events are enumerated by:

```text
AIFC/key-lifecycle-ledger/v1
```

The first predecessor is:

```text
SHA256(
  ASCII("AIFC:KEY_LIFECYCLE_GENESIS:v1")
  || 0x00
  || UTF8(experiment_id)
)
```

The verifier requires:

```text
event_index = 0,1,2,...
previous_event_hash = exact preceding event hash
final_head_hash = exact final event hash
```

For an empty ledger:

```text
final_head_hash = key-lifecycle genesis sentinel
```

Every referenced event and incident-evidence hash must resolve from exact bytes.

## 6. Ledger cutoff

The lifecycle ledger binds:

```text
cutoff_registry_hash
cutoff_registry_sequence
```

The cutoff means only:

> this local lifecycle view claims to include events recorded through this registry position.

It does **not** establish that the claim is globally complete, current, or non-rollbackable.

Every signature being historically evaluated must lie at or before the cutoff.

## 7. Retroactive certificate re-evaluation

AIFC does not evaluate historical trust signature-by-signature in isolation.

Each cryptographically verified receipt belongs to a certificate group with:

```text
certificate_group_id
required_q
signing registry hash
signing registry sequence
```

Before historical replay, Verifier A independently rebinds:

```text
material.required_q
==
resolved signing registry.fault_model.q
```

and:

```text
material.registry_sequence
==
resolved signing registry.registry_sequence
```

This prevents post-crypto weakening of the historical quorum threshold.

For each group:

1. identify signatures whose `(witness_id,key_id)` are untrusted at the signed registry sequence;
2. remove those signatures;
3. recompute distinct surviving witness IDs;
4. recompute distinct surviving failure domains;
5. require both counts to remain at least `q`.

Example:

```text
original certificate:
  w0 + w1 + w2
  q = 3

later evidence:
  w0/k0 compromised from registry sequence <= certificate position

historical replay:
  trusted witnesses = {w1,w2} = 2
  trusted failure domains = 2
  q = 3

result:
  HISTORICAL_QUORUM_COLLAPSE
  evidence invalidated
```

A detected collapse means the **re-evaluation mechanism succeeded** while the evidence failed:

```text
KEY_LIFECYCLE_POLICY_VALID          = PASS
KEY_LIFECYCLE_LEDGER_REPLAY         = PASS
RETROACTIVE_KEY_QUORUM_REEVALUATION = PASS
HISTORICAL_KEY_LIFECYCLE            = FAIL
terminal_grade                      = INVALIDATED_EVIDENCE
```

## 8. Surviving quorum

A known compromise need not always destroy a certificate.

If enough independent trusted witnesses/failure domains remain after removal, the local certificate survives the known-event replay.

However, survival means only:

> no **known event in the supplied local lifecycle chain** destroys this certificate.

It does not prove no omitted compromise event exists.

## 9. The crucial asymmetry

v0.7 intentionally supports asymmetric conclusions:

### Known compromise may invalidate evidence

```text
known lifecycle evidence
-> retroactive boundary
-> signer removal
-> quorum collapse
-> INVALIDATED_EVIDENCE
```

### Absence of compromise events cannot establish historical safety

```text
empty / surviving local lifecycle ledger
!=
proof of no compromise
```

Therefore `AIFC/key-lifecycle-ledger/v1` fixes:

```text
completeness_status
= LOCAL_CHAIN_REPLAYED_EXTERNAL_COMPLETENESS_NOT_PROVEN
```

and the verifier result fixes:

```text
key_lifecycle_summary.external_completeness_proven = false
```

until a later versioned external freshness/transparency gate exists.

## 10. Relationship to external freshness

A locally valid lifecycle chain can itself be stale, truncated, or rebuilt from an older consistent snapshot.

Local hash chaining therefore does not solve:

```text
omitted final events
rollback to an earlier lifecycle head
split lifecycle views
withheld compromise event
```

Those are `EXTERNAL_FRESHNESS_REPLAY` concerns.

A later gate must bind the accepted lifecycle head to roots outside the rollback domain and define how independent observers prove that the accepted head is current enough for the experiment's claim.

Until then:

```text
HISTORICAL_KEY_LIFECYCLE = BLOCKED
EXTERNAL_FRESHNESS_REPLAY = BLOCKED
```

for otherwise locally surviving evidence.

## 11. Wall-clock boundary

Lifecycle event timestamps are metadata.

```text
signed timestamp != compromise boundary proof
signed timestamp != freshness proof
```

Historical validity is expressed in the frozen logical boundary unit (`REGISTRY_SEQUENCE`) and supported by resolved incident evidence.

## 12. Required attack corpus

v0.7 must cover at least:

```text
HISTORICAL_QUORUM_COLLAPSE
HISTORICAL_QUORUM_Q_VS_REGISTRY_MISMATCH
HISTORICAL_REGISTRY_SEQUENCE_REBINDING
KEY_LIFECYCLE_CHAIN_BREAK
KEY_LIFECYCLE_EVENT_INDEX_DISCONTINUITY
KEY_LIFECYCLE_EVENT_COUNT_REBINDING
KEY_LIFECYCLE_FINAL_HEAD_REBINDING
KEY_LIFECYCLE_BUNDLE_REBINDING
KEY_LIFECYCLE_POLICY_REBINDING
UNKNOWN_COMPROMISE_BOUNDARY_NOT_GENESIS
PROSPECTIVE_KEY_EVENT_RETROACTIVE_WITHOUT_COMPROMISE
LATER_BOUNDARY_RELAXATION_ATTEMPT
DANGLING_LIFECYCLE_INCIDENT_EVIDENCE
KEY_LIFECYCLE_CUTOFF_BEFORE_SIGNATURE_SEQUENCE
```

A rebuilt shorter but internally consistent lifecycle chain cannot necessarily be detected locally; that case remains part of the external freshness threat model rather than being falsely declared solved here.

## 13. Claim ceiling

Even after successful v0.7 local lifecycle replay:

```text
ED25519_SIGNATURE_CRYPTO             = PASS for tested path
KEY_LIFECYCLE_POLICY_VALID           = candidate PASS
KEY_LIFECYCLE_LEDGER_REPLAY          = candidate PASS
RETROACTIVE_KEY_QUORUM_REEVALUATION  = candidate PASS
HISTORICAL_KEY_LIFECYCLE             = BLOCKED without external completeness
EXTERNAL_FRESHNESS_REPLAY            = BLOCKED
CAUSAL_D_SEPARATION                   = BLOCKED
TARGET_SOURCE_CRYPTOGRAPHIC_PROOF     = BLOCKED
FULL_STATISTICAL_REPLAY               = BLOCKED
IMPLEMENTATION_A_PASS                 = NOT_ESTABLISHED
AIFC_V1_FROZEN                        = FALSE
PHYSICAL_RETROCAUSALITY               = NOT_OBSERVED
```

If a downstream component attempts a forward-null admitted verdict while external lifecycle completeness remains unproven, v0.7 MUST cap that verdict to `NOT_ADMITTED`.
