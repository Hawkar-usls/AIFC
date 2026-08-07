#!/usr/bin/env python3
"""Standalone AIFC Verifier A evidence replay engine v0.2.

Input is an AIFC/replay-package/v0.2 manifest containing content hashes plus a
content-addressed EvidenceResolver. Every protocol object is resolved from exact
bytes and independently rehashed before use.

Implemented here:
- experiment-plan and machine policy binding;
- complete fixed-horizon ledger replay and publication visibility;
- candidate-set reconstruction and multiplicity;
- candidate provenance policy checks;
- registry chain/fault-model/failure-domain replay (signatures still blocked);
- CREATED, PRE_RETURN and PRE_TARGET_VIEW quorum structural replay;
- frozen pre-target conditioning-view binding;
- canonical rational entropy-bound structure and evidence resolution;
- fixed-event target-selector replay;
- strict byte-level target derivation from resolved raw source bytes;
- exact candidate/target identity;
- evidence-bundle and terminal-event choreography;
- publication-manifest completeness checks.

Still deliberately blocked for full Implementation A:
- Ed25519 cryptographic signature verification;
- independent causal d-separation engine;
- source-specific cryptographic beacon proof verification;
- complete experiment-wide statistical/e-process replay;
- independent cross-language canonicalization.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from fractions import Fraction
import hashlib
from typing import Any, Mapping, Sequence

from canonical import CanonicalizationError, loads_strict, protocol_hash
from frontier import (
    exact_hit_cap,
    experiment_genesis_hash,
    validate_candidate_generation_profile,
    validate_canonical_rational,
    zero_cap_outcome,
)
from resolver import EvidenceResolutionError, EvidenceResolver

NORMAL_NEXT = {
    None: "CREATED",
    "CREATED": "PRE_RETURN_FROZEN",
    "PRE_RETURN_FROZEN": "QUORUM_CERTIFIED",
    "QUORUM_CERTIFIED": "TARGET_ARMED",
    "TARGET_ARMED": "TARGET_OBSERVED",
    "TARGET_OBSERVED": "VERIFIED",
    "VERIFIED": "TERMINAL",
}

TERMINAL_SUBTYPES = {
    "COMPLETED_HIT",
    "COMPLETED_MISS",
    "INVALIDATED_EVIDENCE",
    "ABORTED_PRE_FREEZE",
    "ABORTED_POST_FREEZE_PRE_TARGET",
    "ABORTED_POST_TARGET_PRE_VERIFY",
    "ABORTED_RECOVERY_FAILURE",
}


@dataclass(frozen=True)
class ReplayProblem:
    gate: str
    code: str
    detail: str = ""


class ReplayRejected(ValueError):
    def __init__(self, problem: ReplayProblem):
        super().__init__(f"{problem.gate}:{problem.code}:{problem.detail}")
        self.problem = problem


def _reject(gate: str, code: str, detail: str = "") -> None:
    raise ReplayRejected(ReplayProblem(gate, code, detail))


def _require(condition: bool, gate: str, code: str, detail: str = "") -> None:
    if not condition:
        _reject(gate, code, detail)


def _obj(resolver: EvidenceResolver, content_hash: str, schema: str) -> Mapping[str, Any]:
    resolved = resolver.resolve(content_hash, expected_schema=schema)
    if resolved.parsed_json is None:
        _reject("EVIDENCE_RESOLUTION", "EXPECTED_PROTOCOL_JSON", content_hash)
    return resolved.parsed_json


def _resolve_hashes(resolver: EvidenceResolver, hashes: Sequence[str], gate: str) -> None:
    for content_hash in hashes:
        try:
            resolver.resolve(content_hash)
        except EvidenceResolutionError as exc:
            _reject(gate, "DANGLING_OR_INVALID_EVIDENCE", str(exc))


def registry_genesis_hash(experiment_id: str) -> str:
    payload = b"AIFC:WITNESS_REGISTRY_GENESIS:v1\x00" + experiment_id.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def target_bytes_hash(target_bytes: bytes) -> str:
    return hashlib.sha256(b"AIFC:TARGET_BYTES:v1\x00" + target_bytes).hexdigest()


def hard_witness_bytes(witness: Mapping[str, Any]) -> bytes:
    payload = witness.get("payload128")
    nonce = witness.get("nonce128")
    _require(isinstance(payload, str) and isinstance(nonce, str), "CANDIDATE_SET_REPLAY", "HARD_WITNESS_HEX_TYPE_INVALID")
    try:
        raw = bytes.fromhex(payload + nonce)
    except ValueError as exc:
        _reject("CANDIDATE_SET_REPLAY", "HARD_WITNESS_HEX_INVALID", str(exc))
    _require(len(raw) == 32, "CANDIDATE_SET_REPLAY", "HARD_WITNESS_NOT_256_BITS")
    return raw


def _context(obj: Mapping[str, Any], experiment_id: str, trial_index: int | None = None, run_id: str | None = None) -> None:
    _require(obj.get("experiment_id") == experiment_id, "CONTEXT_BINDING", "EXPERIMENT_ID_MISMATCH", str(obj.get("schema")))
    if trial_index is not None and "trial_index" in obj:
        _require(obj.get("trial_index") == trial_index, "CONTEXT_BINDING", "TRIAL_INDEX_MISMATCH", str(obj.get("schema")))
    if run_id is not None and "run_id" in obj:
        _require(obj.get("run_id") == run_id, "CONTEXT_BINDING", "RUN_ID_MISMATCH", str(obj.get("schema")))


def replay_ledger(events: Sequence[Mapping[str, Any]], experiment_id: str, declared_trial_count: int, experiment_plan_hash: str) -> dict[str, Any]:
    _require(len(events) > 0, "LEDGER_REPLAY", "LEDGER_EMPTY")
    expected_prev = experiment_genesis_hash(experiment_id)
    state: dict[int, str | None] = {}
    ordinals: dict[int, int] = {}
    terminal: dict[int, Mapping[str, Any]] = {}
    hashes: list[str] = []
    by_trial_state: dict[int, dict[str, tuple[Mapping[str, Any], str]]] = {}

    for i, event in enumerate(events):
        _context(event, experiment_id)
        _require(event.get("schema") == "AIFC/trial-ledger-event/v1", "LEDGER_REPLAY", "LEDGER_EVENT_SCHEMA_MISMATCH", str(i))
        _require(event.get("event_index") == i, "LEDGER_REPLAY", "EVENT_INDEX_GAP_OR_REORDER", str(i))
        _require(event.get("previous_event_hash") == expected_prev, "LEDGER_REPLAY", "LEDGER_PREDECESSOR_MISMATCH", str(i))
        trial = event.get("trial_index")
        _require(isinstance(trial, int) and 1 <= trial <= declared_trial_count, "LEDGER_REPLAY", "TRIAL_INDEX_OUTSIDE_PLAN", str(trial))
        _require(trial not in terminal, "LEDGER_REPLAY", "TERMINAL_RESURRECTION", str(trial))

        current = state.get(trial)
        expected_ordinal = ordinals.get(trial, 0)
        _require(event.get("transition_ordinal") == expected_ordinal, "LEDGER_REPLAY", "TRANSITION_ORDINAL_GAP", str(trial))
        _require(event.get("state_from") == current, "LEDGER_REPLAY", "STATE_FROM_MISMATCH", str(trial))
        state_to = event.get("state_to")
        normal = NORMAL_NEXT.get(current)
        if state_to == "TERMINAL" and current is not None:
            _require(event.get("terminal_subtype") in TERMINAL_SUBTYPES, "LEDGER_REPLAY", "TERMINAL_SUBTYPE_INVALID", str(trial))
        else:
            _require(state_to == normal, "LEDGER_REPLAY", "FORBIDDEN_STATE_TRANSITION", f"{current}->{state_to}")
            if state_to != "TERMINAL":
                _require(event.get("terminal_subtype") in (None, ""), "LEDGER_REPLAY", "NONTERMINAL_HAS_TERMINAL_SUBTYPE", str(trial))

        if state_to == "CREATED":
            _require(event.get("payload_hash") == experiment_plan_hash, "EXPERIMENT_PLAN_BINDING", "CREATED_DOES_NOT_BIND_EXPERIMENT_PLAN", str(trial))

        event_hash = protocol_hash(event)
        hashes.append(event_hash)
        expected_prev = event_hash
        state[trial] = state_to
        ordinals[trial] = expected_ordinal + 1
        by_trial_state.setdefault(trial, {})[str(state_to)] = (event, event_hash)
        if state_to == "TERMINAL":
            terminal[trial] = event

    expected_trials = set(range(1, declared_trial_count + 1))
    _require(set(state) == expected_trials, "COMPLETE_TRIAL_PUBLICATION", "MISSING_DECLARED_TRIAL", str(sorted(expected_trials - set(state))))
    _require(set(terminal) == expected_trials, "COMPLETE_TRIAL_PUBLICATION", "NONTERMINAL_DECLARED_TRIAL", str(sorted(expected_trials - set(terminal))))
    return {
        "event_hashes": hashes,
        "final_head": hashes[-1],
        "terminal": terminal,
        "by_trial_state": by_trial_state,
    }


def _state_event(ledger: Mapping[str, Any], trial: int, state: str) -> tuple[Mapping[str, Any], str]:
    try:
        return ledger["by_trial_state"][trial][state]
    except KeyError:
        _reject("LEDGER_REPLAY", "SUBJECT_STATE_EVENT_MISSING", f"trial={trial},state={state}")


def _validate_registry_object(registry: Mapping[str, Any], registry_hash: str, experiment_id: str) -> dict[str, Mapping[str, Any]]:
    _context(registry, experiment_id)
    _require(registry.get("schema") == "AIFC/witness-registry/v1", "WITNESS_REGISTRY_REPLAY", "REGISTRY_SCHEMA_MISMATCH")
    seq = registry.get("registry_sequence")
    _require(isinstance(seq, int) and seq >= 0, "WITNESS_REGISTRY_REPLAY", "REGISTRY_SEQUENCE_INVALID")
    if seq == 0:
        _require(registry.get("previous_registry_hash") == registry_genesis_hash(experiment_id), "WITNESS_REGISTRY_REPLAY", "REGISTRY_GENESIS_PREDECESSOR_MISMATCH")
        _require(registry.get("transition_certificate_hash") is None, "WITNESS_REGISTRY_REPLAY", "GENESIS_REGISTRY_HAS_TRANSITION_CERT")

    fault = registry.get("fault_model")
    _require(isinstance(fault, Mapping), "WITNESS_REGISTRY_REPLAY", "REGISTRY_FAULT_MODEL_MISSING")
    n, f, q = fault.get("n"), fault.get("f"), fault.get("q")
    _require(all(isinstance(x, int) for x in (n, f, q)), "WITNESS_REGISTRY_REPLAY", "REGISTRY_FAULT_MODEL_TYPE_INVALID")
    _require(n >= 1 and 0 <= f < n and 1 <= q <= n, "WITNESS_REGISTRY_REPLAY", "REGISTRY_FAULT_MODEL_RANGE_INVALID")
    _require(2 * q > n + f, "WITNESS_REGISTRY_REPLAY", "REGISTRY_QUORUM_INTERSECTION_UNSAFE")
    _require(fault.get("independence_unit") == "FAILURE_DOMAIN", "WITNESS_REGISTRY_REPLAY", "REGISTRY_INDEPENDENCE_UNIT_INVALID")

    witnesses = registry.get("witnesses")
    _require(isinstance(witnesses, list) and witnesses, "WITNESS_REGISTRY_REPLAY", "REGISTRY_WITNESS_LIST_INVALID")
    _require(len(witnesses) == n, "WITNESS_REGISTRY_REPLAY", "FAULT_MODEL_REBINDING_N")
    by_id: dict[str, Mapping[str, Any]] = {}
    domains: set[str] = set()
    for witness in witnesses:
        wid = witness.get("witness_id")
        domain = witness.get("failure_domain")
        _require(isinstance(wid, str) and wid, "WITNESS_REGISTRY_REPLAY", "WITNESS_ID_INVALID")
        _require(wid not in by_id, "WITNESS_REGISTRY_REPLAY", "DUPLICATE_WITNESS_ID", wid)
        _require(isinstance(domain, str) and domain, "WITNESS_REGISTRY_REPLAY", "FAILURE_DOMAIN_INVALID", wid)
        by_id[wid] = witness
        if witness.get("status") in {"ACTIVE", "OFFLINE"}:
            domains.add(domain)
    _require(len(domains) >= q, "WITNESS_REGISTRY_REPLAY", "INSUFFICIENT_INDEPENDENT_FAILURE_DOMAINS")
    _require(protocol_hash(registry) == registry_hash, "WITNESS_REGISTRY_REPLAY", "REGISTRY_HASH_RECOMPUTE_MISMATCH")
    return by_id


def _active_key(witness: Mapping[str, Any], key_id: str, registry_sequence: int) -> bool:
    if witness.get("status") != "ACTIVE":
        return False
    for key in witness.get("keys", []):
        if key.get("key_id") != key_id or key.get("algorithm") != "Ed25519" or key.get("status") != "ACTIVE":
            continue
        start = key.get("valid_from_registry_sequence")
        end = key.get("valid_until_registry_sequence")
        if not isinstance(start, int) or start > registry_sequence:
            continue
        if end is not None and (not isinstance(end, int) or registry_sequence > end):
            continue
        return True
    return False


def replay_quorum(cert: Mapping[str, Any], registry: Mapping[str, Any], registry_hash: str, *, experiment_id: str, trial_index: int, logical_position: str, content_hash: str, gate: str) -> str:
    _context(cert, experiment_id, trial_index)
    _require(cert.get("schema") == "AIFC/quorum-certificate/v1", gate, "QUORUM_SCHEMA_MISMATCH")
    _require(cert.get("logical_position") == logical_position, gate, "QUORUM_LOGICAL_POSITION_MISMATCH")
    _require(cert.get("content_hash") == content_hash, gate, "QUORUM_CONTENT_HASH_MISMATCH")
    _require(cert.get("registry_hash") == registry_hash, gate, "QUORUM_REGISTRY_HASH_MISMATCH")
    fault = registry["fault_model"]
    _require((cert.get("n"), cert.get("f"), cert.get("q")) == (fault.get("n"), fault.get("f"), fault.get("q")), gate, "FAULT_MODEL_REBINDING")
    q = int(fault["q"])
    witnesses = _validate_registry_object(registry, registry_hash, experiment_id)
    seq = int(registry["registry_sequence"])
    receipts = cert.get("receipts")
    _require(isinstance(receipts, list) and len(receipts) >= q, gate, "QUORUM_RECEIPT_COUNT_INSUFFICIENT")
    seen_ids: set[str] = set()
    seen_domains: set[str] = set()
    for receipt in receipts:
        _context(receipt, experiment_id, trial_index)
        _require(receipt.get("schema") == "AIFC/witness-receipt/v1", gate, "RECEIPT_SCHEMA_MISMATCH")
        _require(receipt.get("logical_position") == logical_position, gate, "RECEIPT_LOGICAL_POSITION_MISMATCH")
        _require(receipt.get("content_hash") == content_hash, gate, "RECEIPT_CONTENT_HASH_MISMATCH")
        _require(receipt.get("registry_hash") == registry_hash, gate, "RECEIPT_REGISTRY_HASH_MISMATCH")
        wid = receipt.get("witness_id")
        _require(wid in witnesses, gate, "RECEIPT_WITNESS_NOT_IN_REGISTRY", str(wid))
        _require(wid not in seen_ids, gate, "DUPLICATE_WITNESS_RECEIPT", str(wid))
        witness = witnesses[str(wid)]
        _require(_active_key(witness, str(receipt.get("key_id")), seq), gate, "RECEIPT_KEY_NOT_ACTIVE", str(wid))
        seen_ids.add(str(wid))
        seen_domains.add(str(witness.get("failure_domain")))
    _require(len(seen_ids) >= q, gate, "DISTINCT_WITNESS_QUORUM_NOT_MET")
    _require(len(seen_domains) >= q, gate, "SAME_FAILURE_DOMAIN_SYBIL")
    return protocol_hash(cert)


def replay_registry_chain(resolver: EvidenceResolver, plan: Mapping[str, Any], transition_hashes: Sequence[str], final_registry_hash: str, experiment_id: str) -> Mapping[str, Any]:
    current_hash = str(plan.get("initial_witness_registry_hash"))
    current = _obj(resolver, current_hash, "AIFC/witness-registry/v1")
    _validate_registry_object(current, current_hash, experiment_id)
    if not transition_hashes:
        _require(current_hash == final_registry_hash, "REGISTRY_TRANSITION_REPLAY", "FINAL_REGISTRY_WITHOUT_TRANSITION")
        return current

    _require(plan.get("allowed_registry_reconfiguration") is True, "REGISTRY_TRANSITION_REPLAY", "REGISTRY_RECONFIGURATION_NOT_ALLOWED_BY_PLAN")
    for cert_hash in transition_hashes:
        cert = _obj(resolver, cert_hash, "AIFC/registry-transition-certificate/v1")
        body = cert.get("transition_body")
        _require(isinstance(body, Mapping) and body.get("schema") == "AIFC/registry-transition-body/v1", "REGISTRY_TRANSITION_REPLAY", "TRANSITION_BODY_INVALID")
        _context(body, experiment_id)
        body_hash = protocol_hash(body)
        _require(cert.get("transition_body_hash") == body_hash, "REGISTRY_TRANSITION_REPLAY", "TRANSITION_BODY_HASH_MISMATCH")
        _require(body.get("previous_registry_hash") == current_hash, "REGISTRY_TRANSITION_REPLAY", "DISCONNECTED_REGISTRY_CHAIN")
        _require(body.get("previous_registry_sequence") == current.get("registry_sequence"), "REGISTRY_TRANSITION_REPLAY", "REGISTRY_SEQUENCE_REBINDING")
        next_hash = body.get("next_registry_hash")
        _require(isinstance(next_hash, str), "REGISTRY_TRANSITION_REPLAY", "NEXT_REGISTRY_HASH_INVALID")
        nxt = _obj(resolver, next_hash, "AIFC/witness-registry/v1")
        _validate_registry_object(nxt, next_hash, experiment_id)
        _require(nxt.get("registry_sequence") == int(current["registry_sequence"]) + 1, "REGISTRY_TRANSITION_REPLAY", "REGISTRY_SEQUENCE_JUMP")
        _require(nxt.get("previous_registry_hash") == current_hash, "REGISTRY_TRANSITION_REPLAY", "NEXT_REGISTRY_PREDECESSOR_MISMATCH")
        _require(nxt.get("transition_certificate_hash") == cert_hash, "REGISTRY_TRANSITION_REPLAY", "NEXT_REGISTRY_TRANSITION_CERT_MISMATCH")

        # Experiment-scoped transition quorums use each registry's own fault model.
        for role, qobj, reg, reg_hash in (
            ("OLD_REGISTRY_AUTHORIZATION", cert.get("old_registry_authorization"), current, current_hash),
            ("NEW_REGISTRY_ACCEPTANCE", cert.get("new_registry_acceptance"), nxt, next_hash),
        ):
            _require(isinstance(qobj, Mapping), "REGISTRY_TRANSITION_REPLAY", "TRANSITION_QUORUM_MISSING", role)
            _require(qobj.get("schema") == "AIFC/registry-transition-quorum/v1", "REGISTRY_TRANSITION_REPLAY", "TRANSITION_QUORUM_SCHEMA_MISMATCH", role)
            _require(qobj.get("experiment_id") == experiment_id, "REGISTRY_TRANSITION_REPLAY", "REGISTRY_EXPERIMENT_REBINDING", role)
            _require(qobj.get("role") == role, "REGISTRY_TRANSITION_REPLAY", "TRANSITION_QUORUM_ROLE_MISMATCH", role)
            _require(qobj.get("transition_body_hash") == body_hash, "REGISTRY_TRANSITION_REPLAY", "TRANSITION_QUORUM_BODY_REBINDING", role)
            _require(qobj.get("signing_registry_hash") == reg_hash, "REGISTRY_TRANSITION_REPLAY", "TRANSITION_QUORUM_REGISTRY_REBINDING", role)
            fault = reg["fault_model"]
            _require((qobj.get("n"), qobj.get("f"), qobj.get("q")) == (fault.get("n"), fault.get("f"), fault.get("q")), "REGISTRY_TRANSITION_REPLAY", "FAULT_MODEL_REBINDING", role)
            members = _validate_registry_object(reg, reg_hash, experiment_id)
            q = int(fault["q"])
            seen_ids: set[str] = set()
            seen_domains: set[str] = set()
            receipts = qobj.get("receipts")
            _require(isinstance(receipts, list) and len(receipts) >= q, "REGISTRY_TRANSITION_REPLAY", "TRANSITION_RECEIPTS_INSUFFICIENT", role)
            for receipt in receipts:
                _require(receipt.get("schema") == "AIFC/registry-transition-receipt/v1", "REGISTRY_TRANSITION_REPLAY", "TRANSITION_RECEIPT_SCHEMA_MISMATCH", role)
                _require(receipt.get("experiment_id") == experiment_id, "REGISTRY_TRANSITION_REPLAY", "REGISTRY_EXPERIMENT_REBINDING", role)
                _require(receipt.get("role") == role, "REGISTRY_TRANSITION_REPLAY", "TRANSITION_RECEIPT_ROLE_MISMATCH", role)
                _require(receipt.get("transition_body_hash") == body_hash, "REGISTRY_TRANSITION_REPLAY", "TRANSITION_RECEIPT_BODY_REBINDING", role)
                _require(receipt.get("signing_registry_hash") == reg_hash, "REGISTRY_TRANSITION_REPLAY", "TRANSITION_RECEIPT_REGISTRY_REBINDING", role)
                wid = str(receipt.get("witness_id"))
                _require(wid in members, "REGISTRY_TRANSITION_REPLAY", "TRANSITION_WITNESS_NOT_IN_REGISTRY", wid)
                _require(wid not in seen_ids, "REGISTRY_TRANSITION_REPLAY", "TRANSITION_DUPLICATE_WITNESS", wid)
                witness = members[wid]
                _require(_active_key(witness, str(receipt.get("key_id")), int(reg["registry_sequence"])), "REGISTRY_TRANSITION_REPLAY", "TRANSITION_KEY_NOT_ACTIVE", wid)
                seen_ids.add(wid)
                seen_domains.add(str(witness.get("failure_domain")))
            _require(len(seen_ids) >= q, "REGISTRY_TRANSITION_REPLAY", "TRANSITION_DISTINCT_WITNESS_QUORUM_NOT_MET", role)
            _require(len(seen_domains) >= q, "REGISTRY_TRANSITION_REPLAY", "SAME_FAILURE_DOMAIN_SYBIL", role)

        current_hash, current = str(next_hash), nxt

    _require(current_hash == final_registry_hash, "REGISTRY_TRANSITION_REPLAY", "FINAL_REGISTRY_NOT_REACHED")
    return current


def replay_candidate_set(resolver: EvidenceResolver, candidate_set_hash: str, hard_hashes: Sequence[str], experiment_id: str, trial_index: int, run_id: str) -> tuple[Mapping[str, Any], list[bytes]]:
    candidate_set = _obj(resolver, candidate_set_hash, "AIFC/candidate-set/v1")
    _context(candidate_set, experiment_id, trial_index, run_id)
    declared = candidate_set.get("hard_witness_hashes")
    _require(isinstance(declared, list) and declared, "CANDIDATE_SET_REPLAY", "CANDIDATE_HASH_LIST_INVALID")
    _require(declared == sorted(declared), "CANDIDATE_SET_REPLAY", "NONCANONICAL_CANDIDATE_SET_ORDER")
    _require(declared == sorted(hard_hashes), "CANDIDATE_SET_REPLAY", "REPLAY_MANIFEST_CANDIDATE_HASH_MISMATCH")
    _require(candidate_set.get("cardinality") == len(declared), "CANDIDATE_SET_REPLAY", "CANDIDATE_CARDINALITY_MISMATCH")
    raw_candidates: list[bytes] = []
    for h in declared:
        witness = _obj(resolver, h, "AIFC/hard-witness/v1")
        _context(witness, experiment_id, trial_index, run_id)
        raw_candidates.append(hard_witness_bytes(witness))
    return candidate_set, raw_candidates


def _validate_plan_and_policies(resolver: EvidenceResolver, plan_hash: str, experiment_id: str) -> dict[str, Mapping[str, Any]]:
    plan = _obj(resolver, plan_hash, "AIFC/experiment-plan/v1")
    _context(plan, experiment_id)
    _require(plan.get("frozen_before_first_created") is True, "EXPERIMENT_PLAN", "PLAN_NOT_FROZEN")
    _require(plan.get("strongest_grade_exactly_one_target_derivation_per_trial") is True, "EXPERIMENT_PLAN", "MULTIPLE_TARGET_DERIVATIONS_ALLOWED")
    mapping = {
        "trial_creation": ("trial_creation_policy_hash", "AIFC/trial-creation-policy/v1"),
        "candidate_generation": ("candidate_generation_policy_hash", "AIFC/candidate-generation-policy/v1"),
        "target_selector": ("target_selector_policy_hash", "AIFC/target-selector-policy/v1"),
        "target_derivation": ("target_derivation_policy_hash", "AIFC/target-derivation-policy/v1"),
        "causal_model": ("causal_model_hash", "AIFC/causal-model/v1"),
        "statistical_plan": ("statistical_plan_hash", "AIFC/statistical-plan/v1"),
        "publication_policy": ("publication_policy_hash", "AIFC/publication-policy/v1"),
        "freshness_policy": ("external_freshness_policy_hash", "AIFC/external-freshness-policy/v1"),
        "conditioning_policy": ("conditioning_view_policy_hash", "AIFC/conditioning-view-policy/v1"),
    }
    out: dict[str, Mapping[str, Any]] = {"plan": plan}
    for name, (field, schema) in mapping.items():
        h = plan.get(field)
        _require(isinstance(h, str), "EXPERIMENT_PLAN", "PLAN_POLICY_HASH_MISSING", field)
        obj = _obj(resolver, h, schema)
        _context(obj, experiment_id)
        out[name] = obj
    return out


def _validate_candidate_profile(resolver: EvidenceResolver, profile: Mapping[str, Any], profile_hash: str, policy: Mapping[str, Any], policy_hash: str, candidate_set: Mapping[str, Any], created_cert_hash: str, experiment_id: str, trial_index: int) -> None:
    _context(profile, experiment_id, trial_index)
    _require(profile.get("policy_hash") == policy_hash, "CANDIDATE_PROVENANCE", "CANDIDATE_POLICY_REBINDING")
    _require(profile.get("created_slot_certificate_hash") == created_cert_hash, "CANDIDATE_PROVENANCE", "CREATED_CERT_REBINDING")
    _require(profile.get("generation_mode") in policy.get("allowed_generation_modes", []), "CANDIDATE_PROVENANCE", "GENERATION_MODE_NOT_ALLOWED")
    k = candidate_set.get("cardinality")
    _require(profile.get("candidate_set_cardinality_upper_bound") == k, "CANDIDATE_PROVENANCE", "PROFILE_K_NOT_EXACT_CANDIDATE_SET")
    _require(isinstance(k, int) and k <= policy.get("maximum_candidate_set_cardinality", 0), "CANDIDATE_PROVENANCE", "CANDIDATE_SET_EXCEEDS_PLAN_POLICY")
    result = validate_candidate_generation_profile(profile, strongest_grade=True)
    _require(result.ok, "CANDIDATE_PROVENANCE", result.code, result.detail)
    for row in profile.get("external_evidence", []):
        resolver.resolve(str(row.get("content_hash")))


def _validate_selector(profile: Mapping[str, Any], policy: Mapping[str, Any], *, profile_hash: str, policy_hash: str, plan_hash: str, pre_return_quorum_hash: str, pre_target_view_quorum_hash: str, experiment_id: str, trial_index: int, resolver: EvidenceResolver) -> None:
    _context(profile, experiment_id, trial_index)
    _require(profile.get("policy_hash") == policy_hash, "TARGET_SELECTOR_REPLAY", "SELECTOR_POLICY_REBINDING")
    for field in ("source_id", "source_protocol_version", "selection_algorithm", "anchor_role"):
        _require(profile.get(field) == policy.get(field), "TARGET_SELECTOR_REPLAY", "SELECTOR_POLICY_FIELD_REBINDING", field)
    _require(profile.get("frozen_before_target_observed") is True, "TARGET_SELECTOR_REPLAY", "POST_HOC_TARGET_SELECTOR")
    _require(profile.get("alternative_selected_events") in (None, []), "TARGET_SELECTOR_REPLAY", "MULTIPLE_TARGET_EVENTS_FORBIDDEN")
    anchor_role = profile.get("anchor_role")
    expected_anchor = {
        "EXPERIMENT_PLAN": plan_hash,
        "PRE_RETURN_QUORUM_CERTIFICATE": pre_return_quorum_hash,
        "PRE_TARGET_VIEW_QUORUM_CERTIFICATE": pre_target_view_quorum_hash,
    }.get(anchor_role)
    _require(expected_anchor is not None and profile.get("anchor_hash") == expected_anchor, "TARGET_SELECTOR_REPLAY", "SELECTOR_ANCHOR_REBINDING")
    resolver.resolve(str(profile.get("selection_transcript_hash")))

    algorithm = profile.get("selection_algorithm")
    if algorithm == "FIXED_EVENT_ID_FROM_PLAN":
        fixed = policy.get("parameters", {}).get("fixed_event_id")
        _require(isinstance(fixed, str) and fixed, "TARGET_SELECTOR_REPLAY", "FIXED_EVENT_ID_MISSING_IN_POLICY")
        _require(profile.get("parameters", {}).get("fixed_event_id") == fixed, "TARGET_SELECTOR_REPLAY", "FIXED_EVENT_PARAMETER_REBINDING")
        _require(profile.get("selected_event_id") == fixed, "TARGET_SELECTOR_REPLAY", "SELECTED_EVENT_RECOMPUTE_MISMATCH")
    else:
        _reject("TARGET_SELECTOR_REPLAY", "SELECTOR_ALGORITHM_REPLAY_NOT_IMPLEMENTED", str(algorithm))


def _json_pointer(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    _require(pointer.startswith("/"), "TARGET_DERIVATION_REPLAY", "JSON_POINTER_INVALID", pointer)
    value = document
    for raw_token in pointer.split("/")[1:]:
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            _require(token.isdigit(), "TARGET_DERIVATION_REPLAY", "JSON_POINTER_ARRAY_INDEX_INVALID", token)
            idx = int(token)
            _require(0 <= idx < len(value), "TARGET_DERIVATION_REPLAY", "JSON_POINTER_INDEX_OUT_OF_RANGE", token)
            value = value[idx]
        elif isinstance(value, Mapping):
            _require(token in value, "TARGET_DERIVATION_REPLAY", "JSON_POINTER_KEY_MISSING", token)
            value = value[token]
        else:
            _reject("TARGET_DERIVATION_REPLAY", "JSON_POINTER_DESCENDS_NONCONTAINER", token)
    return value


def _extract_source(raw: bytes, extraction: Mapping[str, Any]) -> bytes:
    method = extraction.get("method")
    if method == "WHOLE_RAW_BYTES":
        return raw
    try:
        document = loads_strict(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, CanonicalizationError) as exc:
        _reject("TARGET_DERIVATION_REPLAY", "RAW_SOURCE_JSON_PARSE_FAILED", str(exc))
    pointer = extraction.get("json_pointer")
    _require(isinstance(pointer, str), "TARGET_DERIVATION_REPLAY", "JSON_POINTER_MISSING")
    value = _json_pointer(document, pointer)
    _require(isinstance(value, str), "TARGET_DERIVATION_REPLAY", "EXTRACTED_VALUE_NOT_STRING")
    if method == "JSON_POINTER_UTF8_STRING":
        return value.encode("utf-8")
    if method == "JSON_POINTER_HEX_BYTES":
        try:
            return bytes.fromhex(value)
        except ValueError as exc:
            _reject("TARGET_DERIVATION_REPLAY", "EXTRACTED_HEX_INVALID", str(exc))
    if method == "JSON_POINTER_BASE64_BYTES":
        try:
            return base64.b64decode(value, validate=True)
        except Exception as exc:
            _reject("TARGET_DERIVATION_REPLAY", "EXTRACTED_BASE64_INVALID", str(exc))
    _reject("TARGET_DERIVATION_REPLAY", "EXTRACTION_METHOD_UNSUPPORTED", str(method))


def _frame_token(token: str, data: bytes) -> bytes:
    name = token.encode("ascii")
    _require(len(name) <= 65535, "TARGET_DERIVATION_REPLAY", "TOKEN_NAME_TOO_LONG")
    return len(name).to_bytes(2, "big") + name + len(data).to_bytes(8, "big") + data


def derive_target(profile: Mapping[str, Any], raw: bytes, *, target_event_id: str, pre_return_hash: str) -> bytes:
    extracted = _extract_source(raw, profile["extraction"])
    token_data = {
        "EXTRACTED_BYTES": extracted,
        "SOURCE_ID_UTF8": str(profile.get("source_id")).encode("utf-8"),
        "SOURCE_PROTOCOL_VERSION_UTF8": str(profile.get("source_protocol_version")).encode("utf-8"),
        "TARGET_EVENT_ID_UTF8": target_event_id.encode("utf-8"),
        "RUN_ID_UTF8": str(profile.get("run_id")).encode("utf-8"),
        "PRE_RETURN_CERTIFICATE_HASH_BYTES": bytes.fromhex(pre_return_hash),
    }
    transformation = profile.get("transformation")
    _require(isinstance(transformation, Mapping), "TARGET_DERIVATION_REPLAY", "TRANSFORMATION_MISSING")
    _require(transformation.get("framing") == "AIFC_TYPED_LENGTH_PREFIXED_V1", "TARGET_DERIVATION_REPLAY", "AMBIGUOUS_DERIVATION_ENCODING")
    order = transformation.get("input_order")
    _require(isinstance(order, list) and order, "TARGET_DERIVATION_REPLAY", "TRANSFORMATION_INPUT_ORDER_INVALID")
    for token in order:
        _require(token in token_data, "TARGET_DERIVATION_REPLAY", "UNKNOWN_INPUT_TOKEN", str(token))
    algorithm = transformation.get("algorithm")
    if algorithm == "IDENTITY":
        _require(order == ["EXTRACTED_BYTES"], "TARGET_DERIVATION_REPLAY", "IDENTITY_REQUIRES_EXTRACTED_BYTES_ONLY")
        out = extracted
    elif algorithm == "SHA-256":
        framed = b"".join(_frame_token(str(token), token_data[str(token)]) for token in order)
        try:
            sep = str(profile.get("domain_separator")).encode("ascii", errors="strict")
        except UnicodeEncodeError as exc:
            _reject("TARGET_DERIVATION_REPLAY", "TARGET_DOMAIN_SEPARATOR_NONASCII", str(exc))
        out = hashlib.sha256(sep + b"\x00" + framed).digest()
    else:
        _reject("TARGET_DERIVATION_REPLAY", "TARGET_ALGORITHM_UNSUPPORTED", str(algorithm))
    _require(len(out) * 8 == profile.get("output_length_bits"), "TARGET_DERIVATION_REPLAY", "TARGET_OUTPUT_LENGTH_MISMATCH")
    return out


def _validate_causal_evidence(resolver: EvidenceResolver, model: Mapping[str, Any], experiment_id: str) -> None:
    _context(model, experiment_id)
    for node in model.get("nodes", []):
        _resolve_hashes(resolver, node.get("evidence_hashes", []), "CAUSAL_MODEL_EVIDENCE")
    for edge in model.get("edges", []):
        hashes = edge.get("evidence_hashes", [])
        _require(isinstance(hashes, list) and hashes, "CAUSAL_MODEL_EVIDENCE", "EDGE_WITHOUT_EVIDENCE")
        _resolve_hashes(resolver, hashes, "CAUSAL_MODEL_EVIDENCE")
    for claim in model.get("no_edge_claims", []):
        if claim.get("basis") == "EVIDENCE_BACKED":
            hashes = claim.get("evidence_hashes", [])
            _require(isinstance(hashes, list) and hashes, "CAUSAL_MODEL_EVIDENCE", "NO_EDGE_WITHOUT_EVIDENCE")
            _resolve_hashes(resolver, hashes, "CAUSAL_MODEL_EVIDENCE")
        else:
            _reject("CAUSAL_MODEL_EVIDENCE", "UNRESOLVED_NO_EDGE_ASSUMPTION", str(claim.get("source")) + "->" + str(claim.get("target")))
    _require(not model.get("unresolved_assumptions"), "CAUSAL_MODEL_EVIDENCE", "CAUSAL_MODEL_UNRESOLVED_ASSUMPTIONS")


def _validate_publication_manifest(resolver: EvidenceResolver, manifest: Mapping[str, Any], manifest_hash: str, *, experiment_id: str, plan_hash: str, publication_policy_hash: str, declared_trial_count: int, ledger: Mapping[str, Any], subject_trial: int, subject_bundle_hash: str) -> None:
    _context(manifest, experiment_id)
    _require(manifest.get("experiment_plan_hash") == plan_hash, "PUBLICATION_MANIFEST_REPLAY", "PUBLICATION_PLAN_REBINDING")
    _require(manifest.get("publication_policy_hash") == publication_policy_hash, "PUBLICATION_MANIFEST_REPLAY", "PUBLICATION_POLICY_REBINDING")
    _require(manifest.get("declared_trial_count") == declared_trial_count, "PUBLICATION_MANIFEST_REPLAY", "PUBLICATION_TRIAL_COUNT_MISMATCH")
    _require(manifest.get("final_ledger_head_hash") == ledger.get("final_head"), "PUBLICATION_MANIFEST_REPLAY", "PUBLICATION_LEDGER_HEAD_MISMATCH")
    records = manifest.get("trial_records")
    _require(isinstance(records, list) and len(records) == declared_trial_count, "PUBLICATION_MANIFEST_REPLAY", "PUBLICATION_RECORD_COUNT_MISMATCH")
    by_trial: dict[int, Mapping[str, Any]] = {}
    for row in records:
        idx = row.get("trial_index")
        _require(isinstance(idx, int) and 1 <= idx <= declared_trial_count, "PUBLICATION_MANIFEST_REPLAY", "PUBLICATION_TRIAL_INDEX_INVALID")
        _require(idx not in by_trial, "PUBLICATION_MANIFEST_REPLAY", "PUBLICATION_DUPLICATE_TRIAL", str(idx))
        by_trial[idx] = row
    _require(set(by_trial) == set(range(1, declared_trial_count + 1)), "PUBLICATION_MANIFEST_REPLAY", "PUBLICATION_TRIAL_GAP")
    for idx, row in by_trial.items():
        terminal_event = ledger["terminal"][idx]
        terminal_hash = protocol_hash(terminal_event)
        _require(row.get("terminal_event_hash") == terminal_hash, "PUBLICATION_MANIFEST_REPLAY", "PUBLICATION_TERMINAL_HASH_MISMATCH", str(idx))
        _require(row.get("terminal_subtype") == terminal_event.get("terminal_subtype"), "PUBLICATION_MANIFEST_REPLAY", "PUBLICATION_TERMINAL_SUBTYPE_MISMATCH", str(idx))
        bundle_hash = row.get("evidence_bundle_hash")
        if idx == subject_trial:
            _require(bundle_hash == subject_bundle_hash, "PUBLICATION_MANIFEST_REPLAY", "SUBJECT_BUNDLE_PUBLICATION_MISMATCH")
        if bundle_hash is not None:
            resolver.resolve(str(bundle_hash), expected_schema="AIFC/evidence-bundle/v1")
    resolver.resolve(str(manifest.get("external_publication_root_hash")))
    _resolve_hashes(resolver, manifest.get("external_publication_receipt_hashes", []), "PUBLICATION_MANIFEST_REPLAY")
    _require(protocol_hash(manifest) == manifest_hash, "PUBLICATION_MANIFEST_REPLAY", "PUBLICATION_MANIFEST_HASH_MISMATCH")


def verify_replay_manifest(manifest: Mapping[str, Any], resolver: EvidenceResolver) -> dict[str, Any]:
    gates: dict[str, str] = {}
    try:
        _require(manifest.get("schema") == "AIFC/replay-package/v0.2", "REPLAY_PACKAGE", "REPLAY_PACKAGE_SCHEMA_MISMATCH")
        experiment_id = manifest.get("experiment_id")
        subject_trial = manifest.get("subject_trial_index")
        _require(isinstance(experiment_id, str) and experiment_id, "REPLAY_PACKAGE", "EXPERIMENT_ID_INVALID")
        _require(isinstance(subject_trial, int) and subject_trial >= 1, "REPLAY_PACKAGE", "SUBJECT_TRIAL_INVALID")

        plan_hash = str(manifest.get("experiment_plan_hash"))
        plan_objects = _validate_plan_and_policies(resolver, plan_hash, experiment_id)
        plan = plan_objects["plan"]
        gates["EXPERIMENT_PLAN_REPLAY"] = "PASS"
        _require(plan.get("mode") == "FIXED_HORIZON", "STATISTICAL_PLAN_REPLAY", "ANYTIME_EXPERIMENT_REPLAY_NOT_IMPLEMENTED")
        declared_trial_count = plan.get("declared_trial_count")
        _require(isinstance(declared_trial_count, int) and declared_trial_count >= 1, "EXPERIMENT_PLAN_REPLAY", "DECLARED_TRIAL_COUNT_INVALID")
        _require(1 <= subject_trial <= declared_trial_count, "REPLAY_PACKAGE", "SUBJECT_TRIAL_OUTSIDE_PLAN")

        ledger_hashes = manifest.get("ledger_event_hashes")
        _require(isinstance(ledger_hashes, list) and ledger_hashes, "LEDGER_REPLAY", "LEDGER_HASH_LIST_INVALID")
        events = [_obj(resolver, str(h), "AIFC/trial-ledger-event/v1") for h in ledger_hashes]
        ledger = replay_ledger(events, experiment_id, declared_trial_count, plan_hash)
        _require(ledger["event_hashes"] == ledger_hashes, "LEDGER_REPLAY", "LEDGER_HASH_ORDER_MISMATCH")
        gates["LEDGER_REPLAY"] = "PASS"
        gates["COMPLETE_TRIAL_PUBLICATION"] = "PASS"

        bundle_hash = str(manifest.get("evidence_bundle_hash"))
        bundle = _obj(resolver, bundle_hash, "AIFC/evidence-bundle/v1")
        _context(bundle, experiment_id, subject_trial)
        run_id = bundle.get("run_id")
        _require(isinstance(run_id, str) and run_id, "CONTEXT_BINDING", "RUN_ID_INVALID")
        _require(bundle.get("experiment_plan_hash") == plan_hash, "EVIDENCE_BUNDLE_BINDINGS", "BUNDLE_PLAN_HASH_MISMATCH")

        current_registry_hash = str(manifest.get("witness_registry_hash"))
        transition_hashes = manifest.get("registry_transition_certificate_hashes")
        _require(isinstance(transition_hashes, list), "REGISTRY_TRANSITION_REPLAY", "TRANSITION_HASH_LIST_INVALID")
        registry = replay_registry_chain(resolver, plan, transition_hashes, current_registry_hash, experiment_id)
        _require(bundle.get("witness_registry_hash") == current_registry_hash, "EVIDENCE_BUNDLE_BINDINGS", "BUNDLE_REGISTRY_HASH_MISMATCH")
        expected_transition_hash = transition_hashes[-1] if transition_hashes else None
        _require(bundle.get("witness_registry_transition_hash") == expected_transition_hash, "EVIDENCE_BUNDLE_BINDINGS", "BUNDLE_TRANSITION_HASH_MISMATCH")
        gates["REGISTRY_TRANSITION_REPLAY"] = "PASS"
        gates["WITNESS_REGISTRY_FAULT_MODEL"] = "PASS"

        created_event, created_event_hash = _state_event(ledger, subject_trial, "CREATED")
        created_cert_hash = str(manifest.get("created_quorum_certificate_hash"))
        created_cert = _obj(resolver, created_cert_hash, "AIFC/quorum-certificate/v1")
        replay_quorum(created_cert, registry, current_registry_hash, experiment_id=experiment_id, trial_index=subject_trial, logical_position="CREATED", content_hash=created_event_hash, gate="CREATED_QUORUM_REPLAY")
        gates["CREATED_QUORUM_REPLAY"] = "PASS"

        candidate_set_hash = str(manifest.get("candidate_set_hash"))
        hard_hashes = manifest.get("hard_witness_hashes")
        _require(isinstance(hard_hashes, list), "CANDIDATE_SET_REPLAY", "HARD_WITNESS_HASH_LIST_INVALID")
        candidate_set, candidate_bytes = replay_candidate_set(resolver, candidate_set_hash, hard_hashes, experiment_id, subject_trial, run_id)
        gates["CANDIDATE_SET_REPLAY"] = "PASS"

        candidate_profile_hash = str(manifest.get("candidate_generation_profile_hash"))
        candidate_profile = _obj(resolver, candidate_profile_hash, "AIFC/candidate-generation-profile/v1")
        candidate_policy_hash = str(plan.get("candidate_generation_policy_hash"))
        _validate_candidate_profile(resolver, candidate_profile, candidate_profile_hash, plan_objects["candidate_generation"], candidate_policy_hash, candidate_set, created_cert_hash, experiment_id, subject_trial)
        gates["CANDIDATE_PROVENANCE"] = "PASS"

        pre_return_hash = str(manifest.get("pre_return_certificate_hash"))
        pre_return = _obj(resolver, pre_return_hash, "AIFC/pre-return-certificate/v1")
        _context(pre_return, experiment_id, subject_trial, run_id)
        freeze_event, freeze_event_hash = _state_event(ledger, subject_trial, "PRE_RETURN_FROZEN")
        _require(freeze_event.get("payload_hash") == candidate_set_hash, "PRE_RETURN_REPLAY", "FREEZE_EVENT_CANDIDATE_SET_HASH_MISMATCH")
        _require(pre_return.get("experiment_plan_hash") == plan_hash, "PRE_RETURN_REPLAY", "PRE_RETURN_PLAN_REBINDING")
        _require(pre_return.get("freeze_event_hash") == freeze_event_hash, "PRE_RETURN_REPLAY", "FREEZE_EVENT_HASH_MISMATCH")
        _require(pre_return.get("ledger_head_hash") == freeze_event_hash, "PRE_RETURN_REPLAY", "PRE_RETURN_LEDGER_HEAD_MISMATCH")
        _require(pre_return.get("candidate_set_hash") == candidate_set_hash, "PRE_RETURN_REPLAY", "PRE_RETURN_CANDIDATE_SET_REBINDING")
        _require(pre_return.get("candidate_multiplicity") == candidate_set.get("cardinality"), "PRE_RETURN_REPLAY", "PRE_RETURN_MULTIPLICITY_MISMATCH")
        _require(pre_return.get("candidate_generation_profile_hash") == candidate_profile_hash, "PRE_RETURN_REPLAY", "PRE_RETURN_CANDIDATE_PROFILE_REBINDING")
        _require(pre_return.get("target_selector_policy_hash") == plan.get("target_selector_policy_hash"), "PRE_RETURN_REPLAY", "PRE_RETURN_SELECTOR_POLICY_REBINDING")
        _require(pre_return.get("target_derivation_policy_hash") == plan.get("target_derivation_policy_hash"), "PRE_RETURN_REPLAY", "PRE_RETURN_DERIVATION_POLICY_REBINDING")

        pre_q_hash = str(manifest.get("pre_return_quorum_certificate_hash"))
        pre_q = _obj(resolver, pre_q_hash, "AIFC/quorum-certificate/v1")
        replay_quorum(pre_q, registry, current_registry_hash, experiment_id=experiment_id, trial_index=subject_trial, logical_position="PRE_RETURN_FROZEN", content_hash=freeze_event_hash, gate="PRE_RETURN_QUORUM_REPLAY")
        _require(pre_return.get("quorum_certificate_hash") == pre_q_hash, "PRE_RETURN_QUORUM_REPLAY", "PRE_RETURN_QUORUM_HASH_MISMATCH")
        quorum_event, quorum_event_hash = _state_event(ledger, subject_trial, "QUORUM_CERTIFIED")
        _require(quorum_event.get("payload_hash") == pre_q_hash, "PRE_RETURN_QUORUM_REPLAY", "QUORUM_EVENT_PAYLOAD_MISMATCH")
        gates["PRE_RETURN_REPLAY"] = "PASS"
        gates["PRE_RETURN_QUORUM_REPLAY"] = "PASS"

        selector_hash = str(manifest.get("target_selector_profile_hash"))
        selector = _obj(resolver, selector_hash, "AIFC/target-selector-profile/v1")
        derivation_hash = str(manifest.get("target_derivation_profile_hash"))
        derivation = _obj(resolver, derivation_hash, "AIFC/target-derivation-profile/v1")
        _context(derivation, experiment_id, subject_trial, run_id)
        _require(derivation.get("policy_hash") == plan.get("target_derivation_policy_hash"), "TARGET_DERIVATION_REPLAY", "DERIVATION_POLICY_REBINDING")
        _require(derivation.get("target_selector_profile_hash") == selector_hash, "TARGET_DERIVATION_REPLAY", "DERIVATION_SELECTOR_REBINDING")
        derivation_policy = plan_objects["target_derivation"]
        _require(derivation.get("extraction", {}).get("method") in derivation_policy.get("allowed_extraction_methods", []), "TARGET_DERIVATION_REPLAY", "EXTRACTION_METHOD_NOT_ALLOWED")
        _require(derivation.get("transformation", {}).get("algorithm") in derivation_policy.get("allowed_transformation_algorithms", []), "TARGET_DERIVATION_REPLAY", "TRANSFORMATION_NOT_ALLOWED")
        _require(derivation.get("transformation", {}).get("framing") == derivation_policy.get("framing"), "TARGET_DERIVATION_REPLAY", "DERIVATION_FRAMING_POLICY_MISMATCH")
        _require(set(derivation.get("transformation", {}).get("input_order", [])) <= set(derivation_policy.get("allowed_input_tokens", [])), "TARGET_DERIVATION_REPLAY", "DERIVATION_INPUT_TOKEN_NOT_ALLOWED")

        view_hash = str(manifest.get("pre_target_conditioning_view_hash"))
        view = _obj(resolver, view_hash, "AIFC/pre-target-conditioning-view/v1")
        _context(view, experiment_id, subject_trial, run_id)
        _require(view.get("ledger_head_hash") == quorum_event_hash, "PRE_TARGET_VIEW_REPLAY", "CONDITIONING_VIEW_LEDGER_HEAD_MISMATCH")
        expected_view_bindings = {
            "experiment_plan_hash": plan_hash,
            "candidate_set_hash": candidate_set_hash,
            "candidate_generation_profile_hash": candidate_profile_hash,
            "pre_return_certificate_hash": pre_return_hash,
            "pre_return_quorum_certificate_hash": pre_q_hash,
            "witness_registry_hash": current_registry_hash,
            "target_selector_profile_hash": selector_hash,
            "target_derivation_profile_hash": derivation_hash,
            "causal_model_hash": str(plan.get("causal_model_hash")),
        }
        for field, expected in expected_view_bindings.items():
            _require(view.get(field) == expected, "PRE_TARGET_VIEW_REPLAY", "CONDITIONING_VIEW_REBINDING", field)
        _require(not view.get("unresolved_assumptions"), "PRE_TARGET_VIEW_REPLAY", "POST_HOC_CONDITIONING_VIEW_SANITIZATION_OR_UNRESOLVED_VIEW")
        conditioning_policy = plan_objects["conditioning_policy"]
        if conditioning_policy.get("operator_state_evidence_required") is True:
            _require(bool(view.get("operator_state_evidence_hashes")), "PRE_TARGET_VIEW_REPLAY", "OPERATOR_STATE_EVIDENCE_MISSING")
        if conditioning_policy.get("source_state_evidence_required") is True:
            _require(bool(view.get("source_state_evidence_hashes")), "PRE_TARGET_VIEW_REPLAY", "SOURCE_STATE_EVIDENCE_MISSING")
        _resolve_hashes(resolver, view.get("operator_state_evidence_hashes", []), "PRE_TARGET_VIEW_REPLAY")
        _resolve_hashes(resolver, view.get("source_state_evidence_hashes", []), "PRE_TARGET_VIEW_REPLAY")
        _resolve_hashes(resolver, view.get("additional_pre_target_evidence_hashes", []), "PRE_TARGET_VIEW_REPLAY")

        view_q_hash = str(manifest.get("pre_target_view_quorum_certificate_hash"))
        view_q = _obj(resolver, view_q_hash, "AIFC/quorum-certificate/v1")
        replay_quorum(view_q, registry, current_registry_hash, experiment_id=experiment_id, trial_index=subject_trial, logical_position="PRE_TARGET_VIEW_FROZEN", content_hash=view_hash, gate="PRE_TARGET_VIEW_QUORUM_REPLAY")
        armed_event, _ = _state_event(ledger, subject_trial, "TARGET_ARMED")
        _require(armed_event.get("payload_hash") == view_q_hash, "PRE_TARGET_VIEW_QUORUM_REPLAY", "TARGET_ARMED_PAYLOAD_NOT_VIEW_QUORUM")
        gates["PRE_TARGET_VIEW_REPLAY"] = "PASS"
        gates["PRE_TARGET_VIEW_QUORUM_REPLAY"] = "PASS"

        _validate_selector(selector, plan_objects["target_selector"], profile_hash=selector_hash, policy_hash=str(plan.get("target_selector_policy_hash")), plan_hash=plan_hash, pre_return_quorum_hash=pre_q_hash, pre_target_view_quorum_hash=view_q_hash, experiment_id=experiment_id, trial_index=subject_trial, resolver=resolver)
        gates["TARGET_SELECTOR_REPLAY"] = "PASS"

        entropy_hash = str(manifest.get("entropy_profile_hash"))
        entropy = _obj(resolver, entropy_hash, "AIFC/entropy-profile/v1")
        _context(entropy, experiment_id, subject_trial)
        _require(entropy.get("target_selector_profile_hash") == selector_hash, "ENTROPY_PROFILE_REPLAY", "ENTROPY_SELECTOR_REBINDING")
        _require(entropy.get("target_derivation_profile_hash") == derivation_hash, "ENTROPY_PROFILE_REPLAY", "ENTROPY_DERIVATION_REBINDING")
        _require(entropy.get("conditioning_view_hash") == view_hash, "ENTROPY_PROFILE_REPLAY", "POST_HOC_CONDITIONING_VIEW_SANITIZATION")
        _require(entropy.get("source_id") == selector.get("source_id") == derivation.get("source_id"), "ENTROPY_PROFILE_REPLAY", "ENTROPY_SOURCE_REBINDING")
        result, p_i = validate_canonical_rational(entropy.get("point_probability_upper_bound", {}))
        _require(result.ok and p_i is not None, "ENTROPY_PROFILE_REPLAY", result.code, result.detail)
        _require(entropy.get("admission_status") == "ADMITTED", "ENTROPY_PROFILE_REPLAY", "ENTROPY_PROFILE_NOT_ADMITTED")
        _require(not entropy.get("unresolved_assumptions"), "ENTROPY_PROFILE_REPLAY", "ENTROPY_UNRESOLVED_ASSUMPTIONS")
        for row in entropy.get("external_evidence", []):
            resolver.resolve(str(row.get("content_hash")))
        if entropy.get("derivation_document_hash") is not None:
            resolver.resolve(str(entropy.get("derivation_document_hash")))
        gates["ENTROPY_PROFILE_REPLAY"] = "PASS"

        causal_hash = str(manifest.get("causal_model_hash"))
        _require(causal_hash == plan.get("causal_model_hash"), "CAUSAL_MODEL_EVIDENCE", "CAUSAL_MODEL_PLAN_REBINDING")
        causal = _obj(resolver, causal_hash, "AIFC/causal-model/v1")
        _validate_causal_evidence(resolver, causal, experiment_id)
        gates["CAUSAL_EVIDENCE_RESOLUTION"] = "PASS"

        statistical_hash = str(manifest.get("statistical_plan_hash"))
        _require(statistical_hash == plan.get("statistical_plan_hash"), "STATISTICAL_PLAN_REPLAY", "STATISTICAL_PLAN_REBINDING")
        statistical = _obj(resolver, statistical_hash, "AIFC/statistical-plan/v1")
        _context(statistical, experiment_id)
        alpha_res, _ = validate_canonical_rational(statistical.get("alpha", {}))
        _require(alpha_res.ok, "STATISTICAL_PLAN_REPLAY", alpha_res.code, alpha_res.detail)
        _require(statistical.get("mode") == "FIXED_HORIZON", "STATISTICAL_PLAN_REPLAY", "ANYTIME_STATISTICS_NOT_IMPLEMENTED")
        _require(statistical.get("declared_horizon") == declared_trial_count, "STATISTICAL_PLAN_REPLAY", "STATISTICAL_HORIZON_REBINDING")
        _require(statistical.get("fixed_horizon_product_bound_policy") == "ONLY_FOR_DETERMINISTIC_OR_PREREGISTERED_CAP_SEQUENCE", "STATISTICAL_PLAN_REPLAY", "FIXED_HORIZON_BOUND_CONDITIONS_NOT_FROZEN")
        gates["STATISTICAL_PLAN_REPLAY"] = "PASS"

        target_hash = str(manifest.get("target_evidence_hash"))
        target = _obj(resolver, target_hash, "AIFC/target-evidence/v1")
        _context(target, experiment_id, subject_trial)
        _require(target.get("target_selector_profile_hash") == selector_hash, "TARGET_DERIVATION_REPLAY", "TARGET_SELECTOR_PROFILE_REBINDING")
        _require(target.get("target_derivation_profile_hash") == derivation_hash, "TARGET_DERIVATION_REPLAY", "TARGET_DERIVATION_PROFILE_REBINDING")
        _require(target.get("conditioning_view_hash") == view_hash, "TARGET_DERIVATION_REPLAY", "TARGET_CONDITIONING_VIEW_REBINDING")
        _require(target.get("entropy_profile_hash") == entropy_hash, "TARGET_DERIVATION_REPLAY", "TARGET_ENTROPY_REBINDING")
        _require(target.get("target_event_id") == selector.get("selected_event_id"), "TARGET_DERIVATION_REPLAY", "TARGET_EVENT_SELECTOR_MISMATCH")
        raw_resolved = resolver.resolve(str(target.get("raw_source_object_hash")))
        _resolve_hashes(resolver, target.get("source_evidence_hashes", []), "TARGET_SOURCE_EVIDENCE")
        derived = derive_target(derivation, raw_resolved.exact_bytes, target_event_id=str(target.get("target_event_id")), pre_return_hash=pre_return_hash)
        target_hex = target.get("target_bytes_hex")
        _require(isinstance(target_hex, str) and target_hex, "TARGET_DERIVATION_REPLAY", "TARGET_BYTES_REQUIRED")
        try:
            declared_target = bytes.fromhex(target_hex)
        except ValueError as exc:
            _reject("TARGET_DERIVATION_REPLAY", "TARGET_BYTES_HEX_INVALID", str(exc))
        _require(declared_target == derived, "TARGET_DERIVATION_REPLAY", "DERIVED_TARGET_BYTES_MISMATCH")
        _require(target.get("target_canonical_hash") == target_bytes_hash(derived), "TARGET_DERIVATION_REPLAY", "TARGET_CANONICAL_HASH_MISMATCH")
        observed_event, _ = _state_event(ledger, subject_trial, "TARGET_OBSERVED")
        _require(observed_event.get("payload_hash") == target_hash, "TARGET_DERIVATION_REPLAY", "TARGET_OBSERVED_PAYLOAD_MISMATCH")
        gates["TARGET_DERIVATION_REPLAY"] = "PASS"

        exact_match = any(candidate == derived for candidate in candidate_bytes)
        k = int(candidate_set["cardinality"])
        a_i = exact_hit_cap(k, p_i)
        zero = zero_cap_outcome(a_i, exact_match)
        if a_i == 0:
            _require(zero.ok, "STATISTICAL_CAP_STRUCTURE", zero.code, zero.detail)
        gates["EXACT_IDENTITY"] = "PASS"
        gates["STATISTICAL_CAP_STRUCTURE"] = "PASS"

        # Bundle must bind every replayed subject-trial object.
        bindings = {
            "experiment_plan_hash": plan_hash,
            "pre_return_certificate_hash": pre_return_hash,
            "candidate_generation_profile_hash": candidate_profile_hash,
            "candidate_set_hash": candidate_set_hash,
            "candidate_multiplicity": k,
            "target_selector_profile_hash": selector_hash,
            "target_derivation_profile_hash": derivation_hash,
            "conditioning_view_hash": view_hash,
            "entropy_profile_hash": entropy_hash,
            "causal_model_hash": causal_hash,
            "statistical_plan_hash": statistical_hash,
            "witness_registry_hash": current_registry_hash,
            "target_evidence_hash": target_hash,
            "publication_manifest_hash": str(manifest.get("publication_manifest_hash")),
        }
        for field, expected in bindings.items():
            _require(bundle.get(field) == expected, "EVIDENCE_BUNDLE_BINDINGS", "BUNDLE_REBINDING", field)
        _require(bundle.get("candidate_multiplicity") == k, "EVIDENCE_BUNDLE_BINDINGS", "BUNDLE_MULTIPLICITY_MISMATCH")
        if bundle.get("eprocess_state_hash") is not None:
            resolver.resolve(str(bundle.get("eprocess_state_hash")), expected_schema="AIFC/eprocess-state/v1")
        gates["EVIDENCE_BUNDLE_BINDINGS"] = "PASS"

        verified_event, verified_event_hash = _state_event(ledger, subject_trial, "VERIFIED")
        _require(bundle.get("trial_ledger_head_hash") == verified_event_hash, "TERMINAL_BUNDLE_BINDING", "BUNDLE_HEAD_MUST_BE_VERIFIED_EVENT")
        terminal_event = ledger["terminal"][subject_trial]
        _require(terminal_event.get("evidence_bundle_hash") == bundle_hash, "TERMINAL_BUNDLE_BINDING", "TERMINAL_BUNDLE_HASH_MISMATCH")
        expected_subtype = "COMPLETED_HIT" if exact_match else "COMPLETED_MISS"
        _require(terminal_event.get("terminal_subtype") == expected_subtype, "TERMINAL_BUNDLE_BINDING", "TERMINAL_SUBTYPE_IDENTITY_MISMATCH")
        gates["TERMINAL_BUNDLE_BINDING"] = "PASS"

        publication_hash = str(manifest.get("publication_manifest_hash"))
        publication = _obj(resolver, publication_hash, "AIFC/publication-manifest/v1")
        _validate_publication_manifest(resolver, publication, publication_hash, experiment_id=experiment_id, plan_hash=plan_hash, publication_policy_hash=str(plan.get("publication_policy_hash")), declared_trial_count=declared_trial_count, ledger=ledger, subject_trial=subject_trial, subject_bundle_hash=bundle_hash)
        gates["PUBLICATION_MANIFEST_REPLAY"] = "PASS"

        # These remain deliberately blocked in Verifier A replay v0.2.
        gates["ED25519_SIGNATURE_CRYPTO"] = "BLOCKED"
        gates["CAUSAL_D_SEPARATION"] = "BLOCKED"
        gates["TARGET_SOURCE_CRYPTOGRAPHIC_PROOF"] = "BLOCKED"
        gates["FULL_EXPERIMENT_STATISTICAL_REPLAY"] = "BLOCKED"
        gates["BYTE_IDENTICAL_CANONICALIZATION"] = "BLOCKED"

        return {
            "schema": "AIFC/verifier-result/v1",
            "experiment_id": experiment_id,
            "trial_index": subject_trial,
            "verifier_id": "AIFC-Verifier-A",
            "verifier_version": "0.2.0-replay",
            "evidence_bundle_hash": bundle_hash,
            "gate_results": gates,
            "exact_match": exact_match,
            "terminal_grade": "STRUCTURAL_MATCH_ONLY" if exact_match else "NOT_ADMITTED",
            "failure_codes": [],
            "physical_interpretation": "NO_AUTOMATIC_PHYSICAL_RETROCAUSALITY_CLAIM",
            "fail_open": False,
        }
    except (ReplayRejected, EvidenceResolutionError, CanonicalizationError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ReplayRejected):
            gates[exc.problem.gate] = "FAIL"
            code = exc.problem.code
            detail = exc.problem.detail
        elif isinstance(exc, EvidenceResolutionError):
            gates["EVIDENCE_RESOLUTION"] = "FAIL"
            code = "EVIDENCE_RESOLUTION_FAILED"
            detail = str(exc)
        elif isinstance(exc, CanonicalizationError):
            gates["CANONICALIZATION_A"] = "FAIL"
            code = "CANONICALIZATION_REJECTED"
            detail = str(exc)
        else:
            gates["REPLAY_PACKAGE"] = "FAIL"
            code = "MALFORMED_OR_MISSING_EVIDENCE"
            detail = str(exc)
        experiment_id = manifest.get("experiment_id", "UNKNOWN") if isinstance(manifest, Mapping) else "UNKNOWN"
        trial_index = manifest.get("subject_trial_index", 1) if isinstance(manifest, Mapping) else 1
        bundle_hash = manifest.get("evidence_bundle_hash", "0" * 64) if isinstance(manifest, Mapping) else "0" * 64
        return {
            "schema": "AIFC/verifier-result/v1",
            "experiment_id": experiment_id if isinstance(experiment_id, str) and experiment_id else "UNKNOWN",
            "trial_index": trial_index if isinstance(trial_index, int) and trial_index >= 1 else 1,
            "verifier_id": "AIFC-Verifier-A",
            "verifier_version": "0.2.0-replay",
            "evidence_bundle_hash": bundle_hash if isinstance(bundle_hash, str) and len(bundle_hash) == 64 else "0" * 64,
            "gate_results": gates,
            "exact_match": False,
            "terminal_grade": "INVALIDATED_EVIDENCE",
            "failure_codes": [f"{code}:{detail}" if detail else code],
            "physical_interpretation": "NO_AUTOMATIC_PHYSICAL_RETROCAUSALITY_CLAIM",
            "fail_open": False,
        }
