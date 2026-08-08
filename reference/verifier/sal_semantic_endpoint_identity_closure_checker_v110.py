#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

from scientific_assurance_lineage_v14 import git_blob_sha1_bytes  # noqa: E402
import scientific_assurance_lineage_v17 as v17  # noqa: E402
import scientific_assurance_lineage_v18 as v18  # noqa: E402
import scientific_assurance_lineage_v110 as sal  # noqa: E402
import semantic_bridge_endpoint_identity_v1 as endpoint  # noqa: E402

REQUIRED_FILES = [
    "schemas/bridge-derived-semantic-object-v1.schema.json",
    "schemas/semantic-bridge-axiom-v2.schema.json",
    "schemas/semantic-bridge-endpoint-identity-profile-v1.schema.json",
    "schemas/semantic-bridge-theory-v3.schema.json",
    "schemas/entailment-method-capacity-extension-v1.schema.json",
    "schemas/semantic-endpoint-identity-audit-v1.schema.json",
    "schemas/semantic-bridge-execution-profile-v2.schema.json",
    "schemas/schema-identity-registry-v10.schema.json",
    "conformance/AIFC-SEMANTIC-BRIDGE-ENDPOINT-IDENTITY-PROFILE-v1.json",
    "conformance/AIFC-SEMANTIC-BRIDGE-THEORY-v3.json",
    "conformance/AIFC-SEMANTIC-BRIDGE-EXECUTION-PROFILE-v2.json",
    "conformance/AIFC-ENTAILMENT-METHOD-CAPACITY-EXTENSION-v1.json",
    "conformance/AIFC-SEMANTIC-ENDPOINT-IDENTITY-AUDIT-v1.json",
    "conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v10.json",
    "conformance/AIFC-RELEASE-GATE-v1.0.17-draft.json",
    "reference/verifier/semantic_bridge_endpoint_identity_v1.py",
    "reference/verifier/scientific_assurance_lineage_v110.py",
    "reference/verifier/sal_semantic_endpoint_identity_closure_checker_v110.py",
    "reference/tests/test_sal_semantic_endpoint_identity_closure_v110.py",
    ".github/workflows/sal-semantic-endpoint-identity-v110.yml",
    "spec/SCIENTIFIC-ASSURANCE-LINEAGE-v0.7.md",
]

SCHEMA_PATHS = REQUIRED_FILES[:8]
NEW_GATES = [
    "BRIDGE_ENDPOINT_SEMANTIC_IDENTITY",
    "BRIDGE_ATOM_ROLE_IDENTITY_BINDING",
    "BRIDGE_DERIVED_ATOM_PROVENANCE",
    "SEMANTIC_AUTHORITY_STATUS_LINEAGE",
    "ENTAILMENT_METHOD_CONSERVATIVE_CAPACITY_EXTENSION",
    "SAME_QUESTION_METHOD_SEMANTICS_PRESERVATION",
    "BRIDGE_AWARE_EXTENDED_CAPACITY",
]


def fail(msg: str) -> None:
    raise SystemExit(msg)


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def _canonical_bindings() -> tuple[dict[str, str], dict[str, str]]:
    return (
        _load(v17.PREDECESSOR_FORMULA_PATH)["atom_bindings"],
        _load(v17.TARGET_FORMULA_PATH)["atom_bindings"],
    )


def _make_axiom(atom: str, role: str, identity: str) -> dict:
    axiom = {
        "schema": "AIFC/semantic-bridge-axiom/v2",
        "axiom_id": "CHECKER-TEST-AXIOM",
        "entailment_question_id": v17.QUESTION_ID,
        "logical_fragment": "FINITE_CLASSICAL_PROPOSITIONAL_V1",
        "endpoint_identity_profile_id": endpoint.ENDPOINT_PROFILE_ID,
        "normalized_formula_ast": {"op": "ATOM", "id": atom},
        "atom_bindings": {atom: {"semantic_role": role, "semantic_identity": identity}},
        "axiom_authority_status": "SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE",
        "authority_lineage_ref": None,
    }
    axiom["axiom_content_hash"] = endpoint.bridge_axiom_v2_content_hash(axiom)
    return axiom


