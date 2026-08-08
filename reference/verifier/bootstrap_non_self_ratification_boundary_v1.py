#!/usr/bin/env python3
"""SAL v1.16 bootstrap non-self-ratification boundary.

Root-relative theorem only:
within a normative jurisdiction whose independence rule requires a bootstrap
ratifier to lie outside the bootstrap root's reflexive-transitive descendant
closure, no member of that internal closure can independently ratify the root.

This module does NOT establish any external ratifier's authority or bootstrap
legitimacy. Being outside the internal closure is only a structural candidate.
"""
from __future__ import annotations

from dataclasses import dataclass
import inspect
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from canonical import domain_hash
from scientific_assurance_lineage_v13 import git_blob_sha1_bytes
import bootstrap_authority_origin_boundary_v1 as v115

ROOT = Path(__file__).resolve().parents[2]
SOURCE_MAIN_COMMIT = "54a689a73df5d81ac161e848ffd867f3bdf8a15f"
SOURCE_TREE_SHA = "be81ec868103439d75860391cf50d9cd59f2413c"
BOOTSTRAP_COMMIT = "908de7afddcf9f72c98c2b3fb696a41be1e438e0"

ROOT_V1_ID = "AIFC-NORMATIVE-ASSURANCE-ROOTS-V1"
ROOT_V1_PATH = "conformance/AIFC-NORMATIVE-ASSURANCE-ROOTS-v1.json"
ROOT_V1_BLOB = "0aec9d6ad0d54ce10d312d28a8cb0def1729f835"
ROOT_V2_ID = "AIFC-NORMATIVE-ASSURANCE-ROOTS-V2"
ROOT_V2_PATH = "conformance/AIFC-NORMATIVE-ASSURANCE-ROOTS-v2.json"
ROOT_V2_BLOB = "d2bb7f3917f8761836825a4e80f03c1e282fc37d"

V115_AUDIT_ID = "AIFC-SAL-V1.15-BOOTSTRAP-AUTHORITY-ORIGIN-AUDIT-V1"
V115_AUDIT_PATH = "conformance/AIFC-BOOTSTRAP-AUTHORITY-ORIGIN-AUDIT-v1.json"
V115_AUDIT_BLOB = "ed14b065f4a0d74419de10e2880b39aa235023b1"
V115_AUDIT_HASH = "51f8b083c146c9076520fe2880167e6a105fcbc037de5a49813e944c1d93e2d6"

PROFILE_PATH = "conformance/AIFC-BOOTSTRAP-NON-SELF-RATIFICATION-PROFILE-v1.json"
PROFILE_ID = "AIFC-SAL-V1.16-BOOTSTRAP-NON-SELF-RATIFICATION-PROFILE-V1"
PROFILE_HASH = "5134a05188c5d078a2da6cee08783cff5823f53addb5d007c5ebcb6cd2be90ca"
PROFILE_BLOB = "c8628c1d77c737db5821b9eff96e69b40f20a2bb"
PROFILE_DOMAIN = "AIFC:BOOTSTRAP-NON-SELF-RATIFICATION-PROFILE:v1"
AUDIT_DOMAIN = "AIFC:BOOTSTRAP-NON-SELF-RATIFICATION-AUDIT:v1"

BLOCKED_COMPLETENESS = "BLOCKED_UNAUTHORIZED_COMPLETENESS_BASIS"
STRUCTURAL_ONLY = "OUTSIDE_INTERNAL_CLOSURE_STRUCTURAL_CANDIDATE_ONLY_NOT_AUTHORITY"
INTERNAL_REJECTION = "INTERNAL_DESCENDANT_NOT_INDEPENDENT_RATIFIER"


class BootstrapNonSelfRatificationV1Error(ValueError):
    pass


