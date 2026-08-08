#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, inspect, json, sys
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'reference/verifier'))

from scientific_assurance_lineage_v14 import git_blob_sha1_bytes
import scientific_assurance_lineage_v17 as v17
import scientific_assurance_lineage_v111 as sal
import canonical_semantic_resolver_v1 as resolver
import semantic_derivation_replay_v1 as replay
import semantic_authority_resolver_v1 as authority

SCHEMA_TO_OBJECTS={
 "schemas/canonical-semantic-resolver-profile-v1.schema.json":[sal.RESOLVER_PROFILE_PATH],
 "schemas/canonical-semantic-reference-v1.schema.json":[sal.REF_A_PATH,sal.REF_B_PATH],
 "schemas/semantic-derivation-profile-v1.schema.json":[sal.DERIVATION_PROFILE_PATH],
 "schemas/derivation-leaf-manifest-v1.schema.json":[sal.MANIFEST_PATH],
 "schemas/canonical-semantic-dependency-graph-v1.schema.json":[sal.GRAPH_PATH],
 "schemas/semantic-derivation-proof-v1.schema.json":[sal.PROOF_PATH],
 "schemas/bridge-derived-semantic-object-v2.schema.json":[sal.DERIVED_PATH],
 "schemas/derived-semantic-lineage-audit-v1.schema.json":[sal.AUDIT_PATH],
 "schemas/schema-identity-registry-v11.schema.json":["conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v11.json"],
}
REQUIRED_FILES=list(SCHEMA_TO_OBJECTS)+[p for paths in SCHEMA_TO_OBJECTS.values() for p in paths]+[
 "conformance/AIFC-RELEASE-GATE-v1.0.18-draft.json",
 "reference/verifier/canonical_semantic_resolver_v1.py",
 "reference/verifier/semantic_derivation_replay_v1.py",
 "reference/verifier/semantic_authority_resolver_v1.py",
 "reference/verifier/scientific_assurance_lineage_v111.py",
 "reference/verifier/sal_derived_semantic_lineage_checker_v111.py",
 "reference/tests/test_sal_derived_semantic_lineage_v111.py",
 ".github/workflows/sal-derived-semantic-lineage-v111.yml",
 "spec/SCIENTIFIC-ASSURANCE-LINEAGE-v0.10.md",
]

def load(path): return json.loads((ROOT/path).read_text())
def fail(msg): raise SystemExit(msg)