def main() -> None:
    missing = [p for p in REQUIRED_FILES if not (ROOT / p).is_file()]
    if missing:
        fail("SAL_V110_REQUIRED_FILES = FAIL " + repr(missing))
    print(f"SAL_V110_REQUIRED_FILES = PASS ({len(REQUIRED_FILES)}/{len(REQUIRED_FILES)})")

    schema_ids = []
    for path in SCHEMA_PATHS:
        obj = _load(path)
        if obj.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            fail(f"SAL_V110_SCHEMA_HEADER = FAIL:{path}")
        sid = obj.get("properties", {}).get("schema", {}).get("const")
        if not isinstance(sid, str):
            fail(f"SAL_V110_SCHEMA_PROTOCOL_ID = FAIL:{path}")
        schema_ids.append(sid)
    print(f"SAL_V110_SCHEMA_HEADERS = PASS ({len(SCHEMA_PATHS)}/{len(SCHEMA_PATHS)})")

    registry = v17._strict(
        "conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v10.json",
        "AIFC/schema-identity-registry/v10",
    )
    if registry.get("predecessor_registry_git_blob_sha1") != "4aab16f170e25be77db82a41e0f024e3622d26f4":
        fail("SAL_SCHEMA_IDENTITY_REGISTRATION_V10 = FAIL:PREDECESSOR")
    records = registry.get("records")
    if not isinstance(records, list) or len(records) != len(SCHEMA_PATHS):
        fail("SAL_SCHEMA_IDENTITY_REGISTRATION_V10 = FAIL:COUNT")
    if {r.get("schema_id") for r in records} != set(schema_ids):
        fail("SAL_SCHEMA_IDENTITY_REGISTRATION_V10 = FAIL:SET")
    for record in records:
        raw = (ROOT / record["source_path"]).read_bytes()
        if git_blob_sha1_bytes(raw) != record.get("git_blob_sha1"):
            fail("SAL_SCHEMA_IDENTITY_REGISTRATION_V10 = FAIL:GIT")
        if hashlib.sha256(raw).hexdigest() != record.get("raw_schema_sha256"):
            fail("SAL_SCHEMA_IDENTITY_REGISTRATION_V10 = FAIL:RAW")
        if record.get("status") != "REGISTERED_IMMUTABLE_SUCCESSOR_CANDIDATE":
            fail("SAL_SCHEMA_IDENTITY_REGISTRATION_V10 = FAIL:STATUS")
    print(f"SAL_SCHEMA_IDENTITY_REGISTRATION_V10 = PASS ({len(records)}/{len(records)} dual-bound candidate identities)")

    pred, target = _canonical_bindings()
    p_atom = next(iter(pred))
    t_atom = next(iter(target))

    valid = _make_axiom(p_atom, "PREDECESSOR_ATOM", pred[p_atom])
    endpoint.verify_bridge_axiom_endpoint_identity(
        valid,
        expected_question_id=v17.QUESTION_ID,
        predecessor_bindings=pred,
        target_bindings=target,
        derived_object_resolver=lambda ref: {},
        require_authority=False,
    )
    print("BRIDGE_ENDPOINT_SEMANTIC_IDENTITY = PASS_EXACT_CANONICAL_ENDPOINT_LOOKUP_CANDIDATE")

    wrong_identity = _make_axiom(p_atom, "PREDECESSOR_ATOM", "WRONG")
    try:
        endpoint.verify_bridge_axiom_endpoint_identity(
            wrong_identity,
            expected_question_id=v17.QUESTION_ID,
            predecessor_bindings=pred,
            target_bindings=target,
            derived_object_resolver=lambda ref: {},
            require_authority=False,
        )
    except endpoint.SemanticBridgeEndpointIdentityV1Error as exc:
        if "BRIDGE_ATOM_SEMANTIC_IDENTITY_REBINDING" not in str(exc):
            raise
    else:
        fail("BRIDGE_ATOM_SEMANTIC_IDENTITY_REBINDING = NOT_REJECTED")
    print("BRIDGE_ATOM_SEMANTIC_IDENTITY_REBINDING = REJECTED")

    wrong_role = _make_axiom(p_atom, "TARGET_ATOM", pred[p_atom])
    try:
        endpoint.verify_bridge_axiom_endpoint_identity(
            wrong_role,
            expected_question_id=v17.QUESTION_ID,
            predecessor_bindings=pred,
            target_bindings=target,
            derived_object_resolver=lambda ref: {},
            require_authority=False,
        )
    except endpoint.SemanticBridgeEndpointIdentityV1Error as exc:
        if "BRIDGE_ATOM_ROLE_REBINDING" not in str(exc):
            raise
    else:
        fail("BRIDGE_ATOM_ROLE_REBINDING = NOT_REJECTED")
    print("BRIDGE_ATOM_ROLE_REBINDING = REJECTED")
    print("BRIDGE_ATOM_ROLE_IDENTITY_BINDING = PASS_STRICT_CANONICAL_ROLE_LOOKUP_CANDIDATE")

    collision = _make_axiom(p_atom, "BRIDGE_DERIVED_ATOM", "DERIVED:COLLISION")
    collision["atom_bindings"][p_atom]["derived_semantic_object_ref"] = {
        "derived_semantic_object_id": "TEST",
        "source_path": "conformance/test.json",
        "git_blob_sha1": "0" * 40,
        "raw_sha256": "0" * 64,
        "derivation_content_hash": "0" * 64,
    }
    collision["axiom_content_hash"] = endpoint.bridge_axiom_v2_content_hash(collision)
    try:
        endpoint.verify_bridge_axiom_endpoint_identity(
            collision,
            expected_question_id=v17.QUESTION_ID,
            predecessor_bindings=pred,
            target_bindings=target,
            derived_object_resolver=lambda ref: {},
            require_authority=False,
        )
    except endpoint.SemanticBridgeEndpointIdentityV1Error as exc:
        if "BRIDGE_DERIVED_ATOM_COLLISION" not in str(exc):
            raise
    else:
        fail("BRIDGE_DERIVED_ATOM_COLLISION = NOT_REJECTED")
    print("BRIDGE_DERIVED_ATOM_COLLISION = REJECTED")
    print("BRIDGE_DERIVED_ATOM_PROVENANCE = PASS_REQUIRED_BY_V2_LANGUAGE")

    endpoint_profile = sal._verify_endpoint_profile()
    theory = sal._verify_bridge_theory_v3(endpoint_profile)
    method = v18._verify_entailment_method_profile(v17._verify_question(), 18)
    execution = sal._verify_execution_profile_v2(theory, endpoint_profile, method)
    extension = sal._verify_capacity_extension(method)
    if theory.get("bridge_axiom_refs") != []:
        fail("CURRENT_BRIDGE_THEORY = FAIL:EXPECTED_EMPTY")
    if endpoint_profile.get("profile_authority_status") != "SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE":
        fail("ENDPOINT_PROFILE_AUTHORITY = FAIL")
    if execution.get("execution_authority_status") != "SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE":
        fail("EXECUTION_PROFILE_AUTHORITY = FAIL")
    print("CROSS_FORMULA_SEMANTIC_BRIDGE = ABSENT")
    print("BRIDGE_ENDPOINT_IDENTITY_PROFILE_AUTHORITY = NOT_ESTABLISHED_SUCCESSOR_CANDIDATE")
    print("SEMANTIC_BRIDGE_EXECUTION_PROFILE_AUTHORITY = NOT_ESTABLISHED_SUCCESSOR_CANDIDATE")

    if sal._semantic_authority_lineage_blocker() != "BLOCKED_SEMANTIC_AUTHORITY_STATUS_LINEAGE":
        fail("SEMANTIC_AUTHORITY_STATUS_SELF_ASSERTION = FAIL")
    print("SEMANTIC_AUTHORITY_STATUS_SELF_ASSERTION = REJECTED_BY_PRODUCTION_LINEAGE_BLOCKER")
    print("SEMANTIC_AUTHORITY_STATUS_LINEAGE = NOT_ESTABLISHED")

    if sal._capacity_extension_is_admissible(extension, bridge_aware_atom_count=18):
        fail("ENTAILMENT_METHOD_CONSERVATIVE_CAPACITY_EXTENSION = FALSE_PASS")
    if sal._effective_max_atoms(method, extension, bridge_aware_atom_count=18) != 16:
        fail("ENTAILMENT_METHOD_BASE_CAPACITY_MUTATED")
    print("ENTAILMENT_METHOD_CONSERVATIVE_CAPACITY_EXTENSION = NOT_ESTABLISHED_CANDIDATE_OBJECT_ONLY")
    print("SAME_QUESTION_METHOD_SEMANTICS_PRESERVATION = NOT_ESTABLISHED")
    print("BRIDGE_AWARE_EXTENDED_CAPACITY = BLOCKED_NO_AUTHORIZED_EXTENSION_18_GT_16")

    source = inspect.getsource(sal.audit_semantic_endpoint_identity_closure)
    if "endpoint_exec.bridge_bound_entailment_v2" not in source or "finite_propositional_entailment(" in source:
        fail("ENDPOINT_CLOSED_PRODUCTION_SOLVER_BINDING = FAIL")
    print("ENDPOINT_CLOSED_PRODUCTION_SOLVER_BINDING = PASS")

    old_gate = _load("conformance/AIFC-RELEASE-GATE-v1.0.16-draft.json")
    new_gate = _load("conformance/AIFC-RELEASE-GATE-v1.0.17-draft.json")
    old_ids = [x["id"] for x in old_gate["required_checks"]]
    new_ids = [x["id"] for x in new_gate["required_checks"]]
    if len(old_ids) != 115 or len(new_ids) != 122 or new_ids[:115] != old_ids or new_ids[115:] != NEW_GATES:
        fail("SAL_RELEASE_GATE_115_TO_122 = FAIL")
    print("SAL_RELEASE_GATE_115_TO_122 = PASS (7 additive gates)")

    report = sal.audit_semantic_endpoint_identity_closure(
        v17.PREDECESSOR_ID, v17.TARGET_PROFILE_ID, v17.QUESTION_ID
    )
    if report.current_bridge_axiom_count != 0 or report.current_bridge_aware_atom_count != 18:
        fail("SAL_V110_CURRENT_THEOREM_COUNT = FAIL")
    if report.solver_invocation_count != 0 or report.result != "BLOCKED":
        fail("SAL_V110_SOLVER_GATING = FAIL")
    if report.blocked_subtype != "BLOCKED_UNAUTHORIZED_INTERPRETATION":
        fail("SAL_V110_BLOCKED_SUBTYPE = FAIL")
    print("BRIDGE_ENDPOINT_SEMANTIC_IDENTITY = PASS_ENFORCEMENT_IMPLEMENTED_CURRENT_BRIDGE_EMPTY")
    print("BRIDGE_ATOM_ROLE_IDENTITY_BINDING = PASS_STRICT_ROLE_LOOKUP_IMPLEMENTED_CURRENT_BRIDGE_EMPTY")
    print("BRIDGE_DERIVED_ATOM_PROVENANCE = PASS_REQUIRED_BY_V2_LANGUAGE_CURRENT_BRIDGE_EMPTY")
    print("SOLVER_EXECUTION_GATED_BY_ENDPOINT_IDENTITY_CLOSURE = PASS")
    print("SOLVER_INVOCATION_COUNT = 0")
    print("PREDECESSOR_SEMANTIC_ENTAILMENT = BLOCKED_UNAUTHORIZED_INTERPRETATION")
    print("NORMATIVE_COUNTERMODEL = NOT_CLAIMED")
    print("AUTHORITY_CLOSED_FINITE_INDUCTION = NOT_YET_ESTABLISHED")
    print("IMPLEMENTATION_A_PASS = NOT_ESTABLISHED")
    print("AIFC_V1_FROZEN = FALSE")
    print("PLATFORM_TRUST_PROVEN = FALSE")
    print("SAL_GLOBAL_NOVELTY = NOT_ESTABLISHED")
    print("SCIENTIFIC_ASSURANCE_LINEAGE_V1_10_ENDPOINT_IDENTITY_CLOSURE = PASS")


if __name__ == "__main__":
    main()
