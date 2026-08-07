# AIFC Signature Preimage Profile v1

Status: **normative pre-crypto draft profile**.

This profile defines the exact message bytes that a later Ed25519 verifier is required to verify. It does **not** establish Ed25519 cryptographic verification, historical key validity, revocation/compromise handling, freshness, causal isolation, scientific admission, or physical retrocausality.

## 1. Algorithm boundary

AIFC v1 strongest-grade receipts use **pure Ed25519** semantics: Ed25519 signs the exact preimage bytes defined below. AIFC does not introduce a protocol-level SHA-256 prehash before Ed25519 signing and does not admit Ed25519ph under this profile.

The JSON object `AIFC/signature-preimage-policy/v1` is frozen by content hash in `AIFC/experiment-plan/v1` before the first `CREATED` event. Strongest-grade replay accepts only the single normative profile `AIFC-SIGNATURE-PREIMAGE-V1`; claimant-defined field orders, framing variants, receipt families, encodings, or Ed25519 variants are not admissible.

## 2. Domain separator

The message begins with the exact ASCII bytes:

```text
AIFC:SIGNATURE_PREIMAGE:v1
```

followed by one zero byte `0x00`.

## 3. Field framing

Every subsequent field is encoded as:

```text
TAG_U8 || LENGTH_U32BE || VALUE
```

where:

- `TAG_U8` is the one-byte tag fixed by this profile;
- `LENGTH_U32BE` is the exact byte length of `VALUE`, encoded as unsigned 32-bit big-endian;
- fields appear exactly once and in the exact order below;
- string values are exact UTF-8 bytes of strings already required to be NFC by AIFC canonicalization;
- SHA-256/content hashes are lowercase hexadecimal in JSON but are decoded to their exact 32 raw bytes in the signature preimage;
- integer values are unsigned 64-bit big-endian;
- an optional integer is `0x00` when absent and `0x01 || U64BE(value)` when present;
- an optional UTF-8 string is `0x00` when absent and `0x01 || UTF8(value)` when present.

## 4. Frozen tag table

| Tag | Field | Encoding |
|---:|---|---|
| `0x01` | `receipt_schema` | UTF-8 |
| `0x02` | `protocol_version` | UTF-8, derived from frozen experiment plan |
| `0x03` | `signature_profile_id` | UTF-8, exact `AIFC-SIGNATURE-PREIMAGE-V1` |
| `0x04` | `scope_kind` | UTF-8 |
| `0x05` | `experiment_id` | UTF-8 |
| `0x06` | `trial_index_or_absent` | explicit optional U64BE |
| `0x07` | `logical_position_or_transition_role` | UTF-8 |
| `0x08` | `content_schema` | UTF-8, derived from resolved content object |
| `0x09` | `content_hash` | exact 32 bytes |
| `0x0a` | `registry_hash` | exact 32 bytes |
| `0x0b` | `registry_sequence` | U64BE, derived from resolved registry object |
| `0x0c` | `witness_id` | UTF-8 |
| `0x0d` | `key_id` | UTF-8 |
| `0x0e` | `wall_clock_timestamp_or_absent` | explicit optional UTF-8 |

No tag may be reused for another semantic meaning in profile v1.

## 5. Receipt families

Exactly three receipt schemas are admitted by this profile:

### Trial witness receipt

```text
receipt_schema = AIFC/witness-receipt/v1
scope_kind = TRIAL
trial_index = receipt.trial_index
logical_position_or_transition_role = receipt.logical_position
content_hash = receipt.content_hash
registry_hash = receipt.registry_hash
```

### Experiment-plan receipt

```text
receipt_schema = AIFC/experiment-plan-receipt/v1
scope_kind = EXPERIMENT
trial_index = absent
logical_position_or_transition_role = EXPERIMENT_PLAN_FROZEN
content_hash = receipt.content_hash
registry_hash = receipt.registry_hash
```

For strongest-grade replay, the content hash must equal the frozen experiment-plan hash and the resolved content schema must be `AIFC/experiment-plan/v1`.

### Registry-transition receipt

```text
receipt_schema = AIFC/registry-transition-receipt/v1
scope_kind = REGISTRY_TRANSITION
trial_index = absent
logical_position_or_transition_role = receipt.role
content_hash = receipt.transition_body_hash
registry_hash = receipt.signing_registry_hash
```

For strongest-grade replay, the resolved content schema must be `AIFC/registry-transition-body/v1`.

Any other receipt schema is `BLOCKED` until a new normative signature-preimage profile/version explicitly admits it.

## 6. Resolver-derived semantics

Strongest-grade preimage replay MUST NOT accept `protocol_version`, `content_schema`, or `registry_sequence` as claimant-provided semantic inputs.

It must derive them from content-addressed evidence:

```text
experiment_plan_hash
  -> exact experiment plan bytes
  -> protocol_version
  -> signature_preimage_policy_hash
  -> exact normative policy bytes

receipt.registry_hash / receipt.signing_registry_hash
  -> exact witness-registry bytes
  -> registry_sequence

receipt.content_hash / receipt.transition_body_hash
  -> exact protocol object bytes
  -> content_schema
```

Experiment IDs of the plan, policy, registry, content, and receipt must agree. The content object must be runtime-schema-valid before its schema is used in the preimage.

## 7. External encodings

For strongest-grade AIFC v1:

```text
Ed25519 public key = exactly 32 bytes
JSON external encoding = exactly 64 lowercase hexadecimal characters

Ed25519 signature = exactly 64 bytes
JSON external encoding = exactly 128 lowercase hexadecimal characters
```

Base64, padded/unpadded base64, uppercase or mixed-case hexadecimal, alternate-length encodings, and algorithm substitution are not admitted by this profile.

## 8. Timestamp boundary

If a receipt contains `wall_clock_timestamp`, the exact timestamp UTF-8 bytes are included in the signed preimage for integrity.

This does **not** establish freshness:

```text
signed timestamp != freshness proof
```

Causal ordering and anti-rollback freshness remain separate AIFC gates.

## 9. Required adversarial classes

The frozen preimage corpus must cover at least:

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
UNSUPPORTED_RECEIPT_SCHEMA
NON_NORMATIVE_SIGNATURE_PREIMAGE_POLICY
```

The following remain **later crypto/key-lifecycle gates**, not accomplishments of this profile:

```text
REVOKED_KEY_REPLAY
COMPROMISED_KEY_AFTER_BOUNDARY
STALE_REGISTRY_SIGNATURE
ED25519_SIGNATURE_CRYPTO
HISTORICAL_KEY_LIFECYCLE_CRYPTO_REPLAY
```

## 10. Claim ceiling

Passing this profile means only:

> the verifier can independently reconstruct the exact, domain-separated, type-separated message bytes that an AIFC v1 Ed25519 receipt is supposed to cover.

It does not mean the signature is valid, the key was historically trustworthy, the history is fresh, Implementation A is admitted, AIFC v1.0 is frozen, or physical retrocausality has been observed.
