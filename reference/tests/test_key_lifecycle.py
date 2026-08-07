import copy
import sys
import tempfile
import unittest
from pathlib import Path

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from canonical import canonical_json_bytes, raw_evidence_hash  # noqa: E402
from canonical_v02 import protocol_hash_v02  # noqa: E402
from key_lifecycle import (  # noqa: E402
    KeyLifecycleError,
    key_lifecycle_genesis_hash,
    replay_historical_key_lifecycle,
)
from resolver_v02 import EvidenceResolverV02  # noqa: E402
from signature_policy_admission import (  # noqa: E402
    SignaturePreimageMaterial,
    SignaturePreimageReplaySummary,
)


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
            "store_id": "key-lifecycle-test",
            "entries": self.entries,
        })


def registry(exp="exp-1", sequence=3, witness_count=4):
    witnesses = []
    for i in range(witness_count):
        witnesses.append({
            "witness_id": f"w{i}",
            "failure_domain": f"fd-{i}",
            "status": "ACTIVE",
            "keys": [{
                "key_id": f"k{i}",
                "algorithm": "Ed25519",
                "public_key_encoding": "hex",
                "public_key": f"{i+1:02x}" * 32,
                "valid_from_registry_sequence": 0,
                "valid_until_registry_sequence": None,
                "status": "ACTIVE",
                "predecessor_key_id": None,
                "revocation_reason": None,
            }],
        })
    return {
        "schema": "AIFC/witness-registry/v1",
        "registry_id": f"r{sequence}",
        "experiment_id": exp,
        "registry_sequence": sequence,
        "previous_registry_hash": "10" * 32,
        "transition_certificate_hash": None if sequence == 0 else "20" * 32,
        "fault_model": {
            "n": witness_count,
            "f": 1 if witness_count >= 4 else 0,
            "q": 3 if witness_count >= 4 else 2,
            "independence_unit": "FAILURE_DOMAIN",
        },
        "witnesses": witnesses,
    }


def lifecycle_policy(exp="exp-1"):
    return {
        "schema": "AIFC/key-lifecycle-policy/v1",
        "policy_id": "AIFC-KEY-LIFECYCLE-POLICY-V1",
        "experiment_id": exp,
        "boundary_unit": "REGISTRY_SEQUENCE",
        "compromise_semantics": "INVALIDATE_SIGNATURES_AT_OR_AFTER_EARLIEST_UNTRUSTED_SEQUENCE",
        "prospective_revocation_semantics": "INVALIDATE_NEW_SIGNATURES_AT_OR_AFTER_EFFECTIVE_SEQUENCE",
        "event_chain_semantics": "GLOBAL_APPEND_ONLY_HASH_CHAIN",
        "unknown_compromise_boundary_semantics": "INVALIDATE_FROM_REGISTRY_SEQUENCE_ZERO",
        "quorum_reevaluation_semantics": "REMOVE_HISTORICALLY_UNTRUSTED_SIGNATURES_AND_RECOMPUTE_Q_AND_FAILURE_DOMAINS",
        "external_completeness_required": True,
        "wall_clock_not_sufficient": True,
        "frozen_before_first_created": True,
    }


def plan(exp, policy_hash):
    return {
        "schema": "AIFC/experiment-plan/v1",
        "experiment_id": exp,
        "protocol_version": "1.0-draft",
        "mode": "FIXED_HORIZON",
        "trial_creation_policy_hash": "01" * 32,
        "declared_trial_count": 1,
        "initial_witness_registry_hash": "02" * 32,
        "candidate_generation_policy_hash": "03" * 32,
        "target_selector_policy_hash": "04" * 32,
        "target_derivation_policy_hash": "05" * 32,
        "entropy_policy_hash": "06" * 32,
        "signature_preimage_policy_hash": "07" * 32,
        "key_lifecycle_policy_hash": policy_hash,
        "causal_model_hash": "08" * 32,
        "statistical_plan_hash": "09" * 32,
        "publication_policy_hash": "0a" * 32,
        "external_freshness_policy_hash": "0b" * 32,
        "conditioning_view_policy_hash": "0c" * 32,
        "allowed_registry_reconfiguration": True,
        "strongest_grade_exactly_one_target_derivation_per_trial": True,
        "frozen_before_first_created": True,
    }


