# Evidence Resolver

Status: `NORMATIVE DRAFT SUPPLEMENT`

AIFC uses many content hashes. A hash string is not evidence unless the verifier can recover the referenced bytes and independently establish their identity and type.

The resolver abstraction is:

```text
resolve(content_hash)
    ↓
recover exact bytes
    ↓
verify declared content kind/type
    ↓
strict parse if protocol JSON
    ↓
require stored protocol bytes == canonical bytes
    ↓
recompute domain-separated content identity
    ↓
return resolved evidence
```

## Content kinds

Current development store objects are either:

- `AIFC_PROTOCOL_JSON` — canonical AIFC protocol object;
- `RAW_BYTES` — exact non-protocol evidence.

Protocol JSON is identified by its schema-specific AIFC domain separator.

Raw bytes are identified by:

```text
SHA256(ASCII("AIFC:RAW_EVIDENCE:v1") || 0x00 || exact_bytes)
```

## Required rejection paths

A verifier MUST fail closed on at least:

```text
DANGLING_EVIDENCE_HASH
PATH_ESCAPE
CONTENT_KIND_REBINDING
DECLARED_SCHEMA_REBINDING
EXPECTED_SCHEMA_MISMATCH
INVALID_UTF8
DUPLICATE_JSON_KEY
NON_NFC_STRING
NONCANONICAL_STORED_PROTOCOL_BYTES
PROTOCOL_OBJECT_HASH_MISMATCH
RAW_EVIDENCE_HASH_MISMATCH
```

## Why stored canonical bytes matter

It is not sufficient for two byte strings to parse into the same semantic JSON object.

For evidence that is signed, archived, or independently replayed, the exact stored bytes must be uniquely determined. Therefore AIFC protocol evidence is admitted only when:

```text
stored_bytes == canonical_json_bytes(parsed_object)
```

before content identity is accepted.

## External locators

A URL, DOI, IPFS locator, GitHub URL, file path, or human-readable description is metadata until exact bytes are obtained and verified.

Resolver success does not prove the semantic claim carried by those bytes. For example, resolving an entropy-security document proves which document was supplied; a separate evidence-admission rule must determine whether that document justifies the claimed `p_i`.

## Current implementation boundary

Verifier A v0.2 contains a local content-addressed resolver intended for deterministic replay fixtures and preserved evidence stores.

Network acquisition, authenticated remote retrieval, archival durability, and source-specific cryptographic verification remain separate engineering/scientific gates.
