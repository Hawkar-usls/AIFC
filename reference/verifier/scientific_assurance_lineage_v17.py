#!/usr/bin/env python3
"""SAL v1.7 Authoritative Semantic Compilation.

Production entailment accepts only identities. Caller-supplied normative
premise, target, anchors, compiler, or formula objects are forbidden. The
solver is invoked only after semantic closure is authority-admissible.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any, Mapping

from canonical import CanonicalizationError, domain_hash, loads_strict
from schema_runtime import RuntimeSchemaError, validate_protocol_object
from scientific_assurance_lineage_v14 import git_blob_sha1_bytes, git_tree_blob
from scientific_assurance_lineage_v16 import finite_propositional_entailment
from semantic_compiler_v1 import (
    SemanticCompilerV1Error,
    compile_predecessor_formula,
    compile_target_formula,
    entailment_question_id,
    formula_content_hash,
    located_value,
    located_value_sha256,
    semantic_surface_key,
    verify_exact_coverage,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

PREDECESSOR_ID = "AIFC-RELEASE-GATE-v1.0.9-draft"
PREDECESSOR_COMMIT = "7e58b47398fe585b24db6304ee6122871095d668"
PREDECESSOR_PATH = "conformance/AIFC-RELEASE-GATE-v1.0.9-draft.json"
PREDECESSOR_BLOB = "e46cfee9963e61a22bc25e4e68ac5f11781e8d47"
TARGET_PROFILE_ID = "AIFC-LINEAGE-TRANSITION-PROFILE-V1"
TARGET_PROFILE_COMMIT = "5afc09e9a965f8b20d0b07059f1ff753aad920b7"
TARGET_PROFILE_PATH = "conformance/AIFC-LINEAGE-TRANSITION-PROFILE-v1.json"
TARGET_PROFILE_BLOB = "f096dbbb6d6382f58b3f2bbd3b7ad170b46d5e1b"
ENTAILMENT_METHOD = "ANCHOR_GATED_FINITE_PROPOSITIONAL_IMPLICATION_V1"
QUESTION_ID = "994c979c702b81a0940f28b8039ad36cb48060c426f42eb1f333bf1630e473b6"

ANCHOR_PATHS = (
    "conformance/AIFC-SEMANTIC-ANCHOR-AUTHORITY-CLOSED-PROOF-V1.json",
    "conformance/AIFC-SEMANTIC-ANCHOR-GATE-DEFINITION-HISTORICAL-ANCHOR-V1.json",
    "conformance/AIFC-SEMANTIC-ANCHOR-GATE-ATOM-SEMANTIC-IDENTITY-V1.json",
)
TARGET_ANCHOR_PATH = "conformance/AIFC-SEMANTIC-ANCHOR-TARGET-LINEAGE-TRANSITION-PROFILE-V1.json"
PREDECESSOR_COVERAGE_PATH = "conformance/AIFC-PREDECESSOR-SEMANTIC-COVERAGE-v1.json"
TARGET_COVERAGE_PATH = "conformance/AIFC-TARGET-SEMANTIC-COVERAGE-v1.json"
COMPILATION_PROFILE_PATH = "conformance/AIFC-SEMANTIC-COMPILATION-PROFILE-v1.json"
PREDECESSOR_FORMULA_PATH = "conformance/AIFC-PREDECESSOR-SEMANTIC-FORMULA-v1.json"
TARGET_FORMULA_PATH = "conformance/AIFC-TARGET-SEMANTIC-FORMULA-v1.json"
QUESTION_PATH = "conformance/AIFC-ENTAILMENT-QUESTION-v1.json"
AUDIT_PATH = "conformance/AIFC-AUTHORITATIVE-SEMANTIC-COMPILATION-AUDIT-v1.json"
COMPILER_PATH = "reference/verifier/semantic_compiler_v1.py"
COMPILER_BLOB = "b0aa58f1d82f736ee271f4969de4830a523d46ff"
COMPILER_RAW_SHA256 = "a91e5c11e64bce61b8f2bf7b37db3bbde50d10a24d3d326175dfadfa3780f35d"
PROFILE_CONTENT_HASH = "5fc4db7bb813a3549246d3b4a3491c314283e3df94cba27b0a63fc7e9ebfa70f"
PREDECESSOR_FORMULA_HASH = "b8d4771e7fc598ef3398b6995323fbd8d0b3b9f8b86b1b8b736d990527a88353"
TARGET_FORMULA_HASH = "74f0bac1ee3c2229fff6f1b92e1c02fc4a9439c43ab56bc6d199b261c7def047"

PREDECESSOR_REQUIRED_SURFACE = frozenset({
    "REQUIRED_CHECK_ID:AUTHORITY_CLOSED_PROOF",
    "REQUIRED_CHECK_ID:GATE_DEFINITION_HISTORICAL_ANCHOR",
    "REQUIRED_CHECK_ID:GATE_ATOM_SEMANTIC_IDENTITY",
    "FORBIDDEN_SHORTCUT_EXACT:allowing a transition proof to create or select the normative semantics that constitute its own theorem",
    "FORBIDDEN_SHORTCUT_EXACT:allowing a normative root to self-authenticate through a descendant transition",
})
TARGET_REQUIRED_SURFACE = frozenset({
    "PROFILE_FIELD:allowed_authority_transition.from",
    "PROFILE_FIELD:allowed_authority_transition.to",
    "PROFILE_FIELD:allowed_authority_transition.required_evidence.0",
    "PROFILE_FIELD:allowed_authority_transition.required_evidence.1",
    "PROFILE_FIELD:allowed_authority_transition.required_evidence.2",
    "PROFILE_FIELD:allowed_authority_transition.required_evidence.3",
    "PROFILE_FIELD:allowed_authority_transition.required_evidence.4",
    "PROFILE_FIELD:receipt_binding_rule",
    "PROFILE_FIELD:workflow_definition_rule",
    "PROFILE_FIELD:registry_delta_rule",
    "PROFILE_FIELD:artifact_semantic_replay_rule",
    "PROFILE_FIELD:successor_registry_rule",
    "PROFILE_FIELD:authority_status",
})


class ScientificAssuranceLineageV17Error(ValueError):
    pass


@dataclass(frozen=True)
class SemanticCompilationReport:
    question_id: str
    historical_semantic_anchor_provenance: str
    normative_semantic_coverage: str
    semantic_compilation_profile_content_identity: str
    semantic_compilation_profile_authority: str
    semantic_anchor_to_formula_binding: str
    predecessor_formula_content_hash: str
    target_formula_content_hash: str
    entailment_question_identity_preserved: str
    caller_supplied_normative_formula_forbidden: str
    solver_execution_gated_by_semantic_closure: str
    solver_invocation_count: int
    result: str
    blocked_subtype: str | None
    countermodel: Mapping[str, bool] | None


def _strict(path_text: str, schema: str) -> Mapping[str, Any]:
    path = (REPO_ROOT / path_text).resolve()
    try:
        path.relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise ScientificAssuranceLineageV17Error(f"SAL_V17_PATH_ESCAPE:{path_text}") from exc
    raw = path.read_bytes()
    try:
        value = loads_strict(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, CanonicalizationError) as exc:
        raise ScientificAssuranceLineageV17Error(f"SAL_V17_JSON_REJECTED:{path_text}:{exc}") from exc
    if not isinstance(value, Mapping):
        raise ScientificAssuranceLineageV17Error(f"SAL_V17_NOT_OBJECT:{path_text}")
    try:
        validate_protocol_object(value, schema)
    except RuntimeSchemaError as exc:
        raise ScientificAssuranceLineageV17Error(f"SAL_V17_RUNTIME_SCHEMA_REJECTED:{path_text}:{exc}") from exc
    return value


def _read_exact_source(path_text: str, expected_blob: str, commit: str) -> Mapping[str, Any]:
    path = REPO_ROOT / path_text
    raw = path.read_bytes()
    if git_blob_sha1_bytes(raw) != expected_blob:
        raise ScientificAssuranceLineageV17Error(f"SEMANTIC_SOURCE_CURRENT_COPY_REBINDING:{path_text}")
    if git_tree_blob(commit, path_text) != expected_blob:
        raise ScientificAssuranceLineageV17Error(f"HISTORICAL_SEMANTIC_SOURCE_MEMBERSHIP_REBINDING:{commit}:{path_text}")
    try:
        value = loads_strict(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, CanonicalizationError) as exc:
        raise ScientificAssuranceLineageV17Error(f"SEMANTIC_SOURCE_PARSE:{path_text}:{exc}") from exc
    if not isinstance(value, Mapping):
        raise ScientificAssuranceLineageV17Error(f"SEMANTIC_SOURCE_NOT_OBJECT:{path_text}")
    return value


def _verify_anchor(anchor: Mapping[str, Any], source: Mapping[str, Any]) -> set[str]:
    if anchor.get("retroactive_discovery_of_preexisting_executable_semantics") is not False:
        raise ScientificAssuranceLineageV17Error("RETROACTIVE_SEMANTIC_INTERPRETATION_REBINDING")
    if anchor.get("interpretation_status") not in {"INTERPRETATION_CANDIDATE", "AUTHORITY_RATIFIED_INTERPRETATION"}:
        raise ScientificAssuranceLineageV17Error("SEMANTIC_ANCHOR_INTERPRETATION_STATUS_INVALID")
    surfaces: set[str] = set()
    loci = anchor.get("semantic_loci")
    if not isinstance(loci, list) or not loci:
        raise ScientificAssuranceLineageV17Error("SEMANTIC_ANCHOR_LOCI_INVALID")
    for locus in loci:
        if not isinstance(locus, Mapping):
            raise ScientificAssuranceLineageV17Error("SEMANTIC_ANCHOR_LOCUS_INVALID")
        locator_type = str(locus.get("locator_type"))
        locator_value = str(locus.get("locator_value"))
        try:
            located = located_value(source, locator_type, locator_value)
        except SemanticCompilerV1Error as exc:
            raise ScientificAssuranceLineageV17Error(f"SEMANTIC_LOCATOR_REBINDING:{exc}") from exc
        if located_value_sha256(located) != locus.get("located_value_sha256"):
            raise ScientificAssuranceLineageV17Error(f"SEMANTIC_LOCATOR_VALUE_REBINDING:{anchor.get('anchor_id')}:{locator_value}")
        key = semantic_surface_key(locator_type, locator_value)
        if key in surfaces:
            raise ScientificAssuranceLineageV17Error(f"SEMANTIC_LOCATOR_DUPLICATE:{key}")
        surfaces.add(key)
    return surfaces


def _verify_coverage(path_text: str, expected_surface: frozenset[str], actual_surface: set[str]) -> Mapping[str, Any]:
    obj = _strict(path_text, "AIFC/semantic-coverage-manifest/v1")
    if obj.get("entailment_question_id") != QUESTION_ID:
        raise ScientificAssuranceLineageV17Error("SEMANTIC_COVERAGE_QUESTION_REBINDING")
    required = obj.get("required_normative_semantic_surface")
    covered = obj.get("covered_semantic_surface")
    if not isinstance(required, list) or not isinstance(covered, list):
        raise ScientificAssuranceLineageV17Error("SEMANTIC_COVERAGE_ARRAY_INVALID")
    try:
        verify_exact_coverage(required, covered)
    except SemanticCompilerV1Error as exc:
        raise ScientificAssuranceLineageV17Error(str(exc)) from exc
    if set(required) != set(expected_surface):
        raise ScientificAssuranceLineageV17Error("NORMATIVE_SEMANTIC_COVERAGE_REQUIRED_SURFACE_REBINDING")
    if set(covered) != actual_surface:
        raise ScientificAssuranceLineageV17Error("NORMATIVE_SEMANTIC_COVERAGE_OMISSION")
    return obj


def _verify_compilation_profile() -> Mapping[str, Any]:
    profile = _strict(COMPILATION_PROFILE_PATH, "AIFC/semantic-compilation-profile/v1")
    compiler_raw = (REPO_ROOT / COMPILER_PATH).read_bytes()
    if git_blob_sha1_bytes(compiler_raw) != COMPILER_BLOB or profile.get("compiler_git_blob_sha1") != COMPILER_BLOB:
        raise ScientificAssuranceLineageV17Error("SEMANTIC_COMPILER_CONTENT_IDENTITY_REBINDING")
    if hashlib.sha256(compiler_raw).hexdigest() != COMPILER_RAW_SHA256 or profile.get("compiler_raw_sha256") != COMPILER_RAW_SHA256:
        raise ScientificAssuranceLineageV17Error("SEMANTIC_COMPILER_RAW_SHA256_REBINDING")
    material = dict(profile)
    claimed = material.pop("profile_content_hash", None)
    actual = domain_hash("AIFC:SEMANTIC-COMPILATION-PROFILE:v1", material)
    if claimed != PROFILE_CONTENT_HASH or actual != PROFILE_CONTENT_HASH:
        raise ScientificAssuranceLineageV17Error("SEMANTIC_COMPILATION_PROFILE_CONTENT_IDENTITY_REBINDING")
    return profile


def _verify_question() -> Mapping[str, Any]:
    question = _strict(QUESTION_PATH, "AIFC/entailment-question/v1")
    actual = entailment_question_id(
        str(question["predecessor_artifact_id"]),
        str(question["predecessor_git_blob_sha1"]),
        str(question["target_profile_id"]),
        str(question["target_profile_git_blob_sha1"]),
        str(question["entailment_method"]),
    )
    if actual != QUESTION_ID or question.get("question_id") != QUESTION_ID:
        raise ScientificAssuranceLineageV17Error("ENTAILMENT_QUESTION_IDENTITY_REBINDING")
    return question


def _verify_formula(path_text: str, expected_role: str, expected_hash: str, expected_anchor_ids: list[str], coverage_id: str, ast: Mapping[str, Any], bindings: Mapping[str, str]) -> Mapping[str, Any]:
    formula = _strict(path_text, "AIFC/semantic-formula/v1")
    if formula.get("formula_role") != expected_role or formula.get("entailment_question_id") != QUESTION_ID:
        raise ScientificAssuranceLineageV17Error("ENTAILMENT_THEOREM_SUBSTITUTION")
    if formula.get("source_semantic_anchor_ids") != expected_anchor_ids:
        raise ScientificAssuranceLineageV17Error("SEMANTIC_ANCHOR_TO_FORMULA_REBINDING")
    if formula.get("semantic_compilation_profile_id") != "AIFC-SEMANTIC-COMPILATION-PROFILE-V1":
        raise ScientificAssuranceLineageV17Error("PREDECESSOR_SEMANTICS_COMPILATION_REBINDING")
    if formula.get("semantic_coverage_manifest_id") != coverage_id:
        raise ScientificAssuranceLineageV17Error("NORMATIVE_SEMANTIC_COVERAGE_FORMULA_REBINDING")
    if formula.get("normalized_formula_ast") != ast or formula.get("atom_bindings") != bindings:
        raise ScientificAssuranceLineageV17Error("ENTAILMENT_THEOREM_SUBSTITUTION")
    actual_hash = formula_content_hash(expected_role, QUESTION_ID, expected_anchor_ids, "AIFC-SEMANTIC-COMPILATION-PROFILE-V1", coverage_id, ast, bindings)
    if actual_hash != expected_hash or formula.get("formula_content_hash") != expected_hash:
        raise ScientificAssuranceLineageV17Error("SEMANTIC_FORMULA_CONTENT_IDENTITY_REBINDING")
    return formula


def _semantic_closure_blocker(anchors: list[Mapping[str, Any]], profile: Mapping[str, Any], predecessor_coverage: Mapping[str, Any], target_coverage: Mapping[str, Any]) -> str | None:
    if any(anchor.get("interpretation_status") != "AUTHORITY_RATIFIED_INTERPRETATION" or anchor.get("authority_lineage_status") != "AUTHORITY_LINEAGE_ESTABLISHED" for anchor in anchors):
        return "BLOCKED_UNAUTHORIZED_INTERPRETATION"
    if profile.get("compiler_authority_status") != "PREDECESSOR_AUTHORITY_ADMITTED_COMPILER" or profile.get("profile_authority_status") != "AUTHORITY_ADMISSIBLE":
        return "BLOCKED_SEMANTIC_COMPILATION_PROFILE"
    if predecessor_coverage.get("coverage_status") != "AUTHORITY_ADMISSIBLE_EXACT_COVERAGE" or target_coverage.get("coverage_status") != "AUTHORITY_ADMISSIBLE_EXACT_COVERAGE":
        return "BLOCKED_SEMANTIC_COVERAGE_AUTHORITY"
    return None


def audit_authoritative_semantic_compilation(predecessor_identity: str, target_profile_identity: str, entailment_question_identity: str) -> SemanticCompilationReport:
    """Production-path audit. No caller-supplied formulas or compiler are accepted."""
    if predecessor_identity != PREDECESSOR_ID or target_profile_identity != TARGET_PROFILE_ID or entailment_question_identity != QUESTION_ID:
        raise ScientificAssuranceLineageV17Error("ENTAILMENT_QUESTION_IDENTITY_SUBSTITUTION")

    _verify_question()
    predecessor = _read_exact_source(PREDECESSOR_PATH, PREDECESSOR_BLOB, PREDECESSOR_COMMIT)
    target = _read_exact_source(TARGET_PROFILE_PATH, TARGET_PROFILE_BLOB, TARGET_PROFILE_COMMIT)

    anchors: list[Mapping[str, Any]] = []
    predecessor_surface: set[str] = set()
    for path in ANCHOR_PATHS:
        anchor = _strict(path, "AIFC/historical-semantic-anchor/v1")
        if anchor.get("source_artifact_id") != PREDECESSOR_ID or anchor.get("source_commit_sha") != PREDECESSOR_COMMIT or anchor.get("source_git_blob_sha1") != PREDECESSOR_BLOB:
            raise ScientificAssuranceLineageV17Error("HISTORICAL_SEMANTIC_ANCHOR_PROVENANCE_REBINDING")
        predecessor_surface |= _verify_anchor(anchor, predecessor)
        anchors.append(anchor)

    target_anchor = _strict(TARGET_ANCHOR_PATH, "AIFC/historical-semantic-anchor/v1")
    if target_anchor.get("source_artifact_id") != TARGET_PROFILE_ID or target_anchor.get("source_commit_sha") != TARGET_PROFILE_COMMIT or target_anchor.get("source_git_blob_sha1") != TARGET_PROFILE_BLOB:
        raise ScientificAssuranceLineageV17Error("TARGET_PROFILE_TO_FORMULA_REBINDING")
    target_surface = _verify_anchor(target_anchor, target)

    predecessor_coverage = _verify_coverage(PREDECESSOR_COVERAGE_PATH, PREDECESSOR_REQUIRED_SURFACE, predecessor_surface)
    target_coverage = _verify_coverage(TARGET_COVERAGE_PATH, TARGET_REQUIRED_SURFACE, target_surface)
    profile = _verify_compilation_profile()

    pred_ast, pred_bindings = compile_predecessor_formula(anchors)
    target_ast, target_bindings = compile_target_formula(target, list(TARGET_REQUIRED_SURFACE))
    pred_ids = [
        "AIFC-SEMANTIC-ANCHOR-AUTHORITY-CLOSED-PROOF-V1",
        "AIFC-SEMANTIC-ANCHOR-GATE-DEFINITION-HISTORICAL-ANCHOR-V1",
        "AIFC-SEMANTIC-ANCHOR-GATE-ATOM-SEMANTIC-IDENTITY-V1",
    ]
    target_ids = ["AIFC-SEMANTIC-ANCHOR-TARGET-LINEAGE-TRANSITION-PROFILE-V1"]
    _verify_formula(PREDECESSOR_FORMULA_PATH, "PREDECESSOR_PREMISE", PREDECESSOR_FORMULA_HASH, pred_ids, "AIFC-SAL-V1.7-PREDECESSOR-SEMANTIC-COVERAGE-V1", pred_ast, pred_bindings)
    _verify_formula(TARGET_FORMULA_PATH, "TARGET_TRANSITION_PROFILE", TARGET_FORMULA_HASH, target_ids, "AIFC-SAL-V1.7-TARGET-SEMANTIC-COVERAGE-V1", target_ast, target_bindings)

    all_anchors = anchors + [target_anchor]
    blocker = _semantic_closure_blocker(all_anchors, profile, predecessor_coverage, target_coverage)
    solver_invocations = 0
    countermodel = None
    if blocker is not None:
        result = "BLOCKED"
    else:
        solver_invocations = 1
        solver_result = finite_propositional_entailment(pred_ast, target_ast)
        result = solver_result.state
        countermodel = solver_result.countermodel

    audit_obj = _strict(AUDIT_PATH, "AIFC/authoritative-semantic-compilation-audit/v1")
    expected = {
        "entailment_question_id": QUESTION_ID,
        "predecessor_formula_content_hash": PREDECESSOR_FORMULA_HASH,
        "target_formula_content_hash": TARGET_FORMULA_HASH,
        "semantic_compilation_profile_authority": "NOT_ESTABLISHED_SUCCESSOR_CANDIDATE",
        "solver_invocation_count": solver_invocations,
        "result": result,
        "blocked_subtype": blocker,
        "countermodel": countermodel,
    }
    for key, value in expected.items():
        if audit_obj.get(key) != value:
            raise ScientificAssuranceLineageV17Error(f"SAL_V17_AUDIT_RESULT_REBINDING:{key}")
    if blocker is not None and solver_invocations != 0:
        raise ScientificAssuranceLineageV17Error("SOLVER_EXECUTION_BEFORE_SEMANTIC_CLOSURE")

    return SemanticCompilationReport(
        question_id=QUESTION_ID,
        historical_semantic_anchor_provenance="PASS_CANDIDATE_PROVENANCE",
        normative_semantic_coverage="PASS_CANDIDATE_EXACT_COVERAGE",
        semantic_compilation_profile_content_identity="PASS",
        semantic_compilation_profile_authority="NOT_ESTABLISHED_SUCCESSOR_CANDIDATE",
        semantic_anchor_to_formula_binding="PASS_DETERMINISTIC_CANDIDATE_DERIVATION",
        predecessor_formula_content_hash=PREDECESSOR_FORMULA_HASH,
        target_formula_content_hash=TARGET_FORMULA_HASH,
        entailment_question_identity_preserved="PASS",
        caller_supplied_normative_formula_forbidden="PASS",
        solver_execution_gated_by_semantic_closure="PASS",
        solver_invocation_count=solver_invocations,
        result=result,
        blocked_subtype=blocker,
        countermodel=countermodel,
    )
