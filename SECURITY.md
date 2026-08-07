# Security Policy

AIFC treats verifier correctness and evidence integrity as security properties.

## What counts as a security-relevant issue

Please report issues that could cause any of the following:

- a transcript is admitted when a mandatory gate should fail;
- candidate multiplicity is undercounted;
- stale/rollback evidence is accepted as fresh;
- conflicting witness histories are accepted under the declared fault model;
- target binding can be substituted or replayed;
- canonicalization ambiguity changes exact-match semantics;
- an asserted metadata field can promote evidence without external support;
- sequential statistics can be manipulated by peeking/stopping outside the declared model;
- a malformed evidence package bypasses a verifier invariant;
- a test vector expected to fail is silently accepted.

## Reporting

If public disclosure would make it easy to forge apparently valid AIFC evidence before a fix exists, use GitHub's private security-advisory mechanism for this repository when available.

Otherwise, open a GitHub issue with the minimum information needed to reproduce the problem and clearly mark it as an evidence-integrity or verifier-soundness issue.

## Include

Where possible provide:

- affected commit/version;
- minimal malicious transcript or patch;
- expected failure code;
- observed acceptance path;
- whether the attack requires compromised witnesses, entropy source, candidate host, or verifier;
- whether the issue affects the specification, reference implementation, or only one deployment.

## Response philosophy

AIFC is fail-closed. When a soundness issue is credible and unresolved, the affected evidence grade should be considered suspended rather than rhetorically defended.

## Non-security scientific critiques

Questions about novelty, physical interpretation, causal assumptions, or statistical modeling are extremely valuable but should normally be filed as research issues rather than security vulnerabilities unless they enable a concrete false admission.
