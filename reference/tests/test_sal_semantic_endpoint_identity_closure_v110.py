#!/usr/bin/env python3
from __future__ import annotations
import hashlib, inspect, json, sys, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'reference/verifier'))
from scientific_assurance_lineage_v14 import git_blob_sha1_bytes
import scientific_assurance_lineage_v17 as v17
import scientific_assurance_lineage_v18 as v18
import scientific_assurance_lineage_v110 as sal
import semantic_bridge_endpoint_identity_v1 as endpoint
P_ATOM='SEMANTIC_ATOM_86f973c56467be6d01d13657d406838f7128dd5d59c5dade17452de1efc49aa3'; P_ID='REQUIRED_CHECK_ID:AUTHORITY_CLOSED_PROOF'
T_ATOM='TARGET_ATOM_22c5e80e2b404cfa59a307a8e65f99e40b57035061a9b022f85bf3c2e67ea214'; T_ID='PROFILE_FIELD:allowed_authority_transition.from'
def derived(atom,identity,status='SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE'):
 o={'schema':'AIFC/bridge-derived-semantic-object/v1','derived_semantic_object_id':'TEST-DERIVED-OBJECT','entailment_question_id':v17.QUESTION_ID,'atom_id':atom,'semantic_identity':identity,'derivation_kind':'BRIDGE_DERIVED_SEMANTIC_OBJECT_V1','source_semantic_identities':[P_ID,T_ID],'derivation_authority_status':status,'authority_lineage_ref':({'transition_id':'T','receipt_id':'R','authority_registry_id':'A'} if status=='AUTHORITY_ADMISSIBLE' else None)}; o['derivation_content_hash']=endpoint.derived_semantic_object_content_hash(o); return o
def axiom(bindings,ast,status='SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE'):
 a={'schema':'AIFC/semantic-bridge-axiom/v2','axiom_id':'TEST-AXIOM-V2','entailment_question_id':v17.QUESTION_ID,'logical_fragment':'FINITE_CLASSICAL_PROPOSITIONAL_V1','endpoint_identity_profile_id':endpoint.ENDPOINT_PROFILE_ID,'normalized_formula_ast':ast,'atom_bindings':bindings,'axiom_authority_status':status,'authority_lineage_ref':({'transition_id':'T','receipt_id':'R','authority_registry_id':'A'} if status=='AUTHORITY_ADMISSIBLE' else None)}; a['axiom_content_hash']=endpoint.bridge_axiom_v2_content_hash(a); return a
