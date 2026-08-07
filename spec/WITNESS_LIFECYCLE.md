# AIFC Witness Identity and Key Lifecycle — v1.0 Draft

Status: `NORMATIVE DRAFT`

The quorum inequality `2q > n + f` is meaningful only if witness identity, key continuity, and registry reconfiguration are themselves auditable.

## 1. Witness identity

Each witness has a stable `witness_id` and a declared `failure_domain`.

Multiple processes, containers, VMs, or keys controlled by the same rollback/administrative failure domain MUST NOT be counted as independent witnesses unless the fault model explicitly treats them as one domain.

## 2. Registry

The active witness set and key material are defined by a versioned, hash-linked `AIFC/witness-registry/v1` object.

The registry MUST bind experiment identity, monotonically increasing registry sequence, previous registry hash, `(n,f,q)` fault model, witness identities/failure domains, status, key identifiers and validity intervals.

Registry sequence `0` is the experiment's initial registry and MUST be externally rooted by the experiment genesis evidence. Every registry with sequence `>0` MUST carry a `transition_certificate_hash` resolving to an `AIFC/registry-transition-certificate/v1` object.

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

## 5. Key rotation and membership reconfiguration

A key rotation or witness-membership change MUST occur only through a new registry sequence.

For every transition `registry_k -> registry_{k+1}` the transition object MUST bind both registry hashes and MUST contain:

- a valid quorum certificate under the **old** registry authorizing the exact next-registry hash; and
- a valid quorum certificate under the **new** registry accepting the exact previous-registry hash and transition hash.

This joint transition rule is mandatory for AIFC v1.0 FROZEN. A mere `previous_registry_hash` link is provenance, not authorization.

The old and new quorum checks are evaluated independently under their respective `(n,f,q)` fault models. The verifier MUST reject:

- a new registry not authorized by the old registry;
- a transition not accepted by the new registry;
- a sequence jump;
- two different next registries authorized from the same old logical position;
- a disjoint configuration fork whose individual configurations are locally safe but whose transition is not jointly certified.

Schema: [`../schemas/registry-transition-certificate.schema.json`](../schemas/registry-transition-certificate.schema.json).

A new key cannot retroactively validate old certificates. An old key cannot sign positions outside its declared validity interval.

## 6. Revocation and compromise

Revocation is prospective unless the registry explicitly declares a compromise interval requiring historical invalidation review.

When a key is marked `COMPROMISED`, the experiment MUST determine the earliest position at which compromise cannot be excluded. Certificates depending on that key after the uncertainty boundary MUST be re-evaluated under the remaining quorum.

If safety can no longer be established, affected trials are `INVALIDATED_EVIDENCE`, not silently retained at a weaker wording.

## 7. Offline and stale witnesses

`OFFLINE` affects liveness, not identity.

A witness returning from offline state MUST reconcile the latest externally accepted registry/head before issuing new signatures. A stale witness MUST NOT extend an obsolete branch as though it were current.

## 8. Registry rollback

The witness registry and its transition certificates require external continuity. Restoring experiment state and the only copy of the registry chain to an older snapshot defeats the witness layer.

Registry heads and transition certificates MUST be rooted across the declared independent failure domains or an equivalent external append-only/transparency mechanism.

## 9. Required adversarial cases

Before v1.0 FROZEN, the corpus MUST include at least:

- `UNAUTHORIZED_REGISTRY_RECONFIGURATION`;
- `DISJOINT_CONFIG_FORK`;
- `OLD_QUORUM_ONLY_WITHOUT_NEW_ACCEPTANCE`;
- `NEW_QUORUM_ONLY_WITHOUT_OLD_AUTHORIZATION`;
- `REGISTRY_SEQUENCE_JUMP`;
- `REGISTRY_TRANSITION_REPLAY`.
