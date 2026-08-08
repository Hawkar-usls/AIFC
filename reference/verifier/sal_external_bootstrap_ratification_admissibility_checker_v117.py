#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any, Mapping
from jsonschema import Draft202012Validator
from canonical import domain_hash
from scientific_assurance_lineage_v13 import git_blob_sha1_bytes
import external_bootstrap_ratification_admissibility_v1 as sal
ROOT=Path(__file__).resolve().parents[2]
REGISTRY_PATH="conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v19.json"
PREV_PATH="conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v18.json"; PREV_BLOB="0dab11f12005342e61745ed629456a27c9668f87"
AUDIT_PATH="conformance/AIFC-EXTERNAL-BOOTSTRAP-RATIFICATION-ADMISSIBILITY-AUDIT-v1.json"; AUDIT_HASH="f115c673b4dc8e5cf6c4a5501b89278bf9f0094bded8e9bc5b3c0bfd88214661"
BINDING_PATH="conformance/AIFC-EXTERNAL-BOOTSTRAP-RATIFICATION-ADMISSIBILITY-IMPLEMENTATION-BINDING-v1.json"; BINDING_HASH="9de80cb2788c2c33ad36976d5bb89ad5f1c8c022f05ae1154b40e78c477dda4d"
BIND_DOMAIN="AIFC:EXTERNAL-BOOTSTRAP-RATIFICATION-ADMISSIBILITY-IMPLEMENTATION-BINDING:v1"
IMPL="reference/verifier/external_bootstrap_ratification_admissibility_v1.py"; IMPL_BLOB="bf5953ffe1c969b9509b298ce26694c84e5abfc6"; IMPL_RAW="863d01797ec07e1a050649912808e8e351e9a29aadcbf3043284999c820638da"
SCHEMAS=(
("AIFC/external-bootstrap-ratification-candidate/v1","schemas/external-bootstrap-ratification-candidate-v1.schema.json","34d9b56feb0b86cd25d86994470b06f3864cb989","d4036f4aee734fe44249e182416f2456064707c9de98256711b8dda3fb56ce53"),
("AIFC/external-bootstrap-ratification-admissibility-profile/v1","schemas/external-bootstrap-ratification-admissibility-profile-v1.schema.json","aa7317a8c94fbc31f548a8adf62c889f9bf2c321","cd682c027b60e2323626a4b808eba42c9552c8fcd5ac64a97a24dea4b1420f5f"),
("AIFC/external-bootstrap-ratification-admissibility-audit/v1","schemas/external-bootstrap-ratification-admissibility-audit-v1.schema.json","74780b6be64776e414c82b8ab94ae0539c8b3b4f","144bf33ca59c9fb5fb490949edf14baea7b20701a6b56a9d50c9d6a7c7ba6c5b"),
("AIFC/external-bootstrap-ratification-admissibility-implementation-binding/v1","schemas/external-bootstrap-ratification-admissibility-implementation-binding-v1.schema.json","844e1ba28673d06f3f4a0480a5e8e6fc08601e4d","4e41a8e92823b7938a26fefab37bfdad242d27a41bc74a8b14cd440fe35af45c"),
("AIFC/schema-identity-registry/v19","schemas/schema-identity-registry-v19.schema.json","f715ebcf59529221387c32548b95cc660c6db1c9","32d45fdd31cccfba974113f77ee8ad0f6b1a6ffe191b3669d28deb40280d1562"))
def load(p:str)->Mapping[str,Any]:
 x=json.loads((ROOT/p).read_text());
 if not isinstance(x,Mapping): raise SystemExit("V117_NOT_MAPPING:"+p)
 return x
def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()
def bh(x:Mapping[str,Any])->str:
 y=dict(x);y.pop("binding_content_hash",None);return domain_hash(BIND_DOMAIN,y)
