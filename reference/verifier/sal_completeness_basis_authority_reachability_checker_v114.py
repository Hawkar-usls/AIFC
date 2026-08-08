#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any, Mapping
from jsonschema import Draft202012Validator

from canonical import domain_hash
import completeness_basis_authority_reachability_v1 as sal
from scientific_assurance_lineage_v13 import git_blob_sha1_bytes

ROOT=Path(__file__).resolve().parents[2]
REGISTRY_PATH="conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v16.json"
PREDECESSOR_REGISTRY_PATH="conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v15.json"
PREDECESSOR_REGISTRY_BLOB="d8e2b0ec45e6d34336d0fc5484bb5c507ef2ffd9"
AUDIT_PATH="conformance/AIFC-COMPLETENESS-BASIS-AUTHORITY-REACHABILITY-AUDIT-v1.json"
AUDIT_HASH="c3c3833abeacc00de92065a22235cbed6f77e4012da69463780517136b20c287"
BINDING_PATH="conformance/AIFC-COMPLETENESS-BASIS-AUTHORITY-REACHABILITY-IMPLEMENTATION-BINDING-v1.json"
BINDING_ID="AIFC-SAL-V1.14-COMPLETENESS-BASIS-AUTHORITY-REACHABILITY-IMPLEMENTATION-BINDING-V1"
BINDING_HASH="1bb092c2c32a4de182e85c9a40f317ef3c05d59273c75d784c61a5ab9fc97780"
BINDING_DOMAIN="AIFC:COMPLETENESS-BASIS-AUTHORITY-REACHABILITY-IMPLEMENTATION-BINDING:v1"
IMPLEMENTATION_PATH="reference/verifier/completeness_basis_authority_reachability_v1.py"
IMPLEMENTATION_BLOB="cd4ac5014fa97925733084095e8e8d8391a0e0e8"
IMPLEMENTATION_RAW="0a7d0ba0c568b66ca69954e957512001bd816ee047b658145eae07b282c28a8e"

SCHEMAS=(
("AIFC/completeness-basis-authority-reachability-profile/v1","schemas/completeness-basis-authority-reachability-profile-v1.schema.json","579d135b533e8420d281e944bfe4e4f72f0cdbd5","7450ffa2322cd963d9ee91b79aba83455b1c393e082e6e20a2ac897a76083e86"),
("AIFC/completeness-basis-authority-reachability-audit/v1","schemas/completeness-basis-authority-reachability-audit-v1.schema.json","4a2d78638cc93520c11ab5b4249cf6b581acf628","5929a0f8223fdcf9a1a4d03c1f80c5e6a630a5d6a2ef5a66790fbda77f3c97b5"),
("AIFC/completeness-basis-authority-reachability-implementation-binding/v1","schemas/completeness-basis-authority-reachability-implementation-binding-v1.schema.json","c39c1cdca57332b9dac6d3b5d3e9d2ec7d1b428e","73a15351d1910ea5a52829a3cfd005de92ea05967ace43f2f5742ad9cf5e1535"),
("AIFC/schema-identity-registry/v16","schemas/schema-identity-registry-v16.schema.json","604f9198cabcef80e66a444a0466ee2e7b5f9344","550937372f8a21dc6c916a831db6f1a57b290e589c01a283e2d3869e31892d73"),
)

def load(path:str)->Mapping[str,Any]:
    x=json.loads((ROOT/path).read_text(encoding="utf-8"))
    if not isinstance(x,Mapping): raise SystemExit("V114_NOT_MAPPING:"+path)
    return x

