# AIFC Witness Identity and Key Lifecycle — v1.0 Draft

Status: `NORMATIVE DRAFT`

The quorum inequality `2q > n + f` is meaningful only if witness identity and key continuity are themselves auditable.

## 1. Witness identity

Each witness has a stable `witness_id` and a declared `failure_domain`.

Multiple processes, containers, VMs, or keys controlled by the same rollback/administrative failure domain MUST NOT be counted as independent witnesses unless the fault model explicitly treats them as one domain.

## 2. Registry

The active witness set and key material are defined by a versioned, hash-linked `AIFC/witness-registry/v1` object.

The registry MUST bind:

- experiment identity;
- monotonically increasing registry sequence;
- previous registry hash;
- `(n,f,q)` fault model;
- witness identities and failure domains;
- active/retired/revoked/compromised state;
- key identifiers and validity intervals.

Schema: [`../schemas/witness-registry.schema.json`](../schemas/witness-registry.schema.json).

## 3. Quorum admission

A certificate is valid only when:

1. every signature resolves to one active witness and one key valid at the certificate's registry sequence;
2. duplicate signatures from one `witness_id` count once;
3. the distinct-witness count is at least `q`;
4. the declared fault model satisfies `2q > n + f` for safety;
5. every signer binds the same experiment, logical position, content digest, and registry hash.

## 4. Same-position equivocation

An honest witness MUST NOT sign two different content heads for the same logical certificate position.

If two valid signatures from the same witness/key are found on conflicting heads at one logical position, the witness is proven to have equivocated for that position. Both signatures MUST be preserved.

A conflicting certificate is not repaired by choosing the more convenient branch.

## 5. Key rotation

Key rotation MUST be announced in a new registry sequence and MUST identify the predecessor key where one exists.

A new key cannot retroactively validate old certificates. An old key cannot sign positions outside its declared validity interval.

Rotation SHOULD be authorized by the previous active key and/or the quorum policy in force before rotation.

## 6. Revocation and compromise

Revocation is prospective unless the registry explicitly declares a compromise interval requiring historical invalidation review.

When a key is marked `COMPROMISED`, the experiment MUST determine the earliest position at which compromise cannot be excluded. Certificates depending on that key after the uncertainty boundary MUST be re-evaluated under the remaining quorum.

If safety can no longer be established, affected trials are `INVALIDATED_EVIDENCE`, not silently retained at a weaker wording.

## 7. Offline and stale witnesses

`OFFLINE` affects liveness, not identity.

A witness returning from offline state MUST reconcile the latest externally accepted registry/head before issuing new signatures. A stale witness MUST NOT extend an obsolete branch as though it were current.

## 8. Registry rollback

The witness registry itself requires external continuity. Restoring both experiment state and the only copy of the registry to an older snapshot defeats the purpose of the witness layer.

Registry heads SHOULD be replicated across independent failure domains or anchored to a transparency/append-only mechanism.