@dataclass(frozen=True)
class BootstrapNonSelfRatificationReport:
    source_v115_boundary_identity: str
    jurisdiction_root_identity: str
    root_v1_identity: str
    root_v2_identity: str
    root_v2_predecessor_relation: str
    internal_closure_definition: str
    internal_closure_derivation: str
    internal_closure_node_count_current_model: int
    non_self_ratification_theorem: str
    bootstrap_self_ratification: str
    descendant_ratifier_promotion: str
    authority_cycle_ratification: str
    externality_laundering: str
    caller_ratifier_input_surface: str
    outside_closure_semantics: str
    external_ratifier_structural_independence: str
    external_ratifier_authority_admissibility: str
    external_bootstrap_ratification: str
    internal_authority_closure_vs_bootstrap_legitimacy: str
    bootstrap_authority_legitimacy: str
    current_internal_verification_path_to_bootstrap_legitimacy: str
    normative_authority_origin_internal_proof: str
    global_non_self_ratification_theorem_for_all_verification_systems: str
    normative_lineage_completeness: str
    derived_semantic_authority: str
    solver_invocation_count: int
    next_required_basis: str
    status: str


def _load_exact(path_text: str, expected_blob: str, label: str) -> Mapping[str, Any]:
    raw = (ROOT / path_text).read_bytes()
    actual = git_blob_sha1_bytes(raw)
    if actual != expected_blob:
        raise BootstrapNonSelfRatificationV1Error(
            f"V116_EXACT_SOURCE_REBINDING:{label}:{actual}"
        )
    obj = json.loads(raw.decode("utf-8"))
    if not isinstance(obj, Mapping):
        raise BootstrapNonSelfRatificationV1Error("V116_SOURCE_NOT_MAPPING:" + label)
    return obj


def profile_content_hash(profile: Mapping[str, Any]) -> str:
    material = dict(profile)
    material.pop("profile_content_hash", None)
    return domain_hash(PROFILE_DOMAIN, material)


def audit_content_hash(audit: Mapping[str, Any]) -> str:
    material = dict(audit)
    material.pop("audit_content_hash", None)
    return domain_hash(AUDIT_DOMAIN, material)


def verify_profile(profile: Mapping[str, Any]) -> None:
    expected = {
        "schema": "AIFC/bootstrap-non-self-ratification-profile/v1",
        "profile_id": PROFILE_ID,
        "source_main_commit": SOURCE_MAIN_COMMIT,
        "source_tree_sha": SOURCE_TREE_SHA,
        "source_v115_audit_id": V115_AUDIT_ID,
        "source_v115_audit_path": V115_AUDIT_PATH,
        "source_v115_audit_git_blob_sha1": V115_AUDIT_BLOB,
        "source_v115_audit_content_hash": V115_AUDIT_HASH,
        "bootstrap_root_commit": BOOTSTRAP_COMMIT,
        "root_v1_registry_id": ROOT_V1_ID,
        "root_v1_registry_path": ROOT_V1_PATH,
        "root_v1_registry_git_blob_sha1": ROOT_V1_BLOB,
        "root_v2_registry_id": ROOT_V2_ID,
        "root_v2_registry_path": ROOT_V2_PATH,
        "root_v2_registry_git_blob_sha1": ROOT_V2_BLOB,
        "jurisdiction_dependency_edge_direction": "PREDECESSOR_TO_SUCCESSOR",
        "internal_closure_definition": "REFLEXIVE_TRANSITIVE_DESCENDANT_CLOSURE_OF_BOOTSTRAP_ROOT",
        "independent_ratifier_requirement": "RATIFIER_OUTSIDE_INTERNAL_JURISDICTION_CLOSURE",
        "outside_closure_semantics": STRUCTURAL_ONLY,
        "bootstrap_self_ratification": "FORBIDDEN",
        "descendant_ratifier_to_bootstrap_legitimacy": "FORBIDDEN",
        "authority_cycle_to_bootstrap_legitimacy": "FORBIDDEN",
        "externality_label_without_independent_provenance": "FORBIDDEN",
        "caller_ratifier_input_surface": "FORBIDDEN",
        "external_ratifier_authority_admissibility": "NOT_ESTABLISHED",
        "external_bootstrap_ratification": "NOT_PERFORMED",
        "bootstrap_authority_legitimacy": "NOT_ESTABLISHED",
        "normative_lineage_completeness": BLOCKED_COMPLETENESS,
        "profile_authority_status": "SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE",
    }
    for key, value in expected.items():
        if profile.get(key) != value:
            raise BootstrapNonSelfRatificationV1Error("V116_PROFILE_REBINDING:" + key)
    if profile.get("profile_content_hash") != profile_content_hash(profile):
        raise BootstrapNonSelfRatificationV1Error("V116_PROFILE_CONTENT_REBINDING")
    if profile.get("profile_content_hash") != PROFILE_HASH:
        raise BootstrapNonSelfRatificationV1Error("V116_PROFILE_EXACT_HASH_REBINDING")
    for key in (
        "external_ratifier",
        "external_ratifier_receipt",
        "external_authority",
        "bootstrap_legitimacy_proof",
        "authority_lineage_ref",
        "authority_status",
    ):
        if key in profile:
            raise BootstrapNonSelfRatificationV1Error(
                "V116_RATIFIER_OR_LEGITIMACY_INPUT_SURFACE:" + key
            )


