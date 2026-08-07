# Scientific Assurance Lineage — related-work boundary

Status: **TARGETED PRIOR-ART NOTES / SYSTEMATIC REVIEW NOT COMPLETE**

This document records the current boundary around the Scientific Assurance Lineage (SAL) research candidate. It is not a claim of global novelty.

## Closest neighboring families

### Proof-Carrying Code

Proof-Carrying Code (PCC) establishes the general architecture in which a producer supplies code together with a proof that the code satisfies a previously defined safety policy.

Reference starting point:

- George C. Necula, *Proof-Carrying Code*, POPL 1997: https://doi.org/10.1145/263699.263712

SAL does not claim to invent proof-carrying verification. The distinction under study is that SAL makes the **evolution of the conclusion-authorizing policy/verifier semantics themselves** a proof obligation.

### Proof plus authority / authorization logic

Authorization systems already combine semantic reasoning with authority, trust, credentials and signed principals. Therefore `proof + authority` is not a SAL novelty claim.

Reference starting point:

- *By Reason and Authority: A System for Authorization of Proof-Carrying Code*: https://www.sciweavers.org/publications/reason-and-authority-system-authorization-proof-carrying-code

SAL instead asks whether a successor verifier is entitled to change the semantics that determine the authority of its conclusions over inherited evidence.

### Trusted Computing Base recovery and remote attestation

Trusted-computing systems explicitly address changing TCB levels, attestation evidence, verification collateral and relying-party decisions about whether trust can be re-established after platform updates.

Reference starting point:

- Intel, *Trusted Computing Base Recovery*: https://www.intel.com/content/www/us/en/developer/articles/technical/software-security-guidance/best-practices/trusted-computing-base-recovery.html

This is a close conceptual neighbor because trusted machinery evolves and evidence is used to reassess trust. The current SAL distinction is:

```text
TCB recovery / attestation:
    Which trusted platform version/state is running,
    and does it satisfy the relying party's trust policy?

SAL:
    By what authority did the successor machinery change the semantics
    that determine which scientific conclusions are admissible?
```

### Translation validation, refinement and verified evolution

Translation validation checks concrete transformations rather than trusting a transformer globally; refinement and verified-upgrade systems likewise provide important neighboring ideas for semantics-preserving change.

SAL should not claim novelty merely for checking a transition. The narrower target is **authority-preserving evolution of admission semantics**, including inherited rejection preservation, authoritative theorem identity and non-self-authenticating normative roots.

### Scientific provenance and reproducible workflows

Scientific provenance systems preserve data/process lineage for reproducibility and audit. SAL does not claim to invent scientific provenance.

SAL extends the question from `where did this result come from?` to `what lineage authorizes the current verifier to interpret inherited evidence with this strength of conclusion?`

## Current candidate gap

The targeted search performed so far has not identified an exact end-to-end analogue that simultaneously requires all of the following for evolving verifier/admission machinery:

```text
versioned semantic identities
+ authoritative theorem anchoring
+ inherited rejection preservation
+ partial order of admission authority
+ proof-replayed weakening/replacement
+ immutable/versioned hash and validator semantics
+ non-self-authenticating normative roots
+ explicit lineage for changes to conclusion-authorizing semantics
```

This absence is not proof of worldwide novelty.

## Preferred novelty language

Use:

> **We study proof-carrying evolution of scientific assurance machinery: how a verifier, its semantic predicates, admission gates, authority ordering and normative roots may change over time without silently increasing the authority of conclusions accepted from inherited evidence.**

And:

> **Our central requirement is that both conclusions and the semantics authorizing those conclusions have verifiable lineage.**

Do not use:

```text
SAL is the first system combining proofs and authority.
SAL invents proof-carrying verification.
SAL is globally novel.
Assurance-Lineage Soundness is already a proved general theorem.
```

## Current epistemic status

```text
SAL_EXACT_PRIOR_ART = NOT_FOUND_IN_TARGETED_SEARCH
COMPONENT_PRIOR_ART = EXTENSIVE
SAL_COMPOSITION_LEVEL_NOVELTY = PLAUSIBLE_CANDIDATE
GLOBAL_NOVELTY = NOT_ESTABLISHED
SYSTEMATIC_LITERATURE_REVIEW = REQUIRED
FORMAL_SOUNDNESS_PROOF = REQUIRED
```

A security/formal-methods review should explicitly include PCC/PCD, proof-carrying authorization, authorization logics, TCB recovery and remote attestation, translation validation, verified software update frameworks, trusted-computing-base evolution, proof-carrying data/provenance, refinement systems and reproducible scientific workflow literature before any global priority claim is made.
