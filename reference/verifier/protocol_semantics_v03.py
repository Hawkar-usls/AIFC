#!/usr/bin/env python3
"""AIFC v0.3 pre-crypto protocol semantics.

This layer closes two declaration gaps before signature cryptography:
- whether CREATED slots conform to the frozen trial-creation policy;
- whether terminal subtypes are possible from the recorded source state.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from resolver import EvidenceResolutionError
from resolver_v02 import EvidenceResolverV02


class ProtocolSemanticsError(ValueError):
    pass


@dataclass(frozen=True)
class GateOutcome:
    status: str
    code: str
    detail: str = ""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _obj(resolver: EvidenceResolverV02, content_hash: str, schema: str) -> Mapping[str, Any]:
    resolved = resolver.resolve(content_hash, expected_schema=schema)
    if resolved.parsed_json is None:
        raise ProtocolSemanticsError(f"EXPECTED_PROTOCOL_JSON:{content_hash}")
    return resolved.parsed_json


def _state_machine() -> Mapping[str, Any]:
    path = _repo_root() / "conformance" / "state-machine-v1.json"
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ProtocolSemanticsError(f"STATE_MACHINE_LOAD_FAILED:{exc}") from exc
    if obj.get("schema") != "AIFC/state-machine/v1":
        raise ProtocolSemanticsError("STATE_MACHINE_SCHEMA_MISMATCH")
    table = obj.get("terminal_subtypes_by_state")
    if not isinstance(table, Mapping):
        raise ProtocolSemanticsError("TERMINAL_SUBTYPE_TABLE_MISSING")
    return obj


def replay_terminal_semantics(manifest: Mapping[str, Any], resolver: EvidenceResolverV02) -> GateOutcome:
    machine = _state_machine()
    allowed = machine["terminal_subtypes_by_state"]
    hashes = manifest.get("ledger_event_hashes")
    if not isinstance(hashes, list) or not hashes:
        raise ProtocolSemanticsError("LEDGER_HASH_LIST_INVALID")
    for h in hashes:
        event = _obj(resolver, str(h), "AIFC/trial-ledger-event/v1")
        if event.get("state_to") != "TERMINAL":
            continue
        state_from = event.get("state_from")
        subtype = event.get("terminal_subtype")
        permitted = allowed.get(state_from)
        if not isinstance(permitted, list) or subtype not in permitted:
            raise ProtocolSemanticsError(
                f"IMPOSSIBLE_TERMINAL_SUBTYPE:trial={event.get('trial_index')}:{state_from}->{subtype}"
            )
    return GateOutcome("PASS", "TERMINAL_SUBTYPE_SEMANTICS_PASS")


def replay_trial_creation_policy(manifest: Mapping[str, Any], resolver: EvidenceResolverV02) -> GateOutcome:
    experiment_id = manifest.get("experiment_id")
    plan_hash = manifest.get("experiment_plan_hash")
    plan_quorum_hash = manifest.get("experiment_plan_quorum_certificate_hash")
    if not isinstance(experiment_id, str) or not experiment_id:
        raise ProtocolSemanticsError("EXPERIMENT_ID_INVALID")
    if not isinstance(plan_hash, str) or not isinstance(plan_quorum_hash, str):
        raise ProtocolSemanticsError("PLAN_OR_PLAN_QUORUM_HASH_INVALID")

    plan = _obj(resolver, plan_hash, "AIFC/experiment-plan/v1")
    if plan.get("experiment_id") != experiment_id:
        raise ProtocolSemanticsError("EXPERIMENT_PLAN_EXPERIMENT_REBINDING")
    policy_hash = plan.get("trial_creation_policy_hash")
    if not isinstance(policy_hash, str):
        raise ProtocolSemanticsError("TRIAL_CREATION_POLICY_HASH_INVALID")
    policy = _obj(resolver, policy_hash, "AIFC/trial-creation-policy/v1")
    if policy.get("experiment_id") != experiment_id:
        raise ProtocolSemanticsError("TRIAL_CREATION_POLICY_EXPERIMENT_REBINDING")
    if policy.get("frozen_before_first_created") is not True:
        raise ProtocolSemanticsError("TRIAL_CREATION_POLICY_NOT_FROZEN")
    if policy.get("slot_index_rule") != "CONTIGUOUS_ONE_BASED":
        raise ProtocolSemanticsError("TRIAL_CREATION_SLOT_INDEX_RULE_INVALID")
    if policy.get("candidate_generation_before_created_forbidden") is not True:
        raise ProtocolSemanticsError("PRE_CREATED_CANDIDATE_GENERATION_NOT_FORBIDDEN")
    if policy.get("silent_slot_deletion_forbidden") is not True:
        raise ProtocolSemanticsError("SILENT_SLOT_DELETION_NOT_FORBIDDEN")

    ledger_hashes = manifest.get("ledger_event_hashes")
    if not isinstance(ledger_hashes, list) or not ledger_hashes:
        raise ProtocolSemanticsError("LEDGER_HASH_LIST_INVALID")
    created: dict[int, Mapping[str, Any]] = {}
    for h in ledger_hashes:
        event = _obj(resolver, str(h), "AIFC/trial-ledger-event/v1")
        if event.get("state_to") != "CREATED":
            continue
        trial = event.get("trial_index")
        if not isinstance(trial, int) or trial < 1:
            raise ProtocolSemanticsError("CREATED_TRIAL_INDEX_INVALID")
        if trial in created:
            raise ProtocolSemanticsError(f"DUPLICATE_CREATED_SLOT:{trial}")
        if event.get("payload_hash") != plan_hash:
            raise ProtocolSemanticsError(f"CREATED_PLAN_REBINDING:{trial}")
        if event.get("prerequisite_certificate_hash") != plan_quorum_hash:
            raise ProtocolSemanticsError(f"CREATED_WITHOUT_FROZEN_PLAN_QUORUM:{trial}")
        created[trial] = event

    method = policy.get("method")
    if method == "PREALLOCATED_SLOTS":
        declared = plan.get("declared_trial_count")
        if not isinstance(declared, int) or declared < 1:
            raise ProtocolSemanticsError("PREALLOCATED_PLAN_DECLARED_COUNT_INVALID")
        if policy.get("declared_trial_count") != declared:
            raise ProtocolSemanticsError("TRIAL_CREATION_DECLARED_COUNT_REBINDING")
        if policy.get("schedule_or_trigger_spec_hash") is not None:
            raise ProtocolSemanticsError("PREALLOCATED_POLICY_HAS_SCHEDULE_OR_TRIGGER_SPEC")
        expected = set(range(1, declared + 1))
        if set(created) != expected:
            raise ProtocolSemanticsError(
                f"PREALLOCATED_CREATED_SLOT_SET_MISMATCH:missing={sorted(expected-set(created))}:extra={sorted(set(created)-expected)}"
            )
        return GateOutcome("PASS", "TRIAL_CREATION_POLICY_REPLAY_PASS")

    if method in {"DETERMINISTIC_SCHEDULE", "EXTERNAL_TRIGGER_POLICY"}:
        spec_hash = policy.get("schedule_or_trigger_spec_hash")
        if not isinstance(spec_hash, str):
            raise ProtocolSemanticsError("SCHEDULE_OR_TRIGGER_SPEC_HASH_MISSING")
        resolver.resolve(spec_hash)
        return GateOutcome(
            "BLOCKED",
            "CREATED_OUTSIDE_FROZEN_SCHEDULE_OR_TRIGGER_NOT_REPLAYABLE",
            method,
        )

    raise ProtocolSemanticsError(f"TRIAL_CREATION_METHOD_UNKNOWN:{method}")
