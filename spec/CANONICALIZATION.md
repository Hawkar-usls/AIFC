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

## 2. Endianness

Hash-critical AIFC v1 protocol objects are canonical JSON bytes; therefore platform endianness MUST NOT affect canonical bytes.

If a future binary object is introduced, its byte order MUST be specified in that object's schema before use. Native-platform integer layout is forbidden.

## 3. Domain-separated hashing

Raw `SHA256(canonical_json)` MUST NOT be reused across semantic object types.

The v1 pattern is:

```text
SHA256(ASCII(domain_separator) || 0x00 || canonical_bytes)
```

Frozen separators include:

```text
AIFC:HARD_WITNESS:v1
AIFC:TRIAL_LEDGER_EVENT:v1
AIFC:ENTROPY_PROFILE:v1
AIFC:CAUSAL_MODEL:v1
AIFC:WITNESS_REGISTRY:v1
AIFC:QUORUM_CERTIFICATE:v1
AIFC:EVIDENCE_BUNDLE:v1
AIFC:VERIFIER_RESULT:v1
```

Separators are ASCII and case-sensitive.

## 4. Hash algorithm

AIFC v1 uses SHA-256 for content identity and protocol binding unless a specific schema explicitly declares another algorithm.

Algorithm agility MUST NOT be achieved by silently accepting multiple algorithms. A change of hash algorithm requires a versioned schema/profile update.

## 5. Signature input

Signatures MUST bind the domain-separated digest plus the signer identity/key identifier and the logical protocol position required by the relevant certificate schema.

A signature over human-readable text or an uncanonicalized JSON rendering is not an AIFC v1 protocol signature.

## 6. Conformance requirement

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
- nested objects and arrays.

Release criterion:

```text
BYTE_IDENTICAL_CANONICALIZATION = PASS
```
