# Scientific Assurance Lineage — research draft v0.1

Status: **RESEARCH CANDIDATE / NOT A FROZEN AIFC v1 REQUIREMENT**

Scientific Assurance Lineage (SAL) is a candidate general formalization extracted from concrete verifier-evolution failures discovered while hardening AIFC. It is intentionally broader than future-information experiments.

SAL does **not** claim novelty for proof-carrying code, authorization logic, provenance, attestation, refinement, translation validation, or trusted-computing-base recovery individually. The candidate contribution is narrower: proof-carrying evolution of the semantics that authorize scientific conclusions.

## 1. Core object

Model an assurance system as

\[
\mathcal L=(E,\Sigma,G,V,A,\mathcal R,\tau),
\]

where:

- \(E\) — evidence identities;
- \(\Sigma\) — executable semantic / predicate identities;
- \(G\) — admission-gate semantics;
- \(V\) — verifier semantics;
- \(A\) — a partial order of admission authority;
- \(\mathcal R\) — normative / authority roots;
- \(\tau\) — proof-carrying lineage transitions.

SAL constrains the evolution of the whole tuple, not merely the format of one certificate.

## 2. Central distinction

\[
\boxed{\text{proof validity}\neq\text{normative-transition validity}}
\]

A proof

\[
\pi:\bigwedge_i S_i\Rightarrow P
\]

is insufficient for an assurance transition unless the propositions interpreted as \(P\) and \(S_i\) are themselves bound to authoritative semantic identities.

A transition is admissible only when both sides hold:

\[
\operatorname{AuthoritativePremises}
\land
\operatorname{ValidProof}.
\]

For the current Boolean strengthening profile this means at minimum:

\[
\operatorname{Anchor}(P,P_{\rm auth})
\land
\bigwedge_i\operatorname{Anchor}(S_i,S_{i,\rm auth})
\land
\operatorname{Replay}\!\left(\pi:\bigwedge_iS_i\Rightarrow P\right).
\]

## 3. AIFC Law of Proof Anchoring

> **A proof of an assurance transition is admissible only if every authority-bearing proposition used by the proof is bound to an authoritative normative semantic identity independently of that proof.**

Equivalent operational rule:

> **A proof of assurance evolution cannot create the normative authority of the semantics that constitute its own theorem.**

A human-readable intuition is:

> A correct proof does not establish a normative transition unless the theorem being proved is itself authoritatively identified.

## 4. Authority-Closed Proof

Let \(Dep(\pi,T)\) be the directed dependency graph of authority-bearing objects required to interpret theorem \(T\), proved by \(\pi\).

`AuthorityClosed(π,T)` requires:

1. every authority-bearing semantic node resolves to an immutable or lineage-validated identity;
2. every such node is reachable from a previously established normative root;
3. no authoritative dependency is created or normatively defined by \(\pi\);
4. no authoritative dependency is created or normatively defined by a descendant of \(\pi\);
5. the graph is acyclic under the relation `normatively_authorizes`.

In particular, for every authority dependency \(x\) of \(T\):

\[
\pi\not\leadsto x,
\]

where \(\leadsto\) means `creates or normatively defines`.

The proof may consume authoritative premises; it may not manufacture the premises that legitimize itself.

## 5. Normative root law

> **Normative roots must themselves be immutable or lineage-bound.**

Forbidden orientation:

```text
proof
  -> defines predecessor semantics
  -> proves successor strengthens those semantics
```

Required orientation:

```text
historical normative root
        ↓
release identity
        ↓
gate-definition identity
        ↓
atom / predicate identity
        ↓
executable semantics
        ↓
proof
```

No layer may acquire authority merely by referring to itself or to a descendant.

## 6. Assurance laws collected from AIFC hardening

### Law 1 — Do not forget

A mandatory rejection learned by a predecessor verifier must not silently disappear in a successor.

### Law 2 — Do not trust inheritance

A successor or caller must not define the set of predecessor obligations it claims to inherit.

### Law 3 — Replay the proof

A strengthening or equivalence transition is established by executing its proof method, not by accepting a field that claims `PASS`.

### Law 4 — Do not rewrite identity

An issued schema, profile, hash-domain, validator-semantics or authority-order identity must not acquire new semantics under the old identifier.

### Law 5 — Anchor the theorem

Proof replay is admissible only over authoritative predecessor and successor semantics.

### Law 6 — Anchor the roots

The sources that confer normative authority are immutable or evolve through their own valid lineage; they may not self-authenticate through the transition they authorize.

Over all six laws:

