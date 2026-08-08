#!/usr/bin/env python3
"""SAL v1.10 Endpoint Semantic Identity Closure.

Correct bridge execution does not establish correct endpoint meaning. This
successor verifies endpoint identities against the exact content-bound P/T
formula bindings, isolates bridge-derived atoms, and keeps both semantic
authority promotion and capacity extension fail-closed pending later lineage.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

from canonical import domain_hash
from scientific_assurance_lineage_v14 import git_blob_sha1_bytes
import scientific_assurance_lineage_v17 as v17
import scientific_assurance_lineage_v18 as v18
import scientific_assurance_lineage_v19 as v19
import semantic_bridge_endpoint_identity_v1 as endpoint_exec

ROOT = Path(__file__).resolve().parents[2]
ENDPOINT_PROFILE_PATH = "conformance/AIFC-SEMANTIC-BRIDGE-ENDPOINT-IDENTITY-PROFILE-v1.json"
ENDPOINT_PROFILE_ID = "AIFC-SAL-V1.10-SEMANTIC-BRIDGE-ENDPOINT-IDENTITY-PROFILE-V1"
ENDPOINT_PROFILE_HASH = "a86c5695e207b1471507d819899b9536d728cf913ba86adab30516c7be3ea68e"
ENDPOINT_IMPL_PATH = "reference/verifier/semantic_bridge_endpoint_identity_v1.py"
ENDPOINT_IMPL_BLOB = "2afc918646fad98445efb6eff5ea11c8a20dee97"
ENDPOINT_IMPL_RAW_SHA256 = "42c2a968645b433698c9ba4c9f7348e535be580fce6cf25b33320f1026a59a67"
BRIDGE_THEORY_V2_PATH = "conformance/AIFC-SEMANTIC-BRIDGE-THEORY-v2.json"
BRIDGE_THEORY_V2_BLOB = "be5df0af0e69a29d103b61ff86e2ab97d24e957c"
BRIDGE_THEORY_V3_PATH = "conformance/AIFC-SEMANTIC-BRIDGE-THEORY-v3.json"
BRIDGE_THEORY_V3_ID = "AIFC-SAL-V1.10-CROSS-FORMULA-SEMANTIC-BRIDGE-V3"
BRIDGE_THEORY_V3_HASH = "ca6b137997f2a9de62906bd528e705e6d102a83ba7cff42e9d7d2b2b47ebcddb"
EXECUTION_PROFILE_V2_PATH = "conformance/AIFC-SEMANTIC-BRIDGE-EXECUTION-PROFILE-v2.json"
EXECUTION_PROFILE_V2_ID = "AIFC-SAL-V1.10-SEMANTIC-BRIDGE-EXECUTION-PROFILE-V2"
EXECUTION_PROFILE_V2_HASH = "006c548d433f7c36c4b290e08bd9300bcc7ba928f728f18e3b0382bfcd2b1422"
CAPACITY_EXTENSION_PATH = "conformance/AIFC-ENTAILMENT-METHOD-CAPACITY-EXTENSION-v1.json"
CAPACITY_EXTENSION_ID = "AIFC-SAL-V1.10-ENTAILMENT-METHOD-CAPACITY-EXTENSION-V1"
CAPACITY_EXTENSION_HASH = "4ddb637850bcc82584b66fbadb7058774644b389c923a6feb0d707c6c2f45fed"
AUDIT_PATH = "conformance/AIFC-SEMANTIC-ENDPOINT-IDENTITY-AUDIT-v1.json"
AUDIT_ID = "AIFC-SAL-V1.10-SEMANTIC-ENDPOINT-IDENTITY-AUDIT-V1"
AUDIT_HASH = "f71a7bbf4b35d0797a136b57a9211af13e1d58ad780f3d238a00a5bcdbd6d438"


class ScientificAssuranceLineageV110Error(ValueError):
    pass


@dataclass(frozen=True)
class SemanticEndpointIdentityReport:
    question_id: str
    bridge_endpoint_semantic_identity: str
    bridge_atom_role_identity_binding: str
    bridge_derived_atom_provenance: str
    semantic_authority_status_lineage: str
    entailment_method_conservative_capacity_extension: str
    same_question_method_semantics_preservation: str
    bridge_aware_extended_capacity: str
    current_bridge_axiom_count: int
    current_bridge_aware_atom_count: int
    bridge_execution_blockers: tuple[str, ...]
    solver_invocation_count: int
    result: str
    blocked_subtype: str | None
    normative_countermodel: Mapping[str, bool] | None


def _obj(path: str, schema: str, id_field: str, expected_id: str, hash_field: str,
         domain: str, expected_hash: str) -> Mapping[str, Any]:
    obj = v17._strict(path, schema)
    material = dict(obj)
    claimed = material.pop(hash_field, None)
    if obj.get(id_field) != expected_id:
        raise ScientificAssuranceLineageV110Error(f"SAL_V110_ID_REBINDING:{path}")
    if claimed != expected_hash or domain_hash(domain, material) != expected_hash:
        raise ScientificAssuranceLineageV110Error(f"SAL_V110_CONTENT_IDENTITY_REBINDING:{path}")
    return obj


def _verify_endpoint_profile() -> Mapping[str, Any]:
    profile = _obj(
        ENDPOINT_PROFILE_PATH,
        "AIFC/semantic-bridge-endpoint-identity-profile/v1",
        "profile_id",
        ENDPOINT_PROFILE_ID,
        "profile_content_hash",
        "AIFC:SEMANTIC-BRIDGE-ENDPOINT-IDENTITY-PROFILE:v1",
        ENDPOINT_PROFILE_HASH,
    )
    exact = {
        "entailment_question_id": v17.QUESTION_ID,
        "predecessor_formula_source_path": v17.PREDECESSOR_FORMULA_PATH,
        "predecessor_formula_git_blob_sha1": "81d70057c41dd8e5e7fe14d155a661dda5c901ff",
        "predecessor_formula_content_hash": v17.PREDECESSOR_FORMULA_HASH,
        "target_formula_source_path": v17.TARGET_FORMULA_PATH,
        "target_formula_git_blob_sha1": "9f2f25aade7d899f3a6dc6c28bb544ab759105aa",
        "target_formula_content_hash": v17.TARGET_FORMULA_HASH,
        "bridge_axiom_schema_id": "AIFC/semantic-bridge-axiom/v2",
        "derived_semantic_object_schema_id": "AIFC/bridge-derived-semantic-object/v1",
        "implementation_path": ENDPOINT_IMPL_PATH,
        "implementation_git_blob_sha1": ENDPOINT_IMPL_BLOB,
        "implementation_raw_sha256": ENDPOINT_IMPL_RAW_SHA256,
    }
    for key, value in exact.items():
        if profile.get(key) != value:
            raise ScientificAssuranceLineageV110Error(f"BRIDGE_ENDPOINT_PROFILE_REBINDING:{key}")
    for path, blob, label in (
        (v17.PREDECESSOR_FORMULA_PATH, exact["predecessor_formula_git_blob_sha1"], "PREDECESSOR"),
        (v17.TARGET_FORMULA_PATH, exact["target_formula_git_blob_sha1"], "TARGET"),
    ):
        if git_blob_sha1_bytes((ROOT / path).read_bytes()) != blob:
            raise ScientificAssuranceLineageV110Error(f"BRIDGE_{label}_FORMULA_GIT_IDENTITY_REBINDING")
    raw = (ROOT / ENDPOINT_IMPL_PATH).read_bytes()
    if git_blob_sha1_bytes(raw) != ENDPOINT_IMPL_BLOB or hashlib.sha256(raw).hexdigest() != ENDPOINT_IMPL_RAW_SHA256:
        raise ScientificAssuranceLineageV110Error("BRIDGE_ENDPOINT_IMPLEMENTATION_IDENTITY_REBINDING")
    return profile


def _verify_bridge_theory_v3(endpoint_profile: Mapping[str, Any]) -> Mapping[str, Any]:
    if git_blob_sha1_bytes((ROOT / BRIDGE_THEORY_V2_PATH).read_bytes()) != BRIDGE_THEORY_V2_BLOB:
        raise ScientificAssuranceLineageV110Error("BRIDGE_THEORY_V2_LINEAGE_REBINDING")
    theory = _obj(
        BRIDGE_THEORY_V3_PATH,
        "AIFC/semantic-bridge-theory/v3",
        "bridge_theory_id",
        BRIDGE_THEORY_V3_ID,
        "theory_content_hash",
        "AIFC:SEMANTIC-BRIDGE-THEORY:v3",
        BRIDGE_THEORY_V3_HASH,
    )
    exact = {
        "predecessor_bridge_theory_id": v19.BRIDGE_THEORY_V2_ID,
        "predecessor_bridge_theory_git_blob_sha1": BRIDGE_THEORY_V2_BLOB,
        "entailment_question_id": v17.QUESTION_ID,
        "predecessor_formula_content_hash": v17.PREDECESSOR_FORMULA_HASH,
        "target_formula_content_hash": v17.TARGET_FORMULA_HASH,
        "logical_fragment": "FINITE_CLASSICAL_PROPOSITIONAL_V1",
        "endpoint_identity_profile_id": endpoint_profile["profile_id"],
        "endpoint_identity_profile_content_hash": endpoint_profile["profile_content_hash"],
        "bridge_axiom_schema_id": "AIFC/semantic-bridge-axiom/v2",
    }
    for key, value in exact.items():
        if theory.get(key) != value:
            raise ScientificAssuranceLineageV110Error(f"BRIDGE_THEORY_V3_REBINDING:{key}")
    return theory


def _verify_execution_profile_v2(theory: Mapping[str, Any], endpoint_profile: Mapping[str, Any],
                                 method: Mapping[str, Any]) -> Mapping[str, Any]:
    profile = _obj(
        EXECUTION_PROFILE_V2_PATH,
        "AIFC/semantic-bridge-execution-profile/v2",
        "execution_profile_id",
        EXECUTION_PROFILE_V2_ID,
        "profile_content_hash",
        "AIFC:SEMANTIC-BRIDGE-EXECUTION-PROFILE:v2",
        EXECUTION_PROFILE_V2_HASH,
    )
    exact = {
        "predecessor_execution_profile_id": v19.EXECUTION_PROFILE_ID,
        "predecessor_execution_profile_git_blob_sha1": "7e736cd6fd50f1bd4578478762a646914a8c5ba6",
        "entailment_question_id": v17.QUESTION_ID,
        "semantic_bridge_theory_id": theory["bridge_theory_id"],
        "semantic_bridge_theory_content_hash": theory["theory_content_hash"],
        "endpoint_identity_profile_id": endpoint_profile["profile_id"],
        "endpoint_identity_profile_content_hash": endpoint_profile["profile_content_hash"],
        "entailment_method_profile_id": method["method_profile_id"],
        "entailment_method_profile_content_hash": method["method_content_hash"],
        "composition_rule": "PREMISE_AND_ORDERED_ENDPOINT_CLOSED_BRIDGE_AXIOMS_V1",
        "bridge_axiom_schema_id": "AIFC/semantic-bridge-axiom/v2",
        "formula_ast_schema_id": "AIFC/semantic-formula/v1",
        "execution_implementation_path": ENDPOINT_IMPL_PATH,
        "execution_implementation_git_blob_sha1": ENDPOINT_IMPL_BLOB,
        "execution_implementation_raw_sha256": ENDPOINT_IMPL_RAW_SHA256,
    }
    for key, value in exact.items():
        if profile.get(key) != value:
            raise ScientificAssuranceLineageV110Error(f"BRIDGE_EXECUTION_PROFILE_V2_REBINDING:{key}")
    return profile


def _verify_capacity_extension(method: Mapping[str, Any]) -> Mapping[str, Any]:
    extension = _obj(
        CAPACITY_EXTENSION_PATH,
        "AIFC/entailment-method-capacity-extension/v1",
        "extension_id",
        CAPACITY_EXTENSION_ID,
        "extension_content_hash",
        "AIFC:ENTAILMENT-METHOD-CAPACITY-EXTENSION:v1",
        CAPACITY_EXTENSION_HASH,
    )
    exact = {
        "entailment_question_id": v17.QUESTION_ID,
        "base_method_profile_id": method["method_profile_id"],
        "base_method_profile_content_hash": method["method_content_hash"],
        "logical_method_label": v17.ENTAILMENT_METHOD,
        "base_max_atoms": 16,
    }
    for key, value in exact.items():
        if extension.get(key) != value:
            raise ScientificAssuranceLineageV110Error(f"CAPACITY_EXTENSION_REBINDING:{key}")
    return extension


def _capacity_extension_is_admissible(extension: Mapping[str, Any], *, bridge_aware_atom_count: int) -> bool:
    extended = extension.get("extended_max_atoms")
    return all((
        extension.get("old_domain_result_equivalence_status") == "ESTABLISHED_BY_REPLAY",
        extension.get("same_question_method_semantics_preservation_status") == "ESTABLISHED",
        extension.get("bridge_aware_extended_capacity_status") == "CAPACITY_AVAILABLE_FOR_RESOLVED_THEOREM",
        extension.get("extension_authority_status") == "AUTHORITY_ADMISSIBLE",
        extension.get("authority_lineage_status") == "AUTHORITY_LINEAGE_ESTABLISHED",
        extension.get("resolved_bridge_aware_atom_count") == bridge_aware_atom_count,
        isinstance(extended, int),
        isinstance(extended, int) and extended >= bridge_aware_atom_count,
        isinstance(extended, int) and extended >= 16,
    ))


def _effective_max_atoms(method: Mapping[str, Any], extension: Mapping[str, Any], *,
                         bridge_aware_atom_count: int) -> int:
    base = method.get("formal_semantics", {}).get("max_atoms")
    if base != 16:
        raise ScientificAssuranceLineageV110Error("BASE_METHOD_CAPACITY_REBINDING")
    if _capacity_extension_is_admissible(extension, bridge_aware_atom_count=bridge_aware_atom_count):
        return int(extension["extended_max_atoms"])
    return 16


def _semantic_authority_lineage_blocker() -> str:
    return "BLOCKED_SEMANTIC_AUTHORITY_STATUS_LINEAGE"


def _closure_blockers(ps: Mapping[str, Any], ts: Mapping[str, Any], theory: Mapping[str, Any],
                      axioms: Sequence[Mapping[str, Any]], execution: Mapping[str, Any],
                      endpoint: Mapping[str, Any], method: Mapping[str, Any],
                      extension: Mapping[str, Any], count: int,
                      binding: Mapping[str, Any]) -> tuple[str, ...]:
    blockers: list[str] = []
    if not all(
        item.get("selection_authority_status") == "PREDECESSOR_AUTHORITY_ADMITTED_SURFACE"
        and item.get("completeness_claim") == "AUTHORITY_ESTABLISHED_COMPLETE_FOR_QUESTION"
        for item in (ps, ts)
    ):
        blockers.append("BLOCKED_NORMATIVE_SEMANTIC_SURFACE_AUTHORITY")
    if theory.get("abstraction_adequacy_status") != "AUTHORITY_ESTABLISHED":
        blockers.append("BLOCKED_SEMANTIC_ABSTRACTION_ADEQUACY")
    if theory.get("bridge_status") != "AUTHORITY_ADMISSIBLE_BRIDGE_THEORY":
        blockers.append("BLOCKED_CROSS_FORMULA_SEMANTIC_BRIDGE_ABSENT")
    if theory.get("bridge_authority_status") != "AUTHORITY_ADMISSIBLE":
        blockers.append("BLOCKED_CROSS_FORMULA_SEMANTIC_BRIDGE_AUTHORITY")
    if any(axiom.get("axiom_authority_status") != "AUTHORITY_ADMISSIBLE" for axiom in axioms):
        blockers.append("BLOCKED_BRIDGE_AXIOM_AUTHORITY")
    if execution.get("execution_authority_status") != "AUTHORITY_ADMISSIBLE":
        blockers.append("BLOCKED_SEMANTIC_BRIDGE_EXECUTION_BINDING")
    if endpoint.get("profile_authority_status") != "AUTHORITY_ADMISSIBLE":
        blockers.append("BLOCKED_BRIDGE_ENDPOINT_SEMANTIC_IDENTITY_AUTHORITY")
    if method.get("method_authority_status") != "AUTHORITY_ADMISSIBLE":
        blockers.append("BLOCKED_ENTAILMENT_METHOD_AUTHORITY")
    if not _capacity_extension_is_admissible(extension, bridge_aware_atom_count=count):
        blockers.append("BLOCKED_ENTAILMENT_METHOD_CONSERVATIVE_CAPACITY_EXTENSION")
    if binding.get("binding_status") != "DUAL_IDENTITY_ESTABLISHED":
        blockers.append("BLOCKED_ENTAILMENT_QUESTION_SOURCE_DUAL_IDENTITY")
    blockers.append(_semantic_authority_lineage_blocker())
    return tuple(blockers)


def _resolve_derived(ref: Mapping[str, Any]) -> Mapping[str, Any]:
    path = ref.get("source_path")
    if not isinstance(path, str) or not path.startswith("conformance/"):
        raise ScientificAssuranceLineageV110Error("BRIDGE_DERIVED_OBJECT_PATH_INVALID")
    raw = (ROOT / path).read_bytes()
    if git_blob_sha1_bytes(raw) != ref.get("git_blob_sha1") or hashlib.sha256(raw).hexdigest() != ref.get("raw_sha256"):
        raise ScientificAssuranceLineageV110Error("BRIDGE_DERIVED_OBJECT_BYTE_IDENTITY_REBINDING")
    return v17._strict(path, "AIFC/bridge-derived-semantic-object/v1")


def _verify_axiom_reference_binding(ref: Mapping[str, Any], axiom: Mapping[str, Any]) -> None:
    if ref.get("axiom_schema_id") != "AIFC/semantic-bridge-axiom/v2":
        raise ScientificAssuranceLineageV110Error("BRIDGE_THEORY_AXIOM_SCHEMA_REFERENCE_REBINDING")
    if axiom.get("schema") != ref.get("axiom_schema_id"):
        raise ScientificAssuranceLineageV110Error("BRIDGE_THEORY_AXIOM_SCHEMA_REFERENCE_REBINDING")
    if axiom.get("axiom_id") != ref.get("axiom_id"):
        raise ScientificAssuranceLineageV110Error("BRIDGE_THEORY_AXIOM_REFERENCE_REBINDING:ID")
    if axiom.get("axiom_content_hash") != ref.get("axiom_content_hash"):
        raise ScientificAssuranceLineageV110Error("BRIDGE_THEORY_AXIOM_REFERENCE_REBINDING:CONTENT_HASH")


def _resolve_axioms(theory: Mapping[str, Any], predecessor_bindings: Mapping[str, str],
                    target_bindings: Mapping[str, str]) -> tuple[Mapping[str, Any], ...]:
    refs = theory.get("bridge_axiom_refs", [])
    if not isinstance(refs, list):
        raise ScientificAssuranceLineageV110Error("BRIDGE_AXIOM_REFS_INVALID")
    out: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    for ref in refs:
        if not isinstance(ref, Mapping):
            raise ScientificAssuranceLineageV110Error("BRIDGE_AXIOM_REF_INVALID")
        ref_id = ref.get("axiom_id")
        path = ref.get("source_path")
        if not isinstance(ref_id, str) or not ref_id or ref_id in seen:
            raise ScientificAssuranceLineageV110Error("BRIDGE_AXIOM_ID_INVALID_OR_DUPLICATE")
        if not isinstance(path, str) or not path.startswith("conformance/"):
            raise ScientificAssuranceLineageV110Error("BRIDGE_AXIOM_V2_PATH_INVALID")
        seen.add(ref_id)
        raw = (ROOT / path).read_bytes()
        if git_blob_sha1_bytes(raw) != ref.get("git_blob_sha1") or hashlib.sha256(raw).hexdigest() != ref.get("raw_sha256"):
            raise ScientificAssuranceLineageV110Error("BRIDGE_AXIOM_V2_BYTE_IDENTITY_REBINDING")
        axiom = v17._strict(path, "AIFC/semantic-bridge-axiom/v2")
        _verify_axiom_reference_binding(ref, axiom)
        endpoint_exec.verify_bridge_axiom_endpoint_identity(
            axiom,
            expected_question_id=v17.QUESTION_ID,
            predecessor_bindings=predecessor_bindings,
            target_bindings=target_bindings,
            derived_object_resolver=_resolve_derived,
            require_authority=False,
        )
        out.append(axiom)
    return tuple(out)


def audit_semantic_endpoint_identity_closure(predecessor_identity: str, target_profile_identity: str,
                                             entailment_question_identity: str) -> SemanticEndpointIdentityReport:
    if (predecessor_identity, target_profile_identity, entailment_question_identity) != (
        v17.PREDECESSOR_ID, v17.TARGET_PROFILE_ID, v17.QUESTION_ID
    ):
        raise ScientificAssuranceLineageV110Error("ENTAILMENT_QUESTION_IDENTITY_SUBSTITUTION")

    inherited = v19.audit_semantic_bridge_execution_closure(
        predecessor_identity, target_profile_identity, entailment_question_identity
    )
    question = v17._verify_question()
    method = v18._verify_entailment_method_profile(question, 18)
    predecessor_formula = v17._strict(v17.PREDECESSOR_FORMULA_PATH, "AIFC/semantic-formula/v1")
    target_formula = v17._strict(v17.TARGET_FORMULA_PATH, "AIFC/semantic-formula/v1")
    predecessor_ast = predecessor_formula["normalized_formula_ast"]
    target_ast = target_formula["normalized_formula_ast"]
    predecessor_bindings = predecessor_formula["atom_bindings"]
    target_bindings = target_formula["atom_bindings"]

    endpoint_profile = _verify_endpoint_profile()
    theory = _verify_bridge_theory_v3(endpoint_profile)
    execution_profile = _verify_execution_profile_v2(theory, endpoint_profile, method)
    axioms = _resolve_axioms(theory, predecessor_bindings, target_bindings)
    count = endpoint_exec.bridge_aware_atom_count_v2(
        predecessor_ast,
        axioms,
        target_ast,
        expected_question_id=v17.QUESTION_ID,
        predecessor_bindings=predecessor_bindings,
        target_bindings=target_bindings,
        derived_object_resolver=_resolve_derived,
    )
    extension = _verify_capacity_extension(method)
    binding, _, _ = v19._verify_question_source_binding_v2(question)
    predecessor_surface = v18._verify_surface_definition(v18.PREDECESSOR_SURFACE_DEFINITION_PATH, role="PREDECESSOR")
    target_surface = v18._verify_surface_definition(v18.TARGET_SURFACE_DEFINITION_PATH, role="TARGET")
    blockers = _closure_blockers(
        predecessor_surface, target_surface, theory, axioms, execution_profile,
        endpoint_profile, method, extension, count, binding,
    )
    blocker = inherited.blocked_subtype or (blockers[0] if blockers else None)
    solver_invocations = 0
    countermodel = None
    result = "BLOCKED"
    if blocker is None:
        solver_invocations = 1
        solver, _composition = endpoint_exec.bridge_bound_entailment_v2(
            predecessor_ast,
            axioms,
            target_ast,
            expected_question_id=v17.QUESTION_ID,
            predecessor_bindings=predecessor_bindings,
            target_bindings=target_bindings,
            derived_object_resolver=_resolve_derived,
            max_atoms=_effective_max_atoms(method, extension, bridge_aware_atom_count=count),
        )
        result = solver.state
        countermodel = solver.countermodel

    endpoint_status = "PASS_ENFORCEMENT_IMPLEMENTED_CURRENT_BRIDGE_EMPTY"
    role_status = "PASS_STRICT_ROLE_LOOKUP_IMPLEMENTED_CURRENT_BRIDGE_EMPTY"
    derived_status = "PASS_REQUIRED_BY_V2_LANGUAGE_CURRENT_BRIDGE_EMPTY"
    authority = "NOT_ESTABLISHED_SELF_ASSERTION_BLOCKED"
    capacity_extension = "NOT_ESTABLISHED_CANDIDATE_OBJECT_ONLY"
    same_question = "NOT_ESTABLISHED"
    max_atoms = _effective_max_atoms(method, extension, bridge_aware_atom_count=count)
    extended_capacity = (
        "CAPACITY_AVAILABLE"
        if _capacity_extension_is_admissible(extension, bridge_aware_atom_count=count) and count <= max_atoms
        else f"BLOCKED_NO_AUTHORIZED_EXTENSION_{count}_GT_{max_atoms}"
    )

    audit = _obj(
        AUDIT_PATH,
        "AIFC/semantic-endpoint-identity-audit/v1",
        "audit_id",
        AUDIT_ID,
        "audit_content_hash",
        "AIFC:SEMANTIC-ENDPOINT-IDENTITY-AUDIT:v1",
        AUDIT_HASH,
    )
    expected = {
        "entailment_question_id": v17.QUESTION_ID,
        "bridge_theory_id": BRIDGE_THEORY_V3_ID,
        "endpoint_identity_profile_id": ENDPOINT_PROFILE_ID,
        "capacity_extension_id": CAPACITY_EXTENSION_ID,
        "current_bridge_axiom_count": len(axioms),
        "current_bridge_aware_atom_count": count,
        "bridge_endpoint_semantic_identity": endpoint_status,
        "bridge_atom_role_identity_binding": role_status,
        "bridge_derived_atom_provenance": derived_status,
        "semantic_authority_status_lineage": authority,
        "entailment_method_conservative_capacity_extension": capacity_extension,
        "same_question_method_semantics_preservation": same_question,
        "bridge_aware_extended_capacity": extended_capacity,
        "solver_invocation_count": solver_invocations,
        "result": result,
        "blocked_subtype": blocker,
        "normative_countermodel": countermodel,
    }
    for key, value in expected.items():
        if audit.get(key) != value:
            raise ScientificAssuranceLineageV110Error(f"SAL_V110_AUDIT_RESULT_REBINDING:{key}")

    return SemanticEndpointIdentityReport(
        v17.QUESTION_ID,
        endpoint_status,
        role_status,
        derived_status,
        authority,
        capacity_extension,
        same_question,
        extended_capacity,
        len(axioms),
        count,
        blockers,
        solver_invocations,
        result,
        blocker,
        countermodel,
    )
