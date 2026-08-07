#!/usr/bin/env python3
"""Small deterministic binding checks shared by AIFC Verifier A v0.2 tests."""
from __future__ import annotations

from typing import Any, Mapping

from frontier import CheckResult, fail, ok


def validate_target_derivation_bindings_v02(
    profile_hash: str,
    profile: Mapping[str, Any],
    pre_return: Mapping[str, Any],
    entropy_profile: Mapping[str, Any],
    target_evidence: Mapping[str, Any],
) -> CheckResult:
    if profile.get("schema") != "AIFC/target-derivation-profile/v1":
        return fail("TARGET_DERIVATION_PROFILE_SCHEMA_MISMATCH")
    if profile.get("frozen_before_target") is not True:
        return fail("POST_HOC_TARGET_DERIVATION")
    if pre_return.get("target_derivation_policy_hash") != profile.get("policy_hash"):
        return fail("TARGET_DERIVATION_POLICY_REBINDING", "PRE_RETURN")
    for name, obj in (("ENTROPY_PROFILE", entropy_profile), ("TARGET_EVIDENCE", target_evidence)):
        if obj.get("target_derivation_profile_hash") != profile_hash:
            return fail("TARGET_DERIVATION_PROFILE_REBINDING", name)
    selector_hash = profile.get("target_selector_profile_hash")
    if entropy_profile.get("target_selector_profile_hash") != selector_hash:
        return fail("TARGET_SELECTOR_PROFILE_REBINDING", "ENTROPY_PROFILE")
    if target_evidence.get("target_selector_profile_hash") != selector_hash:
        return fail("TARGET_SELECTOR_PROFILE_REBINDING", "TARGET_EVIDENCE")
    if target_evidence.get("conditioning_view_hash") != entropy_profile.get("conditioning_view_hash"):
        return fail("CONDITIONING_VIEW_REBINDING")
    extraction = profile.get("extraction")
    transformation = profile.get("transformation")
    if not isinstance(extraction, Mapping) or extraction.get("method") not in {
        "WHOLE_RAW_BYTES",
        "JSON_POINTER_UTF8_STRING",
        "JSON_POINTER_HEX_BYTES",
        "JSON_POINTER_BASE64_BYTES",
    }:
        return fail("TARGET_EXTRACTION_DSL_INVALID")
    if not isinstance(transformation, Mapping):
        return fail("TARGET_TRANSFORMATION_RULE_MISSING")
    if transformation.get("algorithm") not in {"IDENTITY", "SHA-256"}:
        return fail("TARGET_TRANSFORMATION_ALGORITHM_NOT_STRONGEST_V1")
    if transformation.get("framing") != "AIFC_TYPED_LENGTH_PREFIXED_V1":
        return fail("AMBIGUOUS_DERIVATION_ENCODING")
    if not isinstance(transformation.get("input_order"), list) or not transformation.get("input_order"):
        return fail("TARGET_TRANSFORMATION_INPUT_ORDER_INVALID")
    return ok("TARGET_DERIVATION_BINDINGS_V02_PASS")
