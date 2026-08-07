#!/usr/bin/env python3
"""AIFC Verifier A frontier core v0.1.

This module deliberately implements only deterministic admission logic for the
first four verifier-grade attack surfaces:

- SHADOW_CANDIDATE_POOL
- REGISTRY_RECONFIGURATION_FORK
- POST_HOC_TARGET_DERIVATION
- NONCANONICAL_RATIONAL_BOUND

It is NOT the frozen AIFC verifier and does not establish IMPLEMENTATION_A_PASS.
Cryptographic signature verification, full RFC 8785 cross-implementation
canonicalization, complete causal-DAG evaluation, full ledger replay and the
frozen statistical engine remain separate release gates.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import gcd
import hashlib
import re
from typing import Any, Mapping, Sequence

HEX64 = re.compile(r"^[0-9a-f]{64}$")
DECIMAL_CANON = re.compile(r"^(0|[1-9][0-9]*)$")


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    code: str
    detail: str = ""


def ok(code: str = "PASS", detail: str = "") -> CheckResult:
    return CheckResult(True, code, detail)


def fail(code: str, detail: str = "") -> CheckResult:
    return CheckResult(False, code, detail)


def _is_hex64(value: Any) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def experiment_genesis_hash(experiment_id: str) -> str:
    if not isinstance(experiment_id, str) or not experiment_id:
        raise ValueError("experiment_id must be a non-empty string")
    payload = b"AIFC:EXPERIMENT_GENESIS:v1\x00" + experiment_id.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_canonical_rational(bound: Mapping[str, Any]) -> tuple[CheckResult, Fraction | None]:
    """Validate the v1 exact-rational representation.

    Schema regex is only the first line of defense. Semantic reduction and range
    checks are verifier duties.
    """
    try:
        n_s = bound["numerator_dec"]
        d_s = bound["denominator_dec"]
        reduced_flag = bound["canonical_reduced"]
    except (KeyError, TypeError):
        return fail("RATIONAL_FIELDS_MISSING"), None

    if not isinstance(n_s, str) or DECIMAL_CANON.fullmatch(n_s) is None:
        return fail("NONCANONICAL_RATIONAL_NUMERATOR", repr(n_s)), None
    if not isinstance(d_s, str) or re.fullmatch(r"^[1-9][0-9]*$", d_s) is None:
        return fail("NONCANONICAL_RATIONAL_DENOMINATOR", repr(d_s)), None
    if reduced_flag is not True:
        return fail("RATIONAL_REDUCED_FLAG_REQUIRED"), None

    n, d = int(n_s), int(d_s)
    if d <= 0:
        return fail("RATIONAL_DENOMINATOR_NONPOSITIVE"), None
    if n < 0 or n > d:
        return fail("RATIONAL_OUT_OF_PROBABILITY_RANGE", f"{n}/{d}"), None
    if gcd(n, d) != 1:
        return fail("NONCANONICAL_RATIONAL_NOT_REDUCED", f"{n}/{d}"), None
    if n == 0 and d != 1:
        return fail("NONCANONICAL_ZERO_MUST_BE_0_OVER_1", f"{n}/{d}"), None
    if n == d and (n, d) != (1, 1):
        return fail("NONCANONICAL_ONE_MUST_BE_1_OVER_1", f"{n}/{d}"), None

    return ok("CANONICAL_RATIONAL_PASS"), Fraction(n, d)


def exact_hit_cap(candidate_count: int, p: Fraction) -> Fraction:
    if not isinstance(candidate_count, int) or candidate_count < 1:
        raise ValueError("candidate_count must be a positive integer")
    if p < 0 or p > 1:
        raise ValueError("p must be in [0,1]")
    value = candidate_count * p
    return min(Fraction(1, 1), value)


def zero_cap_outcome(a_i: Fraction, hit: bool) -> CheckResult:
    """Explicit zero-cap branch; never evaluates X_i / a_i when a_i == 0."""
    if a_i != 0:
        return ok("POSITIVE_CAP_USE_STATISTICAL_PROFILE")
    if hit:
        return fail(
            "ZERO_CAP_HIT_FORWARD_NULL_PREMISE_CONTRADICTION",
            "Observed hit has zero probability under the instantiated null/premises.",
        )
    return ok("ZERO_CAP_MISS_PASS")


def validate_candidate_generation_profile(profile: Mapping[str, Any], strongest_grade: bool = True) -> CheckResult:
    if profile.get("schema") != "AIFC/candidate-generation-profile/v1":
        return fail("CANDIDATE_PROFILE_SCHEMA_MISMATCH")
    if not _is_hex64(profile.get("created_slot_certificate_hash")):
        return fail("CANDIDATE_PROFILE_CREATED_BINDING_INVALID")
    k = profile.get("candidate_set_cardinality_upper_bound")
    if not isinstance(k, int) or k < 1:
        return fail("CANDIDATE_PROFILE_CARDINALITY_INVALID")

    selection = profile.get("selection_freedom")
    if not isinstance(selection, Mapping):
        return fail("CANDIDATE_PROFILE_SELECTION_FREEDOM_MISSING")
    if not isinstance(selection.get("hidden_pool_exclusion_basis"), str) or not selection.get("hidden_pool_exclusion_basis"):
        return fail("SHADOW_CANDIDATE_POOL_NOT_ADDRESSED")

    unresolved = profile.get("unresolved_assumptions")
    if not isinstance(unresolved, list):
        return fail("CANDIDATE_PROFILE_UNRESOLVED_ASSUMPTIONS_INVALID")

    evidence = profile.get("external_evidence")
    if not isinstance(evidence, list) or not evidence:
        return fail("CANDIDATE_PROFILE_EXTERNAL_EVIDENCE_MISSING")

    if strongest_grade:
        if selection.get("operator_choice_after_generation") is True:
            return fail("UNDECLARED_OR_DISALLOWED_POST_GENERATION_CANDIDATE_CHOICE")
        if unresolved:
            return fail("SHADOW_CANDIDATE_POOL_NOT_EXCLUDED", "; ".join(map(str, unresolved)))
        if profile.get("admission_status") != "ADMITTED":
            return fail("CANDIDATE_PROFILE_NOT_ADMITTED", str(profile.get("admission_status")))

    return ok("CANDIDATE_GENERATION_PROVENANCE_PASS")


def validate_target_derivation_bindings(
    profile_hash: str,
    profile: Mapping[str, Any],
    pre_return: Mapping[str, Any],
    entropy_profile: Mapping[str, Any],
    target_evidence: Mapping[str, Any],
) -> CheckResult:
    if not _is_hex64(profile_hash):
        return fail("TARGET_DERIVATION_PROFILE_HASH_INVALID")
    if profile.get("schema") != "AIFC/target-derivation-profile/v1":
        return fail("TARGET_DERIVATION_PROFILE_SCHEMA_MISMATCH")
    if profile.get("frozen_before_target") is not True:
        return fail("POST_HOC_TARGET_DERIVATION")

    for obj_name, obj in (
        ("PRE_RETURN", pre_return),
        ("ENTROPY_PROFILE", entropy_profile),
        ("TARGET_EVIDENCE", target_evidence),
    ):
        if obj.get("target_derivation_profile_hash") != profile_hash:
            return fail("TARGET_DERIVATION_PROFILE_REBINDING", obj_name)

    if not _is_hex64(target_evidence.get("raw_source_object_hash")):
        return fail("RAW_SOURCE_OBJECT_BINDING_MISSING")
    if target_evidence.get("target_selector_hash") != profile.get("event_selector_hash"):
        return fail("TARGET_SELECTOR_DERIVATION_MISMATCH")

    rule = profile.get("transformation_rule")
    if not isinstance(rule, Mapping):
        return fail("TARGET_TRANSFORMATION_RULE_MISSING")
    if not isinstance(rule.get("input_order"), list) or not rule.get("input_order"):
        return fail("TARGET_TRANSFORMATION_INPUT_ORDER_INVALID")

    return ok("TARGET_DERIVATION_BINDINGS_PASS")


def _validate_transition_quorum(
    qobj: Mapping[str, Any],
    *,
    expected_role: str,
    expected_registry_hash: str,
    expected_body_hash: str,
) -> CheckResult:
    if qobj.get("schema") != "AIFC/registry-transition-quorum/v1":
        return fail("REGISTRY_TRANSITION_QUORUM_SCHEMA_MISMATCH", expected_role)
    if qobj.get("role") != expected_role:
        return fail("REGISTRY_TRANSITION_QUORUM_ROLE_MISMATCH", expected_role)
    if qobj.get("signing_registry_hash") != expected_registry_hash:
        return fail("REGISTRY_TRANSITION_SIGNING_REGISTRY_MISMATCH", expected_role)
    if qobj.get("transition_body_hash") != expected_body_hash:
        return fail("REGISTRY_TRANSITION_BODY_HASH_REBINDING", expected_role)

    n, f, q = qobj.get("n"), qobj.get("f"), qobj.get("q")
    if not all(isinstance(x, int) for x in (n, f, q)):
        return fail("REGISTRY_TRANSITION_FAULT_MODEL_INVALID", expected_role)
    if n < 1 or f < 0 or q < 1 or f >= n or q > n:
        return fail("REGISTRY_TRANSITION_FAULT_MODEL_RANGE_INVALID", expected_role)
    if 2 * q <= n + f:
        return fail("REGISTRY_TRANSITION_UNSAFE_QUORUM", expected_role)

    receipts = qobj.get("receipts")
    if not isinstance(receipts, list) or len(receipts) < q:
        return fail("REGISTRY_TRANSITION_INSUFFICIENT_RECEIPTS", expected_role)

    seen: set[str] = set()
    for receipt in receipts:
        if not isinstance(receipt, Mapping):
            return fail("REGISTRY_TRANSITION_RECEIPT_UNTYPED", expected_role)
        if receipt.get("schema") != "AIFC/registry-transition-receipt/v1":
            return fail("REGISTRY_TRANSITION_RECEIPT_SCHEMA_MISMATCH", expected_role)
        if receipt.get("role") != expected_role:
            return fail("REGISTRY_TRANSITION_RECEIPT_ROLE_MISMATCH", expected_role)
        if receipt.get("signing_registry_hash") != expected_registry_hash:
            return fail("REGISTRY_TRANSITION_RECEIPT_REGISTRY_REBINDING", expected_role)
        if receipt.get("transition_body_hash") != expected_body_hash:
            return fail("REGISTRY_TRANSITION_RECEIPT_BODY_REBINDING", expected_role)
        wid = receipt.get("witness_id")
        if not isinstance(wid, str) or not wid:
            return fail("REGISTRY_TRANSITION_WITNESS_ID_INVALID", expected_role)
        seen.add(wid)

    if len(seen) < q:
        return fail("REGISTRY_TRANSITION_DISTINCT_WITNESS_QUORUM_NOT_MET", expected_role)

    # v0.1 frontier limitation: signatures and key-registry intervals are not yet
    # cryptographically verified here. Full Implementation A remains blocked.
    return ok("REGISTRY_TRANSITION_STRUCTURAL_QUORUM_PASS", expected_role)


def validate_registry_transition(certificate: Mapping[str, Any]) -> CheckResult:
    if certificate.get("schema") != "AIFC/registry-transition-certificate/v1":
        return fail("REGISTRY_TRANSITION_CERT_SCHEMA_MISMATCH")

    body = certificate.get("transition_body")
    if not isinstance(body, Mapping) or body.get("schema") != "AIFC/registry-transition-body/v1":
        return fail("REGISTRY_TRANSITION_BODY_INVALID")
    prev_seq, next_seq = body.get("previous_registry_sequence"), body.get("next_registry_sequence")
    if not isinstance(prev_seq, int) or not isinstance(next_seq, int) or next_seq != prev_seq + 1:
        return fail("REGISTRY_SEQUENCE_JUMP")
    prev_hash, next_hash = body.get("previous_registry_hash"), body.get("next_registry_hash")
    body_hash = certificate.get("transition_body_hash")
    if not all(_is_hex64(x) for x in (prev_hash, next_hash, body_hash)):
        return fail("REGISTRY_TRANSITION_HASH_BINDING_INVALID")

    old_q = certificate.get("old_registry_authorization")
    new_q = certificate.get("new_registry_acceptance")
    if not isinstance(old_q, Mapping):
        return fail("OLD_QUORUM_AUTHORIZATION_MISSING")
    if not isinstance(new_q, Mapping):
        return fail("NEW_QUORUM_ACCEPTANCE_MISSING")

    old_res = _validate_transition_quorum(
        old_q,
        expected_role="OLD_REGISTRY_AUTHORIZATION",
        expected_registry_hash=prev_hash,
        expected_body_hash=body_hash,
    )
    if not old_res.ok:
        return old_res
    new_res = _validate_transition_quorum(
        new_q,
        expected_role="NEW_REGISTRY_ACCEPTANCE",
        expected_registry_hash=next_hash,
        expected_body_hash=body_hash,
    )
    if not new_res.ok:
        return new_res

    return ok(
        "REGISTRY_TRANSITION_STRUCTURAL_PASS",
        "Signature/key-interval verification remains pending in Verifier A v0.1.",
    )


def validate_release_manifest_structure(manifest: Mapping[str, Any], required_gate_ids: Sequence[str]) -> CheckResult:
    if manifest.get("schema") != "AIFC/release-manifest/v1":
        return fail("RELEASE_MANIFEST_SCHEMA_MISMATCH")
    rows = manifest.get("gate_results")
    if not isinstance(rows, list):
        return fail("RELEASE_MANIFEST_GATE_RESULTS_MISSING")

    ids: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping):
            return fail("RELEASE_MANIFEST_GATE_RESULT_UNTYPED")
        gid = row.get("gate_id")
        if not isinstance(gid, str):
            return fail("RELEASE_MANIFEST_GATE_ID_INVALID")
        ids.append(gid)
        if not _is_hex64(row.get("evidence_hash")):
            return fail("RELEASE_MANIFEST_EVIDENCE_HASH_INVALID", gid)

    if len(ids) != len(set(ids)):
        return fail("RELEASE_MANIFEST_DUPLICATE_GATE")
    if set(ids) != set(required_gate_ids):
        return fail("RELEASE_MANIFEST_GATE_SET_MISMATCH")

    if manifest.get("overall_status") == "FROZEN_PASS":
        for row in rows:
            if row.get("result") != "PASS":
                return fail("FROZEN_PASS_WITH_NONPASS_GATE", str(row.get("gate_id")))

    return ok("RELEASE_MANIFEST_STRUCTURE_PASS")