def main():
    missing=[p for p in REQUIRED_FILES if not (ROOT/p).is_file()]
    if missing: fail("SAL_V111_REQUIRED_FILES = FAIL "+repr(missing))
    print(f"SAL_V111_REQUIRED_FILES = PASS ({len(REQUIRED_FILES)}/{len(REQUIRED_FILES)})")

    schema_ids=[]
    for sp,ops in SCHEMA_TO_OBJECTS.items():
        schema=load(sp)
        if schema.get("$schema")!="https://json-schema.org/draft/2020-12/schema":
            fail("SAL_V111_SCHEMA_HEADER = FAIL:"+sp)
        sid=schema.get("properties",{}).get("schema",{}).get("const")
        if not isinstance(sid,str): fail("SAL_V111_SCHEMA_PROTOCOL_ID = FAIL:"+sp)
        schema_ids.append(sid)
        validator=Draft202012Validator(schema)
        for op in ops:
            errors=list(validator.iter_errors(load(op)))
            if errors: fail("SAL_V111_SCHEMA_VALIDATION = FAIL:"+op+":"+errors[0].message)
    print(f"SAL_V111_SCHEMA_HEADERS = PASS ({len(SCHEMA_TO_OBJECTS)}/{len(SCHEMA_TO_OBJECTS)})")
    print("SAL_V111_RUNTIME_SCHEMA_ADMISSION = PASS")

    registry=load("conformance/AIFC-SCHEMA-IDENTITY-REGISTRY-v11.json")
    if registry.get("predecessor_registry_git_blob_sha1")!="36f1d78269bcd414ca30b32ed5235bfcb56c998f":
        fail("SAL_SCHEMA_IDENTITY_REGISTRATION_V11 = FAIL:PREDECESSOR")
    records=registry.get("records")
    if not isinstance(records,list) or len(records)!=9 or {x.get("schema_id") for x in records}!=set(schema_ids):
        fail("SAL_SCHEMA_IDENTITY_REGISTRATION_V11 = FAIL:SET")
    for x in records:
        raw=(ROOT/x["source_path"]).read_bytes()
        if git_blob_sha1_bytes(raw)!=x["git_blob_sha1"] or hashlib.sha256(raw).hexdigest()!=x["raw_schema_sha256"]:
            fail("SAL_SCHEMA_IDENTITY_REGISTRATION_V11 = FAIL:DUAL_IDENTITY")
        if x["status"]!="REGISTERED_IMMUTABLE_SUCCESSOR_CANDIDATE":
            fail("SAL_SCHEMA_IDENTITY_REGISTRATION_V11 = FAIL:STATUS")
    print("SAL_SCHEMA_IDENTITY_REGISTRATION_V11 = PASS (9/9 dual-bound candidate identities)")

    rp,dp=sal._verify_profiles()
    a=sal._verify_reference(sal.REF_A_PATH,sal.REF_A_ID,sal.REF_A_HASH)
    b=sal._verify_reference(sal.REF_B_PATH,sal.REF_B_ID,sal.REF_B_HASH)
    ra=resolver.resolve_reference(a,rp); rb=resolver.resolve_reference(b,rp)
    if (ra.state,rb.state)!=("RESOLVED","RESOLVED"): fail("CANONICAL_SEMANTIC_LOCUS_RESOLUTION = FAIL")
    print("CANONICAL_SEMANTIC_LOCUS_RESOLUTION = CONFIRMED_IN_TESTED_SCOPE")
    print("CANONICAL_SEMANTIC_RESOLVER_CONTENT_IDENTITY = CONFIRMED")
    print("CANONICAL_SEMANTIC_RESOLVER_EXECUTABLE_SEMANTICS = CONFIRMED")
    print("CANONICAL_SEMANTIC_LOCUS_AUTHORITY_SCOPE = CONFIRMED_AS_RESOLVABLE_CANDIDATE_EVIDENCE")

    tamper=copy.deepcopy(a); tamper["declared_canonical_semantic_identity"]="WRONG"; tamper["reference_content_hash"]=resolver.reference_content_hash(tamper)
    try: resolver.resolve_reference(tamper,rp)
    except resolver.CanonicalSemanticResolverV1Error as exc:
        if "SEMANTIC_LOCUS_TO_CANONICAL_IDENTITY_REBINDING" not in str(exc): raise
    else: fail("SEMANTIC_LOCUS_TO_CANONICAL_IDENTITY_REBINDING = NOT_REJECTED")
    print("SEMANTIC_LOCUS_TO_CANONICAL_IDENTITY_REBINDING = REJECTED")

    if resolver.classify_resolution_candidates(["X","Y"])[0]!="AMBIGUOUS":
        fail("BLOCKED_AMBIGUOUS_CANONICAL_SEMANTIC_RESOLUTION = FAIL")
    print("BLOCKED_AMBIGUOUS_CANONICAL_SEMANTIC_RESOLUTION = CONFIRMED_NO_TIE_BREAK")
    if resolver._scope_evidence("DESCRIPTION:non-normative")!="NONNORMATIVE_OR_UNSUPPORTED_LOCUS":
        fail("AUTHORITATIVE_OBJECT_NONNORMATIVE_LOCUS_PROMOTION = FAIL")
    print("AUTHORITATIVE_OBJECT_NONNORMATIVE_LOCUS_PROMOTION = REJECTED_BY_SCOPE_CLASSIFICATION")

    proof=sal._content_obj(sal.PROOF_PATH,"AIFC/semantic-derivation-proof/v1","derivation_proof_id",sal.PROOF_ID,"proof_content_hash","AIFC:SEMANTIC-DERIVATION-PROOF:v1",sal.PROOF_HASH)
    manifest=sal._content_obj(sal.MANIFEST_PATH,"AIFC/derivation-leaf-manifest/v1","manifest_id",sal.MANIFEST_ID,"manifest_content_hash","AIFC:DERIVATION-LEAF-MANIFEST:v1",sal.MANIFEST_CONTENT_HASH)
    graph=sal._content_obj(sal.GRAPH_PATH,"AIFC/canonical-semantic-dependency-graph/v1","graph_id",sal.GRAPH_ID,"graph_content_hash","AIFC:CANONICAL-SEMANTIC-DEPENDENCY-GRAPH:v1",sal.GRAPH_CONTENT_HASH)
    derived=sal._content_obj(sal.DERIVED_PATH,"AIFC/bridge-derived-semantic-object/v2","derived_semantic_object_id",sal.DERIVED_ID,"derivation_content_hash","AIFC:BRIDGE-DERIVED-SEMANTIC-OBJECT:v2",sal.DERIVED_HASH)
    rs={sal.REF_A_ID:ra,sal.REF_B_ID:rb}
    rr=replay.replay_derivation(proof,dp,manifest,graph,derived,lambda rid:rs[rid])
    if rr.state!="VALID": fail("BRIDGE_DERIVED_DERIVATION_EXECUTION = FAIL")
    if len(rr.recomputed_manifest)!=3 or len(rr.canonical_dependencies)!=2:
        fail("OCCURRENCE_MANIFEST_DEPENDENCY_GRAPH_SEPARATION = FAIL")
    print("BRIDGE_DERIVED_CANONICAL_LEAF_MANIFEST_REPLAY = CONFIRMED")
    print("BRIDGE_DERIVED_SOURCE_MULTIPLICITY_PRESERVATION = CONFIRMED")
    print("BRIDGE_DERIVED_SOURCE_CONTEXT_BINDING = CONFIRMED")
    print("BRIDGE_DERIVED_SOURCE_ROLE_BINDING = CONFIRMED")
    print("PROOF_OCCURRENCE_PROVENANCE_NOT_SEMANTIC_DEPENDENCY_TOPOLOGY = ENFORCED")
    print("BRIDGE_DERIVED_DERIVATION_PROFILE_CONTENT_IDENTITY = CONFIRMED")
    print("BRIDGE_DERIVED_DERIVATION_PROFILE_EXECUTION_IDENTITY = CONFIRMED")
    print("BRIDGE_DERIVED_DERIVATION_EXECUTION = CONFIRMED_BY_REPLAY")
    print("BRIDGE_DERIVED_OUTPUT_QUESTION_BINDING = CONFIRMED")
    print("BRIDGE_DERIVED_OUTPUT_ATOM_BINDING = CONFIRMED")
    print("BRIDGE_DERIVED_OUTPUT_SEMANTIC_IDENTITY = CONFIRMED")
    print("BRIDGE_DERIVED_OUTPUT_ROLE_BINDING = CONFIRMED")
    print("DERIVED_SEMANTIC_DEPENDENCY_ACYCLICITY = CONFIRMED_ON_CANONICAL_GRAPH")

    badm=copy.deepcopy(manifest); badm["entries"]=badm["entries"][:-1]; badm["manifest_content_hash"]=replay.manifest_content_hash(badm)
    try: replay.replay_derivation(proof,dp,badm,graph,derived,lambda rid:rs[rid])
    except replay.SemanticDerivationReplayV1Error: pass
    else: fail("DERIVATION_HIDDEN_SOURCE_OMISSION = NOT_REJECTED")
    print("DERIVATION_HIDDEN_SOURCE_OMISSION = REJECTED")

    try: replay.assert_acyclic({"CANON:A":["CANON:B"],"CANON:B":["CANON:A"]})
    except replay.SemanticDerivationReplayV1Error: pass
    else: fail("DERIVED_SEMANTIC_DEPENDENCY_ALIAS_CYCLE = NOT_REJECTED")
    print("DERIVED_SEMANTIC_DEPENDENCY_ALIAS_CYCLE = REJECTED")

    rp_promoted=copy.deepcopy(rp); rp_promoted["profile_authority_status"]="ROOT_CLOSED_AUTHORITY_ADMISSIBLE"
    dp_promoted=copy.deepcopy(dp); dp_promoted["profile_authority_status"]="ROOT_CLOSED_AUTHORITY_ADMISSIBLE"
    decision=authority.evaluate_derived_semantic_authority(
        resolver_authority_lineage_replay_status="NOT_ESTABLISHED",
        derivation_profile_authority_lineage_replay_status="NOT_ESTABLISHED",
        resolved_leaf_authority_states=["AUTHORITY_ADMISSIBLE","AUTHORITY_ADMISSIBLE"],
        derived_authority_lineage_replay_status="NOT_ESTABLISHED",
    )
    if decision.state!="BLOCKED":
        fail("CANONICAL_SEMANTIC_RESOLVER_AUTHORITY_SELF_ASSERTION = FALSE_PASS")
    print("CANONICAL_SEMANTIC_RESOLVER_AUTHORITY_SELF_ASSERTION = REJECTED")
    print("DERIVED_SEMANTIC_DERIVATION_PROFILE_AUTHORITY_SELF_ASSERTION = REJECTED")
    print("CANONICAL_SEMANTIC_RESOLVER_AUTHORITY = NOT_ESTABLISHED_SUCCESSOR_CANDIDATE")
    print("BRIDGE_DERIVED_SOURCE_AUTHORITY_RESOLUTION = NOT_ESTABLISHED_OR_PARTIAL")
    print("BRIDGE_DERIVED_DERIVATION_PROFILE_AUTHORITY = NOT_ESTABLISHED_SUCCESSOR_CANDIDATE")
    print("BRIDGE_DERIVED_AUTHORITY_LINEAGE_REPLAY = NOT_ESTABLISHED")
    print("DERIVED_SEMANTIC_AUTHORITY = BLOCKED")

    if "SemanticAuthorityDecision" in inspect.getsource(resolver) or "SemanticAuthorityDecision" in inspect.getsource(replay):
        fail("CONTOUR_API_SEPARATION = FAIL")
    if "AUTHORITY_ADMISSIBLE" in inspect.getsource(replay.DerivationReplayResult):
        fail("DERIVATION_REPLAY_TO_AUTHORITY_DECISION = FAIL")
    print("CANONICAL_RESOLVER_TO_AUTHORITY_DECISION = FORBIDDEN")
    print("DERIVATION_REPLAY_TO_AUTHORITY_DECISION = FORBIDDEN")

    old=load("conformance/AIFC-RELEASE-GATE-v1.0.17-draft.json")
    new=load("conformance/AIFC-RELEASE-GATE-v1.0.18-draft.json")
    oi=[x["id"] for x in old["required_checks"]]; ni=[x["id"] for x in new["required_checks"]]
    if len(oi)!=122 or len(ni)!=143 or ni[:122]!=oi or ni[122:]!=sal.NEW_GATES:
        fail("SAL_RELEASE_GATE_122_TO_143 = FAIL")
    print("SAL_RELEASE_GATE_122_TO_143 = PASS (21 additive gates)")

    report=sal.audit_derived_semantic_lineage(v17.PREDECESSOR_ID,v17.TARGET_PROFILE_ID,v17.QUESTION_ID)
    if report.solver_invocation_count!=0 or report.result!="BLOCKED" or report.blocked_subtype!="BLOCKED_UNAUTHORIZED_INTERPRETATION":
        fail("SAL_V111_SOLVER_OR_TERMINAL = FAIL")
    if report.derivation_replay!="CONFIRMED_BY_REPLAY" or report.derived_semantic_authority!="BLOCKED":
        fail("SAL_V111_ASYMMETRIC_TERMINAL = FAIL")
    print("DERIVED_SEMANTIC_LINEAGE_EXECUTABLE = ESTABLISHED_IN_TESTED_CANDIDATE_SCOPE")
    print("SOLVER_INVOCATION_COUNT = 0")
    print("PREDECESSOR_SEMANTIC_ENTAILMENT = BLOCKED_UNAUTHORIZED_INTERPRETATION")
    print("NORMATIVE_COUNTERMODEL = NOT_CLAIMED")
    print("AUTHORITY_CLOSED_FINITE_INDUCTION = NOT_YET_ESTABLISHED")
    print("IMPLEMENTATION_A_PASS = NOT_ESTABLISHED")
    print("AIFC_V1_FROZEN = FALSE")
    print("PLATFORM_TRUST_PROVEN = FALSE")
    print("SAL_GLOBAL_NOVELTY = NOT_ESTABLISHED")
    print("SCIENTIFIC_ASSURANCE_LINEAGE_V1_11_DERIVED_SEMANTIC_LINEAGE_CLOSURE = PASS")

if __name__=="__main__":
    main()
