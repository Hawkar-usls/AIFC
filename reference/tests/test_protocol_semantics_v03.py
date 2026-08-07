import sys
import tempfile
import unittest
from pathlib import Path

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from canonical import canonical_json_bytes, raw_evidence_hash  # noqa: E402
from canonical_v02 import protocol_hash_v02  # noqa: E402
from protocol_semantics_v03 import (  # noqa: E402
    ProtocolSemanticsError,
    replay_terminal_semantics,
    replay_trial_creation_policy,
)
from resolver_v02 import EvidenceResolverV02  # noqa: E402

H = lambda c: c * 64


class Store:
    def __init__(self, root: Path):
        self.root = root
        self.entries = []
        (root / "objects").mkdir(parents=True, exist_ok=True)

    def protocol(self, obj):
        h = protocol_hash_v02(obj)
        rel = f"objects/{h}.json"
        (self.root / rel).write_bytes(canonical_json_bytes(obj))
        self.entries.append({
            "content_hash": h,
            "relative_path": rel,
            "content_kind": "AIFC_PROTOCOL_JSON",
            "declared_schema": obj["schema"],
            "media_type": "application/json",
        })
        return h

    def raw(self, data: bytes):
        h = raw_evidence_hash(data)
        rel = f"objects/{h}.bin"
        (self.root / rel).write_bytes(data)
        self.entries.append({
            "content_hash": h,
            "relative_path": rel,
            "content_kind": "RAW_BYTES",
            "media_type": "application/octet-stream",
        })
        return h

    def resolver(self):
        return EvidenceResolverV02(self.root, {
            "schema": "AIFC/evidence-store-index/v1",
            "store_id": "semantics-test",
            "entries": self.entries,
        })


def creation_policy(method="PREALLOCATED_SLOTS", declared=2, spec_hash=None):
    return {
        "schema": "AIFC/trial-creation-policy/v1",
        "policy_id": "tcp-1",
        "experiment_id": "exp-1",
        "method": method,
        "slot_index_rule": "CONTIGUOUS_ONE_BASED",
        "declared_trial_count": declared,
        "schedule_or_trigger_spec_hash": spec_hash,
        "candidate_generation_before_created_forbidden": True,
        "silent_slot_deletion_forbidden": True,
        "frozen_before_first_created": True,
    }


def experiment_plan(policy_hash, declared=2):
    return {
        "schema": "AIFC/experiment-plan/v1",
        "experiment_id": "exp-1",
        "protocol_version": "1.0-draft",
        "mode": "FIXED_HORIZON",
        "trial_creation_policy_hash": policy_hash,
        "declared_trial_count": declared,
        "initial_witness_registry_hash": H("1"),
        "candidate_generation_policy_hash": H("2"),
        "target_selector_policy_hash": H("3"),
        "target_derivation_policy_hash": H("4"),
        "entropy_policy_hash": H("5"),
        "causal_model_hash": H("6"),
        "statistical_plan_hash": H("7"),
        "publication_policy_hash": H("8"),
        "external_freshness_policy_hash": H("9"),
        "conditioning_view_policy_hash": H("a"),
        "allowed_registry_reconfiguration": False,
        "strongest_grade_exactly_one_target_derivation_per_trial": True,
        "frozen_before_first_created": True,
    }


def event(index, trial, state_from, state_to, subtype, payload_hash, prerequisite=None):
    return {
        "schema": "AIFC/trial-ledger-event/v1",
        "experiment_id": "exp-1",
        "event_index": index,
        "trial_index": trial,
        "run_id": f"run-{trial}",
        "transition_ordinal": 0 if state_from is None else 1,
        "state_from": state_from,
        "state_to": state_to,
        "terminal_subtype": subtype,
        "previous_event_hash": H("b"),
        "prerequisite_certificate_hash": prerequisite,
        "payload_hash": payload_hash,
        "evidence_bundle_hash": None,
        "reason_code": "TEST",
    }


