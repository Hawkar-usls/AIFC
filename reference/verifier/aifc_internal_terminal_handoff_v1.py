#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PREDECESSOR_MAIN = "b8a1f3acf9d8444affccdb6b0b754f19e6a08949"
PREDECESSOR_TREE = "9534c147ba29cc53f7f321b4101907a04818c3bc"
V116_AUDIT_PATH = "conformance/AIFC-BOOTSTRAP-NON-SELF-RATIFICATION-AUDIT-v1.json"
V116_AUDIT_GIT_BLOB_SHA1 = "a2d3fe6bd7b80c778da05740df5cc7c4953acf5e"
RELEASE_GATE_PATH = "conformance/AIFC-RELEASE-GATE-v1.json"
RELEASE_GATE_GIT_BLOB_SHA1 = "8047effc218c5b15120539b011722b272ae0fa37"
ROADMAP_PATH = "ROADMAP.md"
PRIOR_ART_PATH = "docs/PRIOR_ART_BOUNDARY.md"


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _require(condition: bool, label: str) -> None:
    if not condition:
        raise RuntimeError(label)


def verify() -> dict[str, str | int | bool]:
    # This verifier is intentionally a handoff verifier, not a new source of
    # normative authority. It binds the already-tested SAL v1.16 boundary and
    # confirms that unresolved work is genuinely external/cross-implementation.
    _require(_git("rev-parse", f"{PREDECESSOR_MAIN}^{{tree}}") == PREDECESSOR_TREE,
             "PREDECESSOR_TREE_IDENTITY_MISMATCH")
    _require(_git("hash-object", V116_AUDIT_PATH) == V116_AUDIT_GIT_BLOB_SHA1,
             "V116_AUDIT_IDENTITY_MISMATCH")
    _require(_git("hash-object", RELEASE_GATE_PATH) == RELEASE_GATE_GIT_BLOB_SHA1,
             "RELEASE_GATE_IDENTITY_MISMATCH")

    audit = _load_json(V116_AUDIT_PATH)
    gate = _load_json(RELEASE_GATE_PATH)
    roadmap = (ROOT / ROADMAP_PATH).read_text(encoding="utf-8")
    prior_art = (ROOT / PRIOR_ART_PATH).read_text(encoding="utf-8")

    expected_audit = {
        "non_self_ratification_theorem": "ESTABLISHED_FOR_ROOT_RELATIVE_DESCENDANT_CLOSURE",
        "bootstrap_self_ratification": "REJECTED_BY_INDEPENDENCE_RULE",
        "descendant_ratifier_promotion": "REJECTED",
        "authority_cycle_ratification": "REJECTED_FAIL_CLOSED_BY_DAG_CHECK",
        "caller_ratifier_input_surface": "FORBIDDEN_NO_CALLER_INPUT_SURFACE",
        "external_ratifier_structural_independence": "NOT_ESTABLISHED_NO_EXTERNAL_RATIFICATION_OBJECT",
        "external_ratifier_authority_admissibility": "NOT_ESTABLISHED",
        "external_bootstrap_ratification": "NOT_PERFORMED",
        "bootstrap_authority_legitimacy": "NOT_ESTABLISHED",
        "current_internal_verification_path_to_bootstrap_legitimacy": "ABSENT",
        "normative_authority_origin_internal_proof": "NOT_ESTABLISHED_BY_INTERNAL_VERIFICATION",
        "normative_lineage_completeness": "BLOCKED_UNAUTHORIZED_COMPLETENESS_BASIS",
        "derived_semantic_authority": "BLOCKED",
        "next_required_basis": "EXTERNALLY_ANCHORED_NON_DESCENDANT_RATIFICATION_WITH_SEPARATE_AUTHORITY_ADMISSIBILITY",
        "status": "BOOTSTRAP_NON_SELF_RATIFICATION_BOUNDARY_CONFIRMED_IN_CURRENT_TESTED_SCOPE",
    }
    for key, value in expected_audit.items():
        _require(audit.get(key) == value, f"V116_AUDIT_FIELD_MISMATCH:{key}")
    _require(audit.get("solver_invocation_count") == 0, "SOLVER_INVOCATION_COUNT_NONZERO")

    _require(gate.get("profile") == "AIFC-v1.0-FROZEN", "RELEASE_GATE_PROFILE_MISMATCH")
    _require(gate.get("status") == "DRAFT_NOT_SATISFIED", "PREMATURE_FROZEN_STATUS")
    required_checks = {
        row["id"] for row in gate.get("required_checks", []) if row.get("required") is True
    }
    required_external = {
        "IMPLEMENTATION_B_PASS",
        "BYTE_IDENTICAL_CANONICALIZATION",
        "TARGET_SOURCE_CRYPTOGRAPHIC_PROOF",
        "EXTERNAL_BENCH_EVIDENCE_ROOTED_OUTSIDE_GENESIS",
    }
    _require(required_external <= required_checks, "EXTERNAL_RELEASE_GATES_MISSING")
    shortcuts = set(gate.get("forbidden_shortcuts", []))
    _require("using one implementation twice as independent implementations" in shortcuts,
             "IMPLEMENTATION_B_INDEPENDENCE_SHORTCUT_NOT_FORBIDDEN")
    _require("setting FROZEN_PASS without resolving every required gate evidence object" in shortcuts,
             "FROZEN_PASS_SHORTCUT_NOT_FORBIDDEN")

    roadmap_tokens = [
        "Phase 4 — External public-randomness bench",
        "Phase 5 — Independent second implementation",
        "Phase 6 — Prior-art and manuscript freeze",
        "Phase 7 — AIFC v1.0 release",
        "PREMATURE_V1_FROZEN_TAG = FORBIDDEN",
        "RETROCAUSALITY_PROVED_BY_VERIFIER = FORBIDDEN",
    ]
    for token in roadmap_tokens:
        _require(token in roadmap, f"ROADMAP_BOUNDARY_MISSING:{token}")

    prior_art_tokens = [
        "AIFC_GLOBAL_NOVELTY = NOT_ESTABLISHED",
        "PHYSICAL_RETROCAUSALITY = NOT_OBSERVED",
        "Global scientific novelty is not yet established.",
    ]
    for token in prior_art_tokens:
        _require(token in prior_art, f"PRIOR_ART_BOUNDARY_MISSING:{token}")

    return {
        "PREDECESSOR_MAIN": PREDECESSOR_MAIN,
        "PREDECESSOR_TREE": PREDECESSOR_TREE,
        "V116_AUDIT_IDENTITY": "CONFIRMED_PINNED_GIT_BLOB",
        "RELEASE_GATE_IDENTITY": "CONFIRMED_PINNED_GIT_BLOB",
        "NON_SELF_RATIFICATION_BOUNDARY": "CONFIRMED_IN_CURRENT_TESTED_SCOPE",
        "CURRENT_INTERNAL_PATH_TO_BOOTSTRAP_LEGITIMACY": "ABSENT",
        "AIFC_INTERNAL_ASSURANCE_LINEAGE_TERMINAL": "ESTABLISHED_IN_CURRENT_TESTED_SCOPE",
        "AIFC_ARTICLE_PUBLICATION_READINESS": "READY_WITH_EXPLICIT_DRAFT_AND_CLAIM_CEILING",
        "AIFC_V1_FROZEN": False,
        "IMPLEMENTATION_B": "NOT_ESTABLISHED",
        "EXTERNAL_PUBLIC_RANDOMNESS_BENCH": "NOT_ESTABLISHED",
        "EXTERNAL_BOOTSTRAP_RATIFICATION": "NOT_PERFORMED",
        "BOOTSTRAP_AUTHORITY_LEGITIMACY": "NOT_ESTABLISHED",
        "GLOBAL_NOVELTY": "NOT_ESTABLISHED",
        "PHYSICAL_RETROCAUSALITY": "NOT_OBSERVED",
        "SOLVER_INVOCATION_COUNT": 0,
        "NEXT_PHASE": "PUBLIC_COMMUNICATION_AND_EXTERNAL_FALSIFICATION",
    }


def main() -> int:
    result = verify()
    for key, value in result.items():
        if isinstance(value, bool):
            value = "TRUE" if value else "FALSE"
        print(f"{key} = {value}")
    print("AIFC_INTERNAL_TERMINAL_HANDOFF_V1 = PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