def bundle(exp, plan_hash, registry_hash, ledger_hash):
    return {
        "schema": "AIFC/evidence-bundle/v1",
        "experiment_id": exp,
        "trial_index": 1,
        "run_id": "run-1",
        "experiment_plan_hash": plan_hash,
        "trial_ledger_head_hash": "11" * 32,
        "pre_return_certificate_hash": "12" * 32,
        "candidate_generation_profile_hash": "13" * 32,
        "candidate_set_hash": "14" * 32,
        "candidate_multiplicity": 1,
        "target_selector_profile_hash": "15" * 32,
        "target_derivation_profile_hash": "16" * 32,
        "conditioning_view_hash": "17" * 32,
        "entropy_profile_hash": "18" * 32,
        "causal_model_hash": "19" * 32,
        "statistical_plan_hash": "1a" * 32,
        "witness_registry_hash": registry_hash,
        "witness_registry_transition_hash": None,
        "key_lifecycle_ledger_hash": ledger_hash,
        "target_evidence_hash": "1b" * 32,
        "eprocess_state_hash": None,
        "additional_evidence_hashes": [],
    }


def signature_summary(registry_hash, q=3, witnesses=(0, 1, 2), sequence=3, group="certificate-A"):
    materials = []
    for i in witnesses:
        receipt = {
            "schema": "AIFC/witness-receipt/v1",
            "witness_id": f"w{i}",
            "key_id": f"k{i}",
        }
        materials.append(SignaturePreimageMaterial(
            receipt_schema="AIFC/witness-receipt/v1",
            receipt=receipt,
            preimage=f"message-{i}".encode(),
            registry_hash=registry_hash,
            registry_sequence=sequence,
            witness_id=f"w{i}",
            key_id=f"k{i}",
            certificate_group_id=group,
            required_q=q,
        ))
    return SignaturePreimageReplaySummary(
        receipt_count=len(materials),
        preimage_sha256s=tuple("aa" * 32 for _ in materials),
        materials=tuple(materials),
    )


def event(exp, index, previous, witness_id, key_id, registry_hash, evidence_hash, *,
          event_type="COMPROMISE_DISCOVERED", effective=3, recorded=3, basis="EXACT_KNOWN"):
    return {
        "schema": "AIFC/key-lifecycle-event/v1",
        "experiment_id": exp,
        "event_index": index,
        "previous_event_hash": previous,
        "event_type": event_type,
        "witness_id": witness_id,
        "key_id": key_id,
        "subject_registry_hash": registry_hash,
        "recorded_against_registry_hash": registry_hash,
        "recorded_against_registry_sequence": recorded,
        "effective_from_registry_sequence": effective,
        "boundary_basis": basis,
        "evidence_hashes": [evidence_hash],
        "reason_code": "TEST_LIFECYCLE_EVENT",
        "wall_clock_timestamp": None,
    }


