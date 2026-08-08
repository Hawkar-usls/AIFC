#!/usr/bin/env python3
from __future__ import annotations
import copy, inspect, json
from pathlib import Path
import sys, unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"reference"/"verifier"))

import bootstrap_authority_origin_boundary_v1 as sal
import sal_bootstrap_authority_origin_checker_v115 as checker
from scientific_assurance_lineage_v13 import git_blob_sha1_bytes
import scientific_assurance_lineage_v16 as sal16

def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

class T(unittest.TestCase):
    def setUp(self):
        self.profile=load(sal.PROFILE_PATH)
        self.audit=load(checker.AUDIT_PATH)
        self.binding=load(checker.BINDING_PATH)

    def test_current_origin_boundary(self):
        r=sal.audit_current_origin()
        self.assertEqual(r.status,"BOOTSTRAP_AUTHORITY_ORIGIN_BOUNDARY_CONFIRMED_IN_CURRENT_TESTED_SCOPE")
        self.assertEqual(r.bootstrap_authority_legitimacy,"NOT_ESTABLISHED")
        self.assertEqual(r.current_internal_verification_path_to_bootstrap_legitimacy,"ABSENT")
        self.assertEqual(r.solver_invocation_count,0)

    def test_public_audit_has_no_args(self):
        self.assertEqual(list(inspect.signature(sal.audit_current_origin).parameters),[])

    def test_profile_identity(self):
        sal.verify_profile(self.profile)
        self.assertEqual(self.profile["profile_content_hash"],sal.PROFILE_HASH)

    def test_root_v1_exact_designation(self):
        root=load(sal.ROOT_V1_PATH)
        self.assertEqual(git_blob_sha1_bytes((ROOT/sal.ROOT_V1_PATH).read_bytes()),sal.ROOT_V1_BLOB)
        self.assertEqual(root["bootstrap_root_commit"],sal.BOOTSTRAP_COMMIT)

    def test_root_v2_exact_continuation(self):
        root=load(sal.ROOT_V2_PATH)
        self.assertEqual(git_blob_sha1_bytes((ROOT/sal.ROOT_V2_PATH).read_bytes()),sal.ROOT_V2_BLOB)
        self.assertEqual(root["predecessor_registry_id"],sal.ROOT_V1_ID)
        self.assertEqual(root["predecessor_registry_git_blob_sha1"],sal.ROOT_V1_BLOB)

    def test_bootstrap_status_preserves_nonlegitimacy(self):
        x=load(sal.BOOTSTRAP_STATUS_PATH)
        self.assertEqual(git_blob_sha1_bytes((ROOT/sal.BOOTSTRAP_STATUS_PATH).read_bytes()),sal.BOOTSTRAP_STATUS_BLOB)
        self.assertEqual(x["authority_basis_status"],"IMPLICIT_NOT_YET_FIRST_CLASS")
        self.assertFalse(x["retroactive_discovery_of_preexisting_authority"])
        self.assertEqual(x["external_bootstrap_ratification_status"],"NOT_PERFORMED")
        self.assertEqual(x["normative_authority_claim"],"NOT_ESTABLISHED_BY_THIS_OBJECT")

    def test_source_existence_lemma(self):
        self.assertEqual(sal16.verify_no_normative_authority_ex_nihilo_instance({"A","B"},{("A","B")}),"SOURCE_NODE_EXISTS")

    def test_source_existence_cycle_rejected(self):
        with self.assertRaises(Exception):
            sal16.verify_no_normative_authority_ex_nihilo_instance({"A","B"},{("A","B"),("B","A")})

    def test_source_existence_implementation_identity(self):
        self.assertEqual(git_blob_sha1_bytes((ROOT/sal.SOURCE_EXISTENCE_IMPL_PATH).read_bytes()),sal.SOURCE_EXISTENCE_IMPL_BLOB)

    def test_designation_to_legitimacy_rejected(self):
        b=copy.deepcopy(self.profile); b["bootstrap_designation_to_legitimacy"]="ALLOWED"
        b["profile_content_hash"]=sal.profile_content_hash(b)
        with self.assertRaises(Exception): sal.verify_profile(b)

    def test_source_existence_to_legitimacy_rejected(self):
        b=copy.deepcopy(self.profile); b["source_existence_to_legitimacy"]="ALLOWED"
        b["profile_content_hash"]=sal.profile_content_hash(b)
        with self.assertRaises(Exception): sal.verify_profile(b)

    def test_execution_attestation_to_legitimacy_rejected(self):
        b=copy.deepcopy(self.profile); b["execution_attestation_to_legitimacy"]="ALLOWED"
        b["profile_content_hash"]=sal.profile_content_hash(b)
        with self.assertRaises(Exception): sal.verify_profile(b)

    def test_ci_attestation_to_legitimacy_rejected(self):
        b=copy.deepcopy(self.profile); b["ci_attestation_to_legitimacy"]="ALLOWED"
        b["profile_content_hash"]=sal.profile_content_hash(b)
        with self.assertRaises(Exception): sal.verify_profile(b)

    def test_successor_authority_to_bootstrap_legitimacy_rejected(self):
        b=copy.deepcopy(self.profile); b["successor_authority_to_bootstrap_legitimacy"]="ALLOWED"
        b["profile_content_hash"]=sal.profile_content_hash(b)
        with self.assertRaises(Exception): sal.verify_profile(b)

    def test_external_ratification_injection_rejected(self):
        b=copy.deepcopy(self.profile); b["external_ratification"]={"status":"PERFORMED"}
        b["profile_content_hash"]=sal.profile_content_hash(b)
        with self.assertRaises(Exception): sal.verify_profile(b)

    def test_successor_receipt_is_execution_only(self):
        r=load(sal.SUCCESSOR_RECEIPT_PATH)
        self.assertEqual(git_blob_sha1_bytes((ROOT/sal.SUCCESSOR_RECEIPT_PATH).read_bytes()),sal.SUCCESSOR_RECEIPT_BLOB)
        self.assertEqual(r["receipt_id"],sal.SUCCESSOR_RECEIPT_ID)
        self.assertEqual(r["tested_source_commit"],sal.SUCCESSOR_RECEIPT_COMMIT)
        self.assertFalse(r["platform_trust_proven"])
        self.assertNotIn("bootstrap_authority_legitimacy",r)

    def test_audit_legitimacy_promotion_rejected(self):
        b=copy.deepcopy(self.audit); b["bootstrap_authority_legitimacy"]="ESTABLISHED"
        b["audit_content_hash"]=sal.audit_content_hash(b)
        with self.assertRaises(Exception): sal.verify_declared_audit(b)

    def test_retroactive_authority_promotion_rejected(self):
        b=copy.deepcopy(self.audit); b["retroactive_discovery_of_preexisting_authority"]=True
        b["audit_content_hash"]=sal.audit_content_hash(b)
        with self.assertRaises(Exception): sal.verify_declared_audit(b)

    def test_implementation_binding_exact(self):
        checker.verify_binding(self.binding)

    def test_implementation_rebindings_rejected(self):
        for k,v in (("implementation_path","reference/verifier/canonical.py"),("implementation_git_blob_sha1","0"*40),("implementation_raw_sha256","0"*64)):
            b=copy.deepcopy(self.binding); b[k]=v; b["binding_content_hash"]=checker.binding_hash(b)
            with self.subTest(k=k):
                with self.assertRaises(SystemExit): checker.verify_binding(b)

    def test_implementation_binding_self_authority_rejected(self):
        b=copy.deepcopy(self.binding); b["authority_status"]="ROOT_CLOSED_AUTHORITY_ADMISSIBLE"
        b["binding_content_hash"]=checker.binding_hash(b)
        with self.assertRaises(SystemExit): checker.verify_binding(b)

if __name__=="__main__": unittest.main()
