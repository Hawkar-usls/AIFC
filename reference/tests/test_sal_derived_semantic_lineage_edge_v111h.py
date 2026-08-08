#!/usr/bin/env python3
from __future__ import annotations
import copy,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'reference/verifier'))
import semantic_derivation_replay_v1 as replay, semantic_lineage_edge_binding_v1 as edge
import scientific_assurance_lineage_v17 as v17, scientific_assurance_lineage_v111 as v111, scientific_assurance_lineage_v111h as sal
class T(unittest.TestCase):
 def L(self,p):return json.loads((ROOT/p).read_text())
 def raw(self,o):return (json.dumps(o,ensure_ascii=False,separators=(',',':'))+'\n').encode()
 def data(self):
  p={'PROFILE':v111.DERIVATION_PROFILE_PATH,'PROOF':v111.PROOF_PATH,'MANIFEST':v111.MANIFEST_PATH,'GRAPH':v111.GRAPH_PATH,'DERIVED':v111.DERIVED_PATH,'QUESTION':'conformance/AIFC-ENTAILMENT-QUESTION-v1.json'}
  return {k:self.L(x) for k,x in p.items()},{k:(ROOT/x).read_bytes() for k,x in p.items()},self.L(sal.BINDING_PATH)
 def mutate(self,key,field,value,hfield,hfn):
  o,r,b=self.data();o=copy.deepcopy(o);r=dict(r);o[key][field]=value;o[key][hfield]=hfn(o[key]);r[key]=self.raw(o[key]);return o,r,b
 def test_current_graph(self):
  o,r,b=self.data();v,e,g=edge.verify_binding_receipt(b,o,r);self.assertEqual((len(v),len(e),g),(6,9,sal.LINEAGE_GRAPH_IDENTITY))
 def test_declared_edge_rebindings(self):
  cases=[('PROOF','declared_leaf_manifest_id','OTHER','proof_content_hash',replay.proof_content_hash,'PROOF_TO_MANIFEST:OBJECT_ID'),('PROOF','declared_leaf_manifest_hash','0'*64,'proof_content_hash',replay.proof_content_hash,'PROOF_TO_MANIFEST'),('PROOF','declared_dependency_graph_id','OTHER','proof_content_hash',replay.proof_content_hash,'PROOF_TO_DEPENDENCY_GRAPH:OBJECT_ID'),('PROOF','declared_dependency_graph_hash','0'*64,'proof_content_hash',replay.proof_content_hash,'PROOF_TO_DEPENDENCY_GRAPH'),('MANIFEST','derivation_profile_id','OTHER','manifest_content_hash',replay.manifest_content_hash,'MANIFEST_TO_PROFILE:OBJECT_ID'),('DERIVED','derivation_profile_id','OTHER','derivation_content_hash',replay.derived_content_hash,'DERIVED_TO_PROFILE:OBJECT_ID'),('DERIVED','derivation_proof_content_hash','0'*64,'derivation_content_hash',replay.derived_content_hash,'DERIVED_TO_PROOF'),('DERIVED','canonical_leaf_manifest_hash','0'*64,'derivation_content_hash',replay.derived_content_hash,'DERIVED_TO_MANIFEST'),('DERIVED','canonical_dependency_graph_id','OTHER','derivation_content_hash',replay.derived_content_hash,'DERIVED_TO_DEPENDENCY_GRAPH:OBJECT_ID')]
  for c in cases:
   with self.subTest(c=c):
    o,r,b=self.mutate(*c[:5])
    with self.assertRaisesRegex(edge.SemanticLineageEdgeBindingV1Error,c[5]):edge.verify_binding_receipt(b,o,r)
 def test_graph_question_rebinding(self):
  o,r,b=self.data();o=copy.deepcopy(o);r=dict(r);q='0'*64;o['GRAPH']['entailment_question_id']=q;o['GRAPH']['dependency_graph_hash']=replay.dependency_graph_hash(o['GRAPH']['derived_semantic_identity'],o['GRAPH']['dependencies'],q);o['GRAPH']['graph_content_hash']=replay.graph_content_hash(o['GRAPH']);r['GRAPH']=self.raw(o['GRAPH'])
  o['PROOF']['declared_dependency_graph_hash']=o['GRAPH']['dependency_graph_hash'];o['PROOF']['proof_content_hash']=replay.proof_content_hash(o['PROOF']);r['PROOF']=self.raw(o['PROOF'])
  o['DERIVED']['canonical_dependency_graph_hash']=o['GRAPH']['dependency_graph_hash'];o['DERIVED']['derivation_content_hash']=replay.derived_content_hash(o['DERIVED']);r['DERIVED']=self.raw(o['DERIVED'])
  with self.assertRaisesRegex(edge.SemanticLineageEdgeBindingV1Error,'GRAPH_TO_QUESTION:OBJECT_ID'):edge.verify_binding_receipt(b,o,r)
 def test_receipt_rebindings_and_omission(self):
  o,r,b=self.data()
  for kind in ('projection','vertex','omit'):
   t=copy.deepcopy(b)
   if kind=='projection':t['edges'][1]['resolved_target_semantic_projection_hash']='0'*64;t['lineage_edge_set_hash']=edge.edge_set_hash(t['edges']);t['lineage_graph_identity']=edge.lineage_graph_identity(t['vertices'],t['edges']);needle='DERIVED_SEMANTIC_LINEAGE_EDGE_REBINDING'
   elif kind=='vertex':t['vertices'][2]['raw_sha256']='0'*64;t['lineage_graph_identity']=edge.lineage_graph_identity(t['vertices'],t['edges']);needle='LINEAGE_VERTEX_WHOLE_OBJECT_IDENTITY_REBINDING'
   else:t['edges']=t['edges'][:-1];t['lineage_edge_set_hash']=edge.edge_set_hash(t['edges']);t['lineage_graph_identity']=edge.lineage_graph_identity(t['vertices'],t['edges']);needle='LINEAGE_EDGE_SET_OMISSION_OR_INJECTION'
   t['binding_content_hash']=edge.binding_content_hash(t)
   with self.subTest(kind=kind),self.assertRaisesRegex(edge.SemanticLineageEdgeBindingV1Error,needle):edge.verify_binding_receipt(t,o,r)
 def test_bytes_object_rebinding(self):
  o,r,b=self.data();o=copy.deepcopy(o);o['PROOF']['declared_leaf_manifest_id']='OTHER';o['PROOF']['proof_content_hash']=replay.proof_content_hash(o['PROOF'])
  with self.assertRaisesRegex(edge.SemanticLineageEdgeBindingV1Error,'LINEAGE_VERTEX_BYTES_TO_OBJECT_REBINDING:PROOF'):edge.verify_binding_receipt(b,o,r)
 def test_audit_authority_blocked_solver_zero(self):
  x=SimpleNamespace(solver_invocation_count=0,derived_semantic_authority='BLOCKED',result='BLOCKED',blocked_subtype='BLOCKED_UNAUTHORIZED_INTERPRETATION')
  with patch.object(sal.v111,'audit_derived_semantic_lineage',return_value=x):r=sal.audit_derived_semantic_lineage_edge_binding(v17.PREDECESSOR_ID,v17.TARGET_PROFILE_ID,v17.QUESTION_ID)
  self.assertEqual((r.edge_identity,r.derived_semantic_authority,r.solver_invocation_count),('ESTABLISHED_IN_TESTED_SCOPE','BLOCKED',0))
if __name__=='__main__':unittest.main()
