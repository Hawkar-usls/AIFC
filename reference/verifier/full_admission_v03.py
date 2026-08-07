#!/usr/bin/env python3
"""Authoritative AIFC Verifier A v0.3 pre-crypto admission path."""
from __future__ import annotations

from typing import Any, Mapping

from full_admission_v02 import verify_replay_manifest as verify_v02
from protocol_semantics_v03 import (
    ProtocolSemanticsError,
    replay_terminal_semantics,
    replay_trial_creation_policy,
)
from resolver import EvidenceResolutionError
from resolver_v02 import EvidenceResolverV02
from schema_runtime import RuntimeSchemaError, validate_protocol_object


def _invalid(manifest: Mapping[str, Any], gate: str, code: str, detail: str = "") -> dict[str, Any]:
    experiment_id = manifest.get("experiment_id")
    trial_index = manifest.get("subject_trial_index")
    bundle_hash = manifest.get("evidence_bundle_hash")
    return {
        "schema": "AIFC/verifier-result/v1",
        "experiment_id": experiment_id if isinstance(experiment_id, str) and experiment_id else "UNKNOWN",
        "trial_index": trial_index if isinstance(trial_index, int) and trial_index >= 1 else 1,
        "verifier_id": "AIFC-Verifier-A",
        "verifier_version": "0.3.0-self-audit",
        "evidence_bundle_hash": bundle_hash if isinstance(bundle_hash, str) and len(bundle_hash) == 64 else "0" * 64,
        "gate_results": {gate: "FAIL"},
        "exact_match": False,
        "terminal_grade": "INVALIDATED_EVIDENCE",
        "failure_codes": [f"{code}:{detail}" if detail else code],
        "physical_interpretation": "NO_AUTOMATIC_PHYSICAL_RETROCAUSALITY_CLAIM",
        "fail_open": False,
    }


def verify_replay_manifest(manifest: Mapping[str, Any], resolver: EvidenceResolverV02) -> dict[str, Any]:
    try:
        validate_protocol_object(manifest, "AIFC/replay-package/v0.2")
    except RuntimeSchemaError as exc:
        return _invalid(manifest, "RUNTIME_JSON_SCHEMA_ADMISSION", "REPLAY_PACKAGE_SCHEMA_REJECTED", str(exc))

    try:
        trial_creation = replay_trial_creation_policy(manifest, resolver)
        terminal_semantics = replay_terminal_semantics(manifest, resolver)
    except (ProtocolSemanticsError, EvidenceResolutionError) as exc:
        text = str(exc)
        gate = "TERMINAL_SUBTYPE_SEMANTICS" if "TERMINAL" in text else "TRIAL_CREATION_POLICY_REPLAY"
        code = "IMPOSSIBLE_TERMINAL_SUBTYPE" if "IMPOSSIBLE_TERMINAL_SUBTYPE" in text else "TRIAL_CREATION_OR_TERMINAL_SEMANTICS_REJECTED"
        return _invalid(manifest, gate, code, text)

    result = verify_v02(manifest, resolver)
    gates = result.setdefault("gate_results", {})

    if gates.get("LEDGER_REPLAY") == "PASS":
        gates["DECLARED_TRIAL_LEDGER_COVERAGE"] = "PASS"

    # The v0.2 core set COMPLETE_TRIAL_PUBLICATION immediately after ledger coverage.
    # v0.3 makes the gate semantically exact: it is PASS only after publication replay.
    if gates.get("PUBLICATION_MANIFEST_REPLAY") == "PASS":
        gates["COMPLETE_TRIAL_PUBLICATION"] = "PASS"
    elif gates.get("COMPLETE_TRIAL_PUBLICATION") == "PASS":
        gates["COMPLETE_TRIAL_PUBLICATION"] = "BLOCKED"

    gates["RUNTIME_JSON_SCHEMA_ADMISSION"] = "PASS"
    gates["TERMINAL_SUBTYPE_SEMANTICS"] = terminal_semantics.status
    gates["TRIAL_CREATION_POLICY_REPLAY"] = trial_creation.status

    if trial_creation.status != "PASS":
        result.setdefault("failure_codes", []).append(
            f"{trial_creation.code}:{trial_creation.detail}" if trial_creation.detail else trial_creation.code
        )
        if result.get("terminal_grade") not in {"INVALIDATED_EVIDENCE", "NOT_ADMITTED"}:
            result["terminal_grade"] = "NOT_ADMITTED"

    result["verifier_version"] = "0.3.0-self-audit"
    return result
