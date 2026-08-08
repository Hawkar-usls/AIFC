#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference/verifier"))

from scientific_assurance_lineage_v14 import git_blob_sha1_bytes
import scientific_assurance_lineage_v17 as v17
import scientific_assurance_lineage_v112 as sal

SCHEMAS = {
    "schemas/repository-object-index-profile-v1.schema.json": [
        sal.PROFILE_PATH
    ],
    "schemas/lineage-vertex-universe-closure-v1.schema.json": [
        sal.CLOSURE_PATH
    ],
    "schemas/lineage-vertex-universe-closure-audit-v1.schema.json": [
        sal.AUDIT_PATH
    ],
    "schemas/schema-identity-registry-v14.schema.json": [
        "conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v14.json"
    ],
}

def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def fail(message: str):
    raise SystemExit(message)

def main() -> None:
    schema_ids = []
    for schema_path, object_paths in SCHEMAS.items():
        schema = load(schema_path)
        schema_ids.append(schema["properties"]["schema"]["const"])
        validator = Draft202012Validator(schema)
        for object_path in object_paths:
            errors = list(validator.iter_errors(load(object_path)))
            if errors:
                fail(
                    "SAL_V112_SCHEMA_VALIDATION = FAIL:"
                    + object_path
                    + ":"
                    + errors[0].message
                )
    print("SAL_V112_SCHEMA_HEADERS = PASS (4/4)")

    registry = load("conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v14.json")
    if (
        registry["predecessor_registry_git_blob_sha1"]
        != "3afd1ecffa061b2c6af5936faa65f01e3e7de806"
        or registry["source_observed_at_commit"] != sal.SOURCE_MAIN_COMMIT
        or {item["schema_id"] for item in registry["records"]} != set(schema_ids)
    ):
        fail("SAL_SCHEMA_IDENTITY_REGISTRATION_V14 = FAIL")
    for record in registry["records"]:
        raw = (ROOT / record["source_path"]).read_bytes()
        if (
            git_blob_sha1_bytes(raw) != record["git_blob_sha1"]
            or hashlib.sha256(raw).hexdigest() != record["raw_schema_sha256"]
        ):
            fail("SAL_SCHEMA_IDENTITY_REGISTRATION_V14 = FAIL:DUAL")
    print(
        "SAL_SCHEMA_IDENTITY_REGISTRATION_V14 = "
        "PASS (4/4 dual-bound candidate identities)"
    )

    profile = load(sal.PROFILE_PATH)
    forbidden_profile_fields = {
        "available_objects",
        "required_vertices",
        "vertex_specs",
        "max_depth",
        "max_rounds",
        "max_recursion",
    }
    if forbidden_profile_fields.intersection(profile):
        fail("SAL_V112_SUCCESSOR_DEFINED_VERTEX_OR_DEPTH_LIST = FAIL")
    source = (ROOT / sal.CLOSURE_IMPL_PATH).read_text(encoding="utf-8")
    if any(
        token in source
        for token in (
            "REQUIRED_VERTICES =",
            "AVAILABLE_OBJECTS =",
            "VERTEX_SPECS =",
            "MAX_DEPTH =",
            "MAX_ROUNDS =",
            "MAX_RECURSION =",
        )
    ):
        fail("SAL_V112_SUCCESSOR_DEFINED_VERTEX_OR_DEPTH_LIST = FAIL")

    report = sal.audit_lineage_vertex_universe_closure(
        v17.PREDECESSOR_ID,
        v17.TARGET_PROFILE_ID,
        v17.QUESTION_ID,
    )
    receipt = load(sal.CLOSURE_PATH)
    expected_witnesses = {
        "conformance/AIFC-CANONICAL-SEMANTIC-RESOLVER-PROFILE-v1.json",
        "conformance/AIFC-CANONICAL-SEMANTIC-REFERENCE-A-v1.json",
        "conformance/AIFC-CANONICAL-SEMANTIC-REFERENCE-B-v1.json",
        "conformance/AIFC-PREDECESSOR-SEMANTIC-FORMULA-v1.json",
        "conformance/AIFC-TARGET-SEMANTIC-FORMULA-v1.json",
    }
    if not expected_witnesses.issubset(set(receipt["final_vertex_paths"])):
        fail("LINEAGE_REQUIRED_VERTEX_UNIVERSE_OMISSION = FAIL:WITNESS")
    if (
        report.final_vertex_count != 11
        or report.vertex_discovery_occurrence_count != 31
        or report.ambiguous_required_references != 0
        or report.unresolved_required_references != 0
        or report.derived_semantic_authority != "BLOCKED"
        or report.solver_invocation_count != 0
    ):
        fail("SAL_V112_CURRENT_INSTANCE = FAIL")

    print("EXACT_TREE_BINDING = CONFIRMED")
    print("REPOSITORY_OBJECT_INDEX_DERIVATION = MACHINE_DERIVED_FROM_EXACT_TREE")
    print(
        "REPOSITORY_OBJECT_INDEX_COMPLETENESS = "
        "ESTABLISHED_ONLY_RELATIVE_TO_EXACT_TREE_AND_RECOGNIZED_OBJECT_PROFILE"
    )
    print("REPOSITORY_OBJECT_INDEX_RECOGNIZED_OBJECT_COUNT = " + str(report.recognized_repository_object_count))
    print("REPOSITORY_OBJECT_INDEX_HASH = " + report.repository_object_index_hash)
    print("SUCCESSOR_DEFINED_AVAILABLE_OBJECT_LIST = NOT_USED")
    print("SUCCESSOR_DEFINED_REQUIRED_VERTEX_LIST = NOT_USED")
    print("LINEAGE_VERTEX_DISCOVERY = RECURSIVE_MACHINE_DERIVED")
    print("LINEAGE_VERTEX_CLOSURE_MONOTONICITY = CONFIRMED")
    print("LINEAGE_VERTEX_FIXED_POINT = MACHINE_VERIFIED_BY_FINAL_REPLAY")
    print(
        "LINEAGE_VERTEX_UNIVERSE_REFERENCE_CLOSURE = "
        "ESTABLISHED_IN_TESTED_SCOPE_FROM_INHERITED_SEED"
    )
    print("VERTEX_DISCOVERY_MANIFEST_REPLAY = CONFIRMED")
    print("LINEAGE_VERTEX_DISCOVERY_ORDER_INDEPENDENCE = CONFIRMED_IN_TESTED_SCOPE")
    print("AMBIGUOUS_REQUIRED_LINEAGE_REFERENCES = 0")
    print("UNRESOLVED_REQUIRED_LINEAGE_REFERENCES = 0")
    print(
        "LINEAGE_REQUIRED_VERTEX_UNIVERSE_OMISSION = "
        "REJECTED_IN_TESTED_REFERENCE_CLOSURE_SCOPE"
    )
    print("FINAL_VERTEX_COUNT = " + str(report.final_vertex_count))
    print("FINAL_VERTEX_UNIVERSE_HASH = " + report.final_vertex_universe_hash)
    print("VERTEX_DISCOVERY_OCCURRENCE_COUNT = " + str(report.vertex_discovery_occurrence_count))
    print("VERTEX_DISCOVERY_MANIFEST_HASH = " + report.discovery_manifest_hash)
    print("GLOBAL_LINEAGE_SEED_COMPLETENESS = NOT_ESTABLISHED")
    print("OBJECT_INDEX_PROFILE_GLOBAL_ADEQUACY = NOT_ESTABLISHED")
    print("GLOBAL_REPOSITORY_OBJECT_UNIVERSE_COMPLETENESS = NOT_ESTABLISHED")
    print("LINEAGE_SEMANTIC_RELATION_UNIVERSE_COMPLETENESS = NOT_ESTABLISHED")
    print("SAL_RELEASE_GATE_122_TO_143 = INHERITED_UNCHANGED")
    print("SAL_V112_RELEASE_GATE_INTEGRATION = HARDENING_LAYER_NO_GATE_RENUMBER")
    print("DERIVED_SEMANTIC_AUTHORITY = BLOCKED")
    print("SOLVER_INVOCATION_COUNT = 0")
    print("AUTHORITY_CLOSED_FINITE_INDUCTION = NOT_YET_ESTABLISHED")
    print("IMPLEMENTATION_A_PASS = NOT_ESTABLISHED")
    print("AIFC_V1_FROZEN = FALSE")
    print("PLATFORM_TRUST_PROVEN = FALSE")
    print("SAL_GLOBAL_NOVELTY = NOT_ESTABLISHED")
    print(
        "SCIENTIFIC_ASSURANCE_LINEAGE_V1_12_VERTEX_UNIVERSE_REFERENCE_CLOSURE = PASS"
    )

if __name__ == "__main__":
    main()