def _normalized_graph(
    nodes: Iterable[str], edges: Iterable[tuple[str, str]]
) -> tuple[frozenset[str], tuple[tuple[str, str], ...]]:
    node_set = frozenset(nodes)
    if not node_set:
        raise BootstrapNonSelfRatificationV1Error("V116_EMPTY_JURISDICTION_GRAPH")
    edge_set: set[tuple[str, str]] = set()
    for edge in edges:
        if not isinstance(edge, tuple) or len(edge) != 2:
            raise BootstrapNonSelfRatificationV1Error("V116_MALFORMED_JURISDICTION_EDGE")
        u, v = edge
        if u not in node_set or v not in node_set:
            raise BootstrapNonSelfRatificationV1Error("V116_UNKNOWN_JURISDICTION_NODE")
        edge_set.add((u, v))
    return node_set, tuple(sorted(edge_set))


def descendant_closure(
    root: str, nodes: Iterable[str], edges: Iterable[tuple[str, str]]
) -> frozenset[str]:
    node_set, edge_tuple = _normalized_graph(nodes, edges)
    if root not in node_set:
        raise BootstrapNonSelfRatificationV1Error("V116_ROOT_NOT_IN_JURISDICTION_GRAPH")
    adjacency = {n: [] for n in node_set}
    indegree = {n: 0 for n in node_set}
    for u, v in edge_tuple:
        adjacency[u].append(v)
        indegree[v] += 1
    ready = sorted(n for n, d in indegree.items() if d == 0)
    seen = 0
    while ready:
        n = ready.pop(0)
        seen += 1
        for nxt in sorted(adjacency[n]):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                ready.append(nxt)
                ready.sort()
    if seen != len(node_set):
        raise BootstrapNonSelfRatificationV1Error("V116_JURISDICTION_CYCLE")
    closure = {root}
    work = [root]
    while work:
        n = work.pop()
        for nxt in adjacency[n]:
            if nxt not in closure:
                closure.add(nxt)
                work.append(nxt)
    return frozenset(closure)


def assess_ratifier(
    root: str,
    nodes: Iterable[str],
    edges: Iterable[tuple[str, str]],
    ratifier: str,
    *,
    claimed_external: bool = False,
) -> str:
    node_set = frozenset(nodes)
    if ratifier not in node_set:
        raise BootstrapNonSelfRatificationV1Error("V116_RATIFIER_PROVENANCE_UNBOUND")
    closure = descendant_closure(root, node_set, edges)
    if ratifier in closure:
        # A label cannot launder descendant provenance into independence.
        return INTERNAL_REJECTION
    # Outside closure is necessary only. It is not an authority decision.
    return STRUCTURAL_ONLY


def verify_non_self_ratification_theorem(
    root: str, nodes: Iterable[str], edges: Iterable[tuple[str, str]]
) -> str:
    node_set, edge_tuple = _normalized_graph(nodes, edges)
    closure = descendant_closure(root, node_set, edge_tuple)
    for ratifier in closure:
        if assess_ratifier(root, node_set, edge_tuple, ratifier) != INTERNAL_REJECTION:
            raise BootstrapNonSelfRatificationV1Error("V116_THEOREM_REPLAY_FAILURE")
    return "ESTABLISHED_FOR_ROOT_RELATIVE_DESCENDANT_CLOSURE"


