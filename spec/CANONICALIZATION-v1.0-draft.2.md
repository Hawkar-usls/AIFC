# AIFC Canonicalization Profile — v1.0 Draft 2 Supplement

Status: `NORMATIVE DRAFT SUPPLEMENT / NOT FROZEN`

This supplement extends `CANONICALIZATION.md` for the PR #5 preregistration/replay object set. All earlier strict UTF-8, duplicate-key, NFC, no-float, safe-integer, JCS, canonical-rational, no-self-hash and typed-framing rules remain in force.

## Additional protocol domains

The v1 draft domain registry additionally includes:

```text
AIFC/entropy-policy/v1
  -> AIFC:ENTROPY_POLICY:v1

AIFC/experiment-plan-receipt/v1
  -> AIFC:EXPERIMENT_PLAN_RECEIPT:v1

AIFC/experiment-plan-quorum/v1
  -> AIFC:EXPERIMENT_PLAN_QUORUM:v1
```

Their content identities use the normal protocol-object rule:

```text
SHA256(ASCII(domain_separator) || 0x00 || canonical_json_bytes)
```

## Plan preregistration hash direction

The preregistration chain is intentionally acyclic:

```text
hash(EXPERIMENT_PLAN)
      ↓
experiment-plan receipts bind plan hash
      ↓
hash(EXPERIMENT_PLAN_QUORUM)
      ↓
first CREATED.prerequisite_certificate_hash
```

The experiment plan does not contain its plan-quorum hash. The plan quorum therefore certifies the already-defined plan rather than requiring a fixed point.

The first `CREATED` event also binds:

```text
payload_hash = experiment_plan_hash
```

so both the plan identity and its prior external certification are explicit in the trial ledger.

## Scope separation

`AIFC/experiment-plan-receipt/v1` and `AIFC/experiment-plan-quorum/v1` deliberately contain no `trial_index`.

They exist before the first trial slot and are therefore experiment-scoped. Reusing a trial-scoped quorum type for this purpose is nonconformant.

## Stored-byte requirement

These new protocol objects are subject to the same strict resolver rule as all AIFC protocol JSON:

```text
stored_bytes == canonical_json_bytes(parsed_object)
```

before the content hash may be admitted.

## Cross-implementation freeze

Before v1.0 FROZEN, Implementation A and Implementation B must produce byte-identical canonical bytes and identical digests for plan, plan receipt, plan quorum and entropy-policy vectors, including malicious variants with:

- reordered keys;
- non-NFC strings;
- duplicate keys;
- rebinding of experiment ID;
- rebinding of content/registry hash;
- unsafe integer representation;
- noncanonical stored bytes.

Until then:

```text
BYTE_IDENTICAL_CANONICALIZATION = NOT_ESTABLISHED
AIFC_V1_FROZEN = FALSE
```
