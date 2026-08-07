# AIFC Canonicalization Profile — v1.0 Draft

Status: `NORMATIVE DRAFT`

Exact-bit evidence is meaningless unless independent implementations agree on the exact byte representation.

## 1. JSON profile

AIFC protocol objects MUST satisfy all of the following before hashing or signature:

1. input MUST be valid UTF-8;
2. duplicate JSON object keys MUST be rejected;
3. all Unicode strings MUST be in NFC normalization form; non-NFC input MUST be rejected rather than silently rewritten during verification;
4. JSON numbers other than integers are forbidden in hash-critical protocol objects; probabilities and non-integral quantities MUST use explicit decimal strings or rational objects;
5. JSON integers MUST lie in the interoperable exact range `[-9007199254740991, 9007199254740991]` unless a future versioned profile replaces the JSON-number rule; unbounded integers MUST use canonical decimal strings;
6. canonical JSON serialization MUST follow RFC 8785 JSON Canonicalization Scheme after AIFC validation constraints are applied;
7. property names are therefore ordered by UTF-16 code units as required by JCS / ECMAScript ordering;
8. canonical bytes are the UTF-8 encoding of the canonical JSON serialization;
9. no BOM and no trailing newline are part of canonical bytes;
10. invalid UTF-8, duplicate keys, unsupported numeric values, or non-NFC strings are hard failures.

AIFC adds the NFC and number-profile restrictions because semantic equality is not sufficient for byte-identity science.

For content-addressed AIFC protocol evidence, the **stored bytes themselves MUST equal canonical bytes**. It is not enough that a permissive parser can recover the same semantic object. A resolver MUST reject alternate whitespace, alternate key order, noncanonical escaping, BOMs, or other byte-different encodings as `NONCANONICAL_STORED_PROTOCOL_BYTES`.

## 2. Canonical rational profile

Probability/statistical bounds represented as `{numerator_dec, denominator_dec}` MUST have exactly one byte representation for each rational value.

Verifier rules are normative:

- decimal strings contain ASCII digits only;
- no leading zero is permitted except the single string `"0"`;
- denominator MUST be positive;
- numerator MUST satisfy `0 <= numerator <= denominator` where the field represents a probability/betting fraction;
- `gcd(numerator, denominator) = 1`;
- zero MUST be encoded exactly as `0/1`;
- one MUST be encoded exactly as `1/1`.

Therefore `1/2` is canonical while `2/4`, `01/02`, `10/20`, and `0/7` are invalid protocol representations.

The scientific verifier MUST reject a non-reduced or otherwise noncanonical bound even if it is mathematically equal to a valid bound.

If the admitted exact-hit cap `a_i` is zero, an observed hit is a null-model contradiction and the verifier MUST NOT evaluate an expression containing `X_i/a_i`. The zero-cap case MUST take an explicit branch. Division by zero is never implementation-defined behavior.

## 3. Endianness and typed target framing

Hash-critical AIFC v1 protocol objects are canonical JSON bytes; therefore platform endianness MUST NOT affect canonical bytes.

The strongest-grade target derivation DSL uses `AIFC_TYPED_LENGTH_PREFIXED_V1`. Every transformation input token is framed as:

```text
uint16_be(len(ASCII(token_name)))
|| ASCII(token_name)
|| uint64_be(len(token_bytes))
|| token_bytes
```

The framed tokens are concatenated in the exact frozen `input_order`. Native-platform integer layout, delimiter-only concatenation, implicit character encoding, or prose-defined framing is forbidden.

If a future binary object is introduced outside this framing, its byte order MUST be specified in that object's versioned schema before use.

## 4. Domain-separated hashing

Raw `SHA256(canonical_json)` MUST NOT be reused across semantic object types.

The v1 pattern for protocol JSON is:

```text
SHA256(ASCII(domain_separator) || 0x00 || canonical_bytes)
```

The current draft separators are:

```text
AIFC:HARD_WITNESS:v1
AIFC:CANDIDATE_SET:v1
AIFC:PRE_RETURN_CERTIFICATE:v1
AIFC:TRIAL_LEDGER_EVENT:v1
AIFC:TRIAL_CREATION_POLICY:v1
AIFC:EXPERIMENT_PLAN:v1
AIFC:CANDIDATE_GENERATION_POLICY:v1
AIFC:CANDIDATE_GENERATION_PROFILE:v1
AIFC:TARGET_SELECTOR_POLICY:v1
AIFC:TARGET_SELECTOR_PROFILE:v1
AIFC:TARGET_DERIVATION_POLICY:v1
AIFC:TARGET_DERIVATION_PROFILE:v1
AIFC:CONDITIONING_VIEW_POLICY:v1
AIFC:PRE_TARGET_CONDITIONING_VIEW:v1
AIFC:ENTROPY_PROFILE:v1
AIFC:CAUSAL_MODEL:v1
AIFC:STATISTICAL_PLAN:v1
AIFC:EPROCESS_STATE:v1
AIFC:WITNESS_REGISTRY:v1
AIFC:WITNESS_RECEIPT:v1
AIFC:QUORUM_CERTIFICATE:v1
AIFC:REGISTRY_TRANSITION_BODY:v1
AIFC:REGISTRY_TRANSITION_RECEIPT:v1
AIFC:REGISTRY_TRANSITION_QUORUM:v1
AIFC:REGISTRY_TRANSITION_CERTIFICATE:v1
AIFC:EXTERNAL_FRESHNESS_POLICY:v1
AIFC:PUBLICATION_POLICY:v1
AIFC:PUBLICATION_MANIFEST:v1
AIFC:TARGET_EVIDENCE:v1
AIFC:EVIDENCE_BUNDLE:v1
AIFC:VERIFIER_RESULT:v1
AIFC:RELEASE_MANIFEST:v1
AIFC:EVIDENCE_STORE_INDEX:v1
```

