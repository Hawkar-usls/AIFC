#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'reference/verifier'))
from scientific_assurance_lineage_v14 import git_blob_sha1_bytes
import semantic_lineage_edge_binding_v1 as edge
import scientific_assurance_lineage_v17 as v17
import scientific_assurance_lineage_v111 as v111
import scientific_assurance_lineage_v111h as sal
S={'schemas/derived-semantic-lineage-edge-binding-v1.schema.json':[sal.BINDING_PATH],'schemas/derived-semantic-lineage-edge-audit-v1.schema.json':[sal.AUDIT_PATH],'schemas/schema-identity-registry-v12.schema.json':['conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v12.json']}
def L(p):return json.loads((ROOT/p).read_text())
def F(s):raise SystemExit(s)
def data():
 p={'PROFILE':v111.DERIVATION_PROFILE_PATH,'PROOF':v111.PROOF_PATH,'MANIFEST':v111.MANIFEST_PATH,'GRAPH':v111.GRAPH_PATH,'DERIVED':v111.DERIVED_PATH,'QUESTION':'conformance/AIFC-ENTAILMENT-QUESTION-v1.json'}
 return {k:L(x) for k,x in p.items()},{k:(ROOT/x).read_bytes() for k,x in p.items()}
def main():
 ids=[]
 for sp,ops in S.items():
  sc=L(sp);ids.append(sc['properties']['schema']['const']);v=Draft202012Validator(sc)
  for op in ops:
   e=list(v.iter_errors(L(op)))
   if e:F('SAL_V111H_SCHEMA_VALIDATION = FAIL:'+op+':'+e[0].message)
 print('SAL_V111H_SCHEMA_HEADERS = PASS (3/3)')
 reg=L('conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v12.json')
 if reg['predecessor_registry_git_blob_sha1']!='7c04110819e189260b475d75e91a51f2ad53f7d5' or {x['schema_id'] for x in reg['records']}!=set(ids):F('SAL_SCHEMA_IDENTITY_REGISTRATION_V12 = FAIL')
 for x in reg['records']:
  b=(ROOT/x['source_path']).read_bytes()
  if git_blob_sha1_bytes(b)!=x['git_blob_sha1'] or hashlib.sha256(b).hexdigest()!=x['raw_schema_sha256']:F('SAL_SCHEMA_IDENTITY_REGISTRATION_V12 = FAIL:DUAL')
 print('SAL_SCHEMA_IDENTITY_REGISTRATION_V12 = PASS (3/3 dual-bound candidate identities)')
 o,r=data();b=L(sal.BINDING_PATH);vs,es,g=edge.verify_binding_receipt(b,o,r)
 if (len(vs),len(es),g)!=(6,9,sal.LINEAGE_GRAPH_IDENTITY):F('DERIVED_SEMANTIC_LINEAGE_GRAPH_IDENTITY = FAIL')
 for x in ['VERTEX_IDENTITY = ESTABLISHED_IN_V1_11_TESTED_SCOPE','EDGE_IDENTITY = ESTABLISHED_IN_TESTED_SCOPE','DERIVED_SEMANTIC_LINEAGE_EDGE_SET_EXACTNESS = CONFIRMED_9_OF_9','SEMANTIC_PROJECTION_EDGE_BINDING = CONFIRMED_IN_TESTED_SCOPE','WHOLE_OBJECT_EDGE_BINDING = CONFIRMED_IN_TESTED_SCOPE','DERIVED_SEMANTIC_LINEAGE_GRAPH_IDENTITY = ESTABLISHED_IN_TESTED_SCOPE']:print(x)
 print('LINEAGE_EDGE_SET_HASH = '+b['lineage_edge_set_hash']);print('LINEAGE_GRAPH_IDENTITY = '+g)
 if len(L('conformance/AIFC-RELEASE-GATE-v1.0.18-draft.json')['required_checks'])!=143:F('SAL_RELEASE_GATE_122_TO_143 = FAIL')
 print('SAL_RELEASE_GATE_122_TO_143 = INHERITED_UNCHANGED');print('SAL_V111H_RELEASE_GATE_INTEGRATION = HARDENING_LAYER_NO_GATE_RENUMBER')
 x=sal.audit_derived_semantic_lineage_edge_binding(v17.PREDECESSOR_ID,v17.TARGET_PROFILE_ID,v17.QUESTION_ID)
 if x.edge_identity!='ESTABLISHED_IN_TESTED_SCOPE' or x.derived_semantic_authority!='BLOCKED' or x.solver_invocation_count!=0:F('SAL_V111H_TERMINAL = FAIL')
 for s in ['DERIVED_SEMANTIC_LINEAGE_EDGE_BINDING = ESTABLISHED_IN_TESTED_SCOPE','DERIVED_SEMANTIC_AUTHORITY = BLOCKED','SOLVER_INVOCATION_COUNT = 0','AUTHORITY_CLOSED_FINITE_INDUCTION = NOT_YET_ESTABLISHED','IMPLEMENTATION_A_PASS = NOT_ESTABLISHED','AIFC_V1_FROZEN = FALSE','PLATFORM_TRUST_PROVEN = FALSE','SAL_GLOBAL_NOVELTY = NOT_ESTABLISHED','SCIENTIFIC_ASSURANCE_LINEAGE_V1_11H_DERIVED_SEMANTIC_LINEAGE_EDGE_BINDING = PASS']:print(s)
if __name__=='__main__':main()
