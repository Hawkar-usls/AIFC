# AIFC Ed25519 Signature Preimage Profile v1

Status: **NORMATIVE DRAFT / PRE-CRYPTO GATE**

This profile defines the exact bytes that AIFC strongest-grade v1 witnesses will sign with Ed25519. It intentionally does **not** establish signature validity; Ed25519 cryptographic verification is a separate mandatory gate.

## 1. Frozen before the experiment

The experiment plan binds:

```text
signature_preimage_policy_hash
```

which resolves to:

```text
AIFC/signature-preimage-policy/v1
```

For strongest-grade v1 the policy is not claimant-extensible. It selects exactly one normative profile:

```text
policy_id            = AIFC-ED25519-SIGNATURE-PREIMAGE-POLICY-V1
signature_profile_id = AIFC-ED25519-DIRECT-TYPED-V1
signature_algorithm  = Ed25519
prehash_mode         = NONE_DIRECT_ED25519
```

The policy MUST be frozen before the first `CREATED` slot. A signature produced under a message format chosen later is not strongest-grade AIFC evidence.

Historical draft plans without this hash remain readable only so old development corpora can still be replayed. They MUST fail the v0.5 strongest signature-preimage gate and this compatibility allowance MUST be removed before v1.0 FROZEN.

## 2. Preimage header

The exact message begins with:

```text
ASCII("AIFC:SIGNATURE_PREIMAGE:v1") || 0x00
```

No JSON serialization is signed directly.

No implicit Ed25519 prehash is used.

## 3. Field framing

Every field is framed as:

```text
u8(type_tag)
|| u64_be(payload_length)
|| payload_bytes
```

Fields appear exactly once and in ascending tag order.

| Tag | Field | Payload |
|---:|---|---|
| 1 | receipt_schema | exact UTF-8 |
| 2 | protocol_version | exact UTF-8 |
| 3 | signature_profile_id | exact UTF-8 |
| 4 | scope_kind | `TRIAL` or `EXPERIMENT` UTF-8 |
| 5 | experiment_id | exact UTF-8 |
| 6 | trial_index_or_absent | trial: `0x01 || u64_be(index)`; experiment: single `0x00` |
| 7 | logical_position_or_transition_role | exact UTF-8 |
| 8 | content_schema | exact UTF-8 |
| 9 | content_hash | decoded 32-byte SHA-256 value |
| 10 | registry_hash | decoded 32-byte SHA-256 value |
| 11 | registry_sequence | `u64_be(sequence)` |
| 12 | witness_id | exact UTF-8 |
| 13 | key_id | exact UTF-8 |
| 14 | timestamp_present | one byte `0x00` or `0x01` |
| 15 | timestamp_utf8 | exact UTF-8 if present; zero-length payload if absent |

A field omitted because it is “obvious from context” is a different protocol and MUST be rejected.

## 4. Receipt types

The receipt schema itself is signed data.

### Trial witness receipt

```text
receipt_schema = AIFC/witness-receipt/v1
scope_kind     = TRIAL
position       = logical_position
content_hash   = content_hash
registry_hash  = registry_hash
```

### Experiment-plan receipt

```text
receipt_schema = AIFC/experiment-plan-receipt/v1
scope_kind     = EXPERIMENT
trial marker   = explicit absent marker 0x00
position       = EXPERIMENT_PLAN_FROZEN
content_schema = AIFC/experiment-plan/v1
registry_sequence = 0
```

### Registry-transition receipt

```text
receipt_schema = AIFC/registry-transition-receipt/v1
scope_kind     = EXPERIMENT
trial marker   = explicit absent marker 0x00
position       = OLD_REGISTRY_AUTHORIZATION
              | NEW_REGISTRY_ACCEPTANCE
content_schema = AIFC/registry-transition-body/v1
content_hash   = transition_body_hash
registry_hash  = signing_registry_hash
```

## 5. Canonical external encodings

Strongest-grade AIFC v1 uses exactly one representation:

```text
Ed25519 public key = 32 bytes = 64 lowercase hexadecimal characters
Ed25519 signature  = 64 bytes = 128 lowercase hexadecimal characters
```

Base64, padded/unpadded base64, uppercase/mixed-case hexadecimal, shortened encodings, or alternate wrappers are not equivalent strongest-grade protocol objects.

## 6. Timestamp semantics

When a receipt contains a wall-clock timestamp, both its presence flag and exact timestamp string are included in the signature preimage.

Therefore a timestamp cannot be modified without invalidating the later signature.

However:

```text
signed timestamp != freshness proof
```

Freshness remains a separate external evidence gate based on causal/event ordering and roots outside the rollback domain.

## 7. Required replay before crypto

Before attempting Ed25519 verification, Verifier A MUST independently establish:

```text
SIGNATURE_PREIMAGE_POLICY_VALID = PASS
SIGNATURE_PREIMAGE_REPLAY       = PASS
CANONICAL_ED25519_ENCODING      = PASS
```

For every receipt, the verifier rebinds:

- experiment and optional trial;
- logical position / transition role;
- signed content schema and content hash;
- signing registry and registry sequence;
- witness identity and key identity;
- optional timestamp integrity field.

Only then may a later gate attempt:

```text
ED25519_SIGNATURE_CRYPTO
```

## 8. Mandatory attack corpus

At minimum the frozen corpus must cover:

```text
CROSS_PROTOCOL_SIGNATURE_REPLAY
CROSS_RECEIPT_TYPE_REPLAY
CROSS_EXPERIMENT_SIGNATURE_REPLAY
CROSS_TRIAL_SIGNATURE_REPLAY
LOGICAL_POSITION_REBINDING
CONTENT_SCHEMA_REBINDING
REGISTRY_REBINDING
REGISTRY_SEQUENCE_REBINDING
WITNESS_ID_SUBSTITUTION
KEY_ID_SUBSTITUTION
TRANSITION_ROLE_REBINDING
SIGNATURE_ENCODING_MALLEABILITY
PUBLIC_KEY_ENCODING_AMBIGUITY
TIMESTAMP_TAMPER
```

The following attacks require the later crypto/key-lifecycle layer and remain blocked at v0.5:

```text
REVOKED_KEY_REPLAY
COMPROMISED_KEY_AFTER_BOUNDARY
STALE_REGISTRY_SIGNATURE
```

## 9. Claim boundary

A successful preimage replay proves only that the verifier and witness can agree on **which exact bytes would be signed**.

It does not prove that:

- the signature is valid;
- the key was uncompromised at the relevant historical position;
- the receipt is fresh rather than a valid stale history;
- the causal model is complete;
- the target source proof is valid;
- a future-information effect exists.

Therefore during v0.5:

```text
SIGNATURE_PREIMAGE_REPLAY = candidate PASS
ED25519_SIGNATURE_CRYPTO  = BLOCKED
IMPLEMENTATION_A_PASS     = NOT_ESTABLISHED
AIFC_V1_FROZEN            = FALSE
```
