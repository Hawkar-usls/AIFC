#!/usr/bin/env python3
"""Deterministic candidate semantic compiler for SAL v1.7.

Identity of this implementation is content-bound by the semantic compilation
profile. Authority is deliberately separate: this module MUST NOT by itself make
its interpretations or compiled formulas normative.
"""
from __future__ import annotations

import hashlib
from typing import Any, Mapping, Sequence

from canonical import canonical_json_bytes, domain_hash

FORMULA_DOMAIN = "AIFC:SEMANTIC-FORMULA:v1"
QUESTION_DOMAIN = "AIFC:ENTAILMENT-QUESTION:v1"


class SemanticCompilerV1Error(ValueError):
    pass


def located_value(document: Mapping[str, Any], locator_type: str, locator_value: str) -> Any:
    if locator_type == "REQUIRED_CHECK_ID":
        rows = document.get("required_checks")
        if not isinstance(rows, list):
            raise SemanticCompilerV1Error("SEMANTIC_LOCATOR_REQUIRED_CHECKS_NOT_ARRAY")
        matches = [row for row in rows if isinstance(row, Mapping) and row.get("id") == locator_value]
        if len(matches) != 1:
            raise SemanticCompilerV1Error(f"SEMANTIC_LOCATOR_REQUIRED_CHECK_CARDINALITY:{locator_value}:{len(matches)}")
        return matches[0]
    if locator_type == "FORBIDDEN_SHORTCUT_EXACT":
        rows = document.get("forbidden_shortcuts")
        if not isinstance(rows, list):
            raise SemanticCompilerV1Error("SEMANTIC_LOCATOR_FORBIDDEN_SHORTCUTS_NOT_ARRAY")
        matches = [row for row in rows if row == locator_value]
        if len(matches) != 1:
            raise SemanticCompilerV1Error(f"SEMANTIC_LOCATOR_FORBIDDEN_SHORTCUT_CARDINALITY:{len(matches)}")
        return matches[0]
    if locator_type == "PROFILE_FIELD":
        current: Any = document
        for part in locator_value.split("."):
            if isinstance(current, Mapping):
                if part not in current:
                    raise SemanticCompilerV1Error(f"SEMANTIC_LOCATOR_PROFILE_FIELD_MISSING:{locator_value}")
                current = current[part]
            elif isinstance(current, list) and part.isdigit():
                index = int(part)
                if index < 0 or index >= len(current):
                    raise SemanticCompilerV1Error(f"SEMANTIC_LOCATOR_PROFILE_INDEX:{locator_value}")
                current = current[index]
            else:
                raise SemanticCompilerV1Error(f"SEMANTIC_LOCATOR_PROFILE_TRAVERSAL:{locator_value}")
        return current
    raise SemanticCompilerV1Error(f"SEMANTIC_LOCATOR_TYPE_UNSUPPORTED:{locator_type}")


def located_value_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def semantic_surface_key(locator_type: str, locator_value: str) -> str:
    return f"{locator_type}:{locator_value}"


def verify_exact_coverage(required: Sequence[str], covered: Sequence[str]) -> None:
    required_set = set(required)
    covered_set = set(covered)
    if len(required_set) != len(required) or len(covered_set) != len(covered):
        raise SemanticCompilerV1Error("NORMATIVE_SEMANTIC_COVERAGE_DUPLICATE")
    if covered_set != required_set:
        missing = sorted(required_set - covered_set)
        extra = sorted(covered_set - required_set)
        raise SemanticCompilerV1Error(f"NORMATIVE_SEMANTIC_COVERAGE_OMISSION:missing={missing}:extra={extra}")


def atom_id(anchor_id: str, locator_type: str, locator_value: str) -> str:
    material = {
        "anchor_id": anchor_id,
        "locator_type": locator_type,
        "locator_value": locator_value,
    }
    return "SEMANTIC_ATOM_" + domain_hash("AIFC:SEMANTIC-ATOM:v1", material)


def compile_predecessor_formula(anchors: Sequence[Mapping[str, Any]]) -> tuple[Mapping[str, Any], Mapping[str, str]]:
    atoms: list[Mapping[str, Any]] = []
    bindings: dict[str, str] = {}
    for anchor in sorted(anchors, key=lambda row: str(row["anchor_id"])):
        for locus in sorted(anchor["semantic_loci"], key=lambda row: (str(row["locator_type"]), str(row["locator_value"]))):
            atom = atom_id(str(anchor["anchor_id"]), str(locus["locator_type"]), str(locus["locator_value"]))
            atoms.append({"op": "ATOM", "id": atom})
            bindings[atom] = semantic_surface_key(str(locus["locator_type"]), str(locus["locator_value"]))
    if not atoms:
        raise SemanticCompilerV1Error("PREDECESSOR_FORMULA_EMPTY")
    return {"op": "AND", "args": atoms}, bindings


def compile_target_formula(target_profile: Mapping[str, Any], required_surface: Sequence[str]) -> tuple[Mapping[str, Any], Mapping[str, str]]:
    atoms: list[Mapping[str, Any]] = []
    bindings: dict[str, str] = {}
    for surface in sorted(required_surface):
        if not surface.startswith("PROFILE_FIELD:"):
            raise SemanticCompilerV1Error(f"TARGET_SURFACE_LOCATOR_INVALID:{surface}")
        locator = surface.split(":", 1)[1]
        value = located_value(target_profile, "PROFILE_FIELD", locator)
        material = {"profile_id": target_profile.get("profile_id"), "locator": locator, "value": value}
        atom = "TARGET_ATOM_" + domain_hash("AIFC:TARGET-SEMANTIC-ATOM:v1", material)
        atoms.append({"op": "ATOM", "id": atom})
        bindings[atom] = surface
    if not atoms:
        raise SemanticCompilerV1Error("TARGET_FORMULA_EMPTY")
    return {"op": "AND", "args": atoms}, bindings


def formula_content_hash(formula_role: str, question_id: str, source_anchor_ids: Sequence[str], profile_id: str, coverage_id: str, ast: Mapping[str, Any], atom_bindings: Mapping[str, str]) -> str:
    material = {
        "schema": "AIFC/semantic-formula/v1",
        "formula_role": formula_role,
        "entailment_question_id": question_id,
        "source_semantic_anchor_ids": list(source_anchor_ids),
        "semantic_compilation_profile_id": profile_id,
        "semantic_coverage_manifest_id": coverage_id,
        "normalized_formula_ast": ast,
        "atom_bindings": dict(atom_bindings),
        "derivation_status": "DETERMINISTIC_CANDIDATE_DERIVATION",
    }
    return domain_hash(FORMULA_DOMAIN, material)


def entailment_question_id(predecessor_artifact_id: str, predecessor_git_blob_sha1: str, target_profile_id: str, target_profile_git_blob_sha1: str, entailment_method: str) -> str:
    material = {
        "schema": "AIFC/entailment-question/v1",
        "predecessor_artifact_id": predecessor_artifact_id,
        "predecessor_git_blob_sha1": predecessor_git_blob_sha1,
        "target_profile_id": target_profile_id,
        "target_profile_git_blob_sha1": target_profile_git_blob_sha1,
        "entailment_method": entailment_method,
    }
    return domain_hash(QUESTION_DOMAIN, material)
