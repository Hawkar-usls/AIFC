#!/usr/bin/env python3
"""SAL v1.8 Semantic Abstraction Closure.

This layer preserves the issued v1 entailment question and the v1.7 theorem
construction, but refuses to let a proof about a propositional abstraction acquire
normative force until the abstraction relation itself is authority-admissible.

Production input remains identity-only. No caller-supplied formulas, semantic
surface, bridge theory, entailment method implementation, or compiler are accepted.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from canonical import domain_hash
from scientific_assurance_lineage_v14 import git_blob_sha1_bytes
from scientific_assurance_lineage_v16 import finite_propositional_entailment
import scientific_assurance_lineage_v17 as v17
from semantic_compiler_v1 import (
    SemanticCompilerV1Error,
    compile_predecessor_formula,
    compile_target_formula,
    verify_exact_coverage,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

PREDECESSOR_SURFACE_DEFINITION_PATH = "conformance/AIFC-PREDECESSOR-SEMANTIC-SURFACE-DEFINITION-v1.json"
TARGET_SURFACE_DEFINITION_PATH = "conformance/AIFC-TARGET-SEMANTIC-SURFACE-DEFINITION-v1.json"
BRIDGE_THEORY_PATH = "conformance/AIFC-SEMANTIC-BRIDGE-THEORY-v1.json"
METHOD_PROFILE_PATH = "conformance/AIFC-ENTAILMENT-METHOD-PROFILE-v1.json"
QUESTION_SOURCE_BINDING_PATH = "conformance/AIFC-ENTAILMENT-QUESTION-SOURCE-BINDING-v1.json"
AUDIT_PATH = "conformance/AIFC-SEMANTIC-ABSTRACTION-CLOSURE-AUDIT-v1.json"

PREDECESSOR_SURFACE_DEFINITION_ID = "AIFC-SAL-V1.8-PREDECESSOR-REQUIRED-SEMANTIC-SURFACE-V1"
TARGET_SURFACE_DEFINITION_ID = "AIFC-SAL-V1.8-TARGET-REQUIRED-SEMANTIC-SURFACE-V1"
BRIDGE_THEORY_ID = "AIFC-SAL-V1.8-CROSS-FORMULA-SEMANTIC-BRIDGE-V1"
METHOD_PROFILE_ID = "AIFC-SAL-V1.8-ENTAILMENT-METHOD-PROFILE-V1"
QUESTION_SOURCE_BINDING_ID = "AIFC-SAL-V1.8-ENTAILMENT-QUESTION-SOURCE-BINDING-V1"

PREDECESSOR_SURFACE_DEFINITION_HASH = "1ca06e84d436f36d946dcdedadc6c4db54b906ebe47e20fabf04d974820193af"
TARGET_SURFACE_DEFINITION_HASH = "70f14f3040a9b4c98a1c018728cd35d0235517e61255731d0e8cf34c780cb099"
BRIDGE_THEORY_HASH = "30a5dbe7f8e0d62c8d9a8fa5bcbfa649847ae0394ba7a3c9889d44fb06ab56d6"
METHOD_PROFILE_HASH = "fb6055c0bc2f9a6e6b0daef8269200d0f914e8428d4d2fd8e13e06e15acd7255"
QUESTION_SOURCE_BINDING_HASH = "817e77196258b82f0b49a0886f603dd4622b5b994e0c2857ecf5d8c2056e9d2b"

METHOD_SOLVER_PATH = "reference/verifier/scientific_assurance_lineage_v16.py"
METHOD_SOLVER_GIT_BLOB_SHA1 = "5d6534c51418b776c6e456dc14416a0804d7bb09"


class ScientificAssuranceLineageV18Error(ValueError):
    pass


@dataclass(frozen=True)
class SemanticAbstractionReport:
    question_id: str
    normative_semantic_surface_authority: str
    semantic_abstraction_adequacy: str
    cross_formula_semantic_bridge_identity: str
    cross_formula_semantic_bridge_authority: str
    cross_formula_semantic_bridge: str
    disjoint_semantic_vocabulary: str
    disjoint_vocabulary_trivial_refutation: str
    entailment_method_content_identity: str
    entailment_method_authority: str
    entailment_method_capacity_for_issued_question: str
    entailment_question_source_dual_identity: str
    abstraction_closure_blockers: tuple[str, ...]
    solver_invocation_count: int
    result: str
    blocked_subtype: str | None
    normative_countermodel: Mapping[str, bool] | None


def _content_hash(
    path: str,
    schema: str,
    *,
    id_field: str,
    expected_id: str,
    hash_field: str,
    domain: str,
    expected_hash: str,
) -> Mapping[str, Any]:
    obj = v17._strict(path, schema)
    if obj.get(id_field) != expected_id or obj.get("entailment_question_id") != v17.QUESTION_ID:
        raise ScientificAssuranceLineageV18Error(f"SAL_V18_OBJECT_IDENTITY_REBINDING:{expected_id}")
    material = dict(obj)
    claimed = material.pop(hash_field, None)
    actual = domain_hash(domain, material)
    if claimed != expected_hash or actual != expected_hash:
        raise ScientificAssuranceLineageV18Error(f"SAL_V18_CONTENT_IDENTITY_REBINDING:{expected_id}")
    return obj


def _verify_surface_definition(path: str, *, role: str) -> Mapping[str, Any]:
    if role == "PREDECESSOR":
        expected_id = PREDECESSOR_SURFACE_DEFINITION_ID
        expected_hash = PREDECESSOR_SURFACE_DEFINITION_HASH
        source_id = v17.PREDECESSOR_ID
        source_blob = v17.PREDECESSOR_BLOB
        coverage_id = "AIFC-SAL-V1.7-PREDECESSOR-SEMANTIC-COVERAGE-V1"
    elif role == "TARGET":
        expected_id = TARGET_SURFACE_DEFINITION_ID
        expected_hash = TARGET_SURFACE_DEFINITION_HASH
        source_id = v17.TARGET_PROFILE_ID
        source_blob = v17.TARGET_PROFILE_BLOB
        coverage_id = "AIFC-SAL-V1.7-TARGET-SEMANTIC-COVERAGE-V1"
    else:
        raise ScientificAssuranceLineageV18Error(f"SAL_V18_SURFACE_ROLE:{role}")
    obj = _content_hash(
        path,
        "AIFC/semantic-surface-definition/v1",
        id_field="definition_id",
        expected_id=expected_id,
        hash_field="definition_content_hash",
        domain="AIFC:SEMANTIC-SURFACE-DEFINITION:v1",
        expected_hash=expected_hash,
    )
    if obj.get("surface_role") != role:
        raise ScientificAssuranceLineageV18Error("NORMATIVE_SEMANTIC_SURFACE_SELECTION_REBINDING")
    if obj.get("source_artifact_id") != source_id or obj.get("source_git_blob_sha1") != source_blob:
        raise ScientificAssuranceLineageV18Error("SEMANTIC_COVERAGE_UNIVERSE_INJECTION")
    if obj.get("coverage_manifest_id") != coverage_id:
        raise ScientificAssuranceLineageV18Error("SEMANTIC_COVERAGE_UNIVERSE_INJECTION")
    required = obj.get("required_normative_semantic_surface")
    if not isinstance(required, list) or not required or len(required) != len(set(required)):
        raise ScientificAssuranceLineageV18Error("REQUIRED_SEMANTIC_SURFACE_INVALID")
    return obj


def _verify_coverage_against_definition(
    path: str,
    definition: Mapping[str, Any],
    actual_surface: set[str],
) -> Mapping[str, Any]:
    coverage = v17._strict(path, "AIFC/semantic-coverage-manifest/v1")
    if coverage.get("entailment_question_id") != v17.QUESTION_ID:
        raise ScientificAssuranceLineageV18Error("SEMANTIC_COVERAGE_QUESTION_REBINDING")
    if coverage.get("coverage_id") != definition.get("coverage_manifest_id"):
        raise ScientificAssuranceLineageV18Error("SEMANTIC_COVERAGE_UNIVERSE_INJECTION")
    required = coverage.get("required_normative_semantic_surface")
    covered = coverage.get("covered_semantic_surface")
    if not isinstance(required, list) or not isinstance(covered, list):
        raise ScientificAssuranceLineageV18Error("SEMANTIC_COVERAGE_ARRAY_INVALID")
    try:
        verify_exact_coverage(required, covered)
    except SemanticCompilerV1Error as exc:
        raise ScientificAssuranceLineageV18Error(str(exc)) from exc
    authoritative_candidate_surface = definition.get("required_normative_semantic_surface")
    if required != authoritative_candidate_surface:
        raise ScientificAssuranceLineageV18Error("NORMATIVE_SEMANTIC_SURFACE_SELECTION_REBINDING")
    if set(covered) != actual_surface:
        raise ScientificAssuranceLineageV18Error("REQUIRED_SEMANTIC_SURFACE_OMISSION")
    return coverage


def _verify_bridge_theory() -> Mapping[str, Any]:
    bridge = _content_hash(
        BRIDGE_THEORY_PATH,
        "AIFC/semantic-bridge-theory/v1",
        id_field="bridge_theory_id",
        expected_id=BRIDGE_THEORY_ID,
        hash_field="theory_content_hash",
        domain="AIFC:SEMANTIC-BRIDGE-THEORY:v1",
        expected_hash=BRIDGE_THEORY_HASH,
    )
    if bridge.get("predecessor_formula_content_hash") != v17.PREDECESSOR_FORMULA_HASH:
        raise ScientificAssuranceLineageV18Error("CROSS_FORMULA_SEMANTIC_BRIDGE_PREDECESSOR_REBINDING")
    if bridge.get("target_formula_content_hash") != v17.TARGET_FORMULA_HASH:
        raise ScientificAssuranceLineageV18Error("CROSS_FORMULA_SEMANTIC_BRIDGE_TARGET_REBINDING")
    axioms = bridge.get("bridge_axioms")
    if not isinstance(axioms, list):
        raise ScientificAssuranceLineageV18Error("CROSS_FORMULA_SEMANTIC_BRIDGE_AXIOMS_INVALID")
    if bridge.get("bridge_status") == "ABSENT_NO_AUTHORITY_ADMISSIBLE_AXIOMS" and axioms:
        raise ScientificAssuranceLineageV18Error("CROSS_FORMULA_SEMANTIC_BRIDGE_STATUS_REBINDING")
    return bridge


def _verify_entailment_method_profile(question: Mapping[str, Any], issued_atom_count: int) -> Mapping[str, Any]:
    profile = _content_hash(
        METHOD_PROFILE_PATH,
        "AIFC/entailment-method-profile/v1",
        id_field="method_profile_id",
        expected_id=METHOD_PROFILE_ID,
        hash_field="method_content_hash",
        domain="AIFC:ENTAILMENT-METHOD-PROFILE:v1",
        expected_hash=METHOD_PROFILE_HASH,
    )
    if profile.get("method_label") != question.get("entailment_method"):
        raise ScientificAssuranceLineageV18Error("ENTAILMENT_METHOD_SEMANTICS_REBINDING")
    if profile.get("solver_source_path") != METHOD_SOLVER_PATH or profile.get("solver_git_blob_sha1") != METHOD_SOLVER_GIT_BLOB_SHA1:
        raise ScientificAssuranceLineageV18Error("SAME_ENTAILMENT_METHOD_ID_MUTATION")
    solver_raw = (REPO_ROOT / METHOD_SOLVER_PATH).read_bytes()
    if git_blob_sha1_bytes(solver_raw) != METHOD_SOLVER_GIT_BLOB_SHA1:
        raise ScientificAssuranceLineageV18Error("SAME_ENTAILMENT_METHOD_ID_MUTATION")
    if profile.get("issued_question_atom_count") != issued_atom_count:
        raise ScientificAssuranceLineageV18Error("ENTAILMENT_METHOD_ISSUED_QUESTION_ATOM_COUNT_REBINDING")
    return profile


def _verify_question_source_binding(question: Mapping[str, Any]) -> Mapping[str, Any]:
    binding = _content_hash(
        QUESTION_SOURCE_BINDING_PATH,
        "AIFC/entailment-question-source-binding/v1",
        id_field="binding_id",
        expected_id=QUESTION_SOURCE_BINDING_ID,
        hash_field="binding_content_hash",
        domain="AIFC:ENTAILMENT-QUESTION-SOURCE-BINDING:v1",
        expected_hash=QUESTION_SOURCE_BINDING_HASH,
    )
    pairs = (
        ("predecessor_artifact_id", "predecessor_artifact_id"),
        ("predecessor_git_blob_sha1", "predecessor_git_blob_sha1"),
        ("target_profile_id", "target_profile_id"),
        ("target_profile_git_blob_sha1", "target_profile_git_blob_sha1"),
    )
    for binding_field, question_field in pairs:
        if binding.get(binding_field) != question.get(question_field):
            raise ScientificAssuranceLineageV18Error("ENTAILMENT_QUESTION_SOURCE_BINDING_REBINDING")
    if binding.get("binding_status") == "DUAL_IDENTITY_ESTABLISHED":
        if not binding.get("predecessor_raw_sha256") or not binding.get("target_profile_raw_sha256"):
            raise ScientificAssuranceLineageV18Error("ENTAILMENT_QUESTION_SOURCE_DUAL_IDENTITY_FALSE_PASS")
    return binding


def _positive_conjunction_atoms(formula: Mapping[str, Any]) -> set[str] | None:
    if formula.get("op") == "ATOM":
        atom = formula.get("id")
        return {str(atom)} if isinstance(atom, str) and atom else None
    if formula.get("op") != "AND":
        return None
    args = formula.get("args")
    if not isinstance(args, list) or not args:
        return None
    atoms: set[str] = set()
    for arg in args:
        if not isinstance(arg, Mapping) or arg.get("op") != "ATOM":
            return None
        atom = arg.get("id")
        if not isinstance(atom, str) or not atom:
            return None
        atoms.add(atom)
    return atoms if len(atoms) == len(args) else None


def _latent_disjoint_refutation(premise: Mapping[str, Any], target: Mapping[str, Any]) -> tuple[str, str, int]:
    p = _positive_conjunction_atoms(premise)
    t = _positive_conjunction_atoms(target)
    if p is None or t is None:
        return "NOT_DISJOINT", "NOT_ESTABLISHED", 0
    union_count = len(p | t)
    if p.isdisjoint(t) and p and t:
        return "CONFIRMED", "LATENT_IF_SOLVER_PREMATURELY_ENABLED", union_count
    return "NOT_DISJOINT", "NOT_ESTABLISHED", union_count


def _abstraction_closure_blockers(
    predecessor_surface: Mapping[str, Any],
    target_surface: Mapping[str, Any],
    bridge: Mapping[str, Any],
    method: Mapping[str, Any],
    question_binding: Mapping[str, Any],
) -> tuple[str, ...]:
    blockers: list[str] = []
    surfaces_authoritative = all(
        obj.get("selection_authority_status") == "PREDECESSOR_AUTHORITY_ADMITTED_SURFACE"
        and obj.get("completeness_claim") == "AUTHORITY_ESTABLISHED_COMPLETE_FOR_QUESTION"
        for obj in (predecessor_surface, target_surface)
    )
    if not surfaces_authoritative:
        blockers.append("BLOCKED_NORMATIVE_SEMANTIC_SURFACE_AUTHORITY")
    if bridge.get("abstraction_adequacy_status") != "AUTHORITY_ESTABLISHED":
        blockers.append("BLOCKED_SEMANTIC_ABSTRACTION_ADEQUACY")
    if bridge.get("bridge_status") != "AUTHORITY_ADMISSIBLE_BRIDGE_THEORY":
        blockers.append("BLOCKED_CROSS_FORMULA_SEMANTIC_BRIDGE_ABSENT")
    if bridge.get("bridge_authority_status") != "AUTHORITY_ADMISSIBLE":
        blockers.append("BLOCKED_CROSS_FORMULA_SEMANTIC_BRIDGE_AUTHORITY")
    if method.get("method_authority_status") != "AUTHORITY_ADMISSIBLE":
        blockers.append("BLOCKED_ENTAILMENT_METHOD_AUTHORITY")
    formal = method.get("formal_semantics")
    max_atoms = formal.get("max_atoms") if isinstance(formal, Mapping) else None
    issued = method.get("issued_question_atom_count")
    if not isinstance(max_atoms, int) or not isinstance(issued, int) or issued > max_atoms:
        blockers.append("BLOCKED_ENTAILMENT_METHOD_CAPACITY_FOR_ISSUED_QUESTION")
    if question_binding.get("binding_status") != "DUAL_IDENTITY_ESTABLISHED":
        blockers.append("BLOCKED_ENTAILMENT_QUESTION_SOURCE_DUAL_IDENTITY")
    return tuple(blockers)


def audit_semantic_abstraction_closure(
    predecessor_identity: str,
    target_profile_identity: str,
    entailment_question_identity: str,
) -> SemanticAbstractionReport:
    """Identity-only production path. Solver execution is last and authority-gated."""
    if (
        predecessor_identity != v17.PREDECESSOR_ID
        or target_profile_identity != v17.TARGET_PROFILE_ID
        or entailment_question_identity != v17.QUESTION_ID
    ):
        raise ScientificAssuranceLineageV18Error("ENTAILMENT_QUESTION_IDENTITY_SUBSTITUTION")

    question = v17._verify_question()
    predecessor = v17._read_exact_source(v17.PREDECESSOR_PATH, v17.PREDECESSOR_BLOB, v17.PREDECESSOR_COMMIT)
    target = v17._read_exact_source(v17.TARGET_PROFILE_PATH, v17.TARGET_PROFILE_BLOB, v17.TARGET_PROFILE_COMMIT)

    anchors: list[Mapping[str, Any]] = []
    predecessor_actual_surface: set[str] = set()
    for path in v17.ANCHOR_PATHS:
        anchor = v17._strict(path, "AIFC/historical-semantic-anchor/v1")
        if (
            anchor.get("source_artifact_id") != v17.PREDECESSOR_ID
            or anchor.get("source_commit_sha") != v17.PREDECESSOR_COMMIT
            or anchor.get("source_git_blob_sha1") != v17.PREDECESSOR_BLOB
        ):
            raise ScientificAssuranceLineageV18Error("HISTORICAL_SEMANTIC_ANCHOR_PROVENANCE_REBINDING")
        predecessor_actual_surface |= v17._verify_anchor(anchor, predecessor)
        anchors.append(anchor)

    target_anchor = v17._strict(v17.TARGET_ANCHOR_PATH, "AIFC/historical-semantic-anchor/v1")
    if (
        target_anchor.get("source_artifact_id") != v17.TARGET_PROFILE_ID
        or target_anchor.get("source_commit_sha") != v17.TARGET_PROFILE_COMMIT
        or target_anchor.get("source_git_blob_sha1") != v17.TARGET_PROFILE_BLOB
    ):
        raise ScientificAssuranceLineageV18Error("TARGET_PROFILE_TO_FORMULA_REBINDING")
    target_actual_surface = v17._verify_anchor(target_anchor, target)

    predecessor_surface = _verify_surface_definition(PREDECESSOR_SURFACE_DEFINITION_PATH, role="PREDECESSOR")
    target_surface = _verify_surface_definition(TARGET_SURFACE_DEFINITION_PATH, role="TARGET")
    predecessor_coverage = _verify_coverage_against_definition(
        v17.PREDECESSOR_COVERAGE_PATH, predecessor_surface, predecessor_actual_surface
    )
    target_coverage = _verify_coverage_against_definition(
        v17.TARGET_COVERAGE_PATH, target_surface, target_actual_surface
    )
    compilation_profile = v17._verify_compilation_profile()

    pred_ast, pred_bindings = compile_predecessor_formula(anchors)
    target_required = target_surface["required_normative_semantic_surface"]
    target_ast, target_bindings = compile_target_formula(target, target_required)
    pred_ids = [
        "AIFC-SEMANTIC-ANCHOR-AUTHORITY-CLOSED-PROOF-V1",
        "AIFC-SEMANTIC-ANCHOR-GATE-DEFINITION-HISTORICAL-ANCHOR-V1",
        "AIFC-SEMANTIC-ANCHOR-GATE-ATOM-SEMANTIC-IDENTITY-V1",
    ]
    target_ids = ["AIFC-SEMANTIC-ANCHOR-TARGET-LINEAGE-TRANSITION-PROFILE-V1"]
    v17._verify_formula(
        v17.PREDECESSOR_FORMULA_PATH,
        "PREDECESSOR_PREMISE",
        v17.PREDECESSOR_FORMULA_HASH,
        pred_ids,
        predecessor_surface["coverage_manifest_id"],
        pred_ast,
        pred_bindings,
    )
    v17._verify_formula(
        v17.TARGET_FORMULA_PATH,
        "TARGET_TRANSITION_PROFILE",
        v17.TARGET_FORMULA_HASH,
        target_ids,
        target_surface["coverage_manifest_id"],
        target_ast,
        target_bindings,
    )

    disjoint, latent_refutation, union_count = _latent_disjoint_refutation(pred_ast, target_ast)
    bridge = _verify_bridge_theory()
    method = _verify_entailment_method_profile(question, union_count)
    question_binding = _verify_question_source_binding(question)

    all_anchors = anchors + [target_anchor]
    legacy_blocker = v17._semantic_closure_blocker(
        all_anchors, compilation_profile, predecessor_coverage, target_coverage
    )
    abstraction_blockers = _abstraction_closure_blockers(
        predecessor_surface, target_surface, bridge, method, question_binding
    )

    solver_invocations = 0
    countermodel = None
    blocker = legacy_blocker or (abstraction_blockers[0] if abstraction_blockers else None)
    if blocker is not None:
        result = "BLOCKED"
    else:
        formal = method["formal_semantics"]
        solver_invocations = 1
        solver_result = finite_propositional_entailment(
            pred_ast, target_ast, max_atoms=int(formal["max_atoms"])
        )
        result = solver_result.state
        countermodel = solver_result.countermodel

    audit = v17._strict(AUDIT_PATH, "AIFC/semantic-abstraction-audit/v1")
    expected = {
        "entailment_question_id": v17.QUESTION_ID,
        "predecessor_surface_definition_id": PREDECESSOR_SURFACE_DEFINITION_ID,
        "target_surface_definition_id": TARGET_SURFACE_DEFINITION_ID,
        "semantic_bridge_theory_id": BRIDGE_THEORY_ID,
        "entailment_method_profile_id": METHOD_PROFILE_ID,
        "question_source_binding_id": QUESTION_SOURCE_BINDING_ID,
        "normative_semantic_surface_authority": "NOT_ESTABLISHED",
        "semantic_abstraction_adequacy": "NOT_ESTABLISHED",
        "cross_formula_semantic_bridge_identity": "PASS_CONTENT_IDENTIFIED_EMPTY_THEORY",
        "cross_formula_semantic_bridge_authority": "NOT_ESTABLISHED",
        "cross_formula_semantic_bridge": "ABSENT",
        "disjoint_semantic_vocabulary": "CONFIRMED",
        "disjoint_vocabulary_trivial_refutation": "LATENT_IF_SOLVER_PREMATURELY_ENABLED",
        "entailment_method_content_identity": "PASS_CANDIDATE_EXACT_SOURCE_AND_FORMAL_SEMANTICS",
        "entailment_method_authority": "NOT_ESTABLISHED",
        "entailment_method_capacity_for_issued_question": "BLOCKED_ATOM_LIMIT_18_GT_16",
        "entailment_question_source_dual_identity": "NOT_ESTABLISHED",
        "solver_invocation_count": solver_invocations,
        "result": result,
        "blocked_subtype": blocker,
        "normative_countermodel": countermodel,
    }
    for key, value in expected.items():
        if audit.get(key) != value:
            raise ScientificAssuranceLineageV18Error(f"SAL_V18_AUDIT_RESULT_REBINDING:{key}")
    if blocker is not None and solver_invocations != 0:
        raise ScientificAssuranceLineageV18Error("SOLVER_EXECUTION_BEFORE_SEMANTIC_ABSTRACTION_CLOSURE")

    return SemanticAbstractionReport(
        question_id=v17.QUESTION_ID,
        normative_semantic_surface_authority="NOT_ESTABLISHED",
        semantic_abstraction_adequacy="NOT_ESTABLISHED",
        cross_formula_semantic_bridge_identity="PASS_CONTENT_IDENTIFIED_EMPTY_THEORY",
        cross_formula_semantic_bridge_authority="NOT_ESTABLISHED",
        cross_formula_semantic_bridge="ABSENT",
        disjoint_semantic_vocabulary=disjoint,
        disjoint_vocabulary_trivial_refutation=latent_refutation,
        entailment_method_content_identity="PASS_CANDIDATE_EXACT_SOURCE_AND_FORMAL_SEMANTICS",
        entailment_method_authority="NOT_ESTABLISHED",
        entailment_method_capacity_for_issued_question="BLOCKED_ATOM_LIMIT_18_GT_16",
        entailment_question_source_dual_identity="NOT_ESTABLISHED",
        abstraction_closure_blockers=abstraction_blockers,
        solver_invocation_count=solver_invocations,
        result=result,
        blocked_subtype=blocker,
        normative_countermodel=countermodel,
    )
