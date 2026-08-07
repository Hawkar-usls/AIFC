# AIFC External Replication Guide

This guide describes a minimal path for a laboratory or independent researcher to implement AIFC without trusting JANUS or Genesis.

## 1. Independent components

A minimal external bench SHOULD separate:

1. **Candidate host** — creates and freezes PRE_RETURN bytes.
2. **Witness quorum** — certifies the frozen state and freshness.
3. **Entropy / target source** — produces the designated future target only after freeze.
4. **Verifier host** — independently reconstructs the evidence package.
5. **Publication archive** — preserves complete transcripts and null results.

The strongest design uses distinct administrative and rollback failure domains.

## 2. Recommended first witness configuration

A practical baseline is:

```text
n = 4 witnesses
f = 1 Byzantine witness tolerated by the safety model
q = 3 signatures required
```

because `2q > n+f` gives `6 > 5`.

The four witnesses MUST NOT merely be four processes on one machine if that machine can be rolled back as one unit.

## 3. Choose the future target source

Good candidates include independently operated public randomness beacons or a separately operated hardware randomness source with verifiable entropy evidence.

The future event-selection rule MUST be frozen before the selected output exists.

Example:

```text
Select the first beacon round scheduled at least 120 seconds after
receipt of a valid 3-of-4 PRE_RETURN certificate.
```

The value `120 seconds` and the round-selection rule must be preregistered.

Do not let the operator pick among future rounds after seeing any outputs.

## 4. Freeze one exact hard candidate

Prefer one candidate per trial.

Example canonical object:

```json
{
  "schema": "AIFC/hard-witness/v1",
  "run_id": "uuid-v4-or-equivalent",
  "payload128": "00000000000000000000000000000000",
  "nonce128": "00000000000000000000000000000000"
}
```

The candidate bytes and canonicalization rule must be public to the verifier and immutable before target generation.

## 5. Build the PRE_RETURN certificate

Each witness should sign or otherwise authenticate a record containing at least:

- protocol version;
- `run_id`;
- candidate digest;
- logical sequence number;
- previous witness head / continuity binding;
- witness identifier;
- local receipt time and monotonic state if available;
- target-selection rule identifier;
- no target output itself.

The quorum certificate should be archived before the target event becomes eligible.

## 6. Record complete pre-target side information

The experiment must preserve enough information to justify its entropy claim relative to the real pre-target history.

At minimum record:

- prior target rounds/results visible to the system;
- candidate-generation process state relevant to target prediction;
- network connections between failure domains;
- target source state that is public or available;
- witness and operator actions;
- software versions and configuration hashes;
- any caches, prefetchers, or background services capable of touching target data;
- restart/snapshot/recovery events.

If this cannot be audited, lower the evidence grade.

## 7. Generate target only after freeze

Once the quorum certificate is valid, the predetermined target event may occur.

The target evidence package should bind:

- exact target bytes;
- exact target event/round;
- source authenticity evidence;
- publication/generation metadata;
- source-chain verification when available;
- all transformations used to derive the final hard target.

No transformation may be selected after inspecting PRE_RETURN for similarity.

## 8. Verify exact identity

The verifier reconstructs canonical bytes independently and computes:

```text
X_i = 1 if target belongs to frozen candidate set
      0 otherwise
```

For strongest trials, `K_i = 1`.

Semantic reinterpretation is not allowed at this layer.

## 9. Apply entropy and sequential evidence

The analysis must justify a history-wise null cap `p_i`.

Then:

```text
a_i = min(1, K_i * p_i)
```

Use either:

- a preregistered fixed horizon; or
- the frozen anytime-valid e-process.

Do not choose the analysis after observing whether a hit occurred.

## 10. Publish all initiated trials

For every trial, publish one machine-readable terminal state:

```text
ADMITTED_HIT
ADMITTED_MISS
INVALID_PREREGISTERED_TECHNICAL_REASON
UNRESOLVED_EVIDENCE_FAILURE
```

No silent deletion.

## 11. What an independent replication should change

A strong replication changes as many implementation details as practical while preserving the specification:

- independent verifier implementation;
- different witness operators;
- different storage/hosting provider;
- different operating system or language;
- independently built transcript parser;
- independently reproduced entropy-source verification;
- ideally a second target source.

Agreement across shared code is weaker than agreement across independent implementations.

## 12. Minimal publication package

A replication should publish:

```text
protocol version
preregistration
source code hashes
binary/container hashes where applicable
candidate transcript
witness receipts
future target evidence
causal DAG / isolation declaration
entropy-bound derivation
multiplicity ledger
stopping/e-process configuration
verifier output
negative and invalid runs
full machine-readable archive hash
```

## 13. Interpretation

Even a fully admitted exact hit that crosses the frozen statistical threshold is not, by itself, proof of retrocausality.

It is a signal to attack the premises harder and replicate independently.
