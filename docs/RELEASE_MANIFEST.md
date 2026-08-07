# Proof-Carrying Release Manifest

Status: `NORMATIVE DRAFT`

The frozen release gate is not satisfied by changing a status string.

A final AIFC v1.0 release MUST carry an `AIFC/release-manifest/v1` object. Every required gate listed by the frozen release-gate profile MUST have one machine-readable result containing:

- gate identifier;
- `PASS`, `FAIL`, `BLOCKED`, or `UNRESOLVED`;
- evidence hash;
- verifier identity and version;
- run/commit identifier;
- optional notes hash.

Schema: [`../schemas/release-manifest.schema.json`](../schemas/release-manifest.schema.json).

## FROZEN rule

`overall_status = FROZEN_PASS` is admissible only if:

1. the manifest covers the exact required gate set for the frozen release-gate profile;
2. every required gate is present exactly once;
3. every required gate result is `PASS`;
4. every evidence hash resolves to the preserved evidence object/artifact;
5. the declared verifier/run identifiers are reproducible;
6. the repository commit and release-gate profile hash match the released bytes;
7. the manifest hash verifies under the frozen canonicalization profile.

A human approval, README badge, Git tag, or CI green check cannot substitute for missing per-gate evidence.

The draft repository MUST keep `AIFC_V1_FROZEN = FALSE` until the proof-carrying manifest verifies.