class ProtocolSemanticsTests(unittest.TestCase):
    def test_preallocated_slots_are_replayed_exactly(self):
        with tempfile.TemporaryDirectory() as td:
            store = Store(Path(td))
            policy_hash = store.protocol(creation_policy())
            plan_hash = store.protocol(experiment_plan(policy_hash))
            plan_q = H("c")
            e1 = store.protocol(event(0, 1, None, "CREATED", None, plan_hash, plan_q))
            e2 = store.protocol(event(1, 2, None, "CREATED", None, plan_hash, plan_q))
            manifest = {
                "experiment_id": "exp-1",
                "experiment_plan_hash": plan_hash,
                "experiment_plan_quorum_certificate_hash": plan_q,
                "ledger_event_hashes": [e1, e2],
            }
            outcome = replay_trial_creation_policy(manifest, store.resolver())
            self.assertEqual(outcome.status, "PASS")

    def test_missing_preallocated_created_slot_fails(self):
        with tempfile.TemporaryDirectory() as td:
            store = Store(Path(td))
            policy_hash = store.protocol(creation_policy())
            plan_hash = store.protocol(experiment_plan(policy_hash))
            plan_q = H("c")
            e1 = store.protocol(event(0, 1, None, "CREATED", None, plan_hash, plan_q))
            manifest = {
                "experiment_id": "exp-1",
                "experiment_plan_hash": plan_hash,
                "experiment_plan_quorum_certificate_hash": plan_q,
                "ledger_event_hashes": [e1],
            }
            with self.assertRaises(ProtocolSemanticsError) as ctx:
                replay_trial_creation_policy(manifest, store.resolver())
            self.assertIn("PREALLOCATED_CREATED_SLOT_SET_MISMATCH", str(ctx.exception))

    def test_schedule_creation_is_blocked_until_condition_replay_exists(self):
        with tempfile.TemporaryDirectory() as td:
            store = Store(Path(td))
            spec = store.raw(b"frozen deterministic schedule specification")
            policy_hash = store.protocol(creation_policy("DETERMINISTIC_SCHEDULE", declared=1, spec_hash=spec))
            plan_hash = store.protocol(experiment_plan(policy_hash, declared=1))
            plan_q = H("c")
            e1 = store.protocol(event(0, 1, None, "CREATED", None, plan_hash, plan_q))
            manifest = {
                "experiment_id": "exp-1",
                "experiment_plan_hash": plan_hash,
                "experiment_plan_quorum_certificate_hash": plan_q,
                "ledger_event_hashes": [e1],
            }
            outcome = replay_trial_creation_policy(manifest, store.resolver())
            self.assertEqual(outcome.status, "BLOCKED")
            self.assertEqual(outcome.code, "CREATED_OUTSIDE_FROZEN_SCHEDULE_OR_TRIGGER_NOT_REPLAYABLE")

    def test_created_to_completed_hit_is_impossible(self):
        with tempfile.TemporaryDirectory() as td:
            store = Store(Path(td))
            bad = store.protocol(event(0, 1, "CREATED", "TERMINAL", "COMPLETED_HIT", H("d"), None))
            with self.assertRaises(ProtocolSemanticsError) as ctx:
                replay_terminal_semantics({"ledger_event_hashes": [bad]}, store.resolver())
            self.assertIn("IMPOSSIBLE_TERMINAL_SUBTYPE", str(ctx.exception))

    def test_created_to_post_target_abort_is_impossible(self):
        with tempfile.TemporaryDirectory() as td:
            store = Store(Path(td))
            bad = store.protocol(event(0, 1, "CREATED", "TERMINAL", "ABORTED_POST_TARGET_PRE_VERIFY", H("d"), None))
            with self.assertRaises(ProtocolSemanticsError) as ctx:
                replay_terminal_semantics({"ledger_event_hashes": [bad]}, store.resolver())
            self.assertIn("IMPOSSIBLE_TERMINAL_SUBTYPE", str(ctx.exception))

    def test_created_to_pre_freeze_abort_is_valid(self):
        with tempfile.TemporaryDirectory() as td:
            store = Store(Path(td))
            good = store.protocol(event(0, 1, "CREATED", "TERMINAL", "ABORTED_PRE_FREEZE", H("d"), None))
            outcome = replay_terminal_semantics({"ledger_event_hashes": [good]}, store.resolver())
            self.assertEqual(outcome.status, "PASS")


if __name__ == "__main__":
    unittest.main()
