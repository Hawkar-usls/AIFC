#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, inspect, json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'reference'/'verifier'))
import external_bootstrap_ratification_admissibility_v1 as sal
import bootstrap_non_self_ratification_boundary_v1 as v116
import sal_external_bootstrap_ratification_admissibility_checker_v117 as checker
from scientific_assurance_lineage_v13 import git_blob_sha1_bytes

def load(p:str):return json.loads((ROOT/p).read_text())
def candidate():
 h='1'*64
 return {"schema":sal.CANDIDATE_SCHEMA_ID,"candidate_id":"EXTERNAL-RATIFIER-CANDIDATE-TEST","bootstrap_root_commit":sal.BOOTSTRAP_COMMIT,"ratifier_identity":"EXTERNAL-RATIFIER-TEST","ratification_scope":"BOOTSTRAP_ROOT_LEGITIMACY_ONLY","ratification_statement_hash":h,"ratifier_provenance_ref":"external://ratifier/provenance","ratifier_provenance_hash":h,"non_descendant_provenance_ref":"external://independence/proof","non_descendant_provenance_hash":h,"authority_basis_ref":"external://authority/basis","authority_basis_hash":h,"authentication_evidence_ref":"external://auth/evidence","authentication_evidence_hash":h,"candidate_semantics":sal.CANDIDATE_ONLY}
