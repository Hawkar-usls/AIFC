#!/usr/bin/env python3
"""SAL v1.11 Derived Semantic Lineage Closure.

Execution lineage is separated from semantic authority. This layer resolves
exact semantic loci, normalizes a derivation proof, recomputes occurrence
provenance and dependency topology, replays the candidate derivation, binds the
output, and proves canonical-graph acyclicity. It does not authorize the
resolver, sources, or derivation rule, and it does not invoke the entailment
solver.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any, Mapping

from canonical import domain_hash, loads_strict
from scientific_assurance_lineage_v14 import git_blob_sha1_bytes
import scientific_assurance_lineage_v17 as v17
import scientific_assurance_lineage_v110 as v110
import canonical_semantic_resolver_v1 as resolver
import semantic_derivation_replay_v1 as replay
import semantic_authority_resolver_v1 as authority

ROOT = Path(__file__).resolve().parents[2]

RESOLVER_PROFILE_PATH = "conformance/AIFC-CANONICAL-SEMANTIC-RESOLVER-PROFILE-v1.json"
RESOLVER_PROFILE_ID = "AIFC-SAL-V1.11-CANONICAL-SEMANTIC-RESOLVER-PROFILE-V1"
RESOLVER_PROFILE_HASH = "68bba1204a6e49aeaf363152214915e7998d9f84d826c81a188f4a68bd9eab6f"
REF_A_PATH = "conformance/AIFC-CANONICAL-SEMANTIC-REFERENCE-A-v1.json"
REF_A_ID = "AIFC-SAL-V1.11-SEMANTIC-REF-A"
REF_A_HASH = "c93658f9eb68f47e9c86fa9efbe31805f5164467afb79bdb99c66306d9568996"
REF_B_PATH = "conformance/AIFC-CANONICAL-SEMANTIC-REFERENCE-B-v1.json"
REF_B_ID = "AIFC-SAL-V1.11-SEMANTIC-REF-B"
REF_B_HASH = "39d272f8fbf4467a3a011d1852cadc8084d0dd4c187768996b57f0822f251152"
DERIVATION_PROFILE_PATH = "conformance/AIFC-SEMANTIC-DERIVATION-PROFILE-v1.json"
DERIVATION_PROFILE_ID = "AIFC-SAL-V1.11-SEMANTIC-DERIVATION-PROFILE-V1"
DERIVATION_PROFILE_HASH = "d16c01f080ceeb4d0888c70c3644448572dda0bbe752d1aec2b7780366dae399"
MANIFEST_PATH = "conformance/AIFC-DERIVATION-LEAF-MANIFEST-v1.json"
MANIFEST_ID = "AIFC-SAL-V1.11-DERIVATION-LEAF-MANIFEST-V1"
MANIFEST_CONTENT_HASH = "c91ed79e6fee8c725ee509ff23f767f97e6c9a780cdce47155cb61d21b54d2c8"
PROOF_PATH = "conformance/AIFC-SEMANTIC-DERIVATION-PROOF-v1.json"
PROOF_ID = "AIFC-SAL-V1.11-SEMANTIC-DERIVATION-PROOF-V1"
PROOF_HASH = "cc8d54a3dd8d08c406fa91830152fe13561dfef28289daa92dec36cadea263a0"
GRAPH_PATH = "conformance/AIFC-CANONICAL-SEMANTIC-DEPENDENCY-GRAPH-v1.json"
GRAPH_ID = "AIFC-SAL-V1.11-CANONICAL-SEMANTIC-DEPENDENCY-GRAPH-V1"
GRAPH_CONTENT_HASH = "c2c0ad44496aa20b4e0e41d8d7e8eb2a2381a62074a7d4b57b4ba900dc481c31"
DERIVED_PATH = "conformance/AIFC-BRIDGE-DERIVED-SEMANTIC-OBJECT-v2.json"
DERIVED_ID = "AIFC-SAL-V1.11-BRIDGE-DERIVED-SEMANTIC-OBJECT-V2"
DERIVED_HASH = "8073b6acd0d5da9363155bd3a3f2ad18554f5620d489cce6a104c2d1a36e588b"
DERIVED_SEMANTIC_IDENTITY = "DERIVED_SEMANTIC:f78c6dd6d5a77aec20f1964e2d363c8d3b6edeb47f455c88fb4680d00f4cde5f"
AUDIT_PATH = "conformance/AIFC-DERIVED-SEMANTIC-LINEAGE-AUDIT-v1.json"
AUDIT_ID = "AIFC-SAL-V1.11-DERIVED-SEMANTIC-LINEAGE-AUDIT-V1"

RESOLVER_IMPL_PATH = "reference/verifier/canonical_semantic_resolver_v1.py"
RESOLVER_IMPL_BLOB = "66c566bbb46d2af3b7844547706275282cefbaa7"
RESOLVER_IMPL_RAW_SHA256 = "f05130fbf4fa0f0ac8e4682ac1a3f3b0436cec4aba411e953ac2b403cc7cc5fb"
REPLAY_IMPL_PATH = "reference/verifier/semantic_derivation_replay_v1.py"
REPLAY_IMPL_BLOB = "5f93500a95cc494b74e8fc9b96ea310a94aab9d5"
REPLAY_IMPL_RAW_SHA256 = "1a885c9408f4181e389e5ba417565b5a782bbecadb5b61063395b6153aa296c9"
AUTHORITY_IMPL_PATH = "reference/verifier/semantic_authority_resolver_v1.py"
AUTHORITY_IMPL_BLOB = "dfc596570123a7251e450606d981556a46a4f044"
AUTHORITY_IMPL_RAW_SHA256 = "ecafdec490f03d67accd8fa814e2d05eeaa903b958576bc8fadeac0b2bb38294"

NEW_GATES = ['CANONICAL_SEMANTIC_LOCUS_RESOLUTION', 'CANONICAL_SEMANTIC_RESOLVER_CONTENT_IDENTITY', 'CANONICAL_SEMANTIC_RESOLVER_EXECUTABLE_SEMANTICS', 'CANONICAL_SEMANTIC_LOCUS_AUTHORITY_SCOPE', 'CANONICAL_SEMANTIC_RESOLVER_AUTHORITY', 'BRIDGE_DERIVED_CANONICAL_LEAF_MANIFEST_REPLAY', 'BRIDGE_DERIVED_SOURCE_MULTIPLICITY_PRESERVATION', 'BRIDGE_DERIVED_SOURCE_CONTEXT_BINDING', 'BRIDGE_DERIVED_SOURCE_ROLE_BINDING', 'BRIDGE_DERIVED_DERIVATION_PROFILE_CONTENT_IDENTITY', 'BRIDGE_DERIVED_DERIVATION_PROFILE_EXECUTION_IDENTITY', 'BRIDGE_DERIVED_DERIVATION_REPLAY', 'BRIDGE_DERIVED_OUTPUT_QUESTION_BINDING', 'BRIDGE_DERIVED_OUTPUT_ATOM_BINDING', 'BRIDGE_DERIVED_OUTPUT_SEMANTIC_IDENTITY', 'BRIDGE_DERIVED_OUTPUT_ROLE_BINDING', 'DERIVED_SEMANTIC_DEPENDENCY_ACYCLICITY', 'BRIDGE_DERIVED_SOURCE_AUTHORITY_RESOLUTION', 'BRIDGE_DERIVED_DERIVATION_PROFILE_AUTHORITY', 'BRIDGE_DERIVED_AUTHORITY_LINEAGE_REPLAY', 'DERIVED_SEMANTIC_AUTHORITY']

class ScientificAssuranceLineageV111Error(ValueError):
    pass

@dataclass(frozen=True)
class DerivedSemanticLineageReport:
    question_id: str
    canonical_semantic_locus_resolution: str
    canonical_semantic_resolver_content_identity: str
    canonical_semantic_resolver_executable_semantics: str
    canonical_semantic_locus_authority_scope: str
    canonical_semantic_resolver_authority: str
    canonical_leaf_manifest_replay: str
    source_multiplicity_preservation: str
    source_context_binding: str
    source_role_binding: str
    derivation_profile_content_identity: str
    derivation_profile_execution_identity: str
    derivation_replay: str
    output_question_binding: str
    output_atom_binding: str
    output_semantic_identity: str
    output_role_binding: str
    dependency_acyclicity: str
    source_authority_resolution: str
    derivation_profile_authority: str
    authority_lineage_replay: str
    derived_semantic_authority: str
    solver_invocation_count: int
    result: str
    blocked_subtype: str | None

def _load(path: str) -> Mapping[str, Any]:
    obj = loads_strict((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(obj, Mapping):
        raise ScientificAssuranceLineageV111Error(f"SAL_V111_OBJECT_NOT_MAPPING:{path}")
    return obj

def _verify_bytes(path: str, blob: str, raw_sha256: str) -> None:
    raw = (ROOT / path).read_bytes()
    if git_blob_sha1_bytes(raw) != blob:
        raise ScientificAssuranceLineageV111Error(f"SAL_V111_IMPLEMENTATION_GIT_REBINDING:{path}")
    if hashlib.sha256(raw).hexdigest() != raw_sha256:
        raise ScientificAssuranceLineageV111Error(f"SAL_V111_IMPLEMENTATION_RAW_REBINDING:{path}")

def _content_obj(path: str, schema: str, id_field: str, expected_id: str,
                 hash_field: str, domain: str, expected_hash: str) -> Mapping[str, Any]:
    obj = _load(path)
    if obj.get("schema") != schema or obj.get(id_field) != expected_id:
        raise ScientificAssuranceLineageV111Error(f"SAL_V111_OBJECT_ID_REBINDING:{path}")
    material = dict(obj); claimed = material.pop(hash_field, None)
    actual = domain_hash(domain, material)
    if claimed != expected_hash or actual != expected_hash:
        raise ScientificAssuranceLineageV111Error(f"SAL_V111_CONTENT_IDENTITY_REBINDING:{path}")
    return obj

def _verify_profiles() -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    rp = _content_obj(
        RESOLVER_PROFILE_PATH, "AIFC/canonical-semantic-resolver-profile/v1",
        "resolver_profile_id", RESOLVER_PROFILE_ID, "profile_content_hash",
        "AIFC:CANONICAL-SEMANTIC-RESOLVER-PROFILE:v1", RESOLVER_PROFILE_HASH,
    )
    dp = _content_obj(
        DERIVATION_PROFILE_PATH, "AIFC/semantic-derivation-profile/v1",
        "derivation_profile_id", DERIVATION_PROFILE_ID, "profile_content_hash",
        "AIFC:SEMANTIC-DERIVATION-PROFILE:v1", DERIVATION_PROFILE_HASH,
    )
    _verify_bytes(RESOLVER_IMPL_PATH, RESOLVER_IMPL_BLOB, RESOLVER_IMPL_RAW_SHA256)
    _verify_bytes(REPLAY_IMPL_PATH, REPLAY_IMPL_BLOB, REPLAY_IMPL_RAW_SHA256)
    _verify_bytes(AUTHORITY_IMPL_PATH, AUTHORITY_IMPL_BLOB, AUTHORITY_IMPL_RAW_SHA256)
    if rp.get("implementation_git_blob_sha1") != RESOLVER_IMPL_BLOB or rp.get("implementation_raw_sha256") != RESOLVER_IMPL_RAW_SHA256:
        raise ScientificAssuranceLineageV111Error("CANONICAL_SEMANTIC_RESOLUTION_PROFILE_SUBSTITUTION")
    if dp.get("execution_implementation_git_blob_sha1") != REPLAY_IMPL_BLOB or dp.get("execution_implementation_raw_sha256") != REPLAY_IMPL_RAW_SHA256:
        raise ScientificAssuranceLineageV111Error("DERIVATION_PROFILE_EXECUTION_IMPLEMENTATION_REBINDING")
    if dp.get("resolver_profile_id") != rp.get("resolver_profile_id") or dp.get("resolver_profile_content_hash") != rp.get("profile_content_hash"):
        raise ScientificAssuranceLineageV111Error("DERIVATION_PROFILE_RESOLVER_REBINDING")
    return rp, dp

def _verify_reference(path: str, expected_id: str, expected_hash: str) -> Mapping[str, Any]:
    return _content_obj(
        path, "AIFC/canonical-semantic-reference/v1",
        "semantic_reference_id", expected_id, "reference_content_hash",
        "AIFC:CANONICAL-SEMANTIC-REFERENCE:v1", expected_hash,
    )

def audit_derived_semantic_lineage(
    predecessor_identity: str,
    target_profile_identity: str,
    entailment_question_identity: str,
) -> DerivedSemanticLineageReport:
    if (predecessor_identity, target_profile_identity, entailment_question_identity) != (
        v17.PREDECESSOR_ID, v17.TARGET_PROFILE_ID, v17.QUESTION_ID
    ):
        raise ScientificAssuranceLineageV111Error("ENTAILMENT_QUESTION_IDENTITY_SUBSTITUTION")

    inherited = v110.audit_semantic_endpoint_identity_closure(
        predecessor_identity, target_profile_identity, entailment_question_identity
    )
    rp, dp = _verify_profiles()
    refs = {
        REF_A_ID: _verify_reference(REF_A_PATH, REF_A_ID, REF_A_HASH),
        REF_B_ID: _verify_reference(REF_B_PATH, REF_B_ID, REF_B_HASH),
    }
    resolutions = {rid: resolver.resolve_reference(obj, rp) for rid, obj in refs.items()}
    if any(x.state != "RESOLVED" for x in resolutions.values()):
        raise ScientificAssuranceLineageV111Error("CANONICAL_SEMANTIC_LOCUS_RESOLUTION_BLOCKED")
    if any(x.authority_scope_evidence != "CANDIDATE_NORMATIVE_LOCUS_SCOPE_EVIDENCE" for x in resolutions.values()):
        raise ScientificAssuranceLineageV111Error("CANONICAL_SEMANTIC_LOCUS_AUTHORITY_SCOPE_FAILED")

    proof_obj = _content_obj(
        PROOF_PATH, "AIFC/semantic-derivation-proof/v1", "derivation_proof_id", PROOF_ID,
        "proof_content_hash", "AIFC:SEMANTIC-DERIVATION-PROOF:v1", PROOF_HASH,
    )
    manifest_obj = _content_obj(
        MANIFEST_PATH, "AIFC/derivation-leaf-manifest/v1", "manifest_id", MANIFEST_ID,
        "manifest_content_hash", "AIFC:DERIVATION-LEAF-MANIFEST:v1", MANIFEST_CONTENT_HASH,
    )
    graph_obj = _content_obj(
        GRAPH_PATH, "AIFC/canonical-semantic-dependency-graph/v1", "graph_id", GRAPH_ID,
        "graph_content_hash", "AIFC:CANONICAL-SEMANTIC-DEPENDENCY-GRAPH:v1", GRAPH_CONTENT_HASH,
    )
    derived_obj = _content_obj(
        DERIVED_PATH, "AIFC/bridge-derived-semantic-object/v2", "derived_semantic_object_id", DERIVED_ID,
        "derivation_content_hash", "AIFC:BRIDGE-DERIVED-SEMANTIC-OBJECT:v2", DERIVED_HASH,
    )

    rr = replay.replay_derivation(
        proof_obj, dp, manifest_obj, graph_obj, derived_obj,
        lambda rid: resolutions[rid],
    )
    if rr.state != "VALID":
        raise ScientificAssuranceLineageV111Error("BRIDGE_DERIVED_DERIVATION_REPLAY_NOT_VALID")
    if len(rr.recomputed_manifest) != 3:
        raise ScientificAssuranceLineageV111Error("DERIVED_SEMANTIC_SOURCE_MULTIPLICITY_COLLAPSE")
    identities = [x["canonical_semantic_identity"] for x in rr.recomputed_manifest]
    if identities.count(resolutions[REF_A_ID].canonical_semantic_identity) != 2:
        raise ScientificAssuranceLineageV111Error("DERIVED_SEMANTIC_SOURCE_MULTIPLICITY_COLLAPSE")
    if any(x["semantic_context"] != "DERIVATION_PREMISE" or x["polarity"] != "POSITIVE" for x in rr.recomputed_manifest):
        raise ScientificAssuranceLineageV111Error("DERIVED_SEMANTIC_LEAF_CONTEXT_REBINDING")
    roles = [x["resolved_semantic_role"] for x in rr.recomputed_manifest]
    if roles != ["PREDECESSOR_ATOM","PREDECESSOR_ATOM","TARGET_ATOM"]:
        raise ScientificAssuranceLineageV111Error("DERIVED_SEMANTIC_SOURCE_ROLE_REBINDING")
    if tuple(rr.canonical_dependencies) != tuple(sorted({
        str(resolutions[REF_A_ID].canonical_semantic_identity),
        str(resolutions[REF_B_ID].canonical_semantic_identity),
    })):
        raise ScientificAssuranceLineageV111Error("DERIVED_SEMANTIC_DEPENDENCY_GRAPH_REBINDING")
    replay.assert_acyclic({DERIVED_SEMANTIC_IDENTITY: rr.canonical_dependencies})

    authority_result = authority.evaluate_derived_semantic_authority(
        resolver_authority_lineage_replay_status="NOT_ESTABLISHED",
        derivation_profile_authority_lineage_replay_status="NOT_ESTABLISHED",
        resolved_leaf_authority_states=["NOT_ESTABLISHED"] * len(rr.canonical_dependencies),
        derived_authority_lineage_replay_status="NOT_ESTABLISHED",
    )
    if authority_result.state != "BLOCKED":
        raise ScientificAssuranceLineageV111Error("DERIVED_SEMANTIC_AUTHORITY_FALSE_PROMOTION")

    result = inherited.result
    blocker = inherited.blocked_subtype
    solver_invocations = inherited.solver_invocation_count
    if solver_invocations != 0:
        raise ScientificAssuranceLineageV111Error("SAL_V111_INHERITED_SOLVER_ALREADY_INVOKED")

    statuses = {
        "canonical_semantic_locus_resolution":"CONFIRMED_IN_TESTED_SCOPE",
        "canonical_semantic_resolver_content_identity":"CONFIRMED",
        "canonical_semantic_resolver_executable_semantics":"CONFIRMED",
        "canonical_semantic_locus_authority_scope":"CONFIRMED_AS_RESOLVABLE_CANDIDATE_EVIDENCE",
        "canonical_semantic_resolver_authority":"NOT_ESTABLISHED_SUCCESSOR_CANDIDATE",
        "canonical_leaf_manifest_replay":"CONFIRMED",
        "source_multiplicity_preservation":"CONFIRMED",
        "source_context_binding":"CONFIRMED",
        "source_role_binding":"CONFIRMED",
        "derivation_profile_content_identity":"CONFIRMED",
        "derivation_profile_execution_identity":"CONFIRMED",
        "derivation_replay":"CONFIRMED_BY_REPLAY",
        "output_question_binding":"CONFIRMED",
        "output_atom_binding":"CONFIRMED",
        "output_semantic_identity":"CONFIRMED",
        "output_role_binding":"CONFIRMED",
        "dependency_acyclicity":"CONFIRMED_ON_CANONICAL_GRAPH",
        "source_authority_resolution":"NOT_ESTABLISHED_OR_PARTIAL",
        "derivation_profile_authority":"NOT_ESTABLISHED_SUCCESSOR_CANDIDATE",
        "authority_lineage_replay":"NOT_ESTABLISHED",
        "derived_semantic_authority":"BLOCKED",
    }

    audit = _load(AUDIT_PATH)
    material = dict(audit); claimed = material.pop("audit_content_hash", None)
    if audit.get("schema") != "AIFC/derived-semantic-lineage-audit/v1" or audit.get("audit_id") != AUDIT_ID:
        raise ScientificAssuranceLineageV111Error("SAL_V111_AUDIT_ID_REBINDING")
    if claimed != domain_hash("AIFC:DERIVED-SEMANTIC-LINEAGE-AUDIT:v1", material):
        raise ScientificAssuranceLineageV111Error("SAL_V111_AUDIT_CONTENT_IDENTITY_REBINDING")
    expected = {
        "entailment_question_id":v17.QUESTION_ID,
        "derived_semantic_object_id":DERIVED_ID,
        **statuses,
        "solver_invocation_count":0,
        "result":result,
        "blocked_subtype":blocker,
    }
    for key, value in expected.items():
        if audit.get(key) != value:
            raise ScientificAssuranceLineageV111Error(f"SAL_V111_AUDIT_RESULT_REBINDING:{key}")

    return DerivedSemanticLineageReport(
        v17.QUESTION_ID,
        statuses["canonical_semantic_locus_resolution"],
        statuses["canonical_semantic_resolver_content_identity"],
        statuses["canonical_semantic_resolver_executable_semantics"],
        statuses["canonical_semantic_locus_authority_scope"],
        statuses["canonical_semantic_resolver_authority"],
        statuses["canonical_leaf_manifest_replay"],
        statuses["source_multiplicity_preservation"],
        statuses["source_context_binding"],
        statuses["source_role_binding"],
        statuses["derivation_profile_content_identity"],
        statuses["derivation_profile_execution_identity"],
        statuses["derivation_replay"],
        statuses["output_question_binding"],
        statuses["output_atom_binding"],
        statuses["output_semantic_identity"],
        statuses["output_role_binding"],
        statuses["dependency_acyclicity"],
        statuses["source_authority_resolution"],
        statuses["derivation_profile_authority"],
        statuses["authority_lineage_replay"],
        statuses["derived_semantic_authority"],
        0,
        result,
        blocker,
    )