def raw256(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def binding_hash(x:Mapping[str,Any])->str:
    m=dict(x); m.pop("binding_content_hash",None)
    return domain_hash(BINDING_DOMAIN,m)

def verify_schemas()->None:
    prev=(ROOT/PREDECESSOR_REGISTRY_PATH).read_bytes()
    if git_blob_sha1_bytes(prev)!=PREDECESSOR_REGISTRY_BLOB:
        raise SystemExit("V114_PREDECESSOR_REGISTRY_REBINDING")
    reg=load(REGISTRY_PATH)
    if reg.get("schema")!="AIFC/schema-identity-registry/v16" or reg.get("registry_version")!=16:
        raise SystemExit("V114_REGISTRY_HEADER_REBINDING")
    if reg.get("predecessor_registry_path")!=PREDECESSOR_REGISTRY_PATH or reg.get("predecessor_registry_git_blob_sha1")!=PREDECESSOR_REGISTRY_BLOB:
        raise SystemExit("V114_REGISTRY_PREDECESSOR_REBINDING")
    if reg.get("source_observed_at_commit")!=sal.SOURCE_MAIN_COMMIT:
        raise SystemExit("V114_REGISTRY_SOURCE_COMMIT_REBINDING")
    rows=reg.get("records")
    if not isinstance(rows,list) or len(rows)!=4: raise SystemExit("V114_REGISTRY_COUNT")
    by={r.get("schema_id"):r for r in rows if isinstance(r,Mapping)}
    if set(by)!={x[0] for x in SCHEMAS}: raise SystemExit("V114_REGISTRY_ID_SET")
    for sid,path,blob,rawhash in SCHEMAS:
        raw=(ROOT/path).read_bytes()
        if git_blob_sha1_bytes(raw)!=blob: raise SystemExit("V114_SCHEMA_BLOB:"+sid)
        if raw256(raw)!=rawhash: raise SystemExit("V114_SCHEMA_RAW:"+sid)
        schema=json.loads(raw.decode("utf-8")); Draft202012Validator.check_schema(schema)
        row=by[sid]
        if row.get("source_path")!=path or row.get("git_blob_sha1")!=blob or row.get("raw_schema_sha256")!=rawhash:
            raise SystemExit("V114_REGISTRY_RECORD:"+sid)
        if row.get("first_registered_by_registry_version")!=16 or row.get("status")!="REGISTERED_IMMUTABLE_SUCCESSOR_CANDIDATE":
            raise SystemExit("V114_REGISTRY_STATUS:"+sid)
    Draft202012Validator(json.loads((ROOT/SCHEMAS[0][1]).read_text())).validate(load(sal.REACHABILITY_PROFILE_PATH))
    Draft202012Validator(json.loads((ROOT/SCHEMAS[1][1]).read_text())).validate(load(AUDIT_PATH))
    Draft202012Validator(json.loads((ROOT/SCHEMAS[2][1]).read_text())).validate(load(BINDING_PATH))
    Draft202012Validator(json.loads((ROOT/SCHEMAS[3][1]).read_text())).validate(reg)

def verify_binding(x:Mapping[str,Any])->None:
    expected={
      "schema":"AIFC/completeness-basis-authority-reachability-implementation-binding/v1","binding_id":BINDING_ID,
      "reachability_profile_id":sal.REACHABILITY_PROFILE_ID,
      "reachability_profile_content_hash":sal.REACHABILITY_PROFILE_HASH,
      "implementation_path":IMPLEMENTATION_PATH,
      "implementation_git_blob_sha1":IMPLEMENTATION_BLOB,
      "implementation_raw_sha256":IMPLEMENTATION_RAW,
      "binding_status":"CONFIRMED_DUAL_BOUND_CANDIDATE_EXECUTION_IDENTITY",
      "authority_status":"NOT_ESTABLISHED","binding_content_hash":BINDING_HASH}
    for k,v in expected.items():
        if x.get(k)!=v: raise SystemExit("V114_BINDING_REBINDING:"+k)
    if binding_hash(x)!=BINDING_HASH: raise SystemExit("V114_BINDING_CONTENT_REBINDING")
    raw=(ROOT/IMPLEMENTATION_PATH).read_bytes()
    if git_blob_sha1_bytes(raw)!=IMPLEMENTATION_BLOB: raise SystemExit("V114_IMPL_BLOB_REBINDING")
    if raw256(raw)!=IMPLEMENTATION_RAW: raise SystemExit("V114_IMPL_RAW_REBINDING")

def main()->None:
    verify_schemas()
    verify_binding(load(BINDING_PATH))
    audit=load(AUDIT_PATH)
    if audit.get("audit_content_hash")!=AUDIT_HASH: raise SystemExit("V114_AUDIT_HASH_REBINDING")
    r=sal.verify_declared_audit(audit)
    print("SAL_V114_SCHEMA_HEADERS = PASS (4/4)")
    print("SAL_SCHEMA_IDENTITY_REGISTRATION_V16 = PASS (4/4 dual-bound candidate identities)")
    print("COMPLETENESS_AUTHORITY_REACHABILITY_IMPLEMENTATION_IDENTITY = CONFIRMED_DUAL_BOUND")
    print("COMPLETENESS_AUTHORITY_REACHABILITY_IMPLEMENTATION_REBINDING = REJECTED_IN_TESTED_PATH")
    print("COMPLETENESS_AUTHORITY_REACHABILITY_IMPLEMENTATION_AUTHORITY = NOT_ESTABLISHED")
    for k,v in r.__dict__.items(): print(k.upper(),"=",v)
    print("SAL_RELEASE_GATE_122_TO_143 = INHERITED_UNCHANGED")
    print("SAL_V114_RELEASE_GATE_INTEGRATION = HARDENING_LAYER_NO_GATE_RENUMBER")
    print("AUTHORITY_CLOSED_FINITE_INDUCTION = NOT_YET_ESTABLISHED")
    print("IMPLEMENTATION_A_PASS = NOT_ESTABLISHED")
    print("AIFC_V1_FROZEN = FALSE")
    print("PLATFORM_TRUST_PROVEN = FALSE")
    print("SAL_GLOBAL_NOVELTY = NOT_ESTABLISHED")
    print("SCIENTIFIC_ASSURANCE_LINEAGE_V1_14_COMPLETENESS_BASIS_AUTHORITY_REACHABILITY = PASS")

if __name__=="__main__": main()
