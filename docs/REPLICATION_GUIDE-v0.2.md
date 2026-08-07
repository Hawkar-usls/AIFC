# AIFC External Replication Guide — v0.2 Draft

Status: `DEVELOPMENT GUIDE / NOT FROZEN`

This guide supersedes the earlier replication example for PR #5 evaluation. It describes the evidence shape expected by the content-addressed Verifier A replay path.

## 1. What a replicator should receive

A replication package should not require trust in the producer's in-memory state or local database.

The portable evidence set is conceptually:

```text
replay-package.json
content-addressed evidence-store index
content-addressed exact evidence bytes
frozen AIFC specification/profile version
independent verifier implementation
```

The replay manifest contains content identities, not embedded producer objects.

## 2. Freeze the experiment before trials

Create and canonicalize:

```text
AIFC/experiment-plan/v1
```

Resolve every policy/object referenced by that plan.

Using the initial witness registry, obtain experiment-scoped:

```text
AIFC/experiment-plan-receipt/v1
AIFC/experiment-plan-quorum/v1
```

Only after the plan quorum exists may the first trial slot be created.

The first `CREATED` event must bind:

```text
payload_hash = experiment_plan_hash
prerequisite_certificate_hash = experiment_plan_quorum_hash
```

Then obtain the ordinary trial-scoped `CREATED` quorum certificate.

## 3. Candidate generation

Produce candidate data only after the certified `CREATED` boundary.

Preserve:

- candidate-generation external evidence;
- `AIFC/candidate-generation-profile/v1`;
- every `AIFC/hard-witness/v1`;
- `AIFC/candidate-set/v1`.

The independent verifier must recover candidate multiplicity from the resolved set.

## 4. PRE_RETURN

The `PRE_RETURN_FROZEN` ledger event binds the candidate-set hash.

Preserve the PRE_RETURN certificate and its quorum.

The PRE_RETURN certificate binds target-selector/derivation **policies**, not a target-derived future output.

## 5. Select and define the future challenge

Create the per-trial selector profile according to the frozen selector policy.

Create one target derivation profile according to the frozen derivation policy.

For strongest-grade v1 there is exactly one admitted selector and one admitted derivation per trial.

## 6. Freeze the full pre-target view

Before target observation, construct:

```text
AIFC/pre-target-conditioning-view/v1
```

Resolve and include the required operator/source/pre-target evidence.

Obtain a trial quorum over the view hash.

The `TARGET_ARMED` ledger event binds the view-quorum hash.

Only after this boundary is the target-producing event eligible to be observed.

## 7. Target observation

Preserve the exact raw source object bytes and source-specific proof material.

Create `AIFC/target-evidence/v1` only from the selected event.

The verifier, not the producer, should replay the frozen extraction/framing/transformation from the raw source bytes.

## 8. Entropy evidence

The experiment plan already froze `AIFC/entropy-policy/v1`.

The trial-specific entropy profile must match that policy, bind the frozen pre-target conditioning-view hash and carry all required evidence classes.

Do not write:

```text
p_i = 2^-256 because source is a 256-bit RNG
```

without the proof-carrying source/security/conditioning argument required by policy.

## 9. Verification and terminal publication

The completed order is:

```text
TARGET_OBSERVED
  -> VERIFIED
  -> evidence bundle
  -> TERMINAL binds bundle hash
  -> publication manifest enumerates terminal/bundle
  -> external publication root
```

No initiated trial may disappear.

## 10. Content-addressed evidence store

The development verifier accepts an `AIFC/evidence-store-index/v1` plus a local store root.

Every protocol object must be stored as exact canonical JSON bytes. Raw evidence is hashed over exact bytes.

A replay should fail if a referenced object:

- is missing;
- has the wrong declared type;
- has noncanonical stored bytes;
- rehashes to a different identity;
- escapes the evidence-store root;
- or contradicts a cross-binding.

## 11. Development CLI

The newest PR #5 preregistration-aware development entry point is:

```text
python reference/verifier/aifc_verify_v02.py \
  --package replay-package.json \
  --store-index evidence-store/index.json \
  --store-root evidence-store/
```

The output is a canonical `AIFC/verifier-result/v1` object.

A successful development replay does **not** imply full Implementation A. The verifier result must continue to expose blocked cryptographic/causal/source/statistical/cross-implementation gates.

## 12. What an independent laboratory must not reuse as trust

A true external replication should not rely on:

- Genesis as a scientific trust root;
- a producer's self-reported hashes without resolving bytes;
- the producer's database of “successful trials”;
- one host running several nominal witnesses;
- post-target reconstruction of side information;
- a locally chosen beacon response without source proof;
- the reference verifier as Implementation B.

The goal is not to recreate JANUS. It is to execute the AIFC evidence contract independently.