class T(unittest.TestCase):
 def setUp(self):self.profile=load(sal.PROFILE_PATH);self.audit=load(checker.AUDIT_PATH);self.binding=load(checker.BINDING_PATH)
 def test_current_boundary_blocks(self):
  r=sal.audit_current_external_ratification_admissibility();self.assertEqual(r['external_ratifier_authority_admissibility'],'NOT_ESTABLISHED');self.assertEqual(r['bootstrap_authority_legitimacy'],'NOT_ESTABLISHED');self.assertEqual(r['external_bootstrap_ratification'],'NOT_PERFORMED');self.assertEqual(r['solver_invocation_count'],0)
 def test_production_has_no_caller_candidate_surface(self):self.assertEqual(list(inspect.signature(sal.audit_current_external_ratification_admissibility).parameters),[])
 def test_profile_exact(self):sal.verify_profile(self.profile);self.assertEqual(self.profile['profile_content_hash'],sal.PROFILE_HASH)
 def test_profile_candidate_injection_rejected(self):
  x=copy.deepcopy(self.profile);x['external_ratifier']='SUCCESSOR_CHOSEN';self.assertRaisesRegex(sal.V117Error,'AUTHORITY_OR_CANDIDATE_INPUT_SURFACE|PROFILE_CONTENT_REBINDING',sal.verify_profile,x)
 def test_candidate_schema_is_technical_non_authority(self):
  s=load(sal.CANDIDATE_SCHEMA_PATH);self.assertFalse(s['additionalProperties']);self.assertFalse(set(s['properties'])&set(sal.FORBIDDEN))
 def test_well_formed_candidate_remains_unresolved(self):self.assertEqual(sal.validate_candidate_shape(candidate()),sal.WELL_FORMED)
 def test_independence_plus_authentication_is_not_authority(self):self.assertEqual(sal.combine_non_authorizing_evidence(True,True),sal.BOTH_ONLY);self.assertIn('AUTHORITY_UNRESOLVED',sal.BOTH_ONLY)
 def test_incomplete_evidence_stays_unresolved(self):self.assertEqual(sal.combine_non_authorizing_evidence(True,False),sal.INCOMPLETE)
 def test_candidate_root_rebinding_rejected(self):
  x=candidate();x['bootstrap_root_commit']='0'*40;self.assertRaisesRegex(sal.V117Error,'BOOTSTRAP_ROOT_REBINDING',sal.validate_candidate_shape,x)
 def test_candidate_authority_injection_rejected(self):
  x=candidate();x['authority_admissible']=True;self.assertRaisesRegex(sal.V117Error,'SELF_AUTHORIZATION_FIELD',sal.validate_candidate_shape,x)
 def test_candidate_legitimacy_injection_rejected(self):
  x=candidate();x['bootstrap_authority_legitimacy']='ESTABLISHED';self.assertRaisesRegex(sal.V117Error,'SELF_AUTHORIZATION_FIELD',sal.validate_candidate_shape,x)
 def test_external_label_injection_rejected(self):
  x=candidate();x['external']=True;self.assertRaisesRegex(sal.V117Error,'SELF_AUTHORIZATION_FIELD',sal.validate_candidate_shape,x)
 def test_authority_basis_self_reference_rejected(self):
  x=candidate();x['authority_basis_ref']=x['candidate_id'];self.assertRaisesRegex(sal.V117Error,'AUTHORITY_BASIS_SELF_REFERENCE',sal.validate_candidate_shape,x)
 def test_known_internal_ratifier_rejected(self):
  x=candidate();x['ratifier_identity']=v116.ROOT_V2_ID;self.assertRaisesRegex(sal.V117Error,'KNOWN_INTERNAL_RATIFIER',sal.validate_candidate_shape,x)
 def test_known_internal_authority_basis_rejected(self):
  x=candidate();x['authority_basis_ref']=v116.ROOT_V1_ID;self.assertRaisesRegex(sal.V117Error,'KNOWN_INTERNAL_AUTHORITY_BASIS',sal.validate_candidate_shape,x)
 def test_required_reference_omission_rejected(self):
  x=candidate();del x['non_descendant_provenance_ref'];self.assertRaisesRegex(sal.V117Error,'FIELD_SET_REBINDING',sal.validate_candidate_shape,x)
 def test_authentication_omission_rejected(self):
  x=candidate();del x['authentication_evidence_hash'];self.assertRaisesRegex(sal.V117Error,'FIELD_SET_REBINDING',sal.validate_candidate_shape,x)
 def test_hash_encoding_fail_closed(self):
  x=candidate();x['authority_basis_hash']='bad';self.assertRaisesRegex(sal.V117Error,'HASH_ENCODING',sal.validate_candidate_shape,x)
 def test_v116_boundary_preserved(self):
  p=v116.verify_declared_audit(load(sal.V116_AUDIT_PATH));self.assertEqual(p.non_self_ratification_theorem,'ESTABLISHED_FOR_ROOT_RELATIVE_DESCENDANT_CLOSURE');self.assertEqual(p.external_ratifier_authority_admissibility,'NOT_ESTABLISHED')
 def test_v116_implementation_dual_bound(self):
  raw=(ROOT/sal.V116_IMPLEMENTATION_PATH).read_bytes();self.assertEqual(git_blob_sha1_bytes(raw),sal.V116_IMPLEMENTATION_BLOB);self.assertEqual(hashlib.sha256(raw).hexdigest(),sal.V116_IMPLEMENTATION_RAW)
 def test_designated_intake_absent_and_scope_nonglobal(self):
  self.assertFalse((ROOT/sal.DESIGNATED_INTAKE_PATH).exists());r=sal.audit_current_external_ratification_admissibility();self.assertEqual(r['candidate_discovery_scope'],'DESIGNATED_INTAKE_PATH_ONLY_NOT_GLOBAL_DISCOVERY');self.assertEqual(r['designated_intake_path_status'],'ABSENT')
 def test_declared_audit_exact(self):self.assertEqual(sal.verify_declared_audit(self.audit)['admissibility_separation_invariant'],'STRUCTURAL_INDEPENDENCE_AND_AUTHENTICATION_DO_NOT_IMPLY_AUTHORITY_ADMISSIBILITY')
 def test_audit_authority_promotion_rejected(self):
  x=copy.deepcopy(self.audit);x['external_ratifier_authority_admissibility']='ESTABLISHED';self.assertRaisesRegex(sal.V117Error,'AUDIT_CONTENT_REBINDING|AUDIT_REPORT_REBINDING',sal.verify_declared_audit,x)
 def test_global_claims_stay_open(self):
  r=sal.audit_current_external_ratification_admissibility();self.assertEqual(r['global_external_ratifier_discovery_completeness'],'NOT_ESTABLISHED');self.assertEqual(r['global_authority_admissibility_semantics'],'NOT_ESTABLISHED')
 def test_binding_exact(self):checker.verify_binding(self.binding)
 def test_schema_registry_v19_exact(self):checker.verify_schemas()
 def test_next_basis_is_real_external_object_plus_separate_authority(self):self.assertEqual(sal.audit_current_external_ratification_admissibility()['next_required_basis'],'REAL_EXTERNAL_RATIFICATION_OBJECT_WITH_NON_DESCENDANT_PROVENANCE_AND_SEPARATELY_ADMISSIBLE_AUTHORITY_BASIS')
if __name__=='__main__':unittest.main()
