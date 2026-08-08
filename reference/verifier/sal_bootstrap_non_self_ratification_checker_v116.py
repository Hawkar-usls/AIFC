#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from canonical import domain_hash
from scientific_assurance_lineage_v13 import git_blob_sha1_bytes
import bootstrap_non_self_ratification_boundary_v1 as sal

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = "conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v18.json"
PREDECESSOR_REGISTRY_PATH = "conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v17.json"
PREDECESSOR_REGISTRY_BLOB = "ceade8f9e2e1ec1295f3e4b21d36ba1df7ba65ed"
AUDIT_PATH = "conformance/AIFC-BOOTSTRAP-NON-SELF-RATIFICATION-AUDIT-v1.json"
AUDIT_HASH = "991f234732540aa0e21f11c2e64fe8ca1864ba4be52c5a2c81781ea0257cd5fc"
BINDING_PATH = "conformance/AIFC-BOOTSTRAP-NON-SELF-RATIFICATION-IMPLEMENTATION-BINDING-v1.json"
BINDING_ID = "AIFC-SAL-V1.16-BOOTSTRAP-NON-SELF-RATIFICATION-IMPLEMENTATION-BINDING-V1"
BINDING_HASH = "bff319c06c246b5d685f09297f520418783e7ac1d96b1342ac4f2efe5fe985f9"
BINDING_DOMAIN = "AIFC:BOOTSTRAP-NON-SELF-RATIFICATION-IMPLEMENTATION-BINDING:v1"
IMPLEMENTATION_PATH = "reference/verifier/bootstrap_non_self_ratification_boundary_v1.py"
IMPLEMENTATION_BLOB = "9d4aeca0e68cdf7c48a446d51ec5a49253bde4c7"
IMPLEMENTATION_RAW = "2b4d91863f25677ab2b312228e380386b2ebaafba79f72281ae9b9c65ed5dac9"

SCHEMAS = (
    ("AIFC/bootstrap-non-self-ratification-profile/v1", "schemas/bootstrap-non-self-ratification-profile-v1.schema.json", "f63c51b5d7615a361a3f6da485b601255ebdf584", "ce6a251fc8ad0dd9c5096c20cc90801eb3355e71eddb535cb291abe53901311a"),
    ("AIFC/bootstrap-non-self-ratification-audit/v1", "schemas/bootstrap-non-self-ratification-audit-v1.schema.json", "87a304ba3369d0a9e23b4e9e1b7b8e89bc021376", "7142a50d69b0a6e719b68d6a0444805288682911175ee747d9214e06f0254047"),
    ("AIFC/bootstrap-non-self-ratification-implementation-binding/v1", "schemas/bootstrap-non-self-ratification-implementation-binding-v1.schema.json", "10d5393ee653dd427cd3a0efe834dec98f80048a", "0dedef5e1d83a5cf266cfbf643f46f7c54986794e06daab2bdf4684f1b88a8d0"),
    ("AIFC/schema-identity-registry/v18", "schemas/schema-identity-registry-v18.schema.json", "a3a41257238b3ce6d2bedebd1451ba4084d6ec11", "172fa1857a605abb44273a6eb064dae3be03b7efef788ea5ba7f8841fc4fb9cc"),
)


def load(path: str) -> Mapping[str, Any]:
    obj = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(obj, Mapping):
        raise SystemExit("V116_NOT_MAPPING:" + path)
    return obj


def raw256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def binding_hash(obj: Mapping[str, Any]) -> str:
    material = dict(obj)
    material.pop("binding_content_hash", None)
    return domain_hash(BINDING_DOMAIN, material)