`AIFC/replay-package/v0.2` is a development manifest for Verifier A and is deliberately **not** a frozen v1 evidence object; its schema is versioned but it is not assigned a frozen scientific content-identity domain in v1 draft.

Exact non-protocol evidence bytes use:

```text
SHA256(ASCII("AIFC:RAW_EVIDENCE:v1") || 0x00 || exact_bytes)
```

A URL, locator, file name, or claimed SHA string does not satisfy evidence resolution. The resolver MUST recover the exact bytes and recompute the identity.

## 5. Deterministic genesis predecessors

The trial ledger's first predecessor is:

```text
SHA256(ASCII("AIFC:EXPERIMENT_GENESIS:v1") || 0x00 || UTF8(experiment_id))
```

The initial witness registry (`registry_sequence = 0`) uses:

```text
SHA256(ASCII("AIFC:WITNESS_REGISTRY_GENESIS:v1") || 0x00 || UTF8(experiment_id))
```

Neither sentinel may be replaced by an empty string, all-zero digest, newline-terminated identifier, implementation-local constant, or wall-clock timestamp.

## 6. No self-hash or mutual-hash cycles

A hash-critical protocol object MUST NOT contain its own canonical content hash.

Object identity is the external domain-separated hash of canonical bytes. If an object must bind another object's identity, it stores that other object's hash.

AIFC v1 draft also forbids mutual fixed-point choreography. Current directed bindings are intentionally one-way:

```text
QUORUM_CERTIFIED ledger head
  -> PRE_TARGET_CONDITIONING_VIEW
  -> quorum(view hash)
  -> TARGET_ARMED event

VERIFIED event
  -> EVIDENCE_BUNDLE
  -> TERMINAL event
  -> PUBLICATION_MANIFEST
  -> external publication root

immutable source commit
  -> out-of-tree RELEASE_MANIFEST
  -> GitHub Release / archive record binds manifest hash
```

The pre-target view therefore does not contain the hash of the quorum that signs it; the evidence bundle does not contain a publication-manifest hash; and the release manifest is not required to live inside the source commit whose SHA it binds.

Any future exception requires an explicit versioned preimage rule; no such exception exists in AIFC v1 draft.

## 7. Hash algorithm

AIFC v1 uses SHA-256 for protocol content identity and the current target-hash primitives unless a specific versioned schema explicitly declares another algorithm.

Algorithm agility MUST NOT be achieved by silently accepting multiple algorithms. A change of content-identity hash algorithm requires a versioned schema/profile update.

## 8. Signature input

Signatures MUST bind the domain-separated digest plus the signer identity/key identifier and logical protocol position required by the relevant certificate schema.

A signature over human-readable text or an uncanonicalized JSON rendering is not an AIFC v1 protocol signature.

Signature verification does not establish source unpredictability, causal independence, freshness, or physical interpretation; those are separate gates.

## 9. Conformance requirement

Before v1.0 FROZEN, at least two independent implementations MUST produce byte-identical canonical bytes and identical domain-separated SHA-256 digests for every canonicalization test vector, including:

- key-order permutations, including non-BMP Unicode key ordering;
- Unicode NFC/non-NFC cases;
- escaped control characters;
- slash and backslash cases;
- empty arrays/objects;
- maximum/minimum admitted JSON integers;
- out-of-range integer rejection;
- duplicate-key rejection;
- invalid UTF-8 rejection;
- BOM rejection;
- prohibited floating-point/NaN/Infinity values;
- nested objects and arrays;
- canonical stored protocol bytes versus semantic-equivalent noncanonical storage;
- rational equivalents `1/2`, `2/4`, `01/02` with only `1/2` admitted;
- canonical `0/1` and `1/1`;
- zero-probability e-process branch;
- experiment genesis predecessor hash;
- witness-registry genesis predecessor hash;
- typed target framing;
- raw-evidence content identity;
- every frozen protocol-object domain separator listed above.

Release criterion:

```text
BYTE_IDENTICAL_CANONICALIZATION = PASS
```

A green Verifier A run alone cannot satisfy this criterion; independent Implementation B must reproduce the bytes and digests without importing Verifier A's canonicalization code.