def build(root: Path, event_specs=None):
    event_specs = event_specs or []
    s = Store(root)
    exp = "exp-1"
    registry_obj = registry(exp)
    registry_hash = s.protocol(registry_obj)
    policy_hash = s.protocol(lifecycle_policy(exp))
    plan_hash = s.protocol(plan(exp, policy_hash))
    evidence_hash = s.raw(b"independent lifecycle incident evidence")

    previous = key_lifecycle_genesis_hash(exp)
    event_hashes = []
    event_objects = []
    for index, spec in enumerate(event_specs):
        obj = event(
            exp,
            index,
            previous,
            spec.get("witness_id", "w0"),
            spec.get("key_id", "k0"),
            registry_hash,
            spec.get("evidence_hash", evidence_hash),
            event_type=spec.get("event_type", "COMPROMISE_DISCOVERED"),
            effective=spec.get("effective", 3),
            recorded=spec.get("recorded", 3),
            basis=spec.get("basis", "EXACT_KNOWN"),
        )
        if "previous_override" in spec:
            obj["previous_event_hash"] = spec["previous_override"]
        h = s.protocol(obj)
        event_objects.append(obj)
        event_hashes.append(h)
        previous = h

    ledger = {
        "schema": "AIFC/key-lifecycle-ledger/v1",
        "experiment_id": exp,
        "policy_hash": policy_hash,
        "event_hashes": event_hashes,
        "event_count": len(event_hashes),
        "final_head_hash": previous,
        "cutoff_registry_hash": registry_hash,
        "cutoff_registry_sequence": 3,
        "completeness_status": "LOCAL_CHAIN_REPLAYED_EXTERNAL_COMPLETENESS_NOT_PROVEN",
    }
    ledger_hash = s.protocol(ledger)
    bundle_hash = s.protocol(bundle(exp, plan_hash, registry_hash, ledger_hash))
    manifest = {
        "experiment_id": exp,
        "experiment_plan_hash": plan_hash,
        "evidence_bundle_hash": bundle_hash,
        "key_lifecycle_ledger_hash": ledger_hash,
    }
    return s, manifest, registry_hash, ledger, event_objects, evidence_hash


