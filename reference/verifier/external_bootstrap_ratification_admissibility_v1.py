#!/usr/bin/env python3
"""SAL v1.17 external bootstrap-ratification admissibility boundary.

Structural independence and authentication are necessary evidence channels,
not normative authority. This module creates no external ratifier or authority.
"""
from __future__ import annotations
import hashlib, inspect, json, re
from pathlib import Path
from typing import Any, Mapping
from canonical import domain_hash
from scientific_assurance_lineage_v13 import git_blob_sha1_bytes
import bootstrap_non_self_ratification_boundary_v1 as v116

ROOT = Path(__file__).resolve().parents[2]
SOURCE_MAIN_COMMIT="b8a1f3acf9d8444affccdb6b0b754f19e6a08949"
SOURCE_TREE_SHA="9534c147ba29cc53f7f321b4101907a04818c3bc"
BOOTSTRAP_COMMIT="908de7afddcf9f72c98c2b3fb696a41be1e438e0"
V116_AUDIT_ID="AIFC-SAL-V1.16-BOOTSTRAP-NON-SELF-RATIFICATION-AUDIT-V1"
V116_AUDIT_PATH="conformance/AIFC-BOOTSTRAP-NON-SELF-RATIFICATION-AUDIT-v1.json"
V116_AUDIT_BLOB="a2d3fe6bd7b80c778da05740df5cc7c4953acf5e"
V116_AUDIT_HASH="991f234732540aa0e21f11c2e64fe8ca1864ba4be52c5a2c81781ea0257cd5fc"
V116_IMPLEMENTATION_PATH="reference/verifier/bootstrap_non_self_ratification_boundary_v1.py"
V116_IMPLEMENTATION_BLOB="9d4aeca0e68cdf7c48a446d51ec5a49253bde4c7"
V116_IMPLEMENTATION_RAW="2b4d91863f25677ab2b312228e380386b2ebaafba79f72281ae9b9c65ed5dac9"
CANDIDATE_SCHEMA_ID="AIFC/external-bootstrap-ratification-candidate/v1"
CANDIDATE_SCHEMA_PATH="schemas/external-bootstrap-ratification-candidate-v1.schema.json"
CANDIDATE_SCHEMA_BLOB="34d9b56feb0b86cd25d86994470b06f3864cb989"
CANDIDATE_SCHEMA_RAW="d4036f4aee734fe44249e182416f2456064707c9de98256711b8dda3fb56ce53"
DESIGNATED_INTAKE_PATH="conformance/AIFC-EXTERNAL-BOOTSTRAP-RATIFICATION-CANDIDATE-v1.json"
PROFILE_PATH="conformance/AIFC-EXTERNAL-BOOTSTRAP-RATIFICATION-ADMISSIBILITY-PROFILE-v1.json"
PROFILE_ID="AIFC-SAL-V1.17-EXTERNAL-BOOTSTRAP-RATIFICATION-ADMISSIBILITY-PROFILE-V1"
PROFILE_HASH="b6752ab5f930d0e96dc1a7388bf3ca7a62ffdd4d8085c78a247cc64633f7b119"
PROFILE_BLOB="4e8b204f47d51d1e5aa8d234a9a969d5390f2d8b"
PROFILE_DOMAIN="AIFC:EXTERNAL-BOOTSTRAP-RATIFICATION-ADMISSIBILITY-PROFILE:v1"
AUDIT_DOMAIN="AIFC:EXTERNAL-BOOTSTRAP-RATIFICATION-ADMISSIBILITY-AUDIT:v1"
BLOCKED="BLOCKED_UNAUTHORIZED_COMPLETENESS_BASIS"
CANDIDATE_ONLY="EVIDENCE_ENVELOPE_ONLY_NOT_AUTHORITY"
WELL_FORMED="STRUCTURALLY_WELL_FORMED_RATIFICATION_CANDIDATE_AUTHORITY_UNRESOLVED"
BOTH_ONLY="NECESSARY_EVIDENCE_CHANNELS_PRESENT_AUTHORITY_UNRESOLVED"
INCOMPLETE="EVIDENCE_CHANNELS_INCOMPLETE_AUTHORITY_UNRESOLVED"
HEX64=re.compile(r"^[0-9a-f]{64}$")
REQUIRED=frozenset(("schema","candidate_id","bootstrap_root_commit","ratifier_identity","ratification_scope","ratification_statement_hash","ratifier_provenance_ref","ratifier_provenance_hash","non_descendant_provenance_ref","non_descendant_provenance_hash","authority_basis_ref","authority_basis_hash","authentication_evidence_ref","authentication_evidence_hash","candidate_semantics"))
FORBIDDEN=frozenset(("authority_status","authority_admissible","bootstrap_authority_legitimacy","external_bootstrap_ratification","normative_authority","self_authorized","external"))

