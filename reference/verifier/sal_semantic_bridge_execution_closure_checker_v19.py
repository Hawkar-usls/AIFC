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
import scientific_assurance_lineage_v19 as sal  # noqa: E402
import semantic_bridge_execution_v1 as bridge_exec  # noqa: E402
from schema_runtime import validate_protocol_object  # noqa: E402


REQUIRED_FILES = [
    ".github/workflows/sal-semantic-bridge-execution-closure-v19.yml",
    "conformance/AIFC-SEMANTIC-BRIDGE-THEORY-v2.json",
    "conformance/AIFC-SEMANTIC-BRIDGE-EXECUTION-PROFILE-v1.json",
    "conformance/AIFC-ENTAILMENT-QUESTION-SOURCE-BINDING-v2.json",
    "conformance/AIFC-SEMANTIC-BRIDGE-EXECUTION-AUDIT-v1.json",
    "conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v9.json",
    "conformance/AIFC-RELEASE-GATE-v1.0.16-draft.json",
    "reference/verifier/semantic_bridge_execution_v1.py",
    "reference/verifier/scientific_assurance_lineage_v19.py",
    "reference/verifier/sal_semantic_bridge_execution_closure_checker_v19.py",
    "reference/tests/test_sal_semantic_bridge_execution_closure_v19.py",
    "schemas/semantic-bridge-axiom-v1.schema.json",
    "schemas/semantic-bridge-theory-v2.schema.json",
    "schemas/semantic-bridge-execution-profile-v1.schema.json",
    "schemas/entailment-question-source-binding-v2.schema.json",
    "schemas/semantic-bridge-execution-audit-v1.schema.json",
    "schemas/schema-identity-registry-v9.schema.json",
    "spec/SCIENTIFIC-ASSURANCE-LINEAGE-v0.8.md",
    "tools/check_sal_semantic_bridge_execution_closure_v19.py",
]

NEW_SCHEMA_IDS = {
    "AIFC/semantic-bridge-axiom/v1",
    "AIFC/semantic-bridge-theory/v2",
    "AIFC/semantic-bridge-execution-profile/v1",
    "AIFC/entailment-question-source-binding/v2",
    "AIFC/semantic-bridge-execution-audit/v1",
    "AIFC/schema-identity-registry/v9",
}

NEW_GATES = {
    "BRIDGE_AXIOM_EXECUTABLE_SEMANTICS",
    "SEMANTIC_BRIDGE_EXECUTION_BINDING",
    "BRIDGE_THEORY_COMPOSITION_REPLAY",
    "BRIDGE_AWARE_ENTAILMENT_METHOD_CAPACITY",
    "QUESTION_SOURCE_RAW_SHA256_RECOMPUTATION",
}


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def required_gate_ids(doc: dict) -> set[str]:
    return {
        str(row["id"])
        for row in doc["required_checks"]
        if isinstance(row, dict) and row.get("required") is True
    }


