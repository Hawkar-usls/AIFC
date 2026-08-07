# AIFC Time and Ordering Semantics — v1.0 Draft

Status: `NORMATIVE DRAFT`

AIFC does not use ordinary wall-clock timestamps as its sole causal trust root.

## 1. Primary ordering

The primary protocol order is established by:

- experiment-wide ledger sequence;
- hash-linked prior-event binding;
- externally certified freeze/quorum position;
- deterministic target-selection rule;
- verifiable target-source event/round identity;
- terminal publication position.

Wall-clock timestamps may help humans interpret the transcript, but they do not override contradictory certified event order.

## 2. Timestamp rule

Every wall-clock timestamp MUST be treated as one of:

```text
METADATA_ONLY
EXTERNAL_TIMING_EVIDENCE
```

Default is `METADATA_ONLY`.

A local OS clock, filesystem mtime, application timestamp, or manually entered time MUST NOT establish that target information did or did not exist at freeze.

## 3. External timing evidence

If a protocol requirement depends on an actual elapsed duration — for example `target event at least 120 s after quorum certification` — the experiment MUST declare:

- external time source;
- synchronization method;
- uncertainty/error bound;
- receipt or measurement binding;
- failure behavior when uncertainty overlaps the required interval.

If these are unavailable, the protocol SHOULD instead use discrete externally verifiable event order such as a predetermined future randomness-beacon round.

## 4. Future beacon rounds

When using a public beacon, the selected round/event MUST be determined from frozen pre-target information before that round output is available.

The protocol must distinguish:

```text
round identifier already known
from
round output already available
```

Knowing which future round will be used is allowed. Having target-derived output from that round before freeze is not.

## 5. Clock rollback

A backward jump in a local clock does not by itself imply causal inversion and does not invalidate a correctly ordered ledger.

Likewise, a timestamp claiming an earlier time does not create pre-target evidence if the signed/anchored event order places the object later.

## 6. Tie and uncertainty handling

If the ordering between freeze certification and target availability cannot be established under the declared evidence model, the trial MUST fail closed as `INVALIDATED_EVIDENCE` or an explicitly weaker non-independent grade.

AIFC never resolves ambiguous ordering by choosing the interpretation favorable to an anomaly claim.
