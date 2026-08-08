#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any, Mapping
from jsonschema import Draft202012Validator

from canonical import domain_hash
import bootstrap_authority_origin_boundary_v1 as sal
from scientific_assurance_lineage_v13 import git_blob_sha1_bytes

ROOT=Path(__file__).resolve().parents[2]
REGISTRY_PATH="conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v17.json"
PREDECESSOR_REGISTRY_PATH="conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v16.json"
PREDECESSOR_REGISTRY_BLOB="1f02920c10531d184c80eaab3b9207233e4e7ffa"
AUDIT_PATH="conformance/AIFC-BOOTSTRAP-AUTHORITY-ORIGIN-AUDIT-v1.json"
AUDIT_HASH="51f8b083c146c9076520fe2880167e6a105fcbc037de5a49813e944c1d93e2d6"
BINDING_PATH="conformance/AIFC-BOOTSTRAP-AUTHORITY-ORIGIN-IMPLEMENTATION-BINDING-v1.json"
BINDING_ID="AIFC-SAL-V1.15-BOOTSTRAP-AUTHORITY-ORIGIN-IMPLEMENTATION-BINDING-V1"
BINDING_HASH="0ecc685a99253778f25fcc10151ec21e2a8bdeff7f4b21840a56e5b4d37b9611"
BINDING_DOMAIN="AIFC:BOOTSTRAP-AUTHORITY-ORIGIN-IMPLEMENTATION-BINDING:v1"
IMPLEMENTATION_PATH="reference/verifier/bootstrap_authority_origin_boundary_v1.py"
IMPLEMENTATION_BLOB="7dad1b773058c2f51e2ef8ea7ba2b85d4c340cab"
IMPLEMENTATION_RAW="b90b17a795b89ad73a41d66d1003b7a4a5be1d01ce18ad12bcce677ca2fcb8fe"

SCHEMAS=(
("AIFC/bootstrap-authority-origin-profile/v1","schemas/bootstrap-authority-origin-profile-v1.schema.json","d59bfee4a46f0b1fb70b6ff71ba7d22427a0ef67","2f83e206cae2c9511e8b7dd9b3c186e4050d5cf192b4adced68dd85494490e98"),
("AIFC/bootstrap-authority-origin-audit/v1","schemas/bootstrap-authority-origin-audit-v1.schema.json","b1152b43789f675dfe8d34d8d73e3aac2a802bf9","9c9123622b0085d4f9e11f8296639135b46384455a4734058684acc6065f2c09"),
("AIFC/bootstrap-authority-origin-implementation-binding/v1","schemas/bootstrap-authority-origin-implementation-binding-v1.schema.json","bc8ea864eee4fb380dc323036213d38a9abf6195","811b0dab2149065d524ce447152872aa0c723b5ae5347f0a1f1aee53d6dc7d2a"),
("AIFC/schema-identity-registry/v17","schemas/schema-identity-registry-v17.schema.json","6f5eaf012bff44a89119de044a3cefd1331e64ae","61d78163791bc47480d923e2167500decc02f82eaf3fac2358b3d9169497170d"),
)

def load(path:str)->Mapping[str,Any]:
    x=json.loads((ROOT/path).read_text(encoding="utf-8"))
    if not isinstance(x,Mapping): raise SystemExit("V115_NOT_MAPPING:"+path)
    return x