def verify_schemas() -> None:
    prev = (ROOT / PREDECESSOR_REGISTRY_PATH).read_bytes()
    if git_blob_sha1_bytes(prev) != PREDECESSOR_REGISTRY_BLOB:
        raise SystemExit("V116_PREDECESSOR_REGISTRY_REBINDING")
    registry = load(REGISTRY_PATH)
    if registry.get("schema") != "AIFC/schema-identity-registry/v18":
        raise SystemExit("V116_REGISTRY_SCHEMA_REBINDING")
    if registry.get("registry_version") != 18:
        raise SystemExit("V116_REGISTRY_VERSION_REBINDING")
    if registry.get("predecessor_registry_path") != PREDECESSOR_REGISTRY_PATH:
        raise SystemExit("V116_REGISTRY_PREDECESSOR_PATH_REBINDING")
    if registry.get("predecessor_registry_git_blob_sha1") != PREDECESSOR_REGISTRY_BLOB:
        raise SystemExit("V116_REGISTRY_PREDECESSOR_BLOB_REBINDING")
    if registry.get("source_observed_at_commit") != sal.SOURCE_MAIN_COMMIT:
        raise SystemExit("V116_REGISTRY_SOURCE_COMMIT_REBINDING")
    rows = registry.get("records")
    if not isinstance(rows, list) or len(rows) != 4:
        raise SystemExit("V116_REGISTRY_COUNT")
    by_id = {row.get("schema_id"): row for row in rows if isinstance(row, Mapping)}
    if set(by_id) != {row[0] for row in SCHEMAS}:
        raise SystemExit("V116_REGISTRY_ID_SET")
    for schema_id, path, blob, raw_hash in SCHEMAS:
        raw = (ROOT / path).read_bytes()
        if git_blob_sha1_bytes(raw) != blob:
            raise SystemExit("V116_SCHEMA_BLOB:" + schema_id)
        if raw256(raw) != raw_hash:
            raise SystemExit("V116_SCHEMA_RAW:" + schema_id)
        schema = json.loads(raw.decode("utf-8"))
        Draft202012Validator.check_schema(schema)
        row = by_id[schema_id]
        if row.get("source_path") != path:
            raise SystemExit("V116_REGISTRY_PATH:" + schema_id)
        if row.get("git_blob_sha1") != blob or row.get("raw_schema_sha256") != raw_hash:
            raise SystemExit("V116_REGISTRY_IDENTITY:" + schema_id)
        if row.get("first_registered_by_registry_version") != 18:
            raise SystemExit("V116_REGISTRY_FIRST_VERSION:" + schema_id)
        if row.get("status") != "REGISTERED_IMMUTABLE_SUCCESSOR_CANDIDATE":
            raise SystemExit("V116_REGISTRY_STATUS:" + schema_id)
    Draft202012Validator(json.loads((ROOT / SCHEMAS[0][1]).read_text())).validate(load(sal.PROFILE_PATH))
    Draft202012Validator(json.loads((ROOT / SCHEMAS[1][1]).read_text())).validate(load(AUDIT_PATH))
    Draft202012Validator(json.loads((ROOT / SCHEMAS[2][1]).read_text())).validate(load(BINDING_PATH))
    Draft202012Validator(json.loads((ROOT / SCHEMAS[3][1]).read_text())).validate(registry)


def verify_binding(obj: Mapping[str, Any]) -> None:
    expected = {
        "schema": "AIFC/bootstrap-non-self-ratification-implementation-binding/v1",
        "binding_id": BINDING_ID,
        "profile_id": sal.PROFILE_ID,
        "profile_content_hash": sal.PROFILE_HASH,
        "implementation_path": IMPLEMENTATION_PATH,
        "implementation_git_blob_sha1": IMPLEMENTATION_BLOB,
        "implementation_raw_sha256": IMPLEMENTATION_RAW,
        "binding_status": "CONFIRMED_DUAL_BOUND_CANDIDATE_EXECUTION_IDENTITY",
        "authority_status": "NOT_ESTABLISHED",
        "binding_content_hash": BINDING_HASH,
    }
    for key, value in expected.items():
        if obj.get(key) != value:
            raise SystemExit("V116_BINDING_REBINDING:" + key)
    if binding_hash(obj) != BINDING_HASH:
        raise SystemExit("V116_BINDING_CONTENT_REBINDING")
    raw = (ROOT / IMPLEMENTATION_PATH).read_bytes()
    if git_blob_sha1_bytes(raw) != IMPLEMENTATION_BLOB:
        raise SystemExit("V116_IMPL_BLOB_REBINDING")
    if raw256(raw) != IMPLEMENTATION_RAW:
        raise SystemExit("V116_IMPL_RAW_REBINDING")


def main() -> None:
    verify_schemas()
    verify_binding(load(BINDING_PATH))
    audit = load(AUDIT_PATH)
    if audit.get("audit_content_hash") != AUDIT_HASH:
        raise SystemExit("V116_AUDIT_HASH_REBINDING")
    report = sal.verify_declared_audit(audit)
    print("SAL_V116_SCHEMA_HEADERS = PASS (4/4)")
    print("SAL_SCHEMA_IDENTITY_REGISTRATION_V18 = PASS (4/4 dual-bound candidate identities)")
    print("BOOTSTRAP_NON_SELF_RATIFICATION_IMPLEMENTATION_IDENTITY = CONFIRMED_DUAL_BOUND")
    print("BOOTSTRAP_NON_SELF_RATIFICATION_IMPLEMENTATION_AUTHORITY = NOT_ESTABLISHED")
    for key, value in report.__dict__.items():
        print(key.upper(), "=", value)
    print("SAL_RELEASE_GATE_122_TO_143 = INHERITED_UNCHANGED")
    print("SAL_V116_RELEASE_GATE_INTEGRATION = HARDENING_LAYER_NO_GATE_RENUMBER")
    print("AUTHORITY_CLOSED_FINITE_INDUCTION = NOT_YET_ESTABLISHED")
    print("IMPLEMENTATION_A_PASS = NOT_ESTABLISHED")
    print("AIFC_V1_FROZEN = FALSE")
    print("PLATFORM_TRUST_PROVEN = FALSE")
    print("SAL_GLOBAL_NOVELTY = NOT_ESTABLISHED")
    print("SCIENTIFIC_ASSURANCE_LINEAGE_V1_16_BOOTSTRAP_NON_SELF_RATIFICATION_BOUNDARY = PASS")


if __name__ == "__main__":
    main()