def verify_schemas()->None:
 if git_blob_sha1_bytes((ROOT/PREV_PATH).read_bytes())!=PREV_BLOB: raise SystemExit("V117_PREDECESSOR_REGISTRY_REBINDING")
 r=load(REGISTRY_PATH)
 if (r.get("schema"),r.get("registry_version"),r.get("predecessor_registry_path"),r.get("predecessor_registry_git_blob_sha1"),r.get("source_observed_at_commit"))!=("AIFC/schema-identity-registry/v19",19,PREV_PATH,PREV_BLOB,sal.SOURCE_MAIN_COMMIT): raise SystemExit("V117_REGISTRY_HEADER_REBINDING")
 rows=r.get("records"); by={x.get("schema_id"):x for x in rows or [] if isinstance(x,Mapping)}
 if len(rows or [])!=5 or set(by)!={x[0] for x in SCHEMAS}: raise SystemExit("V117_REGISTRY_ID_SET")
 for sid,p,b,h in SCHEMAS:
  raw=(ROOT/p).read_bytes()
  if git_blob_sha1_bytes(raw)!=b or sha(raw)!=h: raise SystemExit("V117_SCHEMA_IDENTITY:"+sid)
  Draft202012Validator.check_schema(json.loads(raw)); row=by[sid]
  if (row.get("source_path"),row.get("git_blob_sha1"),row.get("raw_schema_sha256"),row.get("first_registered_by_registry_version"),row.get("status"))!=(p,b,h,19,"REGISTERED_IMMUTABLE_SUCCESSOR_CANDIDATE"): raise SystemExit("V117_REGISTRY_ROW:"+sid)
 cs=json.loads((ROOT/SCHEMAS[0][1]).read_text())
 if cs.get("additionalProperties") is not False or set(cs.get("properties",{}))&set(sal.FORBIDDEN): raise SystemExit("V117_CANDIDATE_SCHEMA_SELF_AUTHORIZING")
 for sp,obj in ((SCHEMAS[1][1],load(sal.PROFILE_PATH)),(SCHEMAS[2][1],load(AUDIT_PATH)),(SCHEMAS[3][1],load(BINDING_PATH)),(SCHEMAS[4][1],r)): Draft202012Validator(json.loads((ROOT/sp).read_text())).validate(obj)
def verify_binding(x:Mapping[str,Any])->None:
 fixed={"schema":"AIFC/external-bootstrap-ratification-admissibility-implementation-binding/v1","binding_id":"AIFC-SAL-V1.17-EXTERNAL-BOOTSTRAP-RATIFICATION-ADMISSIBILITY-IMPLEMENTATION-BINDING-V1","profile_id":sal.PROFILE_ID,"profile_content_hash":sal.PROFILE_HASH,"implementation_path":IMPL,"implementation_git_blob_sha1":IMPL_BLOB,"implementation_raw_sha256":IMPL_RAW,"binding_status":"CONFIRMED_DUAL_BOUND_CANDIDATE_EXECUTION_IDENTITY","authority_status":"NOT_ESTABLISHED","binding_content_hash":BINDING_HASH}
 for k,v in fixed.items():
  if x.get(k)!=v: raise SystemExit("V117_BINDING_REBINDING:"+k)
 if bh(x)!=BINDING_HASH: raise SystemExit("V117_BINDING_CONTENT_REBINDING")
 raw=(ROOT/IMPL).read_bytes()
 if git_blob_sha1_bytes(raw)!=IMPL_BLOB or sha(raw)!=IMPL_RAW: raise SystemExit("V117_IMPL_IDENTITY_REBINDING")
def main()->None:
 verify_schemas();verify_binding(load(BINDING_PATH));a=load(AUDIT_PATH)
 if a.get("audit_content_hash")!=AUDIT_HASH: raise SystemExit("V117_AUDIT_HASH_REBINDING")
 r=sal.verify_declared_audit(a)
 print("SAL_V117_SCHEMA_HEADERS = PASS (5/5)");print("SAL_SCHEMA_IDENTITY_REGISTRATION_V19 = PASS (5/5 dual-bound candidate identities)");print("EXTERNAL_BOOTSTRAP_RATIFICATION_ADMISSIBILITY_IMPLEMENTATION_IDENTITY = CONFIRMED_DUAL_BOUND");print("EXTERNAL_BOOTSTRAP_RATIFICATION_ADMISSIBILITY_IMPLEMENTATION_AUTHORITY = NOT_ESTABLISHED")
 for k,v in r.items(): print(k.upper(),"=",v)
 for line in ("SAL_RELEASE_GATE_122_TO_143 = INHERITED_UNCHANGED","SAL_V117_RELEASE_GATE_INTEGRATION = HARDENING_LAYER_NO_GATE_RENUMBER","AUTHORITY_CLOSED_FINITE_INDUCTION = NOT_YET_ESTABLISHED","IMPLEMENTATION_A_PASS = NOT_ESTABLISHED","AIFC_V1_FROZEN = FALSE","PLATFORM_TRUST_PROVEN = FALSE","SAL_GLOBAL_NOVELTY = NOT_ESTABLISHED","SCIENTIFIC_ASSURANCE_LINEAGE_V1_17_EXTERNAL_BOOTSTRAP_RATIFICATION_ADMISSIBILITY_BOUNDARY = PASS"): print(line)
if __name__=="__main__":main()