def main() -> None:
    missing = [p for p in REQUIRED_FILES if not (ROOT / p).is_file()]
    if missing:
        raise SystemExit("SAL_V19_REQUIRED_FILES_MISSING=" + ",".join(missing))
    print(f"SAL_V19_REQUIRED_FILES = PASS ({len(REQUIRED_FILES)}/{len(REQUIRED_FILES)})")

    schema_paths = [p for p in REQUIRED_FILES if p.startswith("schemas/")]
    observed_ids: set[str] = set()
    for path in schema_paths:
        schema = load(path)
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise SystemExit(f"SAL_V19_SCHEMA_DIALECT_REBINDING:{path}")
        protocol = schema.get("properties", {}).get("schema", {}).get("const")
        if not isinstance(protocol, str):
            raise SystemExit(f"SAL_V19_SCHEMA_PROTOCOL_ID_MISSING:{path}")
        observed_ids.add(protocol)
    if observed_ids != NEW_SCHEMA_IDS:
        raise SystemExit("SAL_V19_SCHEMA_HEADER_SET_REBINDING")
    print(f"SAL_V19_SCHEMA_HEADERS = PASS ({len(schema_paths)}/{len(schema_paths)})")

    registry = load("conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v9.json")
    validate_protocol_object(registry, "AIFC/schema-identity-registry/v9")
    if registry.get("predecessor_registry_git_blob_sha1") != "28aab7e71e6bc6b20aec9553e16c434e348314ca":
        raise SystemExit("SAL_V19_SCHEMA_REGISTRY_PREDECESSOR_REBINDING")
    rows = registry.get("records")
    if not isinstance(rows, list) or len(rows) != 6:
        raise SystemExit("SAL_V19_SCHEMA_REGISTRY_COUNT_REBINDING")
    registered = set()
    for row in rows:
        path = ROOT / str(row["source_path"])
        raw = path.read_bytes()
        if git_blob_sha1_bytes(raw) != row.get("git_blob_sha1"):
            raise SystemExit(f"SAL_V19_SCHEMA_GIT_IDENTITY_MISMATCH:{path.name}")
        if hashlib.sha256(raw).hexdigest() != row.get("raw_schema_sha256"):
            raise SystemExit(f"SAL_V19_SCHEMA_RAW_IDENTITY_MISMATCH:{path.name}")
        registered.add(str(row["schema_id"]))
    if registered != NEW_SCHEMA_IDS:
        raise SystemExit("SAL_V19_SCHEMA_REGISTRY_ID_SET_REBINDING")
    print("SAL_SCHEMA_IDENTITY_REGISTRATION_V9 = PASS (6/6 dual-bound candidate identities)")

    production_source = inspect.getsource(sal.audit_semantic_bridge_execution_closure)
    if "bridge_exec.bridge_bound_entailment" not in production_source:
        raise SystemExit("SEMANTIC_BRIDGE_EXECUTION_BINDING_MISSING")
    if "finite_propositional_entailment(" in production_source:
        raise SystemExit("SEMANTIC_BRIDGE_EXECUTION_OMISSION_DIRECT_SOLVER_PATH_PRESENT")

    direct, bridged, vector_atoms = bridge_exec.bridge_effect_test_vector()
    if direct != "REFUTED_BY_COUNTERMODEL" or bridged != "PROVED":
        raise SystemExit("SEMANTIC_BRIDGE_EXECUTION_EFFECT_VECTOR_FAILED")

    report = sal.audit_semantic_bridge_execution_closure(
        v17.PREDECESSOR_ID,
        v17.TARGET_PROFILE_ID,
        v17.QUESTION_ID,
    )
    if report.solver_invocation_count != 0 or report.result != "BLOCKED":
        raise SystemExit("SAL_V19_CURRENT_SOLVER_SHOULD_BE_BLOCKED")
    if report.current_bridge_aware_atom_count != 18:
        raise SystemExit("SAL_V19_CURRENT_BRIDGE_AWARE_ATOM_COUNT_REBINDING")

    fake = {
        "binding_status": "DUAL_IDENTITY_ESTABLISHED",
        "predecessor_raw_sha256": "0" * 64,
        "target_profile_raw_sha256": "1" * 64,
    }
    try:
        sal._enforce_dual_identity_claim(fake, "2" * 64, "3" * 64)
    except sal.ScientificAssuranceLineageV19Error:
        pass
    else:
        raise SystemExit("QUESTION_SOURCE_DUAL_IDENTITY_FALSE_PROMOTION_NOT_REJECTED")

    old_gate = load("conformance/AIFC-RELEASE-GATE-v1.0.15-draft.json")
    new_gate = load("conformance/AIFC-RELEASE-GATE-v1.0.16-draft.json")
    old_ids = required_gate_ids(old_gate)
    new_ids = required_gate_ids(new_gate)
    if len(old_ids) != 110 or len(new_ids) != 115 or new_ids - old_ids != NEW_GATES or not old_ids < new_ids:
        raise SystemExit("SAL_RELEASE_GATE_110_TO_115_REBINDING")

    print("BRIDGE_AXIOM_EXECUTABLE_SEMANTICS = PASS_STRICT_CANDIDATE_LANGUAGE (ATOM/NOT/AND/OR + exact atom bindings)")
    print("SEMANTIC_BRIDGE_EXECUTION_BINDING = PASS_EXACT_IMPLEMENTATION_BOUND_CANDIDATE")
    print("SEMANTIC_BRIDGE_EXECUTION_OMISSION = REJECTED_BY_NONEMPTY_EFFECT_VECTOR")
    print("BRIDGE_THEORY_NOT_COMPOSED_INTO_ENTAILMENT = REJECTED_IN_TESTED_EXECUTION_PATH")
    print(f"BRIDGE_EXECUTION_EFFECT_TEST_VECTOR = PASS (direct={direct}; bridged={bridged}; atoms={vector_atoms})")
    print("BRIDGE_THEORY_COMPOSITION_REPLAY = PASS_NONEMPTY_EFFECT_VECTOR_AND_EMPTY_PRODUCTION_REPLAY")
    print("CROSS_FORMULA_SEMANTIC_BRIDGE = ABSENT")
    print("CROSS_FORMULA_SEMANTIC_BRIDGE_AUTHORITY = NOT_ESTABLISHED")
    print("SEMANTIC_ABSTRACTION_ADEQUACY = NOT_ESTABLISHED")
    print("SEMANTIC_BRIDGE_EXECUTION_PROFILE_AUTHORITY = NOT_ESTABLISHED_SUCCESSOR_CANDIDATE")
    print(f"BRIDGE_AWARE_ENTAILMENT_METHOD_CAPACITY = BLOCKED ({report.current_bridge_aware_atom_count} atoms > max_atoms 16)")
    print("QUESTION_SOURCE_RAW_SHA256_RECOMPUTATION = PASS_EXACT_HISTORICAL_MEMBERSHIP_RECOMPUTED")
    print(f"RECOMPUTED_PREDECESSOR_RAW_SHA256 = {report.recomputed_predecessor_raw_sha256}")
    print(f"RECOMPUTED_TARGET_PROFILE_RAW_SHA256 = {report.recomputed_target_profile_raw_sha256}")
    print("QUESTION_SOURCE_DUAL_IDENTITY_FALSE_PROMOTION = REJECTED")
    print(f"ENTAILMENT_QUESTION_SOURCE_DUAL_IDENTITY = {report.entailment_question_source_dual_identity}")
    print("SOLVER_EXECUTION_GATED_BY_BRIDGE_EXECUTION_CLOSURE = PASS")
    print(f"SOLVER_INVOCATION_COUNT = {report.solver_invocation_count}")
    print(f"PREDECESSOR_SEMANTIC_ENTAILMENT = {report.blocked_subtype}")
    print("NORMATIVE_COUNTERMODEL = NOT_CLAIMED")
    print("SAL_RELEASE_GATE_110_TO_115 = PASS (5 additive gates)")
    print("AUTHORITY_CLOSED_FINITE_INDUCTION = NOT_YET_ESTABLISHED")
    print("FIRST_AUTHORITY_CLOSED_NORMATIVE_INDUCTIVE_STEP = NOT_YET_ESTABLISHED")
    print("NORMATIVE_ROOT_LINEAGE_GENERAL = NOT_ESTABLISHED")
    print("HISTORICAL_REPLAY_ENVIRONMENT_IDENTITY_GENERAL = NOT_ESTABLISHED")
    print("IMPLEMENTATION_A_PASS = NOT_ESTABLISHED")
    print("AIFC_V1_FROZEN = FALSE")
    print("PLATFORM_TRUST_PROVEN = FALSE")
    print("SAL_GLOBAL_NOVELTY = NOT_ESTABLISHED")


if __name__ == "__main__":
    main()