class V117Error(ValueError): pass

def _raw(path:str)->bytes: return (ROOT/path).read_bytes()
def _sha(raw:bytes)->str: return hashlib.sha256(raw).hexdigest()
def _exact(path:str, blob:str, label:str)->Mapping[str,Any]:
    raw=_raw(path); actual=git_blob_sha1_bytes(raw)
    if actual!=blob: raise V117Error(f"V117_EXACT_SOURCE_REBINDING:{label}:{actual}")
    obj=json.loads(raw.decode());
    if not isinstance(obj,Mapping): raise V117Error("V117_SOURCE_NOT_MAPPING:"+label)
    return obj
def _dual(path:str,blob:str,raw256:str,label:str)->None:
    raw=_raw(path)
    if git_blob_sha1_bytes(raw)!=blob: raise V117Error("V117_EXACT_BLOB_REBINDING:"+label)
    if _sha(raw)!=raw256: raise V117Error("V117_EXACT_RAW_REBINDING:"+label)
def profile_content_hash(x:Mapping[str,Any])->str:
    y=dict(x); y.pop("profile_content_hash",None); return domain_hash(PROFILE_DOMAIN,y)
def audit_content_hash(x:Mapping[str,Any])->str:
    y=dict(x); y.pop("audit_content_hash",None); return domain_hash(AUDIT_DOMAIN,y)

def verify_profile(p:Mapping[str,Any])->None:
    fixed={"schema":"AIFC/external-bootstrap-ratification-admissibility-profile/v1","profile_id":PROFILE_ID,"source_main_commit":SOURCE_MAIN_COMMIT,"source_tree_sha":SOURCE_TREE_SHA,"source_v116_audit_id":V116_AUDIT_ID,"source_v116_audit_path":V116_AUDIT_PATH,"source_v116_audit_git_blob_sha1":V116_AUDIT_BLOB,"source_v116_audit_content_hash":V116_AUDIT_HASH,"source_v116_implementation_path":V116_IMPLEMENTATION_PATH,"source_v116_implementation_git_blob_sha1":V116_IMPLEMENTATION_BLOB,"source_v116_implementation_raw_sha256":V116_IMPLEMENTATION_RAW,"bootstrap_root_commit":BOOTSTRAP_COMMIT,"candidate_schema_id":CANDIDATE_SCHEMA_ID,"candidate_schema_path":CANDIDATE_SCHEMA_PATH,"candidate_schema_git_blob_sha1":CANDIDATE_SCHEMA_BLOB,"candidate_schema_raw_sha256":CANDIDATE_SCHEMA_RAW,"designated_intake_path":DESIGNATED_INTAKE_PATH,"candidate_discovery_scope":"DESIGNATED_INTAKE_PATH_ONLY_NOT_GLOBAL_DISCOVERY","current_candidate_status":"ABSENT_AT_DESIGNATED_INTAKE_PATH","candidate_semantics":CANDIDATE_ONLY,"non_descendant_provenance_requirement":"REQUIRED_SEPARATE_EVIDENCE_CHANNEL","authentication_evidence_requirement":"REQUIRED_SEPARATE_EVIDENCE_CHANNEL","authentication_evidence_semantics":"ORIGIN_INTEGRITY_EVIDENCE_ONLY_NOT_AUTHORITY","authority_basis_requirement":"REQUIRED_SEPARATE_EXTERNALLY_ANCHORED_BASIS","authority_basis_self_reference":"FORBIDDEN","known_internal_authority_basis_for_bootstrap_ratification":"FORBIDDEN_IN_CURRENT_ROOT_SCOPE","externality_label_without_provenance":"FORBIDDEN","structural_independence_to_authority_promotion":"FORBIDDEN","authentication_to_authority_promotion":"FORBIDDEN","candidate_to_bootstrap_legitimacy_promotion":"FORBIDDEN","caller_candidate_input_surface":"FORBIDDEN","external_ratifier_authority_admissibility":"NOT_ESTABLISHED","external_bootstrap_ratification":"NOT_PERFORMED","bootstrap_authority_legitimacy":"NOT_ESTABLISHED","global_external_ratifier_discovery_completeness":"NOT_ESTABLISHED","global_authority_admissibility_semantics":"NOT_ESTABLISHED","normative_lineage_completeness":BLOCKED,"profile_authority_status":"SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE"}
    for k,v in fixed.items():
        if p.get(k)!=v: raise V117Error("V117_PROFILE_REBINDING:"+k)
    if p.get("profile_content_hash")!=profile_content_hash(p) or p.get("profile_content_hash")!=PROFILE_HASH: raise V117Error("V117_PROFILE_CONTENT_REBINDING")
    if set(p)&{"external_ratifier","external_ratification_object","external_authority","bootstrap_legitimacy_proof","authority_status","authority_admissible"}: raise V117Error("V117_AUTHORITY_OR_CANDIDATE_INPUT_SURFACE")

