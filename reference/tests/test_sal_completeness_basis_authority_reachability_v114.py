#!/usr/bin/env python3
from __future__ import annotations
import copy, inspect, json
from pathlib import Path
import sys, unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"reference"/"verifier"))
import completeness_basis_authority_reachability_v1 as sal
import sal_completeness_basis_authority_reachability_checker_v114 as checker
from scientific_assurance_lineage_v13 import (
    NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1,
    NORMATIVE_ROOT_REGISTRY_PATH,
    NormativeRootClosureError,
    RootClosedNormativeRepositoryResolver,
    git_blob_sha1_bytes,
)

def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

class T(unittest.TestCase):
    def setUp(self):
        self.profile=load(sal.REACHABILITY_PROFILE_PATH)
        self.audit=load(checker.AUDIT_PATH)
        self.binding=load(checker.BINDING_PATH)

    def test_current_obstruction(self):
        r=sal.audit_current_reachability()
        self.assertEqual(r.status,"AUTHORITY_REACHABILITY_OBSTRUCTION_CONFIRMED_IN_CURRENT_TESTED_SCOPE")
        self.assertEqual(r.normative_lineage_completeness,sal.BLOCKED_COMPLETENESS)
        self.assertEqual(r.solver_invocation_count,0)

    def test_public_audit_has_no_authority_args(self):
        self.assertEqual(list(inspect.signature(sal.audit_current_reachability).parameters),[])

    def test_root_factory_has_no_caller_args(self):
        self.assertEqual(list(inspect.signature(RootClosedNormativeRepositoryResolver.from_repository_authority).parameters),[])

    def test_seed_source_unregistered(self):
        r=RootClosedNormativeRepositoryResolver.from_repository_authority()
        self.assertNotIn(sal.SEED_BASIS_SOURCE_ID,r.records)
        with self.assertRaises(NormativeRootClosureError) as c:
            r.resolve(sal.SEED_BASIS_SOURCE_ID)
        self.assertEqual(str(c.exception),"NORMATIVE_OBJECT_ID_NOT_REGISTERED:"+sal.SEED_BASIS_SOURCE_ID)

    def test_object_source_unregistered(self):
        r=RootClosedNormativeRepositoryResolver.from_repository_authority()
        self.assertNotIn(sal.OBJECT_RECOGNITION_BASIS_SOURCE_ID,r.records)

    def test_reference_source_unregistered(self):
        r=RootClosedNormativeRepositoryResolver.from_repository_authority()
        self.assertNotIn(sal.REFERENCE_SEMANTICS_BASIS_SOURCE_ID,r.records)

    def test_v113_basis_profile_unregistered(self):
        r=RootClosedNormativeRepositoryResolver.from_repository_authority()
        self.assertNotIn(sal.V113_BASIS_PROFILE_ID,r.records)

    def test_direct_registry_injection_rejected(self):
        with self.assertRaises(TypeError) as c:
            RootClosedNormativeRepositoryResolver(ROOT,{})
        self.assertIn("CALLER_SUPPLIED_ROOT_REGISTRY_FORBIDDEN",str(c.exception))

    def test_registered_root_substitution_rejected(self):
        b=copy.deepcopy(self.profile)
        b["seed_basis_source_artifact_id"]="AIFC-RELEASE-GATE-v1.0.8-draft"
        b["profile_content_hash"]=sal.profile_content_hash(b)
        with self.assertRaises(Exception) as c:
            sal.verify_reachability_profile(b)
        self.assertIn("seed_basis_source_artifact_id",str(c.exception))

    def test_unregistered_policy_weakening_rejected(self):
        b=copy.deepcopy(self.profile)
        b["unregistered_target_policy"]="ALLOW"
        b["profile_content_hash"]=sal.profile_content_hash(b)
        with self.assertRaises(Exception):
            sal.verify_reachability_profile(b)

    def test_profile_authority_self_assertion_rejected(self):
        b=copy.deepcopy(self.profile)
        b["profile_authority_status"]="ROOT_CLOSED_AUTHORITY_ADMISSIBLE"
        b["profile_content_hash"]=sal.profile_content_hash(b)
        with self.assertRaises(Exception):
            sal.verify_reachability_profile(b)

    def test_profile_authority_lineage_injection_rejected(self):
        b=copy.deepcopy(self.profile)
        b["authority_lineage_ref"]={"receipt_id":"x"}
        b["profile_content_hash"]=sal.profile_content_hash(b)
        with self.assertRaises(Exception):
            sal.verify_reachability_profile(b)

    def test_root_registry_identity_exact(self):
        raw=(ROOT/NORMATIVE_ROOT_REGISTRY_PATH).read_bytes()
        self.assertEqual(git_blob_sha1_bytes(raw),NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1)
        self.assertEqual(NORMATIVE_ROOT_REGISTRY_GIT_BLOB_SHA1,sal.ROOT_REGISTRY_GIT_BLOB_SHA1)

    def test_audit_content_and_replay(self):
        r=sal.verify_declared_audit(self.audit)
        self.assertEqual(r.solver_invocation_count,0)
        b=copy.deepcopy(self.audit)
        b["seed_completeness_authority_path"]="ESTABLISHED"
        b["audit_content_hash"]=sal.audit_content_hash(b)
        with self.assertRaises(Exception):
            sal.verify_declared_audit(b)

    def test_implementation_binding_exact(self):
        checker.verify_binding(self.binding)

    def test_implementation_rebindings_rejected(self):
        for k,v in (("implementation_path","reference/verifier/canonical.py"),
                    ("implementation_git_blob_sha1","0"*40),
                    ("implementation_raw_sha256","0"*64)):
            b=copy.deepcopy(self.binding)
            b[k]=v
            b["binding_content_hash"]=checker.binding_hash(b)
            with self.subTest(k=k):
                with self.assertRaises(SystemExit):
                    checker.verify_binding(b)

    def test_implementation_binding_authority_self_assertion_rejected(self):
        b=copy.deepcopy(self.binding)
        b["authority_status"]="ROOT_CLOSED_AUTHORITY_ADMISSIBLE"
        b["binding_content_hash"]=checker.binding_hash(b)
        with self.assertRaises(SystemExit):
            checker.verify_binding(b)

    def test_no_receipt_or_ci_authority_surface_and_v113_terminal_preserved(self):
        r=sal.audit_current_reachability()
        self.assertEqual(r.authority_receipt_caller_input_surface,"FORBIDDEN_NO_CALLER_INPUT_SURFACE")
        self.assertEqual(r.ci_receipt_to_normative_authority_promotion,"FORBIDDEN_NO_AUTHORITY_INPUT_SURFACE")
        self.assertEqual(r.external_bootstrap_ratification,"NOT_PERFORMED")
        self.assertEqual(r.derived_semantic_authority,"BLOCKED")
        self.assertEqual(r.solver_invocation_count,0)

if __name__=="__main__": unittest.main()