def _current_jurisdiction_graph() -> tuple[frozenset[str], tuple[tuple[str, str], ...]]:
    # Minimal relation independently replayable from the pinned root chain.
    # It is not a claim that these are all lineage-bearing objects.
    nodes = frozenset((BOOTSTRAP_COMMIT, ROOT_V1_ID, ROOT_V2_ID))
    edges = (
        (BOOTSTRAP_COMMIT, ROOT_V1_ID),
        (ROOT_V1_ID, ROOT_V2_ID),
    )
    return nodes, edges


def audit_current_non_self_ratification() -> BootstrapNonSelfRatificationReport:
    verify_profile(_load_exact(PROFILE_PATH, PROFILE_BLOB, PROFILE_ID))
    root_v1 = _load_exact(ROOT_V1_PATH, ROOT_V1_BLOB, ROOT_V1_ID)
    root_v2 = _load_exact(ROOT_V2_PATH, ROOT_V2_BLOB, ROOT_V2_ID)
    v115_audit = _load_exact(V115_AUDIT_PATH, V115_AUDIT_BLOB, V115_AUDIT_ID)

    if root_v1.get("registry_id") != ROOT_V1_ID:
        raise BootstrapNonSelfRatificationV1Error("V116_ROOT_V1_ID_REBINDING")
    if root_v1.get("bootstrap_root_commit") != BOOTSTRAP_COMMIT:
        raise BootstrapNonSelfRatificationV1Error("V116_BOOTSTRAP_ROOT_REBINDING")
    if root_v2.get("registry_id") != ROOT_V2_ID:
        raise BootstrapNonSelfRatificationV1Error("V116_ROOT_V2_ID_REBINDING")
    if root_v2.get("predecessor_registry_id") != ROOT_V1_ID:
        raise BootstrapNonSelfRatificationV1Error("V116_ROOT_V2_PREDECESSOR_REBINDING")
    if root_v2.get("predecessor_registry_git_blob_sha1") != ROOT_V1_BLOB:
        raise BootstrapNonSelfRatificationV1Error("V116_ROOT_V2_PREDECESSOR_HASH_REBINDING")

    prior = v115.verify_declared_audit(v115_audit)
    if v115_audit.get("audit_content_hash") != V115_AUDIT_HASH:
        raise BootstrapNonSelfRatificationV1Error("V116_V115_AUDIT_HASH_REBINDING")
    if prior.bootstrap_authority_legitimacy != "NOT_ESTABLISHED":
        raise BootstrapNonSelfRatificationV1Error("V116_V115_LEGITIMACY_PROMOTION")
    if prior.current_internal_verification_path_to_bootstrap_legitimacy != "ABSENT":
        raise BootstrapNonSelfRatificationV1Error("V116_V115_INTERNAL_PATH_PROMOTION")
    if prior.external_bootstrap_ratification != "NOT_PERFORMED":
        raise BootstrapNonSelfRatificationV1Error("V116_EXTERNAL_RATIFICATION_REBINDING")

    nodes, edges = _current_jurisdiction_graph()
    closure = descendant_closure(BOOTSTRAP_COMMIT, nodes, edges)
    theorem = verify_non_self_ratification_theorem(BOOTSTRAP_COMMIT, nodes, edges)
    if closure != nodes:
        raise BootstrapNonSelfRatificationV1Error("V116_CURRENT_MODEL_CLOSURE_REBINDING")
    for internal in closure:
        if assess_ratifier(
            BOOTSTRAP_COMMIT, nodes, edges, internal, claimed_external=True
        ) != INTERNAL_REJECTION:
            raise BootstrapNonSelfRatificationV1Error("V116_EXTERNALITY_LAUNDERING_ACCEPTED")

    if inspect.signature(audit_current_non_self_ratification).parameters:
        raise BootstrapNonSelfRatificationV1Error("V116_PRODUCTION_CALLER_SURFACE")

    return BootstrapNonSelfRatificationReport(
        source_v115_boundary_identity="CONFIRMED_PINNED_GIT_BLOB_AND_CONTENT_HASH",
        jurisdiction_root_identity="CONFIRMED_EXACT_BOOTSTRAP_DESIGNATION",
        root_v1_identity="CONFIRMED_PINNED_GIT_BLOB",
        root_v2_identity="CONFIRMED_PINNED_GIT_BLOB",
        root_v2_predecessor_relation="CONFIRMED_EXACT_PREDECESSOR_BINDING",
        internal_closure_definition="REFLEXIVE_TRANSITIVE_DESCENDANT_CLOSURE_OF_BOOTSTRAP_ROOT",
        internal_closure_derivation="MACHINE_DERIVED_IN_PINNED_ROOT_RELATIVE_MODEL",
        internal_closure_node_count_current_model=len(closure),
        non_self_ratification_theorem=theorem,
        bootstrap_self_ratification="REJECTED_BY_INDEPENDENCE_RULE",
        descendant_ratifier_promotion="REJECTED",
        authority_cycle_ratification="REJECTED_FAIL_CLOSED_BY_DAG_CHECK",
        externality_laundering="REJECTED_PROVENANCE_OVERRIDES_LABEL",
        caller_ratifier_input_surface="FORBIDDEN_NO_CALLER_INPUT_SURFACE",
        outside_closure_semantics=STRUCTURAL_ONLY,
        external_ratifier_structural_independence="NOT_ESTABLISHED_NO_EXTERNAL_RATIFICATION_OBJECT",
        external_ratifier_authority_admissibility="NOT_ESTABLISHED",
        external_bootstrap_ratification="NOT_PERFORMED",
        internal_authority_closure_vs_bootstrap_legitimacy="DISTINCT_CONFIRMED_IN_TESTED_ROOT_RELATIVE_MODEL",
        bootstrap_authority_legitimacy="NOT_ESTABLISHED",
        current_internal_verification_path_to_bootstrap_legitimacy="ABSENT",
        normative_authority_origin_internal_proof="NOT_ESTABLISHED_BY_INTERNAL_VERIFICATION",
        global_non_self_ratification_theorem_for_all_verification_systems="NOT_CLAIMED",
        normative_lineage_completeness=BLOCKED_COMPLETENESS,
        derived_semantic_authority="BLOCKED",
        solver_invocation_count=0,
        next_required_basis="EXTERNALLY_ANCHORED_NON_DESCENDANT_RATIFICATION_WITH_SEPARATE_AUTHORITY_ADMISSIBILITY",
        status="BOOTSTRAP_NON_SELF_RATIFICATION_BOUNDARY_CONFIRMED_IN_CURRENT_TESTED_SCOPE",
    )