> **Assurance must be monotone unless the weakening itself carries independently replayable and normatively anchored authorization.**

## 7. Motivating counterexample: correct proof, wrong theorem

Assume the historically issued predecessor gate means

\[
P_{\rm auth}=A\land B\land C.
\]

A claimant supplies a fresh, self-consistent object using the same human gate name but defines

\[
P'=A.
\]

The claimant then supplies successor semantics \(S\) and a valid truth-table proof

\[
S\Rightarrow A.
\]

Every local computational check can pass:

```text
hash resolution       = PASS
canonicalization       = PASS
Boolean proof replay   = PASS
truth table            = PASS
```

Yet the required normative claim

\[
S\Rightarrow(A\land B\land C)
\]

has not been established.

The failure is theorem provenance, not proof execution.

AIFC attack classes:

```text
UNANCHORED_PREDECESSOR_GATE_DEFINITION
GATE_DEFINITION_SEMANTIC_REBINDING
GATE_ATOM_SEMANTIC_REBINDING
RELEASE_GATE_DOCUMENT_REBINDING
```

## 8. Assurance-preserving verifier evolution

Let

\[
\mathcal S_n=(R_n,\Sigma_n,G_n,V_n,A_n)
\]

and

\[
\tau_n:\mathcal S_n\to\mathcal S_{n+1}.
\]

A candidate valid transition preserves all of the following dimensions:

- **Identity preservation** — issued semantic identities are immutable or explicitly lineage-transitioned;
- **Authoritative resolution** — normative predecessor/successor objects are resolved from authoritative roots, not selected by the claimant;
- **Predicate anchoring** — proof atoms/predicates are bound to executable semantics;
- **Authority closure** — a proof cannot self-anchor or descendant-anchor its theorem semantics;
- **Admission-order identity** — the authority partial order is immutable/versioned;
- **Inherited monotonicity** — predecessor rejection obligations remain effective;
- **Proof replay** — every permitted weakening/replacement is independently replayed;
- **Root lineage** — normative roots are immutable or validly transitioned.

## 9. Assurance-Lineage Soundness — theorem target

This is a theorem target, **not yet a proved general theorem**.

Assume:

1. evidence and semantic identities are immutable or connected by valid explicit lineage;
2. normative objects are obtained through an authoritative resolver;
3. proof predicates are bound to executable semantic identities;
4. transition proofs are authority-closed;
5. the admission-authority partial order is immutable/versioned;
6. inherited mandatory rejection semantics are preserved;
7. every weakening/replacement transition is independently proof-replayed;
8. normative roots are immutable or themselves connected by valid lineage.

Then, for inherited evidence \(e\), a successor should not be able to obtain a stronger admission outcome solely by verifier/protocol evolution:

\[
\boxed{
V_{n+1}(W(e))\not\succ_A V_n(e)
}
\]

unless an explicit valid lineage transition normatively authorizes the relevant semantic change.

The targeted attacker classes are:

```text
forgotten rejection
release-gate rebinding
predicate rebinding
schema/profile identity mutation
admission-order mutation
hash-profile mutation
fake strengthening receipt
theorem substitution
self-selected normative root
self/descendant authentication
```

A proof of this theorem target must state precisely which transition classes count as authorized weakening and which trust root is assumed.

## 10. Relationship to AIFC

SAL core does not depend on retrocausality, randomness beacons, exact future targets, or AIFC statistics.

AIFC is the originating case study because repeated adversarial hardening produced concrete failures in:

```text
schema/checker synchronization
CI-result provenance
verifier downgrade composition
same-rank authority escalation
caller-defined inheritance
pre-blessed strengthening evidence
historical hash-domain mutation
candidate unanchored theorem provenance
```

AIFC therefore provides machine-found motivating counterexamples and an executable reference environment for SAL, while SAL remains a candidate general assurance model.

## 11. Novelty boundary

Do not claim:

```text
SAL_INVENTS_PROOFS_PLUS_AUTHORITY = FALSE
SAL_INVENTS_PROOF_CARRYING_CODE = FALSE
SAL_INVENTS_ATTESTATION = FALSE
SAL_GLOBAL_NOVELTY = NOT_ESTABLISHED
ASSURANCE_LINEAGE_SOUNDNESS_GENERAL_THEOREM = NOT_YET_PROVED
```

Candidate research claim:

> **SAL studies proof-carrying evolution of scientific assurance machinery: how verifier semantics, predicates, gates, admission authority and normative roots may change over time without silently increasing the authority of conclusions accepted from inherited evidence.**

A broader systematic review remains required before any global priority claim.