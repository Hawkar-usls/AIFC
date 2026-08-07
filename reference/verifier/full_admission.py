#!/usr/bin/env python3
"""Authoritative top-level AIFC Verifier A v0.2 admission composition."""
from __future__ import annotations

from typing import Any, Mapping

from admission import verify_replay_manifest as verify_after_preregistration
from preregistration import verify_plan_preregistration
from resolver import EvidenceResolver


def verify_replay_manifest(manifest: Mapping[str, Any], resolver: EvidenceResolver) -> dict[str, Any]:
    prereg_failure = verify_plan_preregistration(manifest, resolver)
    if prereg_failure is not None:
        return prereg_failure
    result = verify_after_preregistration(manifest, resolver)
    if result.get("terminal_grade") != "INVALIDATED_EVIDENCE":
        result.setdefault("gate_results", {})["EXPERIMENT_PLAN_PREREGISTRATION"] = "PASS"
    return result