def raw256(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def binding_hash(x:Mapping[str,Any])->str:
    m=dict(x); m.pop("binding_content_hash",None)
    return domain_hash(BINDING_DOMAIN,m)

def verify_schemas()->None:
    prev=(ROOT/PREDECESSOR_REGISTRY_PATH).read_bytes()
    if git_blob_sha1_bytes(prev)!=PREDECESSOR_REGISTRY_BLOB:
        raise SystemExit("V115_PREDECESSOR_REGISTRY_REBINDING")
    reg=load(REGISTRY_PATH)
    if reg.get("schema")!="AIFC/schema-identity-registry/v17" or reg.get("registry_version")!=17:
        raise SystemExit("V115_REGISTRY_HEADER_REBINDING")
    if reg.get("predecessor_registry_path")!=PREDECESSOR_REGISTRY_PATH or reg.get("predecessor_registry_git_blob_sha1")!=PREDECESSOR_REGISTRY_BLOB:
        raise SystemExit("V115_REGISTRY_PREDECESSOR_REBINDING")
    if reg.get("source_observed_at_commit")!=sal.SOURCE_MAIN_COMMIT:
        raise SystemExit("V115_REGISTRY_SOURCE_COMMIT_REBINDING")
    rows=reg.get("records")
    if not isinstance(rows,list) or len(rows)!=4: raise SystemExit("V115_REGISTRY_COUNT")
    by={r.get("schema_id"):r for r in rows if isinstance(r,Mapping)}
    if set(by)!={x[0] for x in SCHEMAS}: raise SystemExit("V115_REGISTRY_ID_SET")
    for sid,path,blob,rawhash in SCHEMAS:
        raw=(ROOT/path).read_bytes()
        if git_blob_sha1_bytes(raw)!=blob: raise SystemExit("V115_SCHEMA_BLOB:"+sid)
        if raw256(raw)!=rawhash: raise SystemExit("V115_SCHEMA_RAW:"+sid)
        schema=json.loads(raw.decode("utf-8")); Draft202012Validator.check_schema(schema)
        row=by[sid]
        if row.get("source_path")!=path or row.get("git_blob_sha1")!=blob or row.get("raw_schema_sha256")!=rawhash:
            raise SystemExit("V115_REGISTRY_RECORD:"+sid)
        if row.get("first_registered_by_registry_version")!=17 or row.get("status")!="REGISTERED_IMMUTABLE_SUCCESSOR_CANDIDATE":
            raise SystemExit("V115_REGISTRY_STATUS:"+sid)
    Draft202012Validator(json.loads((ROOT/SCHEMAS[0][1]).read_text())).validate(load(sal.PROFILE_PATH))
    Draft202012Validator(json.loads((ROOT/SCHEMAS[1][1]).read_text())).validate(load(AUDIT_PATH))
    Draft202012Validator(json.loads((ROOT/SCHEMAS[2][1]).read_text())).validate(load(BINDING_PATH))
    Draft202012Validator(json.loads((ROOT/SCHEMAS[3][1]).read_text())).validate(reg)

def verify_binding(x:Mapping[str,Any])->None:
    expected={
      "schema":"AIFC/bootstrap-authority-origin-implementation-binding/v1","binding_id":BINDING_ID,
      "origin_profile_id":sal.PROFILE_ID,
      "origin_profile_content_hash":sal.PROFILE_HASH,
      "implementation_path":IMPLEMENTATION_PATH,
      "implementation_git_blob_sha1":IMPLEMENTATION_BLOB,
      "implementation_raw_sha256":IMPLEMENTATION_RAW,
      "binding_status":"CONFIRMED_DUAL_BOUND_CANDIDATE_EXECUTION_IDENTITY",
      "authority_status":"NOT_ESTABLISHED","binding_content_hash":BINDING_HASH}
    for k,v in expected.items():
        if x.get(k)!=v: raise SystemExit("V115_BINDING_REBINDING:"+k)
    if binding_hash(x)!=BINDING_HASH: raise SystemExit("V115_BINDING_CONTENT_REBINDING")
    raw=(ROOT/IMPLEMENTATION_PATH).read_bytes()
    if git_blob_sha1_bytes(raw)!=IMPLEMENTATION_BLOB: raise SystemExit("V115_IMPL_BLOB_REBINDING")
    if raw256(raw)!=IMPLEMENTATION_RAW: raise SystemExit("V115_IMPL_RAW_REBINDING")

def main()->None:
    verify_schemas()
    verify_binding(load(BINDING_PATH))
    audit=load(AUDIT_PATH)
    if audit.get("audit_content_hash")!=AUDIT_HASH: raise SystemExit("V115_AUDIT_HASH_REBINDING")
    r=sal.verify_declared_audit(audit)
    print("SAL_V115_SCHEMA_HEADERS = PASS (4/4)")
    print("SAL_SCHEMA_IDENTITY_REGISTRATION_V17 = PASS (4/4 dual-bound candidate identities)")
    print("BOOTSTRAP_AUTHORITY_ORIGIN_IMPLEMENTATION_IDENTITY = CONFIRMED_DUAL_BOUND")
    print("BOOTSTRAP_AUTHORITY_ORIGIN_IMPLEMENTATION_REBINDING = REJECTED_IN_TESTED_PATH")
    print("BOOTSTRAP_AUTHORITY_ORIGIN_IMPLEMENTATION_AUTHORITY = NOT_ESTABLISHED")
    for k,v in r.__dict__.items(): print(k.upper(),"=",v)
    print("SAL_RELEASE_GATE_122_TO_143 = INHERITED_UNCHANGED")
    print("SAL_V115_RELEASE_GATE_INTEGRATION = HARDENING_LAYER_NO_GATE_RENUMBER")
    print("AUTHORITY_CLOSED_FINITE_INDUCTION = NOT_YET_ESTABLISHED")
    print("IMPLEMENTATION_A_PASS = NOT_ESTABLISHED")
    print("AIFC_V1_FROZEN = FALSE")
    print("PLATFORM_TRUST_PROVEN = FALSE")
    print("SAL_GLOBAL_NOVELTY = NOT_ESTABLISHED")
    print("SCIENTIFIC_ASSURANCE_LINEAGE_V1_15_BOOTSTRAP_AUTHORITY_ORIGIN_BOUNDARY = PASS")

if __name__=="__main__": main()
