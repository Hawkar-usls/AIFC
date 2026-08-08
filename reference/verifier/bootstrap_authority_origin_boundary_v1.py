#!/usr/bin/env python3
"""SAL v1.15 bootstrap authority origin boundary.

Exact historical designation, source-existence, and execution-attestation are
verified as distinct facts. This module does not establish bootstrap legitimacy.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from canonical import domain_hash
from scientific_assurance_lineage_v13 import git_blob_sha1_bytes
import scientific_assurance_lineage_v16 as sal16

ROOT = Path(__file__).resolve().parents[2]
SOURCE_MAIN_COMMIT = "903631143bc9b9374973f352e23d8ce92c807707"
SOURCE_TREE_SHA = "824c5b71f11c83faec09e33bffeab08fd965836d"
BOOTSTRAP_COMMIT = "908de7afddcf9f72c98c2b3fb696a41be1e438e0"

ROOT_V1_ID = "AIFC-NORMATIVE-ASSURANCE-ROOTS-V1"
ROOT_V1_PATH = "conformance/AIFC-NORMATIVE-ASSURANCE-ROOTS-v1.json"
ROOT_V1_BLOB = "0aec9d6ad0d54ce10d312d28a8cb0def1729f835"
ROOT_V2_ID = "AIFC-NORMATIVE-ASSURANCE-ROOTS-V2"
ROOT_V2_PATH = "conformance/AIFC-NORMATIVE-ASSURANCE-ROOTS-v2.json"
ROOT_V2_BLOB = "d2bb7f3917f8761836825a4e80f03c1e282fc37d"

BOOTSTRAP_STATUS_ID = "AIFC-SAL-BOOTSTRAP-AUTHORITY-BASE-CASE-STATUS-V1"
BOOTSTRAP_STATUS_PATH = "conformance/AIFC-BOOTSTRAP-AUTHORITY-BASE-CASE-STATUS-v1.json"
BOOTSTRAP_STATUS_BLOB = "412169b325626f5497965c060c81233817eb5099"

SOURCE_EXISTENCE_IMPL_PATH = "reference/verifier/scientific_assurance_lineage_v16.py"
SOURCE_EXISTENCE_IMPL_BLOB = "5d6534c51418b776c6e456dc14416a0804d7bb09"

SUCCESSOR_RECEIPT_ID = "AIFC-SAL-V1.2-EXACT-MAIN-RECEIPT-7e58b47"
SUCCESSOR_RECEIPT_PATH = "conformance/AIFC-NORMATIVE-AUTHORITY-RECEIPT-7e58b47-v1.json"
SUCCESSOR_RECEIPT_BLOB = "49b54886f065ac42ee4ff22935112c60f44d4a6c"
SUCCESSOR_RECEIPT_COMMIT = "7e58b47398fe585b24db6304ee6122871095d668"

PROFILE_PATH = "conformance/AIFC-BOOTSTRAP-AUTHORITY-ORIGIN-PROFILE-v1.json"
PROFILE_ID = "AIFC-SAL-V1.15-BOOTSTRAP-AUTHORITY-ORIGIN-PROFILE-V1"
PROFILE_HASH = "86a623fc484d341769c832338777b2504f11f885a9371dd77c11f18daf03442c"
PROFILE_BLOB = "8c5e3322f9911e727de140f35a0551d73dc99f40"
PROFILE_DOMAIN = "AIFC:BOOTSTRAP-AUTHORITY-ORIGIN-PROFILE:v1"
AUDIT_DOMAIN = "AIFC:BOOTSTRAP-AUTHORITY-ORIGIN-AUDIT:v1"
BLOCKED_COMPLETENESS = "BLOCKED_UNAUTHORIZED_COMPLETENESS_BASIS"


class BootstrapAuthorityOriginBoundaryV1Error(ValueError):
    pass


@dataclass(frozen=True)
class BootstrapAuthorityOriginReport:
    root_v1_identity: str
    root_v2_identity: str
    bootstrap_status_identity: str
    bootstrap_designation_identity: str
    designated_bootstrap_commit: str
    finite_dag_source_existence_lemma: str
    source_existence_scope: str
    bootstrap_authority_basis_status: str
    retroactive_discovery_of_preexisting_authority: bool
    external_bootstrap_ratification: str
    successor_execution_receipt_identity: str
    successor_execution_receipt_semantics: str
    successor_receipt_platform_trust_proven: bool
    bootstrap_designation_to_legitimacy_promotion: str
    source_existence_to_legitimacy_promotion: str
    execution_receipt_to_bootstrap_legitimacy_promotion: str
    ci_attestation_to_bootstrap_legitimacy_promotion: str
    successor_authority_to_bootstrap_legitimacy_promotion: str
    external_ratification_caller_input_surface: str
    bootstrap_authority_legitimacy: str
    current_internal_verification_path_to_bootstrap_legitimacy: str
    normative_authority_origin_internal_proof: str
    normative_lineage_completeness: str
    derived_semantic_authority: str
    solver_invocation_count: int
    status: str


def _load_exact(path_text: str, expected_blob: str, label: str) -> Mapping[str, Any]:
    raw = (ROOT / path_text).read_bytes()
    actual = git_blob_sha1_bytes(raw)
    if actual != expected_blob:
        raise BootstrapAuthorityOriginBoundaryV1Error(
            f"V115_EXACT_SOURCE_REBINDING:{label}:{actual}"
        )
    obj = json.loads(raw.decode("utf-8"))
    if not isinstance(obj, Mapping):
        raise BootstrapAuthorityOriginBoundaryV1Error("V115_SOURCE_NOT_MAPPING:" + label)
    return obj


def profile_content_hash(profile: Mapping[str, Any]) -> str:
    material = dict(profile)
    material.pop("profile_content_hash", None)
    return domain_hash(PROFILE_DOMAIN, material)


def audit_content_hash(audit: Mapping[str, Any]) -> str:
    material = dict(audit)
    material.pop("audit_content_hash", None)
    return domain_hash(AUDIT_DOMAIN, material)


def verify_profile(profile: Mapping[str, Any]) -> None:
    expected = {
        "schema": "AIFC/bootstrap-authority-origin-profile/v1",
        "profile_id": PROFILE_ID,
        "source_main_commit": SOURCE_MAIN_COMMIT,
        "source_tree_sha": SOURCE_TREE_SHA,
        "bootstrap_designation_registry_id": ROOT_V1_ID,
        "bootstrap_designation_registry_path": ROOT_V1_PATH,
        "bootstrap_designation_registry_git_blob_sha1": ROOT_V1_BLOB,
        "successor_normative_root_registry_id": ROOT_V2_ID,
        "successor_normative_root_registry_path": ROOT_V2_PATH,
        "successor_normative_root_registry_git_blob_sha1": ROOT_V2_BLOB,
        "bootstrap_status_object_id": BOOTSTRAP_STATUS_ID,
        "bootstrap_status_object_path": BOOTSTRAP_STATUS_PATH,
        "bootstrap_status_object_git_blob_sha1": BOOTSTRAP_STATUS_BLOB,
        "designated_bootstrap_commit": BOOTSTRAP_COMMIT,
        "source_existence_lemma_implementation_path": SOURCE_EXISTENCE_IMPL_PATH,
        "source_existence_lemma_implementation_git_blob_sha1": SOURCE_EXISTENCE_IMPL_BLOB,
        "successor_execution_receipt_id": SUCCESSOR_RECEIPT_ID,
        "successor_execution_receipt_path": SUCCESSOR_RECEIPT_PATH,
        "successor_execution_receipt_git_blob_sha1": SUCCESSOR_RECEIPT_BLOB,
        "origin_distinction": "SOURCE_EXISTENCE_NOT_SOURCE_LEGITIMACY",
        "bootstrap_designation_to_legitimacy": "FORBIDDEN",
        "source_existence_to_legitimacy": "FORBIDDEN",
        "execution_attestation_to_legitimacy": "FORBIDDEN",
        "ci_attestation_to_legitimacy": "FORBIDDEN",
        "successor_authority_to_bootstrap_legitimacy": "FORBIDDEN",
        "external_ratification_caller_input_surface": "FORBIDDEN",
        "profile_authority_status": "SUCCESSOR_CANDIDATE_NOT_AUTHORITY_ADMISSIBLE",
        "bootstrap_authority_legitimacy": "NOT_ESTABLISHED",
        "normative_lineage_completeness": BLOCKED_COMPLETENESS,
    }
    for key, value in expected.items():
        if profile.get(key) != value:
            raise BootstrapAuthorityOriginBoundaryV1Error("V115_PROFILE_REBINDING:" + key)
    if profile.get("profile_content_hash") != profile_content_hash(profile):
        raise BootstrapAuthorityOriginBoundaryV1Error("V115_PROFILE_CONTENT_REBINDING")
    if profile.get("profile_content_hash") != PROFILE_HASH:
        raise BootstrapAuthorityOriginBoundaryV1Error("V115_PROFILE_EXACT_HASH_REBINDING")
    for key in (
        "bootstrap_legitimacy_proof",
        "external_ratification",
        "external_ratification_receipt",
        "authority_lineage_ref",
        "authority_status",
    ):
        if key in profile:
            raise BootstrapAuthorityOriginBoundaryV1Error("V115_LEGITIMACY_INPUT_SURFACE:" + key)


def audit_current_origin() -> BootstrapAuthorityOriginReport:
    verify_profile(_load_exact(PROFILE_PATH, PROFILE_BLOB, PROFILE_ID))
    root_v1 = _load_exact(ROOT_V1_PATH, ROOT_V1_BLOB, ROOT_V1_ID)
    root_v2 = _load_exact(ROOT_V2_PATH, ROOT_V2_BLOB, ROOT_V2_ID)
    status = _load_exact(BOOTSTRAP_STATUS_PATH, BOOTSTRAP_STATUS_BLOB, BOOTSTRAP_STATUS_ID)
    receipt = _load_exact(SUCCESSOR_RECEIPT_PATH, SUCCESSOR_RECEIPT_BLOB, SUCCESSOR_RECEIPT_ID)

    if root_v1.get("registry_id") != ROOT_V1_ID:
        raise BootstrapAuthorityOriginBoundaryV1Error("V115_ROOT_V1_ID_REBINDING")
    if root_v1.get("bootstrap_root_commit") != BOOTSTRAP_COMMIT:
        raise BootstrapAuthorityOriginBoundaryV1Error("V115_BOOTSTRAP_DESIGNATION_REBINDING")
    if root_v2.get("registry_id") != ROOT_V2_ID:
        raise BootstrapAuthorityOriginBoundaryV1Error("V115_ROOT_V2_ID_REBINDING")
    if root_v2.get("predecessor_registry_id") != ROOT_V1_ID:
        raise BootstrapAuthorityOriginBoundaryV1Error("V115_ROOT_V2_PREDECESSOR_REBINDING")
    if root_v2.get("predecessor_registry_git_blob_sha1") != ROOT_V1_BLOB:
        raise BootstrapAuthorityOriginBoundaryV1Error("V115_ROOT_V2_PREDECESSOR_HASH_REBINDING")

    status_expected = {
        "status_id": BOOTSTRAP_STATUS_ID,
        "designation_source_registry_id": ROOT_V1_ID,
        "designation_source_registry_git_blob_sha1": ROOT_V1_BLOB,
        "designated_bootstrap_commit": BOOTSTRAP_COMMIT,
        "authority_basis_status": "IMPLICIT_NOT_YET_FIRST_CLASS",
        "retroactive_discovery_of_preexisting_authority": False,
        "external_bootstrap_ratification_status": "NOT_PERFORMED",
        "normative_authority_claim": "NOT_ESTABLISHED_BY_THIS_OBJECT",
    }
    for key, value in status_expected.items():
        if status.get(key) != value:
            raise BootstrapAuthorityOriginBoundaryV1Error("V115_BOOTSTRAP_STATUS_REBINDING:" + key)

    if sal16.BOOTSTRAP_COMMIT != BOOTSTRAP_COMMIT:
        raise BootstrapAuthorityOriginBoundaryV1Error("V115_V16_BOOTSTRAP_CONSTANT_REBINDING")
    if git_blob_sha1_bytes((ROOT / SOURCE_EXISTENCE_IMPL_PATH).read_bytes()) != SOURCE_EXISTENCE_IMPL_BLOB:
        raise BootstrapAuthorityOriginBoundaryV1Error("V115_SOURCE_EXISTENCE_IMPLEMENTATION_REBINDING")
    source_existence = sal16.verify_no_normative_authority_ex_nihilo_instance(
        {"BOOTSTRAP_SOURCE", "SUCCESSOR"},
        {("BOOTSTRAP_SOURCE", "SUCCESSOR")},
    )
    if source_existence != "SOURCE_NODE_EXISTS":
        raise BootstrapAuthorityOriginBoundaryV1Error("V115_SOURCE_EXISTENCE_RESULT_REBINDING")

    receipt_expected = {
        "receipt_id": SUCCESSOR_RECEIPT_ID,
        "tested_source_commit": SUCCESSOR_RECEIPT_COMMIT,
        "platform_trust_proven": False,
        "status": "EXACT_POST_MERGE_RECEIPT_CONFIRMED",
    }
    for key, value in receipt_expected.items():
        if receipt.get(key) != value:
            raise BootstrapAuthorityOriginBoundaryV1Error("V115_SUCCESSOR_RECEIPT_REBINDING:" + key)

    return BootstrapAuthorityOriginReport(
        root_v1_identity="CONFIRMED_PINNED_GIT_BLOB",
        root_v2_identity="CONFIRMED_PINNED_GIT_BLOB",
        bootstrap_status_identity="CONFIRMED_PINNED_GIT_BLOB",
        bootstrap_designation_identity="CONFIRMED_EXACT_HISTORICAL_DESIGNATION",
        designated_bootstrap_commit=BOOTSTRAP_COMMIT,
        finite_dag_source_existence_lemma=source_existence,
        source_existence_scope="FINITE_DAG_BASE_CASE_NECESSITY_ONLY",
        bootstrap_authority_basis_status="IMPLICIT_NOT_YET_FIRST_CLASS",
        retroactive_discovery_of_preexisting_authority=False,
        external_bootstrap_ratification="NOT_PERFORMED",
        successor_execution_receipt_identity="CONFIRMED_PINNED_GIT_BLOB",
        successor_execution_receipt_semantics="EXACT_EXECUTION_ATTESTATION_NOT_BOOTSTRAP_LEGITIMACY",
        successor_receipt_platform_trust_proven=False,
        bootstrap_designation_to_legitimacy_promotion="REJECTED",
        source_existence_to_legitimacy_promotion="REJECTED",
        execution_receipt_to_bootstrap_legitimacy_promotion="REJECTED",
        ci_attestation_to_bootstrap_legitimacy_promotion="REJECTED",
        successor_authority_to_bootstrap_legitimacy_promotion="REJECTED",
        external_ratification_caller_input_surface="FORBIDDEN_NO_CALLER_INPUT_SURFACE",
        bootstrap_authority_legitimacy="NOT_ESTABLISHED",
        current_internal_verification_path_to_bootstrap_legitimacy="ABSENT",
        normative_authority_origin_internal_proof="NOT_ESTABLISHED_BY_INTERNAL_VERIFICATION",
        normative_lineage_completeness=BLOCKED_COMPLETENESS,
        derived_semantic_authority="BLOCKED",
        solver_invocation_count=0,
        status="BOOTSTRAP_AUTHORITY_ORIGIN_BOUNDARY_CONFIRMED_IN_CURRENT_TESTED_SCOPE",
    )


def verify_declared_audit(audit: Mapping[str, Any]) -> BootstrapAuthorityOriginReport:
    expected = {
        "schema": "AIFC/bootstrap-authority-origin-audit/v1",
        "audit_id": "AIFC-SAL-V1.15-BOOTSTRAP-AUTHORITY-ORIGIN-AUDIT-V1",
        "source_main_commit": SOURCE_MAIN_COMMIT,
        "source_tree_sha": SOURCE_TREE_SHA,
        "origin_profile_id": PROFILE_ID,
        "origin_profile_content_hash": PROFILE_HASH,
    }
    for key, value in expected.items():
        if audit.get(key) != value:
            raise BootstrapAuthorityOriginBoundaryV1Error("V115_AUDIT_REBINDING:" + key)
    if audit.get("audit_content_hash") != audit_content_hash(audit):
        raise BootstrapAuthorityOriginBoundaryV1Error("V115_AUDIT_CONTENT_REBINDING")
    report = audit_current_origin()
    for key, value in report.__dict__.items():
        if audit.get(key) != value:
            raise BootstrapAuthorityOriginBoundaryV1Error("V115_AUDIT_REPORT_REBINDING:" + key)
    return report
