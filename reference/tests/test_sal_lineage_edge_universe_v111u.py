#!/usr/bin/env python3
from __future__ import annotations
import copy,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'reference/verifier'))
import scientific_assurance_lineage_v17 as v17
import scientific_assurance_lineage_v111h as v111h
import scientific_assurance_lineage_v111u as sal
import semantic_lineage_edge_universe_v1 as universe

class T(unittest.TestCase):
 def L(self,p): return json.loads((ROOT/p).read_text())
 def data(self):
  o,_=v111h._objects_and_raws()
  return {k:copy.deepcopy(v) for k,v in o.items()},self.L(sal.PROFILE_PATH),self.L(sal.UNIVERSE_PATH)
 def test_current_machine_derived_universe_is_15_and_contains_unexpected_proof_to_derived(self):
  o,p,r=self.data();d,h=universe.verify_universe_receipt(r,o,p)
  self.assertEqual((len(d),h),(15,sal.EDGE_UNIVERSE_HASH))
  keys={x['edge_key'] for x in d}
  self.assertIn('PROOF->DERIVED#semantic_identity',keys)
  self.assertIn('PROFILE->QUESTION#question_id',keys)
  self.assertIn('GRAPH->DERIVED#semantic_identity',keys)
 def test_receipt_cannot_define_required_universe_by_omission(self):
  o,p,r=self.data()
  for victim in ('PROFILE->QUESTION#question_id','PROOF->DERIVED#semantic_identity'):
   with self.subTest(victim=victim):
    t=copy.deepcopy(r)
    t['derived_edges']=[x for x in t['derived_edges'] if x['edge_key']!=victim]
    t['derived_edge_count']=len(t['derived_edges'])
    t['edge_universe_hash']=universe.edge_universe_hash(t['derived_edges'])
    t['universe_content_hash']=universe.universe_content_hash(t)
    with self.assertRaisesRegex(universe.LineageEdgeUniverseV1Error,'LINEAGE_REQUIRED_EDGE_UNIVERSE_OMISSION_OR_INJECTION'):
     universe.verify_universe_receipt(t,o,p)
 def test_deriver_discovers_new_cross_vertex_reference_without_required_edge_constant(self):
  o,p,_=self.data()
  before=universe.derive_edge_universe(o,p)
  o['PROOF']['synthetic_derived_object_ref']=o['DERIVED']['derived_semantic_object_id']
  after=universe.derive_edge_universe(o,p)
  self.assertEqual((len(before),len(after)),(15,16))
  self.assertIn('PROOF->DERIVED#derived_semantic_object_id',{x['edge_key'] for x in after})
 def test_question_context_rebindings_are_independent_invariants(self):
  pb=self.L(v111h.BINDING_PATH);pa=self.L(v111h.AUDIT_PATH);ur=self.L(sal.UNIVERSE_PATH);ua=self.L(sal.AUDIT_PATH)
  cases=[(pb,'LINEAGE_BINDING_QUESTION_CONTEXT_REBINDING'),(pa,'LINEAGE_AUDIT_QUESTION_CONTEXT_REBINDING'),(ur,'LINEAGE_UNIVERSE_QUESTION_CONTEXT_REBINDING'),(ua,'LINEAGE_UNIVERSE_AUDIT_QUESTION_CONTEXT_REBINDING')]
  for obj,needle in cases:
   with self.subTest(needle=needle):
    xs=[copy.deepcopy(pb),copy.deepcopy(pa),copy.deepcopy(ur),copy.deepcopy(ua)]
    idx=[pb,pa,ur,ua].index(obj);xs[idx]['entailment_question_id']='0'*64
    with self.assertRaisesRegex(sal.ScientificAssuranceLineageV111UError,needle):
     sal.assert_question_context_objects(*xs,v17.QUESTION_ID)
 def test_profile_is_content_and_execution_bound_but_not_authoritative(self):
  p=self.L(sal.PROFILE_PATH)
  self.assertEqual(p['profile_content_hash'],sal.PROFILE_HASH)
  self.assertEqual(p['execution_implementation_git_blob_sha1'],sal.UNIVERSE_IMPL_BLOB)
  self.assertEqual(p['profile_authority_status'],'SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE')
 def test_production_terminal_preserves_authority_block_and_solver_zero(self):
  inherited=SimpleNamespace(derived_semantic_authority='BLOCKED',solver_invocation_count=0,result='BLOCKED',blocked_subtype='BLOCKED_UNAUTHORIZED_INTERPRETATION')
  with patch.object(sal.v111h,'audit_derived_semantic_lineage_edge_binding',return_value=inherited):
   x=sal.audit_lineage_edge_universe_derivation(v17.PREDECESSOR_ID,v17.TARGET_PROFILE_ID,v17.QUESTION_ID)
  self.assertEqual((x.machine_derived_edge_count,x.additional_derived_edge_count,x.derived_semantic_authority,x.solver_invocation_count),(15,6,'BLOCKED',0))

if __name__=='__main__':unittest.main()
