#!/usr/bin/env python3
"""Standalone AIFC Verifier A replay core v0.2.

The replay core consumes an AIFC/replay-package/v0.2 object and recomputes
protocol-object identities, global ledger continuity/state transitions,
candidate multiplicity, selected quorum structure, entropy-bound structure,
target bindings, exact hard-byte identity and terminal bundle anchoring.

This is intentionally NOT full Implementation A. Cryptographic signature/key
lifecycle verification, independent causal d-separation, external target-source
proof verification, the full statistical engine and cross-implementation JCS
conformance remain blocked release gates.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
from typing import Any, Mapping, Sequence

from canonical import CanonicalizationError, domain_hash
from frontier import (
    CheckResult,
    exact_hit_cap,
    experiment_genesis_hash,
    validate_candidate_generation_profile,
    validate_canonical_rational,
    validate_registry_transition,
    validate_registry_transition_set,
    validate_target_derivation_bindings,
    zero_cap_outcome,
)

DOMAIN_BY_SCHEMA = {
    "AIFC/hard-witness/v1": "AIFC:HARD_WITNESS:v1",
    "AIFC/candidate-set/v1": "AIFC:CANDIDATE_SET:v1",
    "AIFC/pre-return-certificate/v1": "AIFC:PRE_RETURN_CERTIFICATE:v1",
    "AIFC/trial-ledger-event/v1": "AIFC:TRIAL_LEDGER_EVENT:v1",
    "AIFC/candidate-generation-profile/v1": "AIFC:CANDIDATE_GENERATION_PROFILE:v1",
    "AIFC/entropy-profile/v1": "AIFC:ENTROPY_PROFILE:v1",
    "AIFC/target-derivation-profile/v1": "AIFC:TARGET_DERIVATION_PROFILE:v1",
    "AIFC/target-evidence/v1": "AIFC:TARGET_EVIDENCE:v1",
    "AIFC/causal-model/v1": "AIFC:CAUSAL_MODEL:v1",
    "AIFC/witness-registry/v1": "AIFC:WITNESS_REGISTRY:v1",
    "AIFC/witness-receipt/v1": "AIFC:WITNESS_RECEIPT:v1",
    "AIFC/quorum-certificate/v1": "AIFC:QUORUM_CERTIFICATE:v1",
    "AIFC/registry-transition-body/v1": "AIFC:REGISTRY_TRANSITION_BODY:v1",
    "AIFC/registry-transition-receipt/v1": "AIFC:REGISTRY_TRANSITION_RECEIPT:v1",
    "AIFC/registry-transition-quorum/v1": "AIFC:REGISTRY_TRANSITION_QUORUM:v1",
    "AIFC/registry-transition-certificate/v1": "AIFC:REGISTRY_TRANSITION_CERTIFICATE:v1",
    "AIFC/evidence-bundle/v1": "AIFC:EVIDENCE_BUNDLE:v1",
    "AIFC/verifier-result/v1": "AIFC:VERIFIER_RESULT:v1",
    "AIFC/release-manifest/v1": "AIFC:RELEASE_MANIFEST:v1",
}

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


def protocol_hash(obj: Mapping[str, Any]) -> str:
    schema = obj.get("schema")
    separator = DOMAIN_BY_SCHEMA.get(schema)
    if separator is None:
        raise CanonicalizationError(f"no AIFC domain separator registered for schema {schema!r}")
    return domain_hash(separator, obj)


def target_bytes_hash(target_bytes: bytes) -> str:
    return hashlib.sha256(b"AIFC:TARGET_BYTES:v1\x00" + target_bytes).hexdigest()


def hard_witness_bytes(witness: Mapping[str, Any]) -> bytes:
    try:
        payload = witness["payload128"]
        nonce = witness["nonce128"]
    except KeyError as exc:
        _reject("CANDIDATE_SET_REPLAY", "HARD_WITNESS_FIELDS_MISSING", str(exc))
    if not isinstance(payload, str) or not isinstance(nonce, str):
        _reject("CANDIDATE_SET_REPLAY", "HARD_WITNESS_HEX_TYPE_INVALID")
    try:
        raw = bytes.fromhex(payload + nonce)
    except ValueError as exc:
        _reject("CANDIDATE_SET_REPLAY", "HARD_WITNESS_HEX_INVALID", str(exc))
    _require(len(raw) == 32, "CANDIDATE_SET_REPLAY", "HARD_WITNESS_NOT_256_BITS")
    return raw


def _context_equal(obj: Mapping[str, Any], experiment_id: str, trial_index: int, run_id: str | None = None) -> None:
    _require(obj.get("experiment_id") == experiment_id, "CONTEXT_BINDING", "EXPERIMENT_ID_MISMATCH", str(obj.get("schema")))
    if "trial_index" in obj:
        _require(obj.get("trial_index") == trial_index, "CONTEXT_BINDING", "TRIAL_INDEX_MISMATCH", str(obj.get("schema")))
    if run_id is not None and "run_id" in obj:
        _require(obj.get("run_id") == run_id, "CONTEXT_BINDING", "RUN_ID_MISMATCH", str(obj.get("schema")))


def replay_candidate_set(
    candidate_set: Mapping[str, Any],
    hard_witnesses: Sequence[Mapping[str, Any]],
    *,
    experiment_id: str,
    trial_index: int,
    run_id: str,
) -> tuple[str, list[bytes]]:
    _require(candidate_set.get("schema") == "AIFC/candidate-set/v1", "CANDIDATE_SET_REPLAY", "CANDIDATE_SET_SCHEMA_MISMATCH")
    _context_equal(candidate_set, experiment_id, trial_index, run_id)
    declared_hashes = candidate_set.get("hard_witness_hashes")
    cardinality = candidate_set.get("cardinality")
    _require(isinstance(declared_hashes, list) and declared_hashes, "CANDIDATE_SET_REPLAY", "CANDIDATE_HASH_LIST_INVALID")
    _require(declared_hashes == sorted(declared_hashes), "CANDIDATE_SET_REPLAY", "NONCANONICAL_CANDIDATE_SET_ORDER")
    _require(len(declared_hashes) == len(set(declared_hashes)), "CANDIDATE_SET_REPLAY", "DUPLICATE_CANDIDATE_HASH")
    _require(cardinality == len(declared_hashes), "CANDIDATE_SET_REPLAY", "CANDIDATE_CARDINALITY_MISMATCH")
    _require(len(hard_witnesses) == cardinality, "CANDIDATE_SET_REPLAY", "HARD_WITNESS_COUNT_MISMATCH")

    actual: list[tuple[str, bytes]] = []
    for witness in hard_witnesses:
        _require(witness.get("schema") == "AIFC/hard-witness/v1", "CANDIDATE_SET_REPLAY", "HARD_WITNESS_SCHEMA_MISMATCH")
        _context_equal(witness, experiment_id, trial_index, run_id)
        actual.append((protocol_hash(witness), hard_witness_bytes(witness)))
    actual.sort(key=lambda pair: pair[0])
    actual_hashes = [h for h, _ in actual]
    _require(actual_hashes == declared_hashes, "CANDIDATE_SET_REPLAY", "CANDIDATE_MEMBER_HASH_MISMATCH")
    return protocol_hash(candidate_set), [raw for _, raw in actual]


def _quorum_structure(
    cert: Mapping[str, Any],
    *,
    gate: str,
    experiment_id: str,
    trial_index: int,
    logical_position: str,
    content_hash: str,
    registry_hash: str,
) -> str:
    _require(cert.get("schema") == "AIFC/quorum-certificate/v1", gate, "QUORUM_SCHEMA_MISMATCH")
    _context_equal(cert, experiment_id, trial_index)
    _require(cert.get("logical_position") == logical_position, gate, "QUORUM_LOGICAL_POSITION_MISMATCH")
    _require(cert.get("content_hash") == content_hash, gate, "QUORUM_CONTENT_HASH_MISMATCH")
    _require(cert.get("registry_hash") == registry_hash, gate, "QUORUM_REGISTRY_HASH_MISMATCH")
    n, f, q = cert.get("n"), cert.get("f"), cert.get("q")
    _require(all(isinstance(x, int) for x in (n, f, q)), gate, "QUORUM_FAULT_MODEL_TYPE_INVALID")
    _require(n >= 1 and 0 <= f < n and 1 <= q <= n, gate, "QUORUM_FAULT_MODEL_RANGE_INVALID")
    _require(2 * q > n + f, gate, "QUORUM_INTERSECTION_UNSAFE")
    receipts = cert.get("receipts")
    _require(isinstance(receipts, list) and len(receipts) >= q, gate, "QUORUM_RECEIPT_COUNT_INSUFFICIENT")
    seen: set[str] = set()
    for receipt in receipts:
        _require(isinstance(receipt, Mapping), gate, "QUORUM_RECEIPT_UNTYPED")
        _require(receipt.get("schema") == "AIFC/witness-receipt/v1", gate, "QUORUM_RECEIPT_SCHEMA_MISMATCH")
        _context_equal(receipt, experiment_id, trial_index)
        _require(receipt.get("logical_position") == logical_position, gate, "RECEIPT_LOGICAL_POSITION_MISMATCH")
        _require(receipt.get("content_hash") == content_hash, gate, "RECEIPT_CONTENT_HASH_MISMATCH")
        _require(receipt.get("registry_hash") == registry_hash, gate, "RECEIPT_REGISTRY_HASH_MISMATCH")
        wid = receipt.get("witness_id")
        _require(isinstance(wid, str) and wid, gate, "RECEIPT_WITNESS_ID_INVALID")
        seen.add(wid)
    _require(len(seen) >= q, gate, "DISTINCT_WITNESS_QUORUM_NOT_MET")
    return protocol_hash(cert)


def replay_ledger(
    events: Sequence[Mapping[str, Any]],
    *,
    experiment_id: str,
    declared_trial_count: int,
) -> dict[str, Any]:
    _require(isinstance(events, Sequence) and len(events) > 0, "LEDGER_REPLAY", "LEDGER_EMPTY")
    expected_prev = experiment_genesis_hash(experiment_id)
    trial_state: dict[int, str | None] = {}
    trial_ord: dict[int, int] = {}
    terminal: dict[int, Mapping[str, Any]] = {}
    hashes: list[str] = []
    trial_event_hashes: dict[int, dict[str, str]] = {}

    for index, event in enumerate(events):
        _require(isinstance(event, Mapping), "LEDGER_REPLAY", "LEDGER_EVENT_UNTYPED", str(index))
        _require(event.get("schema") == "AIFC/trial-ledger-event/v1", "LEDGER_REPLAY", "LEDGER_EVENT_SCHEMA_MISMATCH", str(index))
        _require(event.get("experiment_id") == experiment_id, "LEDGER_REPLAY", "LEDGER_EXPERIMENT_MISMATCH", str(index))
        _require(event.get("event_index") == index, "LEDGER_REPLAY", "EVENT_INDEX_GAP_OR_REORDER", str(index))
        _require(event.get("previous_event_hash") == expected_prev, "LEDGER_REPLAY", "LEDGER_PREDECESSOR_MISMATCH", str(index))
        trial = event.get("trial_index")
        _require(isinstance(trial, int) and 1 <= trial <= declared_trial_count, "LEDGER_REPLAY", "TRIAL_INDEX_OUTSIDE_DECLARED_PLAN", str(trial))
        _require(trial not in terminal, "LEDGER_REPLAY", "TERMINAL_RESURRECTION", str(trial))

        current = trial_state.get(trial)
        ordinal = trial_ord.get(trial, 0)
        _require(event.get("transition_ordinal") == ordinal, "LEDGER_REPLAY", "TRANSITION_ORDINAL_GAP", str(trial))
        _require(event.get("state_from") == current, "LEDGER_REPLAY", "STATE_FROM_MISMATCH", str(trial))
        state_to = event.get("state_to")
        normal = NORMAL_NEXT.get(current)
        if state_to == "TERMINAL" and current is not None:
            subtype = event.get("terminal_subtype")
            _require(subtype in TERMINAL_SUBTYPES, "LEDGER_REPLAY", "TERMINAL_SUBTYPE_INVALID", str(trial))
        else:
            _require(state_to == normal, "LEDGER_REPLAY", "FORBIDDEN_STATE_TRANSITION", f"{current}->{state_to}")
            if state_to != "TERMINAL":
                _require(event.get("terminal_subtype") in (None, ""), "LEDGER_REPLAY", "NONTERMINAL_HAS_TERMINAL_SUBTYPE", str(trial))

        event_hash = protocol_hash(event)
        hashes.append(event_hash)
        expected_prev = event_hash
        trial_state[trial] = state_to
        trial_ord[trial] = ordinal + 1
        trial_event_hashes.setdefault(trial, {})[str(state_to)] = event_hash
        if state_to == "TERMINAL":
            terminal[trial] = event

    expected_trials = set(range(1, declared_trial_count + 1))
    _require(set(trial_state) == expected_trials, "COMPLETE_TRIAL_PUBLICATION", "MISSING_DECLARED_TRIAL", str(sorted(expected_trials - set(trial_state))))
    _require(set(terminal) == expected_trials, "COMPLETE_TRIAL_PUBLICATION", "NONTERMINAL_DECLARED_TRIAL", str(sorted(expected_trials - set(terminal))))
    return {
        "event_hashes": hashes,
        "final_ledger_head_hash": hashes[-1],
        "terminal_events": terminal,
        "trial_event_hashes": trial_event_hashes,
    }


def _find_event(events: Sequence[Mapping[str, Any]], trial_index: int, state_to: str) -> tuple[Mapping[str, Any], str]:
    matches = [e for e in events if e.get("trial_index") == trial_index and e.get("state_to") == state_to]
    _require(len(matches) == 1, "LEDGER_REPLAY", "SUBJECT_STATE_EVENT_COUNT_INVALID", f"{state_to}:{len(matches)}")
    event = matches[0]
    return event, protocol_hash(event)


def replay_registry_transitions(
    certificates: Sequence[Mapping[str, Any]],
    *,
    experiment_id: str,
    final_registry_hash: str,
    bundle_transition_hash: str | None,
) -> None:
    if not certificates:
        _require(bundle_transition_hash is None, "REGISTRY_TRANSITION_REPLAY", "UNEXPLAINED_REGISTRY_TRANSITION_HASH")
        return
    result = validate_registry_transition_set(certificates)
    _require(result.ok, "REGISTRY_TRANSITION_REPLAY", result.code, result.detail)
    previous_next_hash: str | None = None
    previous_next_sequence: int | None = None
    cert_hashes: list[str] = []
    for cert in certificates:
        _require(cert.get("transition_body", {}).get("experiment_id") == experiment_id, "REGISTRY_TRANSITION_REPLAY", "TRANSITION_EXPERIMENT_MISMATCH")
        body = cert["transition_body"]
        computed_body_hash = protocol_hash(body)
        _require(cert.get("transition_body_hash") == computed_body_hash, "REGISTRY_TRANSITION_REPLAY", "TRANSITION_BODY_HASH_MISMATCH")
        result = validate_registry_transition(cert)
        _require(result.ok, "REGISTRY_TRANSITION_REPLAY", result.code, result.detail)
        if previous_next_hash is not None:
            _require(body.get("previous_registry_hash") == previous_next_hash, "REGISTRY_TRANSITION_REPLAY", "REGISTRY_TRANSITION_CHAIN_HASH_GAP")
            _require(body.get("previous_registry_sequence") == previous_next_sequence, "REGISTRY_TRANSITION_REPLAY", "REGISTRY_TRANSITION_CHAIN_SEQUENCE_GAP")
        previous_next_hash = body.get("next_registry_hash")
        previous_next_sequence = body.get("next_registry_sequence")
        cert_hashes.append(protocol_hash(cert))
    _require(previous_next_hash == final_registry_hash, "REGISTRY_TRANSITION_REPLAY", "FINAL_REGISTRY_NOT_REACHED")
    _require(bundle_transition_hash == cert_hashes[-1], "REGISTRY_TRANSITION_REPLAY", "BUNDLE_TRANSITION_HASH_MISMATCH")


def _entropy_structure(profile: Mapping[str, Any]) -> Fraction:
    _require(profile.get("schema") == "AIFC/entropy-profile/v1", "ENTROPY_PROFILE_REPLAY", "ENTROPY_SCHEMA_MISMATCH")
    result, p = validate_canonical_rational(profile.get("point_probability_upper_bound", {}))
    _require(result.ok and p is not None, "ENTROPY_PROFILE_REPLAY", result.code, result.detail)
    _require(profile.get("admission_status") == "ADMITTED", "ENTROPY_PROFILE_REPLAY", "ENTROPY_PROFILE_NOT_ADMITTED")
    unresolved = profile.get("unresolved_assumptions")
    _require(isinstance(unresolved, list) and not unresolved, "ENTROPY_PROFILE_REPLAY", "ENTROPY_UNRESOLVED_ASSUMPTIONS")
    evidence = profile.get("external_evidence")
    _require(isinstance(evidence, list) and evidence, "ENTROPY_PROFILE_REPLAY", "ENTROPY_EXTERNAL_EVIDENCE_MISSING")
    return p


def verify_replay_package(package: Mapping[str, Any]) -> dict[str, Any]:
    gates: dict[str, str] = {}
    diagnostics: list[str] = []
    try:
        _require(package.get("schema") == "AIFC/replay-package/v0.2", "REPLAY_PACKAGE", "REPLAY_PACKAGE_SCHEMA_MISMATCH")
        experiment_id = package.get("experiment_id")
        declared_trial_count = package.get("declared_trial_count")
        subject_trial = package.get("subject_trial_index")
        _require(isinstance(experiment_id, str) and experiment_id, "REPLAY_PACKAGE", "EXPERIMENT_ID_INVALID")
        _require(isinstance(declared_trial_count, int) and declared_trial_count >= 1, "REPLAY_PACKAGE", "DECLARED_TRIAL_COUNT_INVALID")
        _require(isinstance(subject_trial, int) and 1 <= subject_trial <= declared_trial_count, "REPLAY_PACKAGE", "SUBJECT_TRIAL_INDEX_INVALID")

        bundle = package["evidence_bundle"]
        run_id = bundle.get("run_id")
        _require(isinstance(run_id, str) and run_id, "CONTEXT_BINDING", "RUN_ID_INVALID")
        _context_equal(bundle, experiment_id, subject_trial, run_id)

        ledger = replay_ledger(package["ledger_events"], experiment_id=experiment_id, declared_trial_count=declared_trial_count)
        gates["LEDGER_REPLAY"] = "PASS"
        gates["COMPLETE_TRIAL_PUBLICATION"] = "PASS"

        candidate_set_hash, candidate_bytes = replay_candidate_set(
            package["candidate_set"],
            package["hard_witnesses"],
            experiment_id=experiment_id,
            trial_index=subject_trial,
            run_id=run_id,
        )
        gates["CANDIDATE_SET_REPLAY"] = "PASS"

        profile = package["candidate_generation_profile"]
        _context_equal(profile, experiment_id, subject_trial)
        candidate_profile_hash = protocol_hash(profile)
        c_res = validate_candidate_generation_profile(profile, strongest_grade=True)
        _require(c_res.ok, "CANDIDATE_PROVENANCE", c_res.code, c_res.detail)
        k = package["candidate_set"].get("cardinality")
        _require(profile.get("candidate_set_cardinality_upper_bound") == k, "CANDIDATE_PROVENANCE", "CANDIDATE_PROFILE_K_NOT_EXACT_SET_CARDINALITY")
        gates["CANDIDATE_PROVENANCE"] = "PASS"

        witness_registry = package["witness_registry"]
        registry_hash = protocol_hash(witness_registry)
        _require(bundle.get("witness_registry_hash") == registry_hash, "WITNESS_REGISTRY_BINDING", "BUNDLE_REGISTRY_HASH_MISMATCH")
        gates["WITNESS_REGISTRY_BINDING"] = "PASS"
        replay_registry_transitions(
            package["registry_transition_certificates"],
            experiment_id=experiment_id,
            final_registry_hash=registry_hash,
            bundle_transition_hash=bundle.get("witness_registry_transition_hash"),
        )
        gates["REGISTRY_TRANSITION_REPLAY"] = "PASS"

        created_event, created_event_hash = _find_event(package["ledger_events"], subject_trial, "CREATED")
        created_cert = package["created_quorum_certificate"]
        created_cert_hash = _quorum_structure(
            created_cert,
            gate="CREATED_QUORUM_STRUCTURE",
            experiment_id=experiment_id,
            trial_index=subject_trial,
            logical_position="CREATED",
            content_hash=created_event_hash,
            registry_hash=registry_hash,
        )
        _require(profile.get("created_slot_certificate_hash") == created_cert_hash, "CREATED_QUORUM_STRUCTURE", "CANDIDATE_PROFILE_CREATED_CERT_HASH_MISMATCH")
        gates["CREATED_QUORUM_STRUCTURE"] = "PASS"

        pre_return = package["pre_return_certificate"]
        _context_equal(pre_return, experiment_id, subject_trial, run_id)
        pre_return_hash = protocol_hash(pre_return)
        freeze_event, freeze_event_hash = _find_event(package["ledger_events"], subject_trial, "PRE_RETURN_FROZEN")
        _require(freeze_event.get("payload_hash") == candidate_set_hash, "PRE_RETURN_BINDINGS", "FREEZE_EVENT_CANDIDATE_SET_HASH_MISMATCH")
        _require(pre_return.get("freeze_event_hash") == freeze_event_hash, "PRE_RETURN_BINDINGS", "FREEZE_EVENT_HASH_MISMATCH")
        _require(pre_return.get("ledger_head_hash") == freeze_event_hash, "PRE_RETURN_BINDINGS", "PRE_RETURN_LEDGER_HEAD_NOT_FREEZE_EVENT")
        _require(pre_return.get("candidate_set_hash") == candidate_set_hash, "PRE_RETURN_BINDINGS", "PRE_RETURN_CANDIDATE_SET_HASH_MISMATCH")
        _require(pre_return.get("candidate_multiplicity") == k, "PRE_RETURN_BINDINGS", "PRE_RETURN_MULTIPLICITY_MISMATCH")
        _require(pre_return.get("candidate_generation_profile_hash") == candidate_profile_hash, "PRE_RETURN_BINDINGS", "PRE_RETURN_CANDIDATE_PROFILE_HASH_MISMATCH")
        gates["PRE_RETURN_BINDINGS"] = "PASS"

        pre_q = package["pre_return_quorum_certificate"]
        pre_q_hash = _quorum_structure(
            pre_q,
            gate="PRE_RETURN_QUORUM_STRUCTURE",
            experiment_id=experiment_id,
            trial_index=subject_trial,
            logical_position="PRE_RETURN_FROZEN",
            content_hash=freeze_event_hash,
            registry_hash=registry_hash,
        )
        _require(pre_return.get("quorum_certificate_hash") == pre_q_hash, "PRE_RETURN_QUORUM_STRUCTURE", "PRE_RETURN_QUORUM_HASH_MISMATCH")
        quorum_event, _ = _find_event(package["ledger_events"], subject_trial, "QUORUM_CERTIFIED")
        _require(quorum_event.get("payload_hash") == pre_q_hash, "PRE_RETURN_QUORUM_STRUCTURE", "QUORUM_EVENT_PAYLOAD_HASH_MISMATCH")
        gates["PRE_RETURN_QUORUM_STRUCTURE"] = "PASS"

        entropy = package["entropy_profile"]
        entropy_hash = protocol_hash(entropy)
        p_i = _entropy_structure(entropy)
        gates["ENTROPY_PROFILE_STRUCTURE"] = "PASS"

        derivation = package["target_derivation_profile"]
        derivation_hash = protocol_hash(derivation)
        target = package["target_evidence"]
        target_hash = protocol_hash(target)
        d_res = validate_target_derivation_bindings(derivation_hash, derivation, pre_return, entropy, target)
        _require(d_res.ok, "TARGET_DERIVATION_BINDINGS", d_res.code, d_res.detail)
        _require(entropy.get("target_selector", {}).get("selector_hash") == derivation.get("event_selector_hash"), "TARGET_DERIVATION_BINDINGS", "ENTROPY_SELECTOR_DERIVATION_SELECTOR_MISMATCH")
        _require(target.get("entropy_profile_hash") == entropy_hash, "TARGET_DERIVATION_BINDINGS", "TARGET_ENTROPY_PROFILE_HASH_MISMATCH")
        _require(target.get("source_id") == entropy.get("source_id") == derivation.get("source_id"), "TARGET_DERIVATION_BINDINGS", "TARGET_SOURCE_ID_MISMATCH")
        gates["TARGET_DERIVATION_BINDINGS"] = "PASS"

        causal_hash = protocol_hash(package["causal_model"])
        gates["CAUSAL_MODEL_HASH_BINDING"] = "PASS"

        _require(bundle.get("pre_return_certificate_hash") == pre_return_hash, "EVIDENCE_BUNDLE_BINDINGS", "BUNDLE_PRE_RETURN_HASH_MISMATCH")
        _require(bundle.get("candidate_generation_profile_hash") == candidate_profile_hash, "EVIDENCE_BUNDLE_BINDINGS", "BUNDLE_CANDIDATE_PROFILE_HASH_MISMATCH")
        _require(bundle.get("candidate_set_hash") == candidate_set_hash, "EVIDENCE_BUNDLE_BINDINGS", "BUNDLE_CANDIDATE_SET_HASH_MISMATCH")
        _require(bundle.get("candidate_multiplicity") == k, "EVIDENCE_BUNDLE_BINDINGS", "BUNDLE_MULTIPLICITY_MISMATCH")
        _require(bundle.get("entropy_profile_hash") == entropy_hash, "EVIDENCE_BUNDLE_BINDINGS", "BUNDLE_ENTROPY_HASH_MISMATCH")
        _require(bundle.get("target_derivation_profile_hash") == derivation_hash, "EVIDENCE_BUNDLE_BINDINGS", "BUNDLE_DERIVATION_HASH_MISMATCH")
        _require(bundle.get("causal_model_hash") == causal_hash, "EVIDENCE_BUNDLE_BINDINGS", "BUNDLE_CAUSAL_HASH_MISMATCH")
        _require(bundle.get("target_evidence_hash") == target_hash, "EVIDENCE_BUNDLE_BINDINGS", "BUNDLE_TARGET_EVIDENCE_HASH_MISMATCH")
        gates["EVIDENCE_BUNDLE_BINDINGS"] = "PASS"

        armed_event, _ = _find_event(package["ledger_events"], subject_trial, "TARGET_ARMED")
        observed_event, _ = _find_event(package["ledger_events"], subject_trial, "TARGET_OBSERVED")
        _require(armed_event.get("payload_hash") == derivation_hash, "TARGET_LEDGER_BINDING", "TARGET_ARMED_DERIVATION_HASH_MISMATCH")
        _require(observed_event.get("payload_hash") == target_hash, "TARGET_LEDGER_BINDING", "TARGET_OBSERVED_EVIDENCE_HASH_MISMATCH")
        gates["TARGET_LEDGER_BINDING"] = "PASS"

        target_hex = target.get("target_bytes_hex")
        _require(isinstance(target_hex, str) and target_hex, "EXACT_IDENTITY", "TARGET_BYTES_REQUIRED_FOR_REPLAY")
        try:
            target_bytes = bytes.fromhex(target_hex)
        except ValueError as exc:
            _reject("EXACT_IDENTITY", "TARGET_BYTES_HEX_INVALID", str(exc))
        _require(len(target_bytes) * 8 == derivation.get("output_length_bits"), "EXACT_IDENTITY", "TARGET_OUTPUT_LENGTH_MISMATCH")
        _require(target.get("target_canonical_hash") == target_bytes_hash(target_bytes), "EXACT_IDENTITY", "TARGET_CANONICAL_HASH_MISMATCH")
        exact_match = any(raw == target_bytes for raw in candidate_bytes)
        gates["EXACT_IDENTITY"] = "PASS"

        a_i = exact_hit_cap(k, p_i)
        zero_res = zero_cap_outcome(a_i, exact_match)
        if a_i == 0:
            _require(zero_res.ok, "STATISTICAL_CAP_STRUCTURE", zero_res.code, zero_res.detail)
        gates["STATISTICAL_CAP_STRUCTURE"] = "PASS"

        verified_event, verified_event_hash = _find_event(package["ledger_events"], subject_trial, "VERIFIED")
        bundle_hash = protocol_hash(bundle)
        _require(bundle.get("trial_ledger_head_hash") == verified_event_hash, "TERMINAL_BUNDLE_BINDING", "BUNDLE_LEDGER_HEAD_MUST_BE_VERIFIED_EVENT")
        terminal_event = ledger["terminal_events"][subject_trial]
        _require(terminal_event.get("evidence_bundle_hash") == bundle_hash, "TERMINAL_BUNDLE_BINDING", "TERMINAL_EVENT_BUNDLE_HASH_MISMATCH")
        expected_subtype = "COMPLETED_HIT" if exact_match else "COMPLETED_MISS"
        _require(terminal_event.get("terminal_subtype") == expected_subtype, "TERMINAL_BUNDLE_BINDING", "TERMINAL_SUBTYPE_EXACT_MATCH_MISMATCH")
        gates["TERMINAL_BUNDLE_BINDING"] = "PASS"

        # Deliberately blocked until the corresponding independent engines exist.
        gates["ED25519_KEY_LIFECYCLE_CRYPTO"] = "BLOCKED"
        gates["CAUSAL_D_SEPARATION"] = "BLOCKED"
        gates["TARGET_SOURCE_CRYPTOGRAPHIC_PROOF"] = "BLOCKED"
        gates["FULL_EPROCESS_ENGINE"] = "BLOCKED"
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
            "physical_interpretation": "NO_AUTOMATIC_PHYSICAL_RETROCAUSALITY_CLAIM",
            "fail_open": False,
            "failure_codes": [],
        }
    except (ReplayRejected, CanonicalizationError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ReplayRejected):
            problem = exc.problem
            gates[problem.gate] = "FAIL"
            code = problem.code
            detail = problem.detail
        elif isinstance(exc, CanonicalizationError):
            gates["CANONICALIZATION_A"] = "FAIL"
            code = "CANONICALIZATION_REJECTED"
            detail = str(exc)
        else:
            gates["REPLAY_PACKAGE"] = "FAIL"
            code = "MALFORMED_OR_MISSING_EVIDENCE"
            detail = str(exc)
        diagnostics.append(f"{code}:{detail}" if detail else code)
        bundle = package.get("evidence_bundle", {}) if isinstance(package, Mapping) else {}
        experiment_id = package.get("experiment_id", "UNKNOWN") if isinstance(package, Mapping) else "UNKNOWN"
        trial_index = package.get("subject_trial_index", 1) if isinstance(package, Mapping) else 1
        try:
            bundle_hash = protocol_hash(bundle) if isinstance(bundle, Mapping) and bundle.get("schema") == "AIFC/evidence-bundle/v1" else "0" * 64
        except Exception:
            bundle_hash = "0" * 64
        return {
            "schema": "AIFC/verifier-result/v1",
            "experiment_id": experiment_id if isinstance(experiment_id, str) and experiment_id else "UNKNOWN",
            "trial_index": trial_index if isinstance(trial_index, int) and trial_index >= 1 else 1,
            "verifier_id": "AIFC-Verifier-A",
            "verifier_version": "0.2.0-replay",
            "evidence_bundle_hash": bundle_hash,
            "gate_results": gates,
            "exact_match": False,
            "terminal_grade": "INVALIDATED_EVIDENCE",
            "physical_interpretation": "NO_AUTOMATIC_PHYSICAL_RETROCAUSALITY_CLAIM",
            "fail_open": False,
            "failure_codes": diagnostics,
        }
