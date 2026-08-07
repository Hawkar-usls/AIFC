# Target Derivation Profile

Status: `NORMATIVE DRAFT`

Selecting a future event is not enough. AIFC must also freeze how that event's raw output becomes the exact target bytes.

## Threat

After observing a beacon pulse or other future source object, an operator could choose among multiple transformations: first 256 bits, last 256 bits, a hash, a hash with a round number, XOR partitions, alternate encodings, or other post-hoc derivations. This creates hidden multiplicity even when the future event itself was selected correctly.

## Rule

Before the designated target event is observed, the trial MUST bind an `AIFC/target-derivation-profile/v1` object.

The profile fixes:

- source identity/protocol version;
- raw source-object schema;
- future event selector hash;
- exact extraction rule;
- transformation algorithm and input order;
- domain separator;
- output length;
- profile hash.

Schema: [`../schemas/target-derivation-profile.schema.json`](../schemas/target-derivation-profile.schema.json).

`PRE_RETURN` and the entropy profile MUST bind the same derivation-profile hash. Target evidence MUST bind both the raw source-object hash and the derivation-profile hash.

## Admission rule

A transformation chosen, modified, or ambiguously interpreted after target observation invalidates the independent-future grade. If multiple derivations were preregistered, they are candidate/target multiplicity and MUST be charged by the statistical model.

Required attack: `POST_HOC_TARGET_DERIVATION`.
