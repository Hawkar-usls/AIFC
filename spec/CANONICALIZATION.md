# AIFC Canonicalization Profile — v1.0 Draft

Status: `NORMATIVE DRAFT`

Exact-bit evidence is meaningless unless independent implementations agree on the exact byte representation.

## 1. JSON profile

AIFC protocol objects MUST satisfy all of the following before hashing or signature:

1. input MUST be valid UTF-8;
2. duplicate JSON object keys MUST be rejected;
3. all Unicode strings MUST be in NFC normalization form; non-NFC input MUST be rejected rather than silently rewritten during verification;
4. JSON numbers other than integers are forbidden in hash-critical protocol objects; probabilities and non-integral quantities MUST use explicit decimal strings or rational objects;
5. integers MUST lie in the exact interoperable range declared by the object schema; schemas SHOULD prefer decimal strings for unbounded integers;
6. canonical JSON serialization MUST follow RFC 8785 JSON Canonicalization Scheme after AIFC validation constraints are applied;
7. canonical bytes are the UTF-8 encoding of the canonical JSON serialization;
8. no BOM and no trailing newline are part of canonical bytes;
9. invalid UTF-8, duplicate keys, unsupported numeric values, or non-NFC strings are hard failures.

AIFC adds the NFC and number-profile restrictions because semantic equality is not sufficient for byte-identity science.

## 2. Canonical rational profile

Probability bounds represented as `{numerator_dec, denominator_dec}` MUST have exactly one byte representation for each rational value.

Verifier rules are normative:

- decimal strings contain ASCII digits only;
- no leading zero is permitted except the single string `"0"`;
- denominator MUST be positive;
- numerator MUST satisfy `0 <= numerator <= denominator`;
- `gcd(numerator, denominator) = 1`;
- zero MUST be encoded exactly as `0/1`;
- one MUST be encoded exactly as `1/1`.

Therefore `1/2` is canonical while `2/4`, `01/02`, `10/20`, and `0/7` are invalid protocol representations.

The scientific verifier MUST reject a non-reduced or otherwise noncanonical bound even if it is mathematically equal to a valid bound.

If the admitted exact-hit cap `a_i` is zero, an observed hit is a null-model contradiction and the verifier MUST NOT evaluate an expression containing `X_i/a_i`. The zero-cap case MUST take an explicit branch. Division by zero is never implementation-defined behavior.

## 3. Endianness

Hash-critical AIFC v1 protocol objects are canonical JSON bytes; therefore platform endianness MUST NOT affect canonical bytes.

If a future binary object is introduced, its byte order MUST be specified in that object's schema before use. Native-platform integer layout is forbidden.

## 4. Domain-separated hashing

Raw `SHA256(canonical_json)` MUST NOT be reused across semantic object types.

The v1 pattern is:

```text
SHA256(ASCII(domain_separator) || 0x00 || canonical_bytes)
```

Frozen separators include:

```text
AIFC:HARD_WITNESS:v1
AIFC:PRE_RETURN_CERTIFICATE:v1
AIFC:TRIAL_LEDGER_EVENT:v1
AIFC:CANDIDATE_GENERATION_PROFILE:v1
AIFC:ENTROPY_PROFILE:v1
AIFC:TARGET_DERIVATION_PROFILE:v1
AIFC:TARGET_EVIDENCE:v1
AIFC:CAUSAL_MODEL:v1
AIFC:WITNESS_REGISTRY:v1
AIFC:WITNESS_RECEIPT:v1
AIFC:QUORUM_CERTIFICATE:v1
AIFC:REGISTRY_TRANSITION_BODY:v1
AIFC:REGISTRY_TRANSITION_RECEIPT:v1
AIFC:REGISTRY_TRANSITION_QUORUM:v1
AIFC:REGISTRY_TRANSITION_CERTIFICATE:v1
AIFC:EVIDENCE_BUNDLE:v1
AIFC:VERIFIER_RESULT:v1
AIFC:RELEASE_MANIFEST:v1
```

The ledger's first predecessor is not an empty/all-zero hash. It is separately defined as:

```text
SHA256(ASCII("AIFC:EXPERIMENT_GENESIS:v1") || 0x00 || UTF8(experiment_id))
```

Separators are ASCII and case-sensitive.

## 5. No self-hash fields

A hash-critical protocol object SHOULD NOT contain its own canonical content hash because that creates a circular preimage convention.

Object identity is the external domain-separated hash of canonical bytes. If an object must bind another object's identity, it stores that other object's hash.

Any future exception requires an explicit versioned preimage rule defining exactly which fields are excluded; no such exception exists in AIFC v1 draft.

## 6. Hash algorithm

AIFC v1 uses SHA-256 for content identity and protocol binding unless a specific schema explicitly declares another algorithm.

Algorithm agility MUST NOT be achieved by silently accepting multiple algorithms. A change of hash algorithm requires a versioned schema/profile update.

## 7. Signature input

Signatures MUST bind the domain-separated digest plus the signer identity/key identifier and the logical protocol position required by the relevant certificate schema.

A signature over human-readable text or an uncanonicalized JSON rendering is not an AIFC v1 protocol signature.

## 8. Conformance requirement

Before v1.0 FROZEN, at least two independent implementations MUST produce byte-identical canonical bytes and identical domain-separated SHA-256 digests for every canonicalization test vector, including:

- key-order permutations;
- Unicode NFC/non-NFC cases;
- escaped control characters;
- slash and backslash cases;
- empty arrays/objects;
- maximum declared integers;
- duplicate-key rejection;
- invalid UTF-8 rejection;
- prohibited floating-point values;
- nested objects and arrays;
- rational equivalents `1/2`, `2/4`, `01/02` with only `1/2` admitted;
- canonical `0/1` and `1/1`;
- zero-probability e-process branch;
- experiment genesis predecessor hash;
- all new protocol-object domain separators.

Release criterion:

```text
BYTE_IDENTICAL_CANONICALIZATION = PASS
```
