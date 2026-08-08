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

import bootstrap_non_self_ratification_boundary_v1 as sal
import bootstrap_authority_origin_boundary_v1 as v115
import sal_bootstrap_non_self_ratification_checker_v116 as checker
from scientific_assurance_lineage_v13 import git_blob_sha1_bytes


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class BootstrapNonSelfRatificationV116Tests(unittest.TestCase):
    def setUp(self):
        self.profile = load(sal.PROFILE_PATH)
        self.audit = load(checker.AUDIT_PATH)
        self.binding = load(checker.BINDING_PATH)

    def test_current_boundary_is_blocking_and_solver_zero(self):
        r = sal.audit_current_non_self_ratification()
        self.assertEqual(
            r.status,
            "BOOTSTRAP_NON_SELF_RATIFICATION_BOUNDARY_CONFIRMED_IN_CURRENT_TESTED_SCOPE",
        )
        self.assertEqual(r.bootstrap_authority_legitimacy, "NOT_ESTABLISHED")
        self.assertEqual(r.current_internal_verification_path_to_bootstrap_legitimacy, "ABSENT")
        self.assertEqual(r.external_bootstrap_ratification, "NOT_PERFORMED")
        self.assertEqual(r.solver_invocation_count, 0)

    def test_public_audit_has_no_ratifier_or_authority_args(self):
        self.assertEqual(list(inspect.signature(sal.audit_current_non_self_ratification).parameters), [])

    def test_profile_identity_is_exact(self):
        sal.verify_profile(self.profile)
        self.assertEqual(self.profile["profile_content_hash"], sal.PROFILE_HASH)

    def test_profile_cannot_inject_external_ratifier(self):
        x = copy.deepcopy(self.profile)
        x["external_ratifier"] = "SUCCESSOR_CHOSEN_WITNESS"
        with self.assertRaisesRegex(
            sal.BootstrapNonSelfRatificationV1Error,
            "PROFILE_CONTENT_REBINDING|PROFILE_EXACT_HASH_REBINDING",
        ):
            sal.verify_profile(x)

    def test_profile_cannot_self_assert_authority(self):
        x = copy.deepcopy(self.profile)
        x["authority_status"] = "AUTHORITATIVE"
        with self.assertRaisesRegex(
            sal.BootstrapNonSelfRatificationV1Error,
            "PROFILE_CONTENT_REBINDING|PROFILE_EXACT_HASH_REBINDING",
        ):
            sal.verify_profile(x)

    def test_descendant_closure_is_reflexive_transitive(self):
        nodes = {"r", "a", "b", "x"}
        edges = (("r", "a"), ("a", "b"))
        self.assertEqual(sal.descendant_closure("r", nodes, edges), frozenset({"r", "a", "b"}))

    def test_bootstrap_cannot_self_ratify(self):
        nodes = {"r", "a"}
        edges = (("r", "a"),)
        self.assertEqual(sal.assess_ratifier("r", nodes, edges, "r"), sal.INTERNAL_REJECTION)

    def test_descendant_cannot_ratify_bootstrap(self):
        nodes = {"r", "a", "b"}
        edges = (("r", "a"), ("a", "b"))
        self.assertEqual(sal.assess_ratifier("r", nodes, edges, "b"), sal.INTERNAL_REJECTION)

    def test_externality_label_cannot_launder_descendant_provenance(self):
        nodes = {"r", "a"}
        edges = (("r", "a"),)
        self.assertEqual(
            sal.assess_ratifier("r", nodes, edges, "a", claimed_external=True),
            sal.INTERNAL_REJECTION,
        )

    def test_outside_closure_is_only_structural_candidate_not_authority(self):
        nodes = {"r", "a", "x"}
        edges = (("r", "a"),)
        self.assertEqual(sal.assess_ratifier("r", nodes, edges, "x"), sal.STRUCTURAL_ONLY)

    def test_unbound_ratifier_is_rejected(self):
        nodes = {"r", "a"}
        with self.assertRaisesRegex(sal.BootstrapNonSelfRatificationV1Error, "RATIFIER_PROVENANCE_UNBOUND"):
            sal.assess_ratifier("r", nodes, (("r", "a"),), "x")

    def test_cycle_is_rejected_not_used_as_ratification(self):
        nodes = {"r", "a"}
        edges = (("r", "a"), ("a", "r"))
        with self.assertRaisesRegex(sal.BootstrapNonSelfRatificationV1Error, "JURISDICTION_CYCLE"):
            sal.descendant_closure("r", nodes, edges)

    def test_self_loop_is_rejected(self):
        with self.assertRaisesRegex(sal.BootstrapNonSelfRatificationV1Error, "JURISDICTION_CYCLE"):
            sal.descendant_closure("r", {"r"}, (("r", "r"),))

    def test_unknown_jurisdiction_node_is_rejected(self):
        with self.assertRaisesRegex(sal.BootstrapNonSelfRatificationV1Error, "UNKNOWN_JURISDICTION_NODE"):
            sal.descendant_closure("r", {"r"}, (("r", "x"),))

    def test_non_self_ratification_theorem_replays_on_arbitrary_finite_dag(self):
        nodes = {"r", "a", "b", "x"}
        edges = (("r", "a"), ("a", "b"))
        self.assertEqual(
            sal.verify_non_self_ratification_theorem("r", nodes, edges),
            "ESTABLISHED_FOR_ROOT_RELATIVE_DESCENDANT_CLOSURE",
        )

    def test_current_root_chain_is_exactly_bound(self):
        root1 = load(sal.ROOT_V1_PATH)
        root2 = load(sal.ROOT_V2_PATH)
        self.assertEqual(git_blob_sha1_bytes((ROOT / sal.ROOT_V1_PATH).read_bytes()), sal.ROOT_V1_BLOB)
        self.assertEqual(git_blob_sha1_bytes((ROOT / sal.ROOT_V2_PATH).read_bytes()), sal.ROOT_V2_BLOB)
        self.assertEqual(root1["bootstrap_root_commit"], sal.BOOTSTRAP_COMMIT)
        self.assertEqual(root2["predecessor_registry_id"], sal.ROOT_V1_ID)
        self.assertEqual(root2["predecessor_registry_git_blob_sha1"], sal.ROOT_V1_BLOB)

    def test_v115_boundary_is_preserved_not_promoted(self):
        prior = v115.verify_declared_audit(load(sal.V115_AUDIT_PATH))
        self.assertEqual(prior.bootstrap_authority_legitimacy, "NOT_ESTABLISHED")
        self.assertEqual(prior.current_internal_verification_path_to_bootstrap_legitimacy, "ABSENT")
        self.assertEqual(prior.external_bootstrap_ratification, "NOT_PERFORMED")

    def test_declared_audit_replay_is_exact(self):
        r = sal.verify_declared_audit(self.audit)
        self.assertEqual(r.non_self_ratification_theorem, "ESTABLISHED_FOR_ROOT_RELATIVE_DESCENDANT_CLOSURE")

    def test_declared_audit_legitimacy_promotion_is_rejected(self):
        x = copy.deepcopy(self.audit)
        x["bootstrap_authority_legitimacy"] = "ESTABLISHED"
        with self.assertRaisesRegex(sal.BootstrapNonSelfRatificationV1Error, "AUDIT_CONTENT_REBINDING|AUDIT_REPORT_REBINDING"):
            sal.verify_declared_audit(x)

    def test_implementation_binding_is_exact(self):
        checker.verify_binding(self.binding)

    def test_schema_registry_v18_is_exact_and_valid(self):
        checker.verify_schemas()

    def test_global_impossibility_is_not_claimed(self):
        r = sal.audit_current_non_self_ratification()
        self.assertEqual(r.global_non_self_ratification_theorem_for_all_verification_systems, "NOT_CLAIMED")

    def test_next_basis_requires_external_non_descendant_and_separate_authority(self):
        r = sal.audit_current_non_self_ratification()
        self.assertEqual(
            r.next_required_basis,
            "EXTERNALLY_ANCHORED_NON_DESCENDANT_RATIFICATION_WITH_SEPARATE_AUTHORITY_ADMISSIBILITY",
        )
        self.assertEqual(r.external_ratifier_authority_admissibility, "NOT_ESTABLISHED")

    def test_internal_authority_closure_is_not_bootstrap_legitimacy(self):
        r = sal.audit_current_non_self_ratification()
        self.assertEqual(
            r.internal_authority_closure_vs_bootstrap_legitimacy,
            "DISTINCT_CONFIRMED_IN_TESTED_ROOT_RELATIVE_MODEL",
        )
        self.assertEqual(r.bootstrap_authority_legitimacy, "NOT_ESTABLISHED")


if __name__ == "__main__":
    unittest.main()
