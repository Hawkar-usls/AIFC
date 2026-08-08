#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PREDECESSOR_MAIN = "1eaf6ea1d6874b85cd7e85fba87cfc167bd4441d"
PREDECESSOR_TREE = "a03273fc39e6310934258539e7e4f81fc98fffb9"
V117_AUDIT_PATH = "conformance/AIFC-EXTERNAL-BOOTSTRAP-RATIFICATION-ADMISSIBILITY-AUDIT-v1.json"
V117_AUDIT_GIT_BLOB_SHA1 = "390fc66aece7900df2d754af295959ce668e11a3"
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
    """Replay content-bound terminal semantics without assuming Git history depth.

    The exact PREDECESSOR_MAIN -> PREDECESSOR_TREE relationship is a separate
    mandatory check in the dedicated full-history workflow. Keeping that check
    outside this function makes the same semantic verifier replayable inside
    ordinary shallow-checkout repository test jobs without silently fetching or
    trusting missing history.
    """
    _require(
        _git("hash-object", V117_AUDIT_PATH) == V117_AUDIT_GIT_BLOB_SHA1,
        "V117_AUDIT_IDENTITY_MISMATCH",
    )
    _require(
        _git("hash-object", RELEASE_GATE_PATH) == RELEASE_GATE_GIT_BLOB_SHA1,
        "RELEASE_GATE_IDENTITY_MISMATCH",
    )

    audit = _load_json(V117_AUDIT_PATH)
    gate = _load_json(RELEASE_GATE_PATH)
    roadmap = (ROOT / ROADMAP_PATH).read_text(encoding="utf-8")
    prior_art = (ROOT / PRIOR_ART_PATH).read_text(encoding="utf-8")

    expected_audit = {
        "v116_non_self_ratification_theorem": "PRESERVED_EXACT_ROOT_RELATIVE_BOUNDARY",
        "candidate_discovery_scope": "DESIGNATED_INTAKE_PATH_ONLY_NOT_GLOBAL_DISCOVERY",
        "designated_intake_path_status": "ABSENT",
        "external_ratification_candidate": "NOT_PRESENT_AT_DESIGNATED_INTAKE_PATH",
        "non_descendant_provenance_requirement": "REQUIRED_SEPARATE_EVIDENCE_CHANNEL",
        "authentication_evidence_requirement": "REQUIRED_SEPARATE_EVIDENCE_CHANNEL",
        "authentication_evidence_semantics": "ORIGIN_INTEGRITY_EVIDENCE_ONLY_NOT_AUTHORITY",
        "authority_basis_requirement": "REQUIRED_SEPARATE_EXTERNALLY_ANCHORED_BASIS",
        "admissibility_separation_invariant": "STRUCTURAL_INDEPENDENCE_AND_AUTHENTICATION_DO_NOT_IMPLY_AUTHORITY_ADMISSIBILITY",
        "candidate_self_authorization": "REJECTED_BY_SCHEMA_AND_VALIDATOR",
        "known_internal_authority_basis_laundering": "REJECTED_IN_CURRENT_ROOT_SCOPE",
        "caller_candidate_input_surface": "FORBIDDEN_NO_CALLER_INPUT_SURFACE",
        "external_ratifier_structural_independence": "NOT_ESTABLISHED_NO_CANDIDATE",
        "external_ratification_authentication": "NOT_ESTABLISHED_NO_CANDIDATE",
        "external_ratifier_authority_admissibility": "NOT_ESTABLISHED",
        "external_bootstrap_ratification": "NOT_PERFORMED",
        "bootstrap_authority_legitimacy": "NOT_ESTABLISHED",
        "global_external_ratifier_discovery_completeness": "NOT_ESTABLISHED",
        "global_authority_admissibility_semantics": "NOT_ESTABLISHED",
        "normative_lineage_completeness": "BLOCKED_UNAUTHORIZED_COMPLETENESS_BASIS",
        "derived_semantic_authority": "BLOCKED",
        "next_required_basis": "REAL_EXTERNAL_RATIFICATION_OBJECT_WITH_NON_DESCENDANT_PROVENANCE_AND_SEPARATELY_ADMISSIBLE_AUTHORITY_BASIS",
        "status": "EXTERNAL_BOOTSTRAP_RATIFICATION_ADMISSIBILITY_BOUNDARY_CONFIRMED_NO_CURRENT_CANDIDATE",
    }
    for key, value in expected_audit.items():
        _require(audit.get(key) == value, f"V117_AUDIT_FIELD_MISMATCH:{key}")
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
    _require(
        "using one implementation twice as independent implementations" in shortcuts,
        "IMPLEMENTATION_B_INDEPENDENCE_SHORTCUT_NOT_FORBIDDEN",
    )
    _require(
        "setting FROZEN_PASS without resolving every required gate evidence object" in shortcuts,
        "FROZEN_PASS_SHORTCUT_NOT_FORBIDDEN",
    )

    for token in (
        "Phase 4 — External public-randomness bench",
        "Phase 5 — Independent second implementation",
        "Phase 6 — Prior-art and manuscript freeze",
        "Phase 7 — AIFC v1.0 release",
        "PREMATURE_V1_FROZEN_TAG = FORBIDDEN",
        "RETROCAUSALITY_PROVED_BY_VERIFIER = FORBIDDEN",
    ):
        _require(token in roadmap, f"ROADMAP_BOUNDARY_MISSING:{token}")

    for token in (
        "AIFC_GLOBAL_NOVELTY = NOT_ESTABLISHED",
        "PHYSICAL_RETROCAUSALITY = NOT_OBSERVED",
        "Global scientific novelty is not yet established.",
    ):
        _require(token in prior_art, f"PRIOR_ART_BOUNDARY_MISSING:{token}")

    return {
        "PREDECESSOR_MAIN": PREDECESSOR_MAIN,
        "PREDECESSOR_TREE": PREDECESSOR_TREE,
        "PREDECESSOR_COMMIT_TREE_BINDING": "REQUIRED_SEPARATELY_BY_FULL_HISTORY_WORKFLOW",
        "V117_AUDIT_IDENTITY": "CONFIRMED_PINNED_GIT_BLOB",
        "RELEASE_GATE_IDENTITY": "CONFIRMED_PINNED_GIT_BLOB",
        "V116_NON_SELF_RATIFICATION_BOUNDARY": "PRESERVED_BY_V117",
        "V117_ADMISSIBILITY_SEPARATION_BOUNDARY": "CONFIRMED_IN_CURRENT_TESTED_SCOPE",
        "CURRENT_INTERNAL_PATH_TO_BOOTSTRAP_LEGITIMACY": "ABSENT",
        "AIFC_INTERNAL_ASSURANCE_LINEAGE_TERMINAL": "ESTABLISHED_IN_CURRENT_TESTED_SCOPE",
        "AIFC_ARTICLE_PUBLICATION_READINESS": "READY_WITH_EXPLICIT_DRAFT_AND_CLAIM_CEILING",
        "AIFC_V1_FROZEN": False,
        "IMPLEMENTATION_A_PASS": "NOT_ESTABLISHED",
        "IMPLEMENTATION_B": "NOT_ESTABLISHED",
        "EXTERNAL_PUBLIC_RANDOMNESS_BENCH": "NOT_ESTABLISHED",
        "EXTERNAL_RATIFICATION_CANDIDATE": "NOT_PRESENT_AT_DESIGNATED_INTAKE_PATH",
        "EXTERNAL_RATIFIER_AUTHORITY_ADMISSIBILITY": "NOT_ESTABLISHED",
        "EXTERNAL_BOOTSTRAP_RATIFICATION": "NOT_PERFORMED",
        "BOOTSTRAP_AUTHORITY_LEGITIMACY": "NOT_ESTABLISHED",
        "GLOBAL_NOVELTY": "NOT_ESTABLISHED",
        "PHYSICAL_RETROCAUSALITY": "NOT_OBSERVED",
        "SOLVER_INVOCATION_COUNT": 0,
        "NEXT_REQUIRED_BASIS": "REAL_EXTERNAL_RATIFICATION_OBJECT_WITH_NON_DESCENDANT_PROVENANCE_AND_SEPARATELY_ADMISSIBLE_AUTHORITY_BASIS",
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
