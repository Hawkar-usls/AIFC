# AIFC Verdict Model

Status: `NORMATIVE DRAFT SUPPLEMENT`

AIFC distinguishes two fundamentally different questions:

1. **What did the verifier conclude about one evidence package/trial?**
2. **How mature is the overall research program and its replication evidence?**

These MUST NOT be encoded as one scale.

## Machine trial verdict

The machine-readable `AIFC/verifier-result/v1` concerns one replayed trial/evidence package.

Current allowed terminal classes are intentionally narrow:

```text
INVALIDATED_EVIDENCE
NOT_ADMITTED
STRUCTURAL_MATCH_ONLY
FORWARD_NULL_CONSISTENT_MISS
FORWARD_NULL_INCOMPATIBILITY_CANDIDATE
```

The schema contains no `RETROCAUSALITY_PROVED` value.

### Meaning

`INVALIDATED_EVIDENCE`
: Required evidence is malformed, contradictory, dangling, noncanonical or otherwise invalid.

`NOT_ADMITTED`
: The package may be structurally coherent in some respects, but one or more evidence gates required for the claimed statistical/causal grade are blocked or not implemented.

`STRUCTURAL_MATCH_ONLY`
: Exact identity is present at the byte/structural layer, but the complete causal, entropy, cryptographic, source or statistical admission stack has not established the stronger forward-null result.

`FORWARD_NULL_CONSISTENT_MISS`
: A fully admitted trial produced no exact hit and remains consistent with the specified forward-causal null.

`FORWARD_NULL_INCOMPATIBILITY_CANDIDATE`
: Under a fully admitted evidence stack and statistical rule, the record crosses the specified incompatibility criterion. This still does not identify a physical mechanism.

## Research-program maturity

A separate human/machine summary MAY describe the state of an entire research program, for example:

```text
SPEC_ONLY
REFERENCE_IMPLEMENTATION_PARTIAL
REFERENCE_IMPLEMENTATION_COMPLETE
SECOND_IMPLEMENTATION_COMPLETE
CROSS_IMPLEMENTATION_CONFORMANCE
EXTERNAL_NULL_BENCH_COMPLETE
INDEPENDENT_REPLICATION_COMPLETE
MULTISITE_REPLICATION_COMPLETE
```

These are maturity/replication statements, not per-trial statistical verdicts.

A research program can be highly mature while all physical trials are null. Conversely, one apparently extraordinary trial does not make the program mature.

## Physical interpretation

Every machine verifier result keeps:

```text
physical_interpretation = NO_AUTOMATIC_PHYSICAL_RETROCAUSALITY_CLAIM
```

If a future fully admitted result is statistically incompatible with the specified forward null, scientific interpretation must still consider at least:

- failure of an admitted entropy premise;
- omitted causal side information;
- source-proof failure;
- witness/common-mode failure;
- implementation/specification error;
- statistical-model failure;
- and only after those possibilities survive independent audit, hypotheses involving new physical mechanisms.

AIFC is an evidence-admission protocol, not a mechanism detector.
