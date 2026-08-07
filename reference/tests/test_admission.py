import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

VERIFIER_DIR = Path(__file__).resolve().parents[1] / "verifier"
sys.path.insert(0, str(VERIFIER_DIR))

from admission import verify_replay_manifest  # noqa: E402

H_PLAN = "1" * 64
H_POLICY = "2" * 64
H_PROFILE = "3" * 64
H_EVIDENCE = "4" * 64
H_BUNDLE = "5" * 64


class FakeResolver:
    def __init__(self, objects):
        self.objects = objects

    def resolve(self, content_hash, expected_schema=None):
        if content_hash == H_EVIDENCE:
            return SimpleNamespace(parsed_json=None, exact_bytes=b"evidence")
        obj = self.objects.get(content_hash)
        if obj is None:
            raise ValueError(f"missing:{content_hash}")
        if expected_schema is not None and obj.get("schema") != expected_schema:
            raise ValueError(f"schema:{expected_schema}:{obj.get('schema')}")
        return SimpleNamespace(parsed_json=obj, exact_bytes=b"{}")


def base_objects():
    plan = {
        "schema": "AIFC/experiment-plan/v1",
        "experiment_id": "exp-1",
        "entropy_policy_hash": H_POLICY,
    }
    policy = {
        "schema": "AIFC/entropy-policy/v1",
        "experiment_id": "exp-1",
        "source_id": "beacon-A",
        "source_protocol_version": "v1",
        "allowed_derivation_methods": ["PUBLIC_BEACON_SPECIFICATION"],
        "required_external_evidence_types": ["SOURCE_SECURITY_EVIDENCE"],
        "derivation_spec_hash": None,
        "unresolved_assumptions_policy": "BLOCK_STRONGEST_GRADE",
        "post_target_method_selection_forbidden": True,
        "frozen_before_first_created": True,
    }
    profile = {
        "schema": "AIFC/entropy-profile/v1",
        "experiment_id": "exp-1",
        "trial_index": 1,
        "source_id": "beacon-A",
        "source_protocol_version": "v1",
        "derivation_method": "PUBLIC_BEACON_SPECIFICATION",
        "unresolved_assumptions": [],
        "external_evidence": [
            {"evidence_type": "SOURCE_SECURITY_EVIDENCE", "content_hash": H_EVIDENCE}
        ],
    }
    return {H_PLAN: plan, H_POLICY: policy, H_PROFILE: profile}


def manifest():
    return {
        "schema": "AIFC/replay-package/v0.2",
        "experiment_id": "exp-1",
        "subject_trial_index": 1,
        "experiment_plan_hash": H_PLAN,
        "entropy_profile_hash": H_PROFILE,
        "evidence_bundle_hash": H_BUNDLE,
    }


def downstream_result():
    return {
        "schema": "AIFC/verifier-result/v1",
        "experiment_id": "exp-1",
        "trial_index": 1,
        "verifier_id": "AIFC-Verifier-A",
        "verifier_version": "0.2.0-replay",
        "evidence_bundle_hash": H_BUNDLE,
        "gate_results": {"DOWNSTREAM_CORE": "PASS"},
        "exact_match": False,
        "terminal_grade": "NOT_ADMITTED",
        "failure_codes": [],
        "physical_interpretation": "NO_AUTOMATIC_PHYSICAL_RETROCAUSALITY_CLAIM",
        "fail_open": False,
    }


class EntropyPolicyAdmissionTests(unittest.TestCase):
    def test_preregistered_entropy_policy_passes_to_downstream_replay(self):
        resolver = FakeResolver(base_objects())
        with patch("admission._verify_core", return_value=downstream_result()):
            result = verify_replay_manifest(manifest(), resolver)
        self.assertEqual(result["terminal_grade"], "NOT_ADMITTED")
        self.assertEqual(result["gate_results"].get("ENTROPY_POLICY_REPLAY"), "PASS")

    def test_post_target_entropy_method_substitution_fails_closed(self):
        objects = base_objects()
        objects[H_PROFILE]["derivation_method"] = "CONSERVATIVE_ANALYTIC_BOUND"
        result = verify_replay_manifest(manifest(), FakeResolver(objects))
        self.assertEqual(result["terminal_grade"], "INVALIDATED_EVIDENCE")
        self.assertIn("ENTROPY_DERIVATION_METHOD_NOT_PREREGISTERED", result["failure_codes"][0])

    def test_missing_required_entropy_evidence_class_fails_closed(self):
        objects = base_objects()
        objects[H_PROFILE]["external_evidence"] = [
            {"evidence_type": "SOME_OTHER_EVIDENCE", "content_hash": H_EVIDENCE}
        ]
        result = verify_replay_manifest(manifest(), FakeResolver(objects))
        self.assertEqual(result["terminal_grade"], "INVALIDATED_EVIDENCE")
        self.assertIn("ENTROPY_REQUIRED_EVIDENCE_CLASS_MISSING", result["failure_codes"][0])


if __name__ == "__main__":
    unittest.main()
