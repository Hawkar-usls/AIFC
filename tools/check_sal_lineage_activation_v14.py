#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

from schema_runtime import validate_protocol_object
from scientific_assurance_lineage_v14 import (
    ACTIVATED_IDS,
    NEW_FRONTIER_GATES,
    PROVENANCE_BLOB,
    PROVENANCE_ID,
    PROVENANCE_PATH,
    RECEIPT_V13_BLOB,
    RECEIPT_V13_ID,
    RECEIPT_V13_PATH,
    ROOT_V3_BLOB,
    ROOT_V3_ID,
    ROOT_V3_PATH,
    SCHEMA_REGISTRY_V4_BLOB,
    SCHEMA_REGISTRY_V4_PATH,
    TRANSITION_BLOB,
    TRANSITION_ID,
    TRANSITION_PATH,
    _read_bound_json,
    verify_lineage_activation_live,
)

REQUIRED = [
    "schemas/normative-authority-receipt-v2.schema.json",
    "schemas/authority-receipt-provenance-v1.schema.json",
    "schemas/normative-lineage-transition-v1.schema.json",
    "schemas/normative-assurance-root-registry-v3.schema.json",
    "schemas/schema-identity-registry-v4.schema.json",
    RECEIPT_V13_PATH,
    PROVENANCE_PATH,
    SCHEMA_REGISTRY_V4_PATH,
    "conformance/AIFC-RELEASE-GATE-v1.0.11-draft.json",
    ROOT_V3_PATH,
    TRANSITION_PATH,
    "reference/verifier/scientific_assurance_lineage_v14.py",
    "reference/tests/test_sal_lineage_activation_v14.py",
    "spec/SCIENTIFIC-ASSURANCE-LINEAGE-v0.3.md",
    ".github/workflows/sal-lineage-activation-v14.yml",
]


def main() -> int:
    missing = [p for p in REQUIRED if not (ROOT / p).is_file()]
    if missing:
        raise SystemExit("SAL_LINEAGE_ACTIVATION_REQUIRED_FILES_MISSING:" + ",".join(missing))

    receipt = _read_bound_json(RECEIPT_V13_PATH, RECEIPT_V13_BLOB, RECEIPT_V13_ID)
    provenance = _read_bound_json(PROVENANCE_PATH, PROVENANCE_BLOB, PROVENANCE_ID)
    transition = _read_bound_json(TRANSITION_PATH, TRANSITION_BLOB, TRANSITION_ID)
    root_v3 = _read_bound_json(ROOT_V3_PATH, ROOT_V3_BLOB, ROOT_V3_ID)
    schemas_v4 = _read_bound_json(SCHEMA_REGISTRY_V4_PATH, SCHEMA_REGISTRY_V4_BLOB, "schema-registry-v4")
    validate_protocol_object(receipt, "AIFC/normative-authority-receipt/v2")
    validate_protocol_object(provenance, "AIFC/authority-receipt-provenance/v1")
    validate_protocol_object(transition, "AIFC/normative-lineage-transition/v1")
    validate_protocol_object(root_v3, "AIFC/normative-assurance-root-registry/v3")
    validate_protocol_object(schemas_v4, "AIFC/schema-identity-registry/v4")

    report = verify_lineage_activation_live()

    print(f"SAL_LINEAGE_ACTIVATION_REQUIRED_FILES = PASS ({len(REQUIRED)}/{len(REQUIRED)})")
    print("SAL_V14_SCHEMA_HEADERS = PASS (5/5)")
    print("SAL_SCHEMA_IDENTITY_REGISTRATION_V4 = PASS (5/5 dual-bound candidate identities)")
    print("HISTORICAL_ROOT_COMMIT_MEMBERSHIP = PASS")
    print("PREDECESSOR_ROOT_REGISTRY_MEMBERSHIP = PASS")
    print("AUTHORITY_RECEIPT_PROVENANCE = PASS (2/2 receipts live-replayed)")
    print(f"LINEAGE_TRANSITION_REPLAY = PASS ({len(report.activated_artifact_ids)}/{len(ACTIVATED_IDS)} activated)")
    print("SUCCESSOR_REGISTRY_NON_SELF_PROMOTION = PASS")
    print(f"SAL_RELEASE_GATE_78_TO_83 = PASS ({len(NEW_FRONTIER_GATES)} additive gates)")
    print("CANDIDATE_EEEE61C_TO_AUTHORITATIVE_EEEE61C = PASS_FOR_EXACT_ACTIVATED_SET")
    print("SCIENTIFIC_ASSURANCE_LINEAGE_V1_4_ACTIVATION = PASS")
    print(f"PREDECESSOR_ROOT_REGISTRY = {report.predecessor_registry_id}")
    print(f"SUCCESSOR_ROOT_REGISTRY = {report.successor_registry_candidate_id} (CANDIDATE_ONLY)")
    print("NORMATIVE_ROOT_LINEAGE_FIRST_INDUCTIVE_STEP = ESTABLISHED_IN_THIS_TESTED_TRANSITION_IF_EXACT_HEAD_ATTESTATION_PASSES")
    print("NORMATIVE_ROOT_LINEAGE_GENERAL = NOT_ESTABLISHED")
    print("ROOT_REGISTRY_V3_NORMATIVE_PROMOTION = BLOCKED_PENDING_NEXT_INDEPENDENT_LINEAGE_ATTESTATION")
    print("GATE_DEFINITION_HISTORICAL_ANCHOR = NOT_ESTABLISHED")
    print("GATE_ATOM_SEMANTIC_IDENTITY = NOT_ESTABLISHED")
    print("AUTHORITY_CLOSED_PROOF_GENERAL = NOT_ESTABLISHED")
    print("REAL_SUCCESSOR_WRAPPED_REPLAY = NOT_YET_ESTABLISHED")
    print("HISTORICAL_KEY_LIFECYCLE = BLOCKED")
    print("IMPLEMENTATION_A_PASS = NOT_ESTABLISHED")
    print("AIFC_V1_FROZEN = FALSE")
    print("PLATFORM_TRUST_PROVEN = FALSE")
    print("SAL_GLOBAL_NOVELTY = NOT_ESTABLISHED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