def verify_declared_audit(audit: Mapping[str, Any]) -> BootstrapNonSelfRatificationReport:
    expected = {
        "schema": "AIFC/bootstrap-non-self-ratification-audit/v1",
        "audit_id": "AIFC-SAL-V1.16-BOOTSTRAP-NON-SELF-RATIFICATION-AUDIT-V1",
        "source_main_commit": SOURCE_MAIN_COMMIT,
        "source_tree_sha": SOURCE_TREE_SHA,
        "profile_id": PROFILE_ID,
        "profile_content_hash": PROFILE_HASH,
        "source_v115_audit_id": V115_AUDIT_ID,
        "source_v115_audit_git_blob_sha1": V115_AUDIT_BLOB,
        "source_v115_audit_content_hash": V115_AUDIT_HASH,
    }
    for key, value in expected.items():
        if audit.get(key) != value:
            raise BootstrapNonSelfRatificationV1Error("V116_AUDIT_REBINDING:" + key)
    if audit.get("audit_content_hash") != audit_content_hash(audit):
        raise BootstrapNonSelfRatificationV1Error("V116_AUDIT_CONTENT_REBINDING")
    report = audit_current_non_self_ratification()
    for key, value in report.__dict__.items():
        if audit.get(key) != value:
            raise BootstrapNonSelfRatificationV1Error("V116_AUDIT_REPORT_REBINDING:" + key)
    return report
