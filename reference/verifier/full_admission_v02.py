#!/usr/bin/env python3
"""Authoritative AIFC Verifier A v0.2 top-level admission path."""
from __future__ import annotations

from typing import Any, Mapping

from admission import verify_replay_manifest as verify_after_preregistration
from preregistration_v02 import verify_plan_preregistration
from resolver_v02 import EvidenceResolverV02


def verify_replay_manifest(manifest: Mapping[str, Any], resolver: EvidenceResolverV02) -> dict[str, Any]:
    failure = verify_plan_preregistration(manifest, resolver)
    if failure is not None:
        return failure
    result = verify_after_preregistration(manifest, resolver)
    if result.get("terminal_grade") != "INVALIDATED_EVIDENCE":
        result.setdefault("gate_results", {})["EXPERIMENT_PLAN_PREREGISTRATION"] = "PASS"
    return result