def _internal()->frozenset[str]:
    return frozenset((v116.BOOTSTRAP_COMMIT,v116.ROOT_V1_ID,v116.ROOT_V2_ID,v116.ROOT_V1_PATH,v116.ROOT_V2_PATH,v116.PROFILE_ID,V116_AUDIT_ID))
def validate_candidate_shape(c:Mapping[str,Any])->str:
    bad=set(c)&FORBIDDEN
    if bad: raise V117Error("V117_CANDIDATE_SELF_AUTHORIZATION_FIELD:"+sorted(bad)[0])
    if set(c)!=REQUIRED: raise V117Error("V117_CANDIDATE_FIELD_SET_REBINDING")
    if c.get("schema")!=CANDIDATE_SCHEMA_ID: raise V117Error("V117_CANDIDATE_SCHEMA_REBINDING")
    if c.get("bootstrap_root_commit")!=BOOTSTRAP_COMMIT: raise V117Error("V117_CANDIDATE_BOOTSTRAP_ROOT_REBINDING")
    if c.get("ratification_scope")!="BOOTSTRAP_ROOT_LEGITIMACY_ONLY" or c.get("candidate_semantics")!=CANDIDATE_ONLY: raise V117Error("V117_CANDIDATE_SEMANTICS_REBINDING")
    for k in ("candidate_id","ratifier_identity","ratifier_provenance_ref","non_descendant_provenance_ref","authority_basis_ref","authentication_evidence_ref"):
        if not isinstance(c.get(k),str) or not c[k]: raise V117Error("V117_CANDIDATE_MISSING_OR_INVALID:"+k)
    for k in ("ratification_statement_hash","ratifier_provenance_hash","non_descendant_provenance_hash","authority_basis_hash","authentication_evidence_hash"):
        if not isinstance(c.get(k),str) or not HEX64.fullmatch(c[k]): raise V117Error("V117_CANDIDATE_HASH_ENCODING:"+k)
    if c["authority_basis_ref"]==c["candidate_id"]: raise V117Error("V117_CANDIDATE_AUTHORITY_BASIS_SELF_REFERENCE")
    if c["ratifier_identity"] in _internal(): raise V117Error("V117_KNOWN_INTERNAL_RATIFIER_REJECTED")
    if c["authority_basis_ref"] in _internal(): raise V117Error("V117_KNOWN_INTERNAL_AUTHORITY_BASIS_REJECTED")
    return WELL_FORMED

def combine_non_authorizing_evidence(structural_independence:bool,authentication_integrity:bool)->str:
    if type(structural_independence) is not bool or type(authentication_integrity) is not bool: raise V117Error("V117_EVIDENCE_CHANNEL_TYPE")
    return BOTH_ONLY if structural_independence and authentication_integrity else INCOMPLETE