class HistoricalKeyLifecycleTests(unittest.TestCase):
    def test_empty_local_ledger_replays_but_does_not_prove_completeness(self):
        with tempfile.TemporaryDirectory() as td:
            s, manifest, registry_hash, *_ = build(Path(td), [])
            result = replay_historical_key_lifecycle(
                manifest, s.resolver(), signature_summary(registry_hash, q=3)
            )
            self.assertEqual(result.lifecycle_event_count, 0)
            self.assertEqual(result.invalidated_signature_count, 0)
            self.assertFalse(result.external_completeness_proven)
            self.assertEqual(result.quorum_results[0].trusted_witness_count, 3)

    def test_known_compromise_can_retroactively_collapse_quorum(self):
        with tempfile.TemporaryDirectory() as td:
            s, manifest, registry_hash, *_ = build(Path(td), [{"witness_id": "w0", "effective": 3}])
            with self.assertRaises(KeyLifecycleError) as ctx:
                replay_historical_key_lifecycle(
                    manifest, s.resolver(), signature_summary(registry_hash, q=3)
                )
            self.assertIn("HISTORICAL_QUORUM_COLLAPSE", str(ctx.exception))

    def test_known_compromise_can_remove_one_signer_while_quorum_survives(self):
        with tempfile.TemporaryDirectory() as td:
            s, manifest, registry_hash, *_ = build(Path(td), [{"witness_id": "w0", "effective": 3}])
            result = replay_historical_key_lifecycle(
                manifest, s.resolver(), signature_summary(registry_hash, q=2)
            )
            self.assertEqual(result.invalidated_signature_count, 1)
            q = result.quorum_results[0]
            self.assertEqual(q.trusted_witness_count, 2)
            self.assertEqual(q.trusted_failure_domain_count, 2)
            self.assertEqual(q.required_q, 2)
            self.assertFalse(result.external_completeness_proven)

    def test_unknown_compromise_boundary_must_start_at_genesis(self):
        with tempfile.TemporaryDirectory() as td:
            s, manifest, registry_hash, *_ = build(Path(td), [{
                "witness_id": "w3",
                "effective": 1,
                "basis": "UNKNOWN_FROM_GENESIS",
            }])
            with self.assertRaises(KeyLifecycleError) as ctx:
                replay_historical_key_lifecycle(
                    manifest, s.resolver(), signature_summary(registry_hash, q=3)
                )
            self.assertIn("UNKNOWN_COMPROMISE_BOUNDARY_MUST_START_AT_ZERO", str(ctx.exception))

    def test_prospective_revocation_cannot_be_silently_made_retroactive(self):
        with tempfile.TemporaryDirectory() as td:
            s, manifest, registry_hash, *_ = build(Path(td), [{
                "witness_id": "w3",
                "event_type": "REVOCATION_DECLARED",
                "recorded": 3,
                "effective": 2,
                "basis": "PROSPECTIVE_DECLARATION",
            }])
            with self.assertRaises(KeyLifecycleError) as ctx:
                replay_historical_key_lifecycle(
                    manifest, s.resolver(), signature_summary(registry_hash, q=3)
                )
            self.assertIn("PROSPECTIVE_KEY_EVENT_RETROACTIVE_WITHOUT_COMPROMISE", str(ctx.exception))

    def test_hash_chain_break_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            s, manifest, registry_hash, *_ = build(Path(td), [{
                "witness_id": "w3",
                "previous_override": "ff" * 32,
            }])
            with self.assertRaises(KeyLifecycleError) as ctx:
                replay_historical_key_lifecycle(
                    manifest, s.resolver(), signature_summary(registry_hash, q=3)
                )
            self.assertIn("KEY_LIFECYCLE_CHAIN_BREAK", str(ctx.exception))

    def test_later_event_cannot_relax_earlier_compromise_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            s, manifest, registry_hash, *_ = build(Path(td), [
                {"witness_id": "w0", "effective": 1, "recorded": 3, "basis": "CONSERVATIVE_LOWER_BOUND"},
                {"witness_id": "w0", "effective": 3, "recorded": 3, "basis": "EXACT_KNOWN"},
            ])
            with self.assertRaises(KeyLifecycleError) as ctx:
                replay_historical_key_lifecycle(
                    manifest,
                    s.resolver(),
                    signature_summary(registry_hash, q=3, sequence=2),
                )
            self.assertIn("HISTORICAL_QUORUM_COLLAPSE", str(ctx.exception))

    def test_bundle_lifecycle_hash_rebinding_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            s, manifest, registry_hash, *_ = build(Path(td), [])
            manifest["key_lifecycle_ledger_hash"] = "ee" * 32
            with self.assertRaises(Exception) as ctx:
                replay_historical_key_lifecycle(
                    manifest, s.resolver(), signature_summary(registry_hash, q=3)
                )
            self.assertIn("DANGLING_EVIDENCE_HASH", str(ctx.exception))

    def test_cutoff_before_signature_sequence_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            s, manifest, registry_hash, *_ = build(Path(td), [])
            with self.assertRaises(KeyLifecycleError) as ctx:
                replay_historical_key_lifecycle(
                    manifest, s.resolver(), signature_summary(registry_hash, q=3, sequence=4)
                )
            self.assertIn("KEY_LIFECYCLE_CUTOFF_BEFORE_SIGNATURE_SEQUENCE", str(ctx.exception))

    def test_dangling_lifecycle_incident_evidence_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            s, manifest, registry_hash, *_ = build(Path(td), [{
                "witness_id": "w3",
                "evidence_hash": "dd" * 32,
            }])
            with self.assertRaises(Exception) as ctx:
                replay_historical_key_lifecycle(
                    manifest, s.resolver(), signature_summary(registry_hash, q=3)
                )
            self.assertIn("DANGLING_EVIDENCE_HASH", str(ctx.exception))

    def test_event_recorded_after_lifecycle_cutoff_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            s, manifest, registry_hash, *_ = build(Path(td), [{
                "witness_id": "w3",
                "recorded": 4,
                "effective": 3,
            }])
            with self.assertRaises(Exception) as ctx:
                replay_historical_key_lifecycle(
                    manifest, s.resolver(), signature_summary(registry_hash, q=3)
                )
            # The referenced recording registry is sequence 3, so replay catches the
            # inconsistent declaration before any historical conclusion is possible.
            self.assertTrue(
                "KEY_LIFECYCLE_RECORDED_SEQUENCE_REBINDING" in str(ctx.exception)
                or "KEY_LIFECYCLE_EVENT_AFTER_LEDGER_CUTOFF" in str(ctx.exception)
            )

    def test_unknown_subject_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            s, manifest, registry_hash, *_ = build(Path(td), [{
                "witness_id": "w0",
                "key_id": "not-a-key",
            }])
            with self.assertRaises(KeyLifecycleError) as ctx:
                replay_historical_key_lifecycle(
                    manifest, s.resolver(), signature_summary(registry_hash, q=3)
                )
            self.assertIn("KEY_LIFECYCLE_KEY_NOT_UNIQUE", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