class T(unittest.TestCase):
 def bindings(self):
  return json.loads((ROOT/v17.PREDECESSOR_FORMULA_PATH).read_text())['atom_bindings'],json.loads((ROOT/v17.TARGET_FORMULA_PATH).read_text())['atom_bindings']
 def membership(self): return {(v17.PREDECESSOR_COMMIT,v17.PREDECESSOR_PATH):v17.PREDECESSOR_BLOB,(v17.TARGET_PROFILE_COMMIT,v17.TARGET_PROFILE_PATH):v17.TARGET_PROFILE_BLOB}
 def test_production_api_remains_identity_only(self):
  p=set(inspect.signature(sal.audit_semantic_endpoint_identity_closure).parameters); self.assertEqual(p,{'predecessor_identity','target_profile_identity','entailment_question_identity'}); self.assertFalse({'premise','target','bridge','axiom','solver','binding','authority'}&p)
 def test_production_path_uses_endpoint_closed_solver_only(self):
  s=inspect.getsource(sal.audit_semantic_endpoint_identity_closure); self.assertIn('endpoint_exec.bridge_bound_entailment_v2',s); self.assertNotIn('finite_propositional_entailment(',s); self.assertNotIn('bridge_exec.bridge_bound_entailment(',s)
 def test_exact_predecessor_endpoint_identity_passes(self):
  p,t=self.bindings(); a=axiom({P_ATOM:{'semantic_role':'PREDECESSOR_ATOM','semantic_identity':p[P_ATOM]}},{'op':'ATOM','id':P_ATOM}); self.assertEqual(endpoint.verify_bridge_axiom_endpoint_identity(a,expected_question_id=v17.QUESTION_ID,predecessor_bindings=p,target_bindings=t,derived_object_resolver=lambda r:{},require_authority=False),{P_ATOM})
 def test_predecessor_endpoint_semantic_identity_rebinding_is_rejected(self):
  p,t=self.bindings(); a=axiom({P_ATOM:{'semantic_role':'PREDECESSOR_ATOM','semantic_identity':'WRONG'}},{'op':'ATOM','id':P_ATOM});
  with self.assertRaisesRegex(endpoint.SemanticBridgeEndpointIdentityV1Error,'BRIDGE_ATOM_SEMANTIC_IDENTITY_REBINDING'): endpoint.verify_bridge_axiom_endpoint_identity(a,expected_question_id=v17.QUESTION_ID,predecessor_bindings=p,target_bindings=t,derived_object_resolver=lambda r:{},require_authority=False)
 def test_predecessor_atom_role_rebinding_is_rejected(self):
  p,t=self.bindings(); a=axiom({P_ATOM:{'semantic_role':'TARGET_ATOM','semantic_identity':P_ID}},{'op':'ATOM','id':P_ATOM});
  with self.assertRaisesRegex(endpoint.SemanticBridgeEndpointIdentityV1Error,'BRIDGE_ATOM_ROLE_REBINDING'): endpoint.verify_bridge_axiom_endpoint_identity(a,expected_question_id=v17.QUESTION_ID,predecessor_bindings=p,target_bindings=t,derived_object_resolver=lambda r:{},require_authority=False)
 def test_target_endpoint_semantic_identity_rebinding_is_rejected(self):
  p,t=self.bindings(); a=axiom({T_ATOM:{'semantic_role':'TARGET_ATOM','semantic_identity':'WRONG'}},{'op':'ATOM','id':T_ATOM});
  with self.assertRaisesRegex(endpoint.SemanticBridgeEndpointIdentityV1Error,'BRIDGE_ATOM_SEMANTIC_IDENTITY_REBINDING'): endpoint.verify_bridge_axiom_endpoint_identity(a,expected_question_id=v17.QUESTION_ID,predecessor_bindings=p,target_bindings=t,derived_object_resolver=lambda r:{},require_authority=False)
 def test_bridge_derived_atom_collision_with_endpoint_is_rejected(self):
  p,t=self.bindings(); o=derived(P_ATOM,'DERIVED:X'); ref={'derived_semantic_object_id':o['derived_semantic_object_id'],'source_path':'conformance/test.json','git_blob_sha1':'0'*40,'raw_sha256':'0'*64,'derivation_content_hash':o['derivation_content_hash']}; a=axiom({P_ATOM:{'semantic_role':'BRIDGE_DERIVED_ATOM','semantic_identity':'DERIVED:X','derived_semantic_object_ref':ref}},{'op':'ATOM','id':P_ATOM});
  with self.assertRaisesRegex(endpoint.SemanticBridgeEndpointIdentityV1Error,'BRIDGE_DERIVED_ATOM_COLLISION'): endpoint.verify_bridge_axiom_endpoint_identity(a,expected_question_id=v17.QUESTION_ID,predecessor_bindings=p,target_bindings=t,derived_object_resolver=lambda r:o,require_authority=False)
 def test_bridge_derived_atom_requires_separate_provenance(self):
  p,t=self.bindings(); atom='BRIDGE_DERIVED_TEST'; a=axiom({atom:{'semantic_role':'BRIDGE_DERIVED_ATOM','semantic_identity':'DERIVED:X'}},{'op':'ATOM','id':atom});
  with self.assertRaisesRegex(endpoint.SemanticBridgeEndpointIdentityV1Error,'BRIDGE_DERIVED_ATOM_PROVENANCE_MISSING'): endpoint.verify_bridge_axiom_endpoint_identity(a,expected_question_id=v17.QUESTION_ID,predecessor_bindings=p,target_bindings=t,derived_object_resolver=lambda r:{},require_authority=False)
 def test_bridge_derived_atom_with_content_identified_candidate_object_passes_candidate_semantics(self):
  p,t=self.bindings(); atom='BRIDGE_DERIVED_TEST'; o=derived(atom,'DERIVED:X'); raw=json.dumps(o,sort_keys=True).encode(); ref={'derived_semantic_object_id':o['derived_semantic_object_id'],'source_path':'conformance/test.json','git_blob_sha1':git_blob_sha1_bytes(raw),'raw_sha256':hashlib.sha256(raw).hexdigest(),'derivation_content_hash':o['derivation_content_hash']}; a=axiom({atom:{'semantic_role':'BRIDGE_DERIVED_ATOM','semantic_identity':'DERIVED:X','derived_semantic_object_ref':ref}},{'op':'ATOM','id':atom}); endpoint.verify_bridge_axiom_endpoint_identity(a,expected_question_id=v17.QUESTION_ID,predecessor_bindings=p,target_bindings=t,derived_object_resolver=lambda r:o,require_authority=False)
 def test_candidate_derived_semantics_cannot_satisfy_authority_requirement(self):
  o=derived('BRIDGE_DERIVED_TEST','DERIVED:X');
  with self.assertRaisesRegex(endpoint.SemanticBridgeEndpointIdentityV1Error,'AUTHORITY_NOT_ADMISSIBLE'): endpoint.verify_derived_semantic_object(o,expected_question_id=v17.QUESTION_ID,expected_atom_id='BRIDGE_DERIVED_TEST',expected_semantic_identity='DERIVED:X',require_authority=True)
 def test_endpoint_namespaces_must_be_disjoint(self):
  a=axiom({'A':{'semantic_role':'PREDECESSOR_ATOM','semantic_identity':'P:A'}},{'op':'ATOM','id':'A'});
  with self.assertRaisesRegex(endpoint.SemanticBridgeEndpointIdentityV1Error,'BRIDGE_ENDPOINT_NAMESPACE_COLLISION'): endpoint.verify_bridge_axiom_endpoint_identity(a,expected_question_id=v17.QUESTION_ID,predecessor_bindings={'A':'P:A'},target_bindings={'A':'T:A'},derived_object_resolver=lambda r:{},require_authority=False)
 def test_semantic_authority_status_self_assertion_stays_blocked(self):
  s={'selection_authority_status':'PREDECESSOR_AUTHORITY_ADMITTED_SURFACE','completeness_claim':'AUTHORITY_ESTABLISHED_COMPLETE_FOR_QUESTION'}; th={'abstraction_adequacy_status':'AUTHORITY_ESTABLISHED','bridge_status':'AUTHORITY_ADMISSIBLE_BRIDGE_THEORY','bridge_authority_status':'AUTHORITY_ADMISSIBLE'}; ex={'execution_authority_status':'AUTHORITY_ADMISSIBLE'}; ep={'profile_authority_status':'AUTHORITY_ADMISSIBLE'}; m={'method_authority_status':'AUTHORITY_ADMISSIBLE','formal_semantics':{'max_atoms':16}}; ext={'old_domain_result_equivalence_status':'ESTABLISHED_BY_REPLAY','same_question_method_semantics_preservation_status':'ESTABLISHED','bridge_aware_extended_capacity_status':'CAPACITY_AVAILABLE_FOR_RESOLVED_THEOREM','extension_authority_status':'AUTHORITY_ADMISSIBLE','authority_lineage_status':'AUTHORITY_LINEAGE_ESTABLISHED','resolved_bridge_aware_atom_count':18,'extended_max_atoms':18}; self.assertIn('BLOCKED_SEMANTIC_AUTHORITY_STATUS_LINEAGE',sal._closure_blockers(s,s,th,[],ex,ep,m,ext,18,{'binding_status':'DUAL_IDENTITY_ESTABLISHED'}))
 def test_capacity_extension_candidate_does_not_mutate_base_max_atoms(self):
  m=v18._verify_entailment_method_profile(v17._verify_question(),18); e=sal._verify_capacity_extension(m); self.assertIsNone(e['resolved_bridge_aware_atom_count']); self.assertIsNone(e['extended_max_atoms']); self.assertFalse(sal._capacity_extension_is_admissible(e,bridge_aware_atom_count=18)); self.assertEqual(sal._effective_max_atoms(m,e,bridge_aware_atom_count=18),16)
 def test_same_question_method_label_is_preserved(self):
  e=json.loads((ROOT/sal.CAPACITY_EXTENSION_PATH).read_text()); q=v17._verify_question(); self.assertEqual(e['entailment_question_id'],q['question_id']); self.assertEqual(e['logical_method_label'],q['entailment_method']); self.assertEqual(e['logical_method_label'],v17.ENTAILMENT_METHOD)
 def test_bridge_theory_v3_requires_v2_axiom_language_and_stays_empty_candidate(self):
  ep=sal._verify_endpoint_profile(); th=sal._verify_bridge_theory_v3(ep); self.assertEqual(th['predecessor_bridge_theory_git_blob_sha1'],sal.BRIDGE_THEORY_V2_BLOB); self.assertEqual(th['bridge_axiom_schema_id'],'AIFC/semantic-bridge-axiom/v2'); self.assertEqual(th['bridge_axiom_refs'],[]); self.assertEqual(th['bridge_authority_lineage_status'],'NOT_ESTABLISHED')
 def test_schema_registry_v10_dual_hashes_resolve_exact_source_bytes(self):
  r=v17._strict('conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v10.json','AIFC/schema-identity-registry/v10'); self.assertEqual(r['predecessor_registry_git_blob_sha1'],'4aab16f170e25be77db82a41e0f024e3622d26f4'); self.assertEqual(len(r['records']),8)
  for x in r['records']:
   raw=(ROOT/x['source_path']).read_bytes(); self.assertEqual(git_blob_sha1_bytes(raw),x['git_blob_sha1']); self.assertEqual(hashlib.sha256(raw).hexdigest(),x['raw_schema_sha256'])
 def test_release_frontier_is_exact_115_to_122(self):
  old=json.loads((ROOT/'conformance/AIFC-RELEASE-GATE-v1.0.16-draft.json').read_text()); new=json.loads((ROOT/'conformance/AIFC-RELEASE-GATE-v1.0.17-draft.json').read_text()); oi=[x['id'] for x in old['required_checks']]; ni=[x['id'] for x in new['required_checks']]; self.assertEqual((len(oi),len(ni)),(115,122)); self.assertEqual(ni[:115],oi); self.assertEqual(ni[115:],['BRIDGE_ENDPOINT_SEMANTIC_IDENTITY','BRIDGE_ATOM_ROLE_IDENTITY_BINDING','BRIDGE_DERIVED_ATOM_PROVENANCE','SEMANTIC_AUTHORITY_STATUS_LINEAGE','ENTAILMENT_METHOD_CONSERVATIVE_CAPACITY_EXTENSION','SAME_QUESTION_METHOD_SEMANTICS_PRESERVATION','BRIDGE_AWARE_EXTENDED_CAPACITY'])
 def test_current_production_path_keeps_solver_at_zero(self):
  with patch.object(v17,'git_tree_blob',side_effect=lambda c,p:self.membership()[(c,p)]),patch.object(endpoint,'bridge_bound_entailment_v2',side_effect=AssertionError('solver must not run')) as solver:
   r=sal.audit_semantic_endpoint_identity_closure(v17.PREDECESSOR_ID,v17.TARGET_PROFILE_ID,v17.QUESTION_ID)
  self.assertEqual(r.result,'BLOCKED'); self.assertEqual(r.blocked_subtype,'BLOCKED_UNAUTHORIZED_INTERPRETATION'); self.assertEqual(r.current_bridge_axiom_count,0); self.assertEqual(r.current_bridge_aware_atom_count,18); self.assertEqual(r.bridge_aware_extended_capacity,'BLOCKED_NO_AUTHORIZED_EXTENSION_18_GT_16'); self.assertEqual(r.semantic_authority_status_lineage,'NOT_ESTABLISHED_SELF_ASSERTION_BLOCKED'); self.assertEqual(r.solver_invocation_count,0); solver.assert_not_called()
if __name__=='__main__': unittest.main()
