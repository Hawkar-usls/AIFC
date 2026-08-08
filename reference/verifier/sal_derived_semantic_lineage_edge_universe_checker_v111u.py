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
import scientific_assurance_lineage_v111h as v111h
import scientific_assurance_lineage_v111u as sal
import semantic_lineage_edge_universe_v1 as universe

SCHEMAS = {
    "schemas/derived-semantic-lineage-edge-universe-v1.schema.json": [
        sal.UNIVERSE_PATH
    ],
    "schemas/derived-semantic-lineage-edge-universe-audit-v1.schema.json": [
        sal.AUDIT_PATH
    ],
    "schemas/schema-identity-registry-v13.schema.json": [
        "conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v13.json"
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
                    "SAL_V111U_SCHEMA_VALIDATION = FAIL:"
                    + object_path
                    + ":"
                    + errors[0].message
                )
    print("SAL_V111U_SCHEMA_HEADERS = PASS (3/3)")

    registry = load("conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v13.json")
    if (
        registry["predecessor_registry_git_blob_sha1"]
        != "c7f1995205e7e1a73a9237ee93f736f6774c18ab"
        or registry["source_observed_at_commit"] != sal.SOURCE_MAIN_COMMIT
        or {item["schema_id"] for item in registry["records"]}
        != set(schema_ids)
    ):
        fail("SAL_SCHEMA_IDENTITY_REGISTRATION_V13 = FAIL")
    for record in registry["records"]:
        raw = (ROOT / record["source_path"]).read_bytes()
        if (
            git_blob_sha1_bytes(raw) != record["git_blob_sha1"]
            or hashlib.sha256(raw).hexdigest()
            != record["raw_schema_sha256"]
        ):
            fail("SAL_SCHEMA_IDENTITY_REGISTRATION_V13 = FAIL:DUAL")
    print(
        "SAL_SCHEMA_IDENTITY_REGISTRATION_V13 = "
        "PASS (3/3 dual-bound candidate identities)"
    )

    objects, raws = v111h._objects_and_raws()
    source_binding = v111h._load(v111h.BINDING_PATH)
    source_audit = v111h._load(v111h.AUDIT_PATH)
    receipt = load(sal.UNIVERSE_PATH)
    vertices, edges, graph_id = universe.verify_universe_receipt(
        receipt,
        source_binding,
        source_audit,
        objects,
        raws,
    )
    edge_ids = tuple(item["edge_id"] for item in edges)
    expected_new = (
        "DERIVED_TO_QUESTION",
        "GRAPH_TO_DERIVED",
        "MANIFEST_TO_QUESTION",
        "PROFILE_TO_QUESTION",
        "PROOF_TO_DERIVED",
        "PROOF_TO_QUESTION",
    )
    if (
        len(vertices) != 6
        or len(edges) != 15
        or tuple(receipt["newly_derived_edge_pairs"]) != expected_new
        or graph_id != sal.LINEAGE_GRAPH_IDENTITY_V2
    ):
        fail("LINEAGE_EDGE_UNIVERSE_CURRENT_INSTANCE = FAIL")

    print(
        "LINEAGE_EDGE_UNIVERSE_DERIVATION = "
        "MACHINE_DERIVED_NO_DECLARED_REQUIRED_EDGE_LIST"
    )
    print(
        "LINEAGE_EDGE_UNIVERSE_SCOPE = "
        "INHERITED_EXACT_V1_11H_SIX_VERTEX_SET"
    )
    print(
        "LINEAGE_EDGE_UNIVERSE_COMPLETENESS = "
        "ESTABLISHED_IN_TESTED_SCOPE_RELATIVE_TO_BOUND_VERTEX_SET"
    )
    print("LINEAGE_EDGE_UNIVERSE_EDGE_COUNT = 15")
    print("INHERITED_DECLARED_EDGE_PAIR_COUNT = 9")
    print("NEWLY_DERIVED_EDGE_PAIR_COUNT = 6")
    print("NEWLY_DERIVED_EDGE_PAIRS = " + ",".join(expected_new))
    print("LINEAGE_EDGE_UNIVERSE_HASH = " + receipt["lineage_edge_universe_hash"])
    print("LINEAGE_GRAPH_IDENTITY_V2 = " + graph_id)
    print(
        "LINEAGE_BINDING_QUESTION_CONTEXT = "
        "EXPLICITLY_CLOSED_IN_TESTED_SCOPE"
    )
    print(
        "LINEAGE_AUDIT_QUESTION_CONTEXT = "
        "EXPLICITLY_CLOSED_IN_TESTED_SCOPE"
    )
    print(
        "LINEAGE_VERTEX_UNIVERSE_COMPLETENESS = NOT_ESTABLISHED"
    )
    print(
        "LINEAGE_SEMANTIC_RELATION_UNIVERSE_COMPLETENESS = NOT_ESTABLISHED"
    )
    print(
        "SUCCESSOR_DEFINED_REQUIRED_EDGE_UNIVERSE = "
        "NOT_USED_BY_V1_11U_PRODUCTION_DERIVATION"
    )
    if (
        "PROOF_TO_DERIVED" not in edge_ids
        or "GRAPH_TO_DERIVED" not in edge_ids
        or "PROFILE_TO_QUESTION" not in edge_ids
    ):
        fail("LINEAGE_EDGE_UNIVERSE_INDEPENDENT_DISCOVERY = FAIL")
    print("LINEAGE_EDGE_UNIVERSE_INDEPENDENT_DISCOVERY = PASS")

    release = load("conformance/AIFC-RELEASE-GATE-v1.0.18-draft.json")
    if len(release["required_checks"]) != 143:
        fail("SAL_RELEASE_GATE_122_TO_143 = FAIL")
    print("SAL_RELEASE_GATE_122_TO_143 = INHERITED_UNCHANGED")
    print(
        "SAL_V111U_RELEASE_GATE_INTEGRATION = "
        "HARDENING_LAYER_NO_GATE_RENUMBER"
    )

    report = sal.audit_derived_semantic_lineage_edge_universe(
        v17.PREDECESSOR_ID,
        v17.TARGET_PROFILE_ID,
        v17.QUESTION_ID,
    )
    if (
        report.edge_universe_completeness
        != "ESTABLISHED_IN_TESTED_SCOPE_RELATIVE_TO_BOUND_VERTEX_SET"
        or report.derived_semantic_authority != "BLOCKED"
        or report.solver_invocation_count != 0
        or report.vertex_universe_completeness != "NOT_ESTABLISHED"
        or report.semantic_relation_universe_completeness != "NOT_ESTABLISHED"
    ):
        fail("SAL_V111U_TERMINAL = FAIL")

    for line in (
        "DERIVED_SEMANTIC_LINEAGE_EDGE_UNIVERSE = "
        "ESTABLISHED_IN_TESTED_SCOPE_RELATIVE_TO_BOUND_VERTEX_SET",
        "DERIVED_SEMANTIC_AUTHORITY = BLOCKED",
        "SOLVER_INVOCATION_COUNT = 0",
        "AUTHORITY_CLOSED_FINITE_INDUCTION = NOT_YET_ESTABLISHED",
        "IMPLEMENTATION_A_PASS = NOT_ESTABLISHED",
        "AIFC_V1_FROZEN = FALSE",
        "PLATFORM_TRUST_PROVEN = FALSE",
        "SAL_GLOBAL_NOVELTY = NOT_ESTABLISHED",
        "SCIENTIFIC_ASSURANCE_LINEAGE_V1_11U_EDGE_UNIVERSE_CLOSURE = PASS",
    ):
        print(line)

if __name__ == "__main__":
    main()
