#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference" / "verifier"))

import lineage_completeness_basis_authority_v1 as sal  # noqa: E402


SCHEMA_BINDINGS = (
    (
        "AIFC/lineage-completeness-basis-profile/v1",
        "schemas/lineage-completeness-basis-profile-v1.schema.json",
        "3f1a15babe12bcb410402ee007226b5c4f8bf767",
        "96a04d738bb00598da0359dcc9187d83e97e0828ec198354074133616f4a1a43",
        sal.BASIS_PROFILE_PATH,
    ),
    (
        "AIFC/lineage-completeness-authority-audit/v1",
        "schemas/lineage-completeness-authority-audit-v1.schema.json",
        "2c203080b2c1beb508a5087c3e1c41d1d298088f",
        "52f364f6ec8b76a8f09476cb0360807da00783c70380725f5b35e92175ce8b5c",
        sal.AUDIT_PATH,
    ),
    (
        "AIFC/schema-identity-registry/v15",
        "schemas/schema-identity-registry-v15.schema.json",
        "1a0bd21de0106392caa7aafb740107a80d819b5f",
        "0d2af59c091f5b332eaa5eb1f2a04c662636c7b7de0148094df8e70f270acde6",
        "conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v15.json",
    ),
)

REGISTRY_PATH = "conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v15.json"
PREDECESSOR_REGISTRY_PATH = "conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v14.json"
PREDECESSOR_REGISTRY_BLOB = "15ac242e5e27da154e3f9ed08351de859099dec7"


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def raw(path: str) -> bytes:
    return (ROOT / path).read_bytes()


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def raw_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def verify_schema_and_instance(schema_path: str, object_path: str) -> None:
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(load_json(object_path))


def verify_registry() -> None:
    registry = load_json(REGISTRY_PATH)
    require(registry.get("schema") == "AIFC/schema-identity-registry/v15", "V113_REGISTRY_SCHEMA")
    require(registry.get("registry_version") == 15, "V113_REGISTRY_VERSION")
    require(
        registry.get("predecessor_registry_path") == PREDECESSOR_REGISTRY_PATH,
        "V113_REGISTRY_PREDECESSOR_PATH",
    )
    require(
        git_blob_sha1(raw(PREDECESSOR_REGISTRY_PATH)) == PREDECESSOR_REGISTRY_BLOB,
        "V113_REGISTRY_PREDECESSOR_BLOB",
    )
    require(
        registry.get("predecessor_registry_git_blob_sha1") == PREDECESSOR_REGISTRY_BLOB,
        "V113_REGISTRY_PREDECESSOR_DECLARATION",
    )
    require(
        registry.get("source_observed_at_commit") == sal.SOURCE_MAIN_COMMIT,
        "V113_REGISTRY_SOURCE_COMMIT",
    )

    records = registry.get("records")
    require(isinstance(records, list) and len(records) == 3, "V113_REGISTRY_RECORD_COUNT")
    actual = {record.get("schema_id"): record for record in records if isinstance(record, dict)}
    require(len(actual) == 3, "V113_REGISTRY_DUPLICATE_SCHEMA")

    for schema_id, schema_path, expected_blob, expected_raw, _object_path in SCHEMA_BINDINGS:
        data = raw(schema_path)
        require(git_blob_sha1(data) == expected_blob, "V113_SCHEMA_GIT_BLOB_REBINDING:" + schema_id)
        require(raw_sha256(data) == expected_raw, "V113_SCHEMA_RAW_SHA256_REBINDING:" + schema_id)
        record = actual.get(schema_id)
        require(record is not None, "V113_REGISTRY_RECORD_MISSING:" + schema_id)
        require(record.get("dialect") == "https://json-schema.org/draft/2020-12/schema", "V113_REGISTRY_DIALECT")
        require(record.get("source_path") == schema_path, "V113_REGISTRY_SOURCE_PATH:" + schema_id)
        require(record.get("git_blob_sha1") == expected_blob, "V113_REGISTRY_BLOB_DECLARATION:" + schema_id)
        require(record.get("raw_schema_sha256") == expected_raw, "V113_REGISTRY_RAW_DECLARATION:" + schema_id)
        require(record.get("first_registered_by_registry_version") == 15, "V113_REGISTRY_FIRST_VERSION")
        require(
            record.get("status") == "REGISTERED_IMMUTABLE_SUCCESSOR_CANDIDATE",
            "V113_REGISTRY_STATUS",
        )