def audit_current_external_ratification_admissibility()->dict[str,Any]:
    verify_profile(_exact(PROFILE_PATH,PROFILE_BLOB,PROFILE_ID))
    _dual(CANDIDATE_SCHEMA_PATH,CANDIDATE_SCHEMA_BLOB,CANDIDATE_SCHEMA_RAW,CANDIDATE_SCHEMA_ID)
    _dual(V116_IMPLEMENTATION_PATH,V116_IMPLEMENTATION_BLOB,V116_IMPLEMENTATION_RAW,"V116_IMPLEMENTATION")
    prior_obj=_exact(V116_AUDIT_PATH,V116_AUDIT_BLOB,V116_AUDIT_ID); prior=v116.verify_declared_audit(prior_obj)
    if prior_obj.get("audit_content_hash")!=V116_AUDIT_HASH: raise V117Error("V117_V116_AUDIT_HASH_REBINDING")
    if prior.non_self_ratification_theorem!="ESTABLISHED_FOR_ROOT_RELATIVE_DESCENDANT_CLOSURE": raise V117Error("V117_V116_THEOREM_REBINDING")
    if (prior.external_ratifier_authority_admissibility,prior.external_bootstrap_ratification,prior.bootstrap_authority_legitimacy)!=("NOT_ESTABLISHED","NOT_PERFORMED","NOT_ESTABLISHED"): raise V117Error("V117_V116_AUTHORITY_PROMOTION")
    if (ROOT/DESIGNATED_INTAKE_PATH).exists(): raise V117Error("V117_CURRENT_CANDIDATE_PRESENT_REQUIRES_SUCCESSOR_ASSESSMENT")
    if inspect.signature(audit_current_external_ratification_admissibility).parameters: raise V117Error("V117_PRODUCTION_CALLER_CANDIDATE_SURFACE")
    if combine_non_authorizing_evidence(True,True)!=BOTH_ONLY: raise V117Error("V117_ADMISSIBILITY_SEPARATION_REPLAY_FAILURE")
    return {"source_v116_boundary_identity":"CONFIRMED_PINNED_GIT_BLOB_AND_CONTENT_HASH","source_v116_implementation_identity":"CONFIRMED_DUAL_BOUND","v116_non_self_ratification_theorem":"PRESERVED_EXACT_ROOT_RELATIVE_BOUNDARY","candidate_schema_identity":"CONFIRMED_PINNED_GIT_BLOB_AND_RAW_SHA256","candidate_schema_authority":"NOT_ESTABLISHED_TECHNICAL_SHAPE_ONLY","candidate_discovery_scope":"DESIGNATED_INTAKE_PATH_ONLY_NOT_GLOBAL_DISCOVERY","designated_intake_path_status":"ABSENT","external_ratification_candidate":"NOT_PRESENT_AT_DESIGNATED_INTAKE_PATH","candidate_shape_semantics":"DEFINED_NOT_INSTANTIATED","non_descendant_provenance_requirement":"REQUIRED_SEPARATE_EVIDENCE_CHANNEL","authentication_evidence_requirement":"REQUIRED_SEPARATE_EVIDENCE_CHANNEL","authentication_evidence_semantics":"ORIGIN_INTEGRITY_EVIDENCE_ONLY_NOT_AUTHORITY","authority_basis_requirement":"REQUIRED_SEPARATE_EXTERNALLY_ANCHORED_BASIS","admissibility_separation_invariant":"STRUCTURAL_INDEPENDENCE_AND_AUTHENTICATION_DO_NOT_IMPLY_AUTHORITY_ADMISSIBILITY","candidate_self_authorization":"REJECTED_BY_SCHEMA_AND_VALIDATOR","known_internal_authority_basis_laundering":"REJECTED_IN_CURRENT_ROOT_SCOPE","caller_candidate_input_surface":"FORBIDDEN_NO_CALLER_INPUT_SURFACE","external_ratifier_structural_independence":"NOT_ESTABLISHED_NO_CANDIDATE","external_ratification_authentication":"NOT_ESTABLISHED_NO_CANDIDATE","external_ratifier_authority_admissibility":"NOT_ESTABLISHED","external_bootstrap_ratification":"NOT_PERFORMED","bootstrap_authority_legitimacy":"NOT_ESTABLISHED","global_external_ratifier_discovery_completeness":"NOT_ESTABLISHED","global_authority_admissibility_semantics":"NOT_ESTABLISHED","normative_lineage_completeness":BLOCKED,"derived_semantic_authority":"BLOCKED","solver_invocation_count":0,"next_required_basis":"REAL_EXTERNAL_RATIFICATION_OBJECT_WITH_NON_DESCENDANT_PROVENANCE_AND_SEPARATELY_ADMISSIBLE_AUTHORITY_BASIS","status":"EXTERNAL_BOOTSTRAP_RATIFICATION_ADMISSIBILITY_BOUNDARY_CONFIRMED_NO_CURRENT_CANDIDATE"}

def verify_declared_audit(a:Mapping[str,Any])->dict[str,Any]:
    fixed={"schema":"AIFC/external-bootstrap-ratification-admissibility-audit/v1","audit_id":"AIFC-SAL-V1.17-EXTERNAL-BOOTSTRAP-RATIFICATION-ADMISSIBILITY-AUDIT-V1","source_main_commit":SOURCE_MAIN_COMMIT,"source_tree_sha":SOURCE_TREE_SHA,"profile_id":PROFILE_ID,"profile_content_hash":PROFILE_HASH,"source_v116_audit_id":V116_AUDIT_ID,"source_v116_audit_git_blob_sha1":V116_AUDIT_BLOB,"source_v116_audit_content_hash":V116_AUDIT_HASH}
    for k,v in fixed.items():
        if a.get(k)!=v: raise V117Error("V117_AUDIT_REBINDING:"+k)
    if a.get("audit_content_hash")!=audit_content_hash(a): raise V117Error("V117_AUDIT_CONTENT_REBINDING")
    r=audit_current_external_ratification_admissibility()
    for k,v in r.items():
        if a.get(k)!=v: raise V117Error("V117_AUDIT_REPORT_REBINDING:"+k)
    return r
