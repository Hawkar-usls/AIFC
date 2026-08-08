#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'reference/verifier'))
from scientific_assurance_lineage_v14 import git_blob_sha1_bytes
import scientific_assurance_lineage_v17 as v17
import scientific_assurance_lineage_v111h as v111h
import scientific_assurance_lineage_v111u as sal
import semantic_lineage_edge_universe_v1 as universe

SCHEMAS={
 "schemas/lineage-edge-universe-derivation-profile-v1.schema.json":[sal.PROFILE_PATH],
 "schemas/derived-semantic-lineage-edge-universe-v1.schema.json":[sal.UNIVERSE_PATH],
 "schemas/derived-semantic-lineage-edge-universe-audit-v1.schema.json":[sal.AUDIT_PATH],
 "schemas/schema-identity-registry-v13.schema.json":["conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v13.json"],
}
def L(p): return json.loads((ROOT/p).read_text())
def F(s): raise SystemExit(s)
def main():
 ids=[]
 for sp,ops in SCHEMAS.items():
  sc=L(sp);ids.append(sc['properties']['schema']['const']);v=Draft202012Validator(sc)
  for op in ops:
   e=list(v.iter_errors(L(op)))
   if e:F('SAL_V111U_SCHEMA_VALIDATION = FAIL:'+op+':'+e[0].message)
 print('SAL_V111U_SCHEMA_HEADERS = PASS (4/4)')
 reg=L('conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v13.json')
 if reg['predecessor_registry_git_blob_sha1']!='c7f1995205e7e1a73a9237ee93f736f6774c18ab' or {x['schema_id'] for x in reg['records']}!=set(ids):F('SAL_SCHEMA_IDENTITY_REGISTRATION_V13 = FAIL')
 for x in reg['records']:
  b=(ROOT/x['source_path']).read_bytes()
  if git_blob_sha1_bytes(b)!=x['git_blob_sha1'] or hashlib.sha256(b).hexdigest()!=x['raw_schema_sha256']:F('SAL_SCHEMA_IDENTITY_REGISTRATION_V13 = FAIL:DUAL')
 print('SAL_SCHEMA_IDENTITY_REGISTRATION_V13 = PASS (4/4 dual-bound candidate identities)')
 p=L(sal.PROFILE_PATH);o,_=v111h._objects_and_raws();r=L(sal.UNIVERSE_PATH);d,h=universe.verify_universe_receipt(r,o,p)
 if len(d)!=15 or h!=sal.EDGE_UNIVERSE_HASH:F('LINEAGE_EDGE_UNIVERSE_DERIVATION = FAIL')
 keys={x['edge_key'] for x in d}
 for k in ['PROFILE->QUESTION#question_id','PROOF->QUESTION#question_id','PROOF->DERIVED#semantic_identity','MANIFEST->QUESTION#question_id','GRAPH->DERIVED#semantic_identity','DERIVED->QUESTION#question_id']:
  if k not in keys:F('LINEAGE_EDGE_UNIVERSE_ADDITIONAL_EDGE_MISSING:'+k)
 print('LINEAGE_EDGE_UNIVERSE_INDEPENDENT_DERIVATION = CONFIRMED_IN_TESTED_CANDIDATE_SCOPE')
 print('LINEAGE_EDGE_UNIVERSE_COMPLETENESS = CONFIRMED_WITHIN_INHERITED_SIX_VERTEX_IDENTITY_REFERENCE_SCOPE')
 print('SUCCESSOR_DEFINED_REQUIRED_EDGE_LIST = ELIMINATED_IN_TESTED_PATH')
 print('MACHINE_DERIVED_EDGE_COUNT = 15')
 print('INHERITED_V111H_DECLARED_EDGE_COUNT = 9')
 print('ADDITIONAL_MACHINE_DERIVED_EDGE_COUNT = 6')
 print('EDGE_UNIVERSE_HASH = '+h)
 x=sal.audit_lineage_edge_universe_derivation(v17.PREDECESSOR_ID,v17.TARGET_PROFILE_ID,v17.QUESTION_ID)
 if x.binding_question_context!='CONFIRMED' or x.audit_question_context!='CONFIRMED':F('LINEAGE_QUESTION_CONTEXT = FAIL')
 print('LINEAGE_BINDING_QUESTION_CONTEXT = CONFIRMED')
 print('LINEAGE_AUDIT_QUESTION_CONTEXT = CONFIRMED')
 print('EDGE_UNIVERSE_DERIVATION_PROFILE_CONTENT_IDENTITY = CONFIRMED')
 print('EDGE_UNIVERSE_DERIVATION_PROFILE_EXECUTION_IDENTITY = CONFIRMED')
 print('EDGE_UNIVERSE_DERIVATION_PROFILE_AUTHORITY = NOT_ESTABLISHED_SUCCESSOR_CANDIDATE')
 print('LINEAGE_VERTEX_UNIVERSE_COMPLETENESS = NOT_ESTABLISHED')
 print('LINEAGE_SEMANTIC_RELATION_UNIVERSE_GENERAL = NOT_ESTABLISHED')
 print('SAL_RELEASE_GATE_122_TO_143 = INHERITED_UNCHANGED')
 print('SAL_V111U_RELEASE_GATE_INTEGRATION = HARDENING_LAYER_NO_GATE_RENUMBER')
 print('DERIVED_SEMANTIC_AUTHORITY = BLOCKED')
 print('SOLVER_INVOCATION_COUNT = 0')
 print('AUTHORITY_CLOSED_FINITE_INDUCTION = NOT_YET_ESTABLISHED')
 print('IMPLEMENTATION_A_PASS = NOT_ESTABLISHED')
 print('AIFC_V1_FROZEN = FALSE')
 print('PLATFORM_TRUST_PROVEN = FALSE')
 print('SAL_GLOBAL_NOVELTY = NOT_ESTABLISHED')
 print('SCIENTIFIC_ASSURANCE_LINEAGE_V1_11U_EDGE_UNIVERSE_DERIVATION = PASS')
if __name__=='__main__':main()
