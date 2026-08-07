# Contributing to AIFC

AIFC welcomes skeptical contributions.

The highest-value contribution is often not a feature. It is a counterexample, missing threat, invalid assumption, verifier exploit, or independent replication.

## Preferred contributions

- causal leakage paths missing from the threat model;
- counterexamples to stated probability bounds or protocol compositions;
- entropy-model critiques;
- rollback/replay/fork attacks;
- verifier fail-open bugs;
- independent reimplementations;
- new adversarial test vectors;
- public-beacon integrations;
- prior-art references that narrow or falsify novelty claims;
- null-result replications.

## Evidence standard

A technical claim should include, where applicable:

1. exact version/commit;
2. minimal reproducible input;
3. expected result;
4. observed result;
5. deterministic replay steps;
6. hashes of relevant artifacts;
7. whether the result affects protocol soundness, implementation correctness, or only documentation.

## Claim discipline

Contributions MUST NOT silently promote evidence grades.

In particular:

- a simulation is not physical evidence;
- a signature is not proof of unpredictability;
- a timestamp is not proof of causal isolation;
- a match is not proof of retrocausality;
- absence of found prior art is not proof of global novelty.

## Pull requests

Keep pull requests narrow and auditable.

For changes affecting evidence semantics, include:

```text
CLAIM_BEFORE
CLAIM_AFTER
NEW_ASSUMPTIONS
REMOVED_ASSUMPTIONS
ATTACKS_ADDED
ATTACKS_REMOVED
EVIDENCE_GRADE_IMPACT
```

Changes to normative specification text should identify whether they are:

- `CLARIFICATION`
- `HARDENING`
- `BREAKING_PROTOCOL_CHANGE`
- `EVIDENCE_GRADE_CHANGE`

## Adversarial changes

If you discover a way to make the verifier admit a transcript that violates the specification, treat it as a high-priority correctness/security issue and follow `SECURITY.md` when public disclosure would enable active evidence forgery.

## Style

Prefer:

- explicit assumptions;
- machine-readable evidence;
- canonical serialization;
- independent recomputation;
- negative results;
- precise failure codes.

Avoid:

- rhetorical certainty;
- hidden heuristics;
- post-hoc interpretation;
- unverifiable booleans standing in for external evidence.

## Scientific disagreement

Disagreement with AIFC's premise or usefulness is welcome when technically argued.

The protocol should survive criticism, not avoid it.
