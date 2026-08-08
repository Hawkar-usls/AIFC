#!/usr/bin/env python3
from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference" / "verifier"))

import lineage_completeness_basis_authority_v1 as sal  # noqa: E402
import lineage_vertex_reference_closure_v1 as v112  # noqa: E402


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class TestSALLineageCompletenessBasisAuthorityV113(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.closure = load(sal.V112_CLOSURE_PATH)
        cls.binding = load(sal.SEED_BINDING_PATH)
        cls.object_profile = load(sal.OBJECT_INDEX_PROFILE_PATH)
        cls.basis_profile = load(sal.BASIS_PROFILE_PATH)
        cls.audit = load(sal.AUDIT_PATH)

    def test_current_path_confirms_obstruction_solver_zero(self):
        report = sal.audit_lineage_completeness_basis()
        self.assertEqual(
            report.local_reference_closure,
            "ESTABLISHED_IN_TESTED_SCOPE_FROM_INHERITED_SEED",
        )
        self.assertEqual(
            report.normative_lineage_completeness,
            "BLOCKED_UNAUTHORIZED_COMPLETENESS_BASIS",
        )
        self.assertEqual(report.seed_completeness_authority, "NOT_ESTABLISHED")
        self.assertEqual(
            report.object_recognition_global_adequacy_authority,
            "NOT_ESTABLISHED",
        )
        self.assertEqual(
            report.reference_semantics_global_adequacy_authority,
            "NOT_ESTABLISHED",
        )
        self.assertEqual(report.derived_semantic_authority, "BLOCKED")
        self.assertEqual(report.solver_invocation_count, 0)

    def test_production_audit_has_no_caller_authority_input_surface(self):
        sig = inspect.signature(sal.audit_lineage_completeness_basis)
        self.assertEqual(tuple(sig.parameters), ())

    def test_local_fixed_point_cannot_promote_global_seed_completeness(self):
        bad = copy.deepcopy(self.closure)
        bad["global_lineage_seed_completeness"] = "ESTABLISHED"
        bad["closure_content_hash"] = v112.closure_content_hash(bad)
        with self.assertRaises(sal.LineageCompletenessBasisAuthorityV1Error):
            sal.verify_current_basis_sources(
                bad, self.binding, self.object_profile, self.basis_profile
            )

    def test_exact_seed_identity_does_not_establish_seed_adequacy(self):
        report = sal.verify_current_basis_sources(
            self.closure, self.binding, self.object_profile, self.basis_profile
        )
        self.assertEqual(
            report.seed_basis_identity,
            "CONFIRMED_EXACT_INHERITED_BINDING_PROJECTION",
        )
        self.assertEqual(report.seed_completeness_authority, "NOT_ESTABLISHED")

    def test_object_index_profile_global_adequacy_self_promotion_rejected(self):
        bad = copy.deepcopy(self.object_profile)
        bad["global_adequacy"] = "ESTABLISHED"
        bad["profile_content_hash"] = v112.profile_content_hash(bad)
        with self.assertRaises(Exception) as ctx:
            sal.verify_current_basis_sources(
                self.closure, self.binding, bad, self.basis_profile
            )
        self.assertIn("GLOBAL_ADEQUACY", str(ctx.exception))

    def test_object_index_profile_authority_self_assertion_rejected(self):
        bad = copy.deepcopy(self.object_profile)
        bad["profile_authority_status"] = "ROOT_CLOSED_AUTHORITY_ADMISSIBLE"
        bad["profile_content_hash"] = v112.profile_content_hash(bad)
        with self.assertRaises(Exception) as ctx:
            sal.verify_current_basis_sources(
                self.closure, self.binding, bad, self.basis_profile
            )
        self.assertIn("AUTHORITY_SELF_ASSERTION", str(ctx.exception))

    def test_basis_profile_cannot_self_promote_global_completeness(self):
        bad = copy.deepcopy(self.basis_profile)
        bad["global_normative_lineage_completeness"] = "ESTABLISHED"
        bad["profile_content_hash"] = sal.profile_content_hash(bad)
        with self.assertRaises(sal.LineageCompletenessBasisAuthorityV1Error):
            sal.verify_basis_profile(bad)

    def test_basis_profile_has_no_authority_lineage_input_surface(self):
        bad = copy.deepcopy(self.basis_profile)
        bad["authority_lineage_ref"] = {"anything": "successor"}
        bad["profile_content_hash"] = sal.profile_content_hash(bad)
        with self.assertRaises(sal.LineageCompletenessBasisAuthorityV1Error):
            sal.verify_basis_profile(bad)

    def test_seed_basis_projection_is_exact_and_mutation_changes_it(self):
        good = sal.seed_basis_projection_hash(self.closure, self.binding)
        self.assertEqual(good, sal.SEED_BASIS_HASH)
        bad_binding = copy.deepcopy(self.binding)
        bad_binding["vertices"][0]["raw_sha256"] = "0" * 64
        self.assertNotEqual(
            sal.seed_basis_projection_hash(self.closure, bad_binding),
            good,
        )

    def test_object_recognition_and_reference_semantics_have_separate_identities(self):
        recognition = sal.object_recognition_basis_projection_hash(self.object_profile)
        reference = sal.reference_semantics_basis_projection_hash(self.object_profile)
        self.assertEqual(recognition, sal.OBJECT_RECOGNITION_BASIS_HASH)
        self.assertEqual(reference, sal.REFERENCE_SEMANTICS_BASIS_HASH)
        self.assertNotEqual(recognition, reference)

        recognition_mutation = copy.deepcopy(self.object_profile)
        recognition_mutation["recognized_schemas"][0]["object_id_channel"] = "MUTATED"
        self.assertNotEqual(
            sal.object_recognition_basis_projection_hash(recognition_mutation),
            recognition,
        )
        self.assertEqual(
            sal.reference_semantics_basis_projection_hash(recognition_mutation),
            reference,
        )

        reference_mutation = copy.deepcopy(self.object_profile)
        reference_mutation["reference_rules"][0]["target_identity_channel"] = "MUTATED"
        self.assertEqual(
            sal.object_recognition_basis_projection_hash(reference_mutation),
            recognition,
        )
        self.assertNotEqual(
            sal.reference_semantics_basis_projection_hash(reference_mutation),
            reference,
        )

    def test_current_basis_profile_content_identity(self):
        self.assertEqual(
            sal.profile_content_hash(self.basis_profile),
            sal.BASIS_PROFILE_HASH,
        )
        sal.verify_basis_profile(self.basis_profile)

    def test_audit_object_is_content_bound_and_blocking(self):
        report = sal.verify_current_basis_sources(
            self.closure, self.binding, self.object_profile, self.basis_profile
        )
        self.assertEqual(sal.audit_content_hash(self.audit), sal.AUDIT_HASH)
        sal.verify_audit_object(self.audit, report)
        bad = copy.deepcopy(self.audit)
        bad["normative_lineage_completeness"] = "ESTABLISHED"
        bad["audit_content_hash"] = sal.audit_content_hash(bad)
        with self.assertRaises(sal.LineageCompletenessBasisAuthorityV1Error):
            sal.verify_audit_object(bad, report)


if __name__ == "__main__":
    unittest.main()