def main() -> int:
    for _schema_id, schema_path, _blob, _raw, object_path in SCHEMA_BINDINGS:
        verify_schema_and_instance(schema_path, object_path)
    print("SAL_V113_SCHEMA_HEADERS = PASS (3/3)")

    verify_registry()
    print("SAL_SCHEMA_IDENTITY_REGISTRATION_V15 = PASS (3/3 dual-bound candidate identities)")

    basis_profile = load_json(sal.BASIS_PROFILE_PATH)
    audit = load_json(sal.AUDIT_PATH)
    require(sal.profile_content_hash(basis_profile) == sal.BASIS_PROFILE_HASH, "V113_PROFILE_HASH")
    require(sal.audit_content_hash(audit) == sal.AUDIT_HASH, "V113_AUDIT_HASH")

    report = sal.audit_lineage_completeness_basis()
    require(tuple(inspect.signature(sal.audit_lineage_completeness_basis).parameters) == (), "V113_AUTHORITY_INPUT_SURFACE")

    print("LINEAGE_COMPLETENESS_BASIS_PROFILE_CONTENT_IDENTITY = CONFIRMED")
    print("SEED_BASIS_IDENTITY =", report.seed_basis_identity)
    print("SEED_BASIS_PROJECTION_HASH =", report.seed_basis_projection_hash)
    print("OBJECT_RECOGNITION_BASIS_IDENTITY =", report.object_recognition_basis_identity)
    print("OBJECT_RECOGNITION_BASIS_PROJECTION_HASH =", report.object_recognition_basis_projection_hash)
    print("REFERENCE_SEMANTICS_BASIS_IDENTITY =", report.reference_semantics_basis_identity)
    print("REFERENCE_SEMANTICS_BASIS_PROJECTION_HASH =", report.reference_semantics_basis_projection_hash)
    print("LOCAL_REFERENCE_CLOSURE =", report.local_reference_closure)
    print("SEED_COMPLETENESS_AUTHORITY =", report.seed_completeness_authority)
    print("OBJECT_RECOGNITION_GLOBAL_ADEQUACY_AUTHORITY =", report.object_recognition_global_adequacy_authority)
    print("REFERENCE_SEMANTICS_GLOBAL_ADEQUACY_AUTHORITY =", report.reference_semantics_global_adequacy_authority)
    print("NORMATIVE_LINEAGE_COMPLETENESS =", report.normative_lineage_completeness)
    print("LOCAL_FIXED_POINT_TO_GLOBAL_COMPLETENESS_PROMOTION =", report.local_fixed_point_to_global_completeness_promotion)
    print("EXACT_SEED_IDENTITY_TO_SEED_COMPLETENESS_PROMOTION =", report.exact_seed_identity_to_seed_completeness_promotion)
    print("EXACT_PROFILE_IDENTITY_TO_GLOBAL_ADEQUACY_PROMOTION =", report.exact_profile_identity_to_global_adequacy_promotion)
    print("SUCCESSOR_DEFINED_COMPLETENESS_AUTHORITY =", report.successor_defined_completeness_authority)
    print("COMPLETENESS_BASIS_AUTHORITY_INPUT_SURFACE =", report.completeness_basis_authority_input_surface)
    print("GLOBAL_LINEAGE_SEED_COMPLETENESS =", report.global_lineage_seed_completeness)
    print("OBJECT_INDEX_PROFILE_GLOBAL_ADEQUACY =", report.object_index_profile_global_adequacy)
    print("GLOBAL_REPOSITORY_OBJECT_UNIVERSE_COMPLETENESS =", report.global_repository_object_universe_completeness)
    print("LINEAGE_SEMANTIC_RELATION_UNIVERSE_COMPLETENESS =", report.lineage_semantic_relation_universe_completeness)
    print("SAL_RELEASE_GATE_122_TO_143 = INHERITED_UNCHANGED")
    print("SAL_V113_RELEASE_GATE_INTEGRATION = HARDENING_LAYER_NO_GATE_RENUMBER")
    print("DERIVED_SEMANTIC_AUTHORITY =", report.derived_semantic_authority)
    print("SOLVER_INVOCATION_COUNT =", report.solver_invocation_count)
    print("AUTHORITY_CLOSED_FINITE_INDUCTION = NOT_YET_ESTABLISHED")
    print("IMPLEMENTATION_A_PASS = NOT_ESTABLISHED")
    print("AIFC_V1_FROZEN = FALSE")
    print("PLATFORM_TRUST_PROVEN = FALSE")
    print("SAL_GLOBAL_NOVELTY = NOT_ESTABLISHED")
    print("SCIENTIFIC_ASSURANCE_LINEAGE_V1_13_COMPLETENESS_BASIS_AUTHORITY_BOUNDARY = PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
