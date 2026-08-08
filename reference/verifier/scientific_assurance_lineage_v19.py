#!/usr/bin/env python3
"""SAL v1.9 Semantic Bridge Execution Closure.

This layer does not authorize a bridge. It ensures that any future admissible
bridge has executable syntax, is composed into the prover premise, participates
in method-capacity calculation, and that question-source raw SHA-256 claims are
recomputed from exact historical Git membership.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

from canonical import domain_hash
from scientific_assurance_lineage_v14 import git_blob_sha1_bytes
import scientific_assurance_lineage_v17 as v17
import scientific_assurance_lineage_v18 as v18
from semantic_compiler_v1 import compile_predecessor_formula, compile_target_formula
import semantic_bridge_execution_v1 as bridge_exec

REPO_ROOT = Path(__file__).resolve().parents[2]

BRIDGE_THEORY_V1_PATH = "conformance/AIFC-SEMANTIC-BRIDGE-THEORY-v1.json"
BRIDGE_THEORY_V1_BLOB = "d9532a6ee1dcd611fcd93d2ac66f5c4a982d5463"
BRIDGE_THEORY_V2_PATH = "conformance/AIFC-SEMANTIC-BRIDGE-THEORY-v2.json"
BRIDGE_THEORY_V2_ID = "AIFC-SAL-V1.9-CROSS-FORMULA-SEMANTIC-BRIDGE-V2"
BRIDGE_THEORY_V2_HASH = "d4856ecb21bc1b9306b0bf6a884e6b87c87e264a05b56fbf7ca39d97409038be"

EXECUTION_PROFILE_PATH = "conformance/AIFC-SEMANTIC-BRIDGE-EXECUTION-PROFILE-v1.json"
EXECUTION_PROFILE_ID = "AIFC-SAL-V1.9-SEMANTIC-BRIDGE-EXECUTION-PROFILE-V1"
EXECUTION_PROFILE_HASH = "15e44b8fb5c091c55e80e68ef4dd178881a30a20e03286bb95420739bca47694"
EXECUTION_IMPL_PATH = "reference/verifier/semantic_bridge_execution_v1.py"
EXECUTION_IMPL_BLOB = "2ec3ff451d8e13a969d46b6bfaf0cf2f12e763f7"
EXECUTION_IMPL_RAW_SHA256 = "3bf69ee003d653792f32bea424830ff0b264ef033e05ff9e01005032c7b974d2"

QUESTION_SOURCE_BINDING_V1_BLOB = "fb6e363b98ccd7be912ddda586f1fbc2f9360419"
QUESTION_SOURCE_BINDING_V2_PATH = "conformance/AIFC-ENTAILMENT-QUESTION-SOURCE-BINDING-v2.json"
QUESTION_SOURCE_BINDING_V2_ID = "AIFC-SAL-V1.9-ENTAILMENT-QUESTION-SOURCE-BINDING-V2"
QUESTION_SOURCE_BINDING_V2_HASH = "27d7d0efb42b792de17fd1642ff32d2fe7d783b2ca9a209a945fe64c3369cb9c"

AUDIT_PATH = "conformance/AIFC-SEMANTIC-BRIDGE-EXECUTION-AUDIT-v1.json"
AUDIT_ID = "AIFC-SAL-V1.9-SEMANTIC-BRIDGE-EXECUTION-AUDIT-V1"
AUDIT_HASH = "e9df55671902d54e6d093d926de6027b66c3ce66eb95e7bf82b2461d7bec9d21"

BRIDGE_AXIOM_SCHEMA_BLOB = "1dd24634f0100409546ab52db65250fe21d7fedf"
BRIDGE_AXIOM_SCHEMA_RAW_SHA256 = "4019af8c5cf538cfa1ef43cc56a88a7eaf3d8bce0b2768d37a9e7ad4062484f5"
FORMULA_SCHEMA_BLOB = "8b543131632d294518d41460a40ddbb1542e31e3"
FORMULA_SCHEMA_RAW_SHA256 = "42e13572f3a20c9daa0bac19dce83c7000905a72f03133400f7e05fbd6dea030"


class ScientificAssuranceLineageV19Error(ValueError):
    pass


@dataclass(frozen=True)
class SemanticBridgeExecutionReport:
    question_id: str
    bridge_axiom_executable_semantics: str
    semantic_bridge_execution_binding: str
    bridge_theory_composition_replay: str
    bridge_aware_method_capacity: str
    question_source_raw_sha256_recomputation: str
    recomputed_predecessor_raw_sha256: str
    recomputed_target_profile_raw_sha256: str
    entailment_question_source_dual_identity: str
    current_bridge_axiom_count: int
    current_bridge_aware_atom_count: int
    bridge_execution_blockers: tuple[str, ...]
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
    if obj.get(id_field) != expected_id:
        raise ScientificAssuranceLineageV19Error(f"SAL_V19_ID_REBINDING:{path}")
    material = dict(obj)
    claimed = material.pop(hash_field, None)
    actual = domain_hash(domain, material)
    if claimed != expected_hash or actual != expected_hash:
        raise ScientificAssuranceLineageV19Error(f"SAL_V19_CONTENT_IDENTITY_REBINDING:{path}")
    return obj


def _verify_bridge_theory_v2() -> Mapping[str, Any]:
    raw_v1 = (REPO_ROOT / BRIDGE_THEORY_V1_PATH).read_bytes()
    if git_blob_sha1_bytes(raw_v1) != BRIDGE_THEORY_V1_BLOB:
        raise ScientificAssuranceLineageV19Error("BRIDGE_THEORY_V1_LINEAGE_REBINDING")
    theory = _content_hash(
        BRIDGE_THEORY_V2_PATH,
        "AIFC/semantic-bridge-theory/v2",
        id_field="bridge_theory_id",
        expected_id=BRIDGE_THEORY_V2_ID,
        hash_field="theory_content_hash",
        domain="AIFC:SEMANTIC-BRIDGE-THEORY:v2",
        expected_hash=BRIDGE_THEORY_V2_HASH,
    )
    expected = {
        "predecessor_bridge_theory_id": "AIFC-SAL-V1.8-CROSS-FORMULA-SEMANTIC-BRIDGE-V1",
        "predecessor_bridge_theory_git_blob_sha1": BRIDGE_THEORY_V1_BLOB,
        "entailment_question_id": v17.QUESTION_ID,
        "predecessor_formula_content_hash": v17.PREDECESSOR_FORMULA_HASH,
        "target_formula_content_hash": v17.TARGET_FORMULA_HASH,
        "logical_fragment": "FINITE_CLASSICAL_PROPOSITIONAL_V1",
    }
    for key, value in expected.items():
        if theory.get(key) != value:
            raise ScientificAssuranceLineageV19Error(f"BRIDGE_THEORY_V2_REBINDING:{key}")
    return theory


def _verify_execution_profile(theory: Mapping[str, Any], method: Mapping[str, Any]) -> Mapping[str, Any]:
    profile = _content_hash(
        EXECUTION_PROFILE_PATH,
        "AIFC/semantic-bridge-execution-profile/v1",
        id_field="execution_profile_id",
        expected_id=EXECUTION_PROFILE_ID,
        hash_field="profile_content_hash",
        domain="AIFC:SEMANTIC-BRIDGE-EXECUTION-PROFILE:v1",
        expected_hash=EXECUTION_PROFILE_HASH,
    )
    impl_raw = (REPO_ROOT / EXECUTION_IMPL_PATH).read_bytes()
    if git_blob_sha1_bytes(impl_raw) != EXECUTION_IMPL_BLOB:
        raise ScientificAssuranceLineageV19Error("BRIDGE_EXECUTION_IMPLEMENTATION_GIT_IDENTITY_REBINDING")
    if hashlib.sha256(impl_raw).hexdigest() != EXECUTION_IMPL_RAW_SHA256:
        raise ScientificAssuranceLineageV19Error("BRIDGE_EXECUTION_IMPLEMENTATION_RAW_IDENTITY_REBINDING")
    expected = {
        "entailment_question_id": v17.QUESTION_ID,
        "semantic_bridge_theory_id": BRIDGE_THEORY_V2_ID,
        "semantic_bridge_theory_content_hash": BRIDGE_THEORY_V2_HASH,
        "entailment_method_profile_id": method.get("method_profile_id"),
        "entailment_method_profile_content_hash": method.get("method_content_hash"),
        "composition_rule": "PREMISE_AND_ORDERED_BRIDGE_AXIOMS_V1",
        "bridge_axiom_schema_id": "AIFC/semantic-bridge-axiom/v1",
        "bridge_axiom_schema_git_blob_sha1": BRIDGE_AXIOM_SCHEMA_BLOB,
        "bridge_axiom_schema_raw_sha256": BRIDGE_AXIOM_SCHEMA_RAW_SHA256,
        "formula_ast_schema_id": "AIFC/semantic-formula/v1",
        "formula_ast_schema_git_blob_sha1": FORMULA_SCHEMA_BLOB,
        "formula_ast_schema_raw_sha256": FORMULA_SCHEMA_RAW_SHA256,
        "execution_implementation_path": EXECUTION_IMPL_PATH,
        "execution_implementation_git_blob_sha1": EXECUTION_IMPL_BLOB,
        "execution_implementation_raw_sha256": EXECUTION_IMPL_RAW_SHA256,
    }
    for key, value in expected.items():
        if profile.get(key) != value:
            raise ScientificAssuranceLineageV19Error(f"BRIDGE_EXECUTION_PROFILE_REBINDING:{key}")
    return profile


def _resolve_bridge_axioms(theory: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    refs = theory.get("bridge_axiom_refs")
    if not isinstance(refs, list):
        raise ScientificAssuranceLineageV19Error("BRIDGE_AXIOM_REFS_INVALID")
    out: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    for ref in refs:
        if not isinstance(ref, Mapping):
            raise ScientificAssuranceLineageV19Error("BRIDGE_AXIOM_REF_INVALID")
        axiom_id = ref.get("axiom_id")
        path_text = ref.get("source_path")
        if not isinstance(axiom_id, str) or not axiom_id or axiom_id in seen:
            raise ScientificAssuranceLineageV19Error("BRIDGE_AXIOM_ID_INVALID_OR_DUPLICATE")
        if not isinstance(path_text, str) or not path_text.startswith("conformance/"):
            raise ScientificAssuranceLineageV19Error("BRIDGE_AXIOM_PATH_INVALID")
        seen.add(axiom_id)
        path = (REPO_ROOT / path_text).resolve()
        try:
            path.relative_to(REPO_ROOT.resolve())
        except ValueError as exc:
            raise ScientificAssuranceLineageV19Error("BRIDGE_AXIOM_PATH_ESCAPE") from exc
        raw = path.read_bytes()
        if git_blob_sha1_bytes(raw) != ref.get("git_blob_sha1"):
            raise ScientificAssuranceLineageV19Error("BRIDGE_AXIOM_GIT_IDENTITY_REBINDING")
        if hashlib.sha256(raw).hexdigest() != ref.get("raw_sha256"):
            raise ScientificAssuranceLineageV19Error("BRIDGE_AXIOM_RAW_IDENTITY_REBINDING")
        axiom = v17._strict(path_text, "AIFC/semantic-bridge-axiom/v1")
        if axiom.get("axiom_id") != axiom_id or axiom.get("axiom_content_hash") != ref.get("axiom_content_hash"):
            raise ScientificAssuranceLineageV19Error("BRIDGE_AXIOM_REFERENCE_REBINDING")
        try:
            bridge_exec.verify_bridge_axiom_semantics(
                axiom, expected_question_id=v17.QUESTION_ID, require_authority=False
            )
        except bridge_exec.SemanticBridgeExecutionV1Error as exc:
            raise ScientificAssuranceLineageV19Error(str(exc)) from exc
        out.append(axiom)
    return tuple(out)


def _git_blob_bytes(blob: str) -> bytes:
    try:
        return subprocess.check_output(["git", "cat-file", "blob", blob], cwd=REPO_ROOT)
    except subprocess.CalledProcessError as exc:
        raise ScientificAssuranceLineageV19Error(f"HISTORICAL_BLOB_BYTES_UNAVAILABLE:{blob}") from exc


def _historical_bound_bytes(commit: str, path_text: str, expected_blob: str) -> bytes:
    if v17.git_tree_blob(commit, path_text) != expected_blob:
        raise ScientificAssuranceLineageV19Error(
            f"QUESTION_SOURCE_HISTORICAL_MEMBERSHIP_REBINDING:{commit}:{path_text}"
        )
    raw = _git_blob_bytes(expected_blob)
    if git_blob_sha1_bytes(raw) != expected_blob:
        raise ScientificAssuranceLineageV19Error("QUESTION_SOURCE_HISTORICAL_BLOB_BYTES_REBINDING")
    return raw


def _enforce_dual_identity_claim(
    binding: Mapping[str, Any],
    recomputed_predecessor_raw_sha256: str,
    recomputed_target_raw_sha256: str,
) -> None:
    if binding.get("binding_status") != "DUAL_IDENTITY_ESTABLISHED":
        return
    if binding.get("predecessor_raw_sha256") != recomputed_predecessor_raw_sha256:
        raise ScientificAssuranceLineageV19Error(
            "ENTAILMENT_QUESTION_RAW_SHA256_SELF_ASSERTION:PREDECESSOR"
        )
    if binding.get("target_profile_raw_sha256") != recomputed_target_raw_sha256:
        raise ScientificAssuranceLineageV19Error(
            "ENTAILMENT_QUESTION_RAW_SHA256_SELF_ASSERTION:TARGET"
        )


def _verify_question_source_binding_v2(
    question: Mapping[str, Any],
) -> tuple[Mapping[str, Any], str, str]:
    predecessor_v1 = v18._verify_question_source_binding(question)
    raw_v1 = (REPO_ROOT / v18.QUESTION_SOURCE_BINDING_PATH).read_bytes()
    if git_blob_sha1_bytes(raw_v1) != QUESTION_SOURCE_BINDING_V1_BLOB:
        raise ScientificAssuranceLineageV19Error("QUESTION_SOURCE_BINDING_PREDECESSOR_REBINDING")
    binding = _content_hash(
        QUESTION_SOURCE_BINDING_V2_PATH,
        "AIFC/entailment-question-source-binding/v2",
        id_field="binding_id",
        expected_id=QUESTION_SOURCE_BINDING_V2_ID,
        hash_field="binding_content_hash",
        domain="AIFC:ENTAILMENT-QUESTION-SOURCE-BINDING:v2",
        expected_hash=QUESTION_SOURCE_BINDING_V2_HASH,
    )
    exact = {
        "predecessor_binding_id": predecessor_v1.get("binding_id"),
        "predecessor_binding_git_blob_sha1": QUESTION_SOURCE_BINDING_V1_BLOB,
        "entailment_question_id": v17.QUESTION_ID,
        "predecessor_artifact_id": v17.PREDECESSOR_ID,
        "predecessor_commit_sha": v17.PREDECESSOR_COMMIT,
        "predecessor_source_path": v17.PREDECESSOR_PATH,
        "predecessor_git_blob_sha1": v17.PREDECESSOR_BLOB,
        "target_profile_id": v17.TARGET_PROFILE_ID,
        "target_profile_commit_sha": v17.TARGET_PROFILE_COMMIT,
        "target_profile_source_path": v17.TARGET_PROFILE_PATH,
        "target_profile_git_blob_sha1": v17.TARGET_PROFILE_BLOB,
        "recomputation_rule": "EXACT_HISTORICAL_TREE_MEMBERSHIP_THEN_RAW_SHA256_V1",
    }
    for key, value in exact.items():
        if binding.get(key) != value:
            raise ScientificAssuranceLineageV19Error(f"QUESTION_SOURCE_BINDING_V2_REBINDING:{key}")
    pred_raw = _historical_bound_bytes(
        v17.PREDECESSOR_COMMIT, v17.PREDECESSOR_PATH, v17.PREDECESSOR_BLOB
    )
    target_raw = _historical_bound_bytes(
        v17.TARGET_PROFILE_COMMIT, v17.TARGET_PROFILE_PATH, v17.TARGET_PROFILE_BLOB
    )
    pred_sha = hashlib.sha256(pred_raw).hexdigest()
    target_sha = hashlib.sha256(target_raw).hexdigest()
    _enforce_dual_identity_claim(binding, pred_sha, target_sha)
    return binding, pred_sha, target_sha


def _closure_blockers(
    predecessor_surface: Mapping[str, Any],
    target_surface: Mapping[str, Any],
    theory: Mapping[str, Any],
    bridge_axioms: Sequence[Mapping[str, Any]],
    execution_profile: Mapping[str, Any],
    method: Mapping[str, Any],
    bridge_aware_atom_count: int,
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
    if theory.get("abstraction_adequacy_status") != "AUTHORITY_ESTABLISHED":
        blockers.append("BLOCKED_SEMANTIC_ABSTRACTION_ADEQUACY")
    if theory.get("bridge_status") != "AUTHORITY_ADMISSIBLE_BRIDGE_THEORY":
        blockers.append("BLOCKED_CROSS_FORMULA_SEMANTIC_BRIDGE_ABSENT")
    if theory.get("bridge_authority_status") != "AUTHORITY_ADMISSIBLE":
        blockers.append("BLOCKED_CROSS_FORMULA_SEMANTIC_BRIDGE_AUTHORITY")
    if theory.get("bridge_status") == "AUTHORITY_ADMISSIBLE_BRIDGE_THEORY" and not bridge_axioms:
        blockers.append("BLOCKED_BRIDGE_AXIOM_EXECUTABLE_SEMANTICS")
    if any(ax.get("axiom_authority_status") != "AUTHORITY_ADMISSIBLE" for ax in bridge_axioms):
        blockers.append("BLOCKED_BRIDGE_AXIOM_AUTHORITY")
    if execution_profile.get("execution_authority_status") != "AUTHORITY_ADMISSIBLE":
        blockers.append("BLOCKED_SEMANTIC_BRIDGE_EXECUTION_BINDING")
    if method.get("method_authority_status") != "AUTHORITY_ADMISSIBLE":
        blockers.append("BLOCKED_ENTAILMENT_METHOD_AUTHORITY")
    formal = method.get("formal_semantics")
    max_atoms = formal.get("max_atoms") if isinstance(formal, Mapping) else None
    if not isinstance(max_atoms, int) or bridge_aware_atom_count > max_atoms:
        blockers.append("BLOCKED_BRIDGE_AWARE_ENTAILMENT_METHOD_CAPACITY")
    if question_binding.get("binding_status") != "DUAL_IDENTITY_ESTABLISHED":
        blockers.append("BLOCKED_ENTAILMENT_QUESTION_SOURCE_DUAL_IDENTITY")
    return tuple(blockers)


def audit_semantic_bridge_execution_closure(
    predecessor_identity: str,
    target_profile_identity: str,
    entailment_question_identity: str,
) -> SemanticBridgeExecutionReport:
    """Identity-only production path. The prover is bridge-bound by construction."""
    if (
        predecessor_identity != v17.PREDECESSOR_ID
        or target_profile_identity != v17.TARGET_PROFILE_ID
        or entailment_question_identity != v17.QUESTION_ID
    ):
        raise ScientificAssuranceLineageV19Error("ENTAILMENT_QUESTION_IDENTITY_SUBSTITUTION")

    question = v17._verify_question()
    predecessor = v17._read_exact_source(
        v17.PREDECESSOR_PATH, v17.PREDECESSOR_BLOB, v17.PREDECESSOR_COMMIT
    )
    target = v17._read_exact_source(
        v17.TARGET_PROFILE_PATH, v17.TARGET_PROFILE_BLOB, v17.TARGET_PROFILE_COMMIT
    )

    anchors: list[Mapping[str, Any]] = []
    predecessor_actual_surface: set[str] = set()
    for path in v17.ANCHOR_PATHS:
        anchor = v17._strict(path, "AIFC/historical-semantic-anchor/v1")
        if (
            anchor.get("source_artifact_id") != v17.PREDECESSOR_ID
            or anchor.get("source_commit_sha") != v17.PREDECESSOR_COMMIT
            or anchor.get("source_git_blob_sha1") != v17.PREDECESSOR_BLOB
        ):
            raise ScientificAssuranceLineageV19Error("HISTORICAL_SEMANTIC_ANCHOR_PROVENANCE_REBINDING")
        predecessor_actual_surface |= v17._verify_anchor(anchor, predecessor)
        anchors.append(anchor)

    target_anchor = v17._strict(v17.TARGET_ANCHOR_PATH, "AIFC/historical-semantic-anchor/v1")
    if (
        target_anchor.get("source_artifact_id") != v17.TARGET_PROFILE_ID
        or target_anchor.get("source_commit_sha") != v17.TARGET_PROFILE_COMMIT
        or target_anchor.get("source_git_blob_sha1") != v17.TARGET_PROFILE_BLOB
    ):
        raise ScientificAssuranceLineageV19Error("TARGET_PROFILE_TO_FORMULA_REBINDING")
    target_actual_surface = v17._verify_anchor(target_anchor, target)

    predecessor_surface = v18._verify_surface_definition(
        v18.PREDECESSOR_SURFACE_DEFINITION_PATH, role="PREDECESSOR"
    )
    target_surface = v18._verify_surface_definition(
        v18.TARGET_SURFACE_DEFINITION_PATH, role="TARGET"
    )
    predecessor_coverage = v18._verify_coverage_against_definition(
        v17.PREDECESSOR_COVERAGE_PATH, predecessor_surface, predecessor_actual_surface
    )
    target_coverage = v18._verify_coverage_against_definition(
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

    base_union_count = len(bridge_exec.formula_atoms(pred_ast) | bridge_exec.formula_atoms(target_ast))
    method = v18._verify_entailment_method_profile(question, base_union_count)
    theory = _verify_bridge_theory_v2()
    execution_profile = _verify_execution_profile(theory, method)
    bridge_axioms = _resolve_bridge_axioms(theory)
    try:
        bridge_count = bridge_exec.bridge_aware_atom_count(
            pred_ast, bridge_axioms, target_ast, expected_question_id=v17.QUESTION_ID
        )
        empty_composition = bridge_exec.compose_bridge_premise(
            pred_ast,
            bridge_axioms,
            expected_question_id=v17.QUESTION_ID,
            require_authority=False,
        )
    except bridge_exec.SemanticBridgeExecutionV1Error as exc:
        raise ScientificAssuranceLineageV19Error(str(exc)) from exc
    if not bridge_axioms and empty_composition.composed_premise != pred_ast:
        raise ScientificAssuranceLineageV19Error("EMPTY_BRIDGE_COMPOSITION_REBINDING")

    binding, pred_raw_sha, target_raw_sha = _verify_question_source_binding_v2(question)

    legacy_blocker = v17._semantic_closure_blocker(
        anchors + [target_anchor],
        compilation_profile,
        predecessor_coverage,
        target_coverage,
    )
    bridge_blockers = _closure_blockers(
        predecessor_surface,
        target_surface,
        theory,
        bridge_axioms,
        execution_profile,
        method,
        bridge_count,
        binding,
    )
    blocker = legacy_blocker or (bridge_blockers[0] if bridge_blockers else None)

    solver_invocations = 0
    countermodel = None
    if blocker is not None:
        result = "BLOCKED"
    else:
        formal = method["formal_semantics"]
        solver_invocations = 1
        try:
            solver_result, composition = bridge_exec.bridge_bound_entailment(
                pred_ast,
                bridge_axioms,
                target_ast,
                expected_question_id=v17.QUESTION_ID,
                max_atoms=int(formal["max_atoms"]),
            )
            replay = bridge_exec.compose_bridge_premise(
                pred_ast,
                bridge_axioms,
                expected_question_id=v17.QUESTION_ID,
                require_authority=True,
            )
        except bridge_exec.SemanticBridgeExecutionV1Error as exc:
            raise ScientificAssuranceLineageV19Error(str(exc)) from exc
        if (
            replay.composed_premise != composition.composed_premise
            or replay.composed_premise_hash != composition.composed_premise_hash
        ):
            raise ScientificAssuranceLineageV19Error("BRIDGE_THEORY_COMPOSITION_REPLAY_MISMATCH")
        result = solver_result.state
        countermodel = solver_result.countermodel

    audit = _content_hash(
        AUDIT_PATH,
        "AIFC/semantic-bridge-execution-audit/v1",
        id_field="audit_id",
        expected_id=AUDIT_ID,
        hash_field="audit_content_hash",
        domain="AIFC:SEMANTIC-BRIDGE-EXECUTION-AUDIT:v1",
        expected_hash=AUDIT_HASH,
    )
    expected_audit = {
        "entailment_question_id": v17.QUESTION_ID,
        "bridge_theory_id": BRIDGE_THEORY_V2_ID,
        "execution_profile_id": EXECUTION_PROFILE_ID,
        "question_source_binding_id": QUESTION_SOURCE_BINDING_V2_ID,
        "current_bridge_axiom_count": len(bridge_axioms),
        "current_bridge_aware_atom_count": bridge_count,
        "solver_invocation_count": solver_invocations,
        "result": result,
        "blocked_subtype": blocker,
        "normative_countermodel": countermodel,
    }
    for key, value in expected_audit.items():
        if audit.get(key) != value:
            raise ScientificAssuranceLineageV19Error(f"SAL_V19_AUDIT_RESULT_REBINDING:{key}")
    if blocker is not None and solver_invocations != 0:
        raise ScientificAssuranceLineageV19Error(
            "SOLVER_EXECUTION_BEFORE_BRIDGE_EXECUTION_CLOSURE"
        )

    formal = method.get("formal_semantics")
    max_atoms = formal.get("max_atoms") if isinstance(formal, Mapping) else None
    capacity = (
        "CAPACITY_AVAILABLE"
        if isinstance(max_atoms, int) and bridge_count <= max_atoms
        else f"BLOCKED_ATOM_LIMIT_{bridge_count}_GT_{max_atoms}"
    )
    dual_identity = (
        "ESTABLISHED"
        if binding.get("binding_status") == "DUAL_IDENTITY_ESTABLISHED"
        else "NOT_ESTABLISHED"
    )
    return SemanticBridgeExecutionReport(
        question_id=v17.QUESTION_ID,
        bridge_axiom_executable_semantics="STRICT_EXECUTABLE_AST_AND_ATOM_BINDINGS_IMPLEMENTED_CANDIDATE",
        semantic_bridge_execution_binding="PASS_CANDIDATE_EXACT_IMPLEMENTATION_BOUND",
        bridge_theory_composition_replay="PASS_NONEMPTY_EFFECT_VECTOR_AND_EMPTY_PRODUCTION_REPLAY",
        bridge_aware_method_capacity=capacity,
        question_source_raw_sha256_recomputation="PASS_EXACT_HISTORICAL_MEMBERSHIP_RECOMPUTED_NOT_YET_BOUND",
        recomputed_predecessor_raw_sha256=pred_raw_sha,
        recomputed_target_profile_raw_sha256=target_raw_sha,
        entailment_question_source_dual_identity=dual_identity,
        current_bridge_axiom_count=len(bridge_axioms),
        current_bridge_aware_atom_count=bridge_count,
        bridge_execution_blockers=bridge_blockers,
        solver_invocation_count=solver_invocations,
        result=result,
        blocked_subtype=blocker,
        normative_countermodel=countermodel,
    )
