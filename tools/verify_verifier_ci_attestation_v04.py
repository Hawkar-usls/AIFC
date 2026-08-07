#!/usr/bin/env python3
"""Offline verifier for AIFC/verifier-ci-attestation/v2."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

from canonical import canonical_json_bytes, load_json_strict, raw_evidence_hash  # noqa: E402
from schema_runtime import validate_protocol_object  # noqa: E402

ATTESTATION_DOMAIN = b"AIFC:VERIFIER_CI_ATTESTATION:v2\x00"
ENV_DOMAIN = b"AIFC:EXECUTION_ENVIRONMENT_MANIFEST:v1\x00"
USES_RE = re.compile(r"^\s*uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([0-9a-f]{40})\s*$", re.MULTILINE)


class AttestationRejected(ValueError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise AttestationRejected(code)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def source_set(paths: Iterable[Path]) -> dict:
    rows = []
    for path in sorted({p.resolve() for p in paths}):
        rows.append({"path": path.relative_to(ROOT.resolve()).as_posix(), "raw_sha256": sha256_bytes(path.read_bytes())})
    payload = canonical_json_bytes({"schema": "AIFC/source-set-manifest/v1", "files": rows})
    return {
        "manifest_sha256": hashlib.sha256(b"AIFC:SOURCE_SET_MANIFEST:v1\x00" + payload).hexdigest(),
        "file_count": len(rows),
    }


def checker_paths() -> list[Path]:
    return [
        ROOT / "tools" / "check_repo_conformance.py",
        ROOT / "tools" / "check_preregistration_conformance.py",
        ROOT / "tools" / "check_self_audit_conformance.py",
        ROOT / "tools" / "build_execution_environment_manifest.py",
        ROOT / "tools" / "build_verifier_ci_attestation_v04.py",
        ROOT / "tools" / "verify_verifier_ci_attestation_v04.py",
        ROOT / "tools" / "build_ci_platform_receipt.py",
        ROOT / "tools" / "verify_ci_platform_receipt.py",
    ]


def resolve_evidence_file(row: dict, artifact_dir: Path, code_prefix: str) -> bytes:
    path = artifact_dir / row["path"]
    require(path.is_file(), f"{code_prefix}:MISSING:{row['path']}")
    raw = path.read_bytes()
    require(sha256_bytes(raw) == row["raw_sha256"], f"{code_prefix}:RAW_HASH:{row['path']}")
    require(raw_evidence_hash(raw) == row["aifc_raw_evidence_hash"], f"{code_prefix}:AIFC_HASH:{row['path']}")
    return raw


def parse_exit_bytes(raw: bytes) -> int:
    try:
        text = raw.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError as exc:
        raise AttestationRejected(f"CI_EXIT_EVIDENCE_INVALID_UTF8:{exc}") from exc
    require(re.fullmatch(r"[0-9]{1,3}", text) is not None, "CI_EXIT_EVIDENCE_INVALID_SYNTAX")
    value = int(text, 10)
    require(0 <= value <= 255, "CI_EXIT_EVIDENCE_OUT_OF_RANGE")
    return value


def parse_test_count_bytes(raw: bytes) -> int:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise AttestationRejected(f"CI_UNITTEST_REPORT_INVALID_UTF8:{exc}") from exc
    matches = re.findall(r"^Ran\s+(\d+)\s+tests?\s+in\s+.+$", text, flags=re.MULTILINE)
    require(len(matches) == 1, f"CI_UNITTEST_SUMMARY_AMBIGUOUS:{len(matches)}")
    return int(matches[0], 10)


def verify_report(row: dict, artifact_dir: Path, key: str) -> tuple[int, bytes]:
    output = resolve_evidence_file(row["output"], artifact_dir, f"CI_REPORT:{key}")
    exit_raw = resolve_evidence_file(row["exit_evidence"], artifact_dir, f"CI_EXIT:{key}")
    recomputed_exit = parse_exit_bytes(exit_raw)
    require(recomputed_exit == row["declared_exit_code"], f"CI_EXIT_CODE_REBINDING:{key}")
    return recomputed_exit, output


def parse_freeze_bytes(raw: bytes) -> list[dict]:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise AttestationRejected(f"PIP_FREEZE_INVALID_UTF8:{exc}") from exc
    rows = []
    seen = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        require("==" in stripped, f"PIP_FREEZE_NON_EXACT:{stripped}")
        name, version = stripped.split("==", 1)
        require(bool(name) and bool(version) and " " not in name, f"PIP_FREEZE_INVALID_ROW:{stripped}")
        key = name.lower().replace("_", "-")
        require(key not in seen, f"PIP_FREEZE_DUPLICATE:{name}")
        seen.add(key)
        rows.append({"name": name, "version": version})
    require(bool(rows), "PIP_FREEZE_EMPTY")
    return sorted(rows, key=lambda row: row["name"].lower().replace("_", "-"))


def verify_environment(att: dict, artifact_dir: Path, workflow_path: Path) -> None:
    row = att["execution_environment"]
    path = artifact_dir / row["path"]
    require(path.is_file(), "EXECUTION_ENVIRONMENT_MANIFEST_MISSING")
    raw = path.read_bytes()
    require(sha256_bytes(raw) == row["raw_sha256"], "EXECUTION_ENVIRONMENT_RAW_HASH_MISMATCH")
    require(raw_evidence_hash(raw) == row["aifc_raw_evidence_hash"], "EXECUTION_ENVIRONMENT_AIFC_HASH_MISMATCH")
    require(hashlib.sha256(ENV_DOMAIN + raw).hexdigest() == row["protocol_content_hash"], "EXECUTION_ENVIRONMENT_PROTOCOL_HASH_MISMATCH")
    env = load_json_strict(path)
    require(isinstance(env, dict), "EXECUTION_ENVIRONMENT_NOT_OBJECT")
    validate_protocol_object(env, "AIFC/execution-environment-manifest/v1")
    require(env["tested_source_commit_sha"] == att["tested_source_commit_sha"], "SAME_TREE_DIFFERENT_EXECUTION_ENVIRONMENT:SOURCE_COMMIT")

    lock_path = ROOT / env["dependency_lock"]["path"]
    require(lock_path.is_file(), "EXECUTION_ENVIRONMENT_LOCK_MISSING")
    require(sha256_bytes(lock_path.read_bytes()) == env["dependency_lock"]["raw_sha256"], "SAME_TREE_DIFFERENT_EXECUTION_ENVIRONMENT:LOCK_HASH")
    require(env["dependency_lock"]["require_hashes"] is True, "DEPENDENCY_LOCK_REQUIRE_HASHES_FALSE")
    require(env["dependency_lock"]["only_binary"] is True, "DEPENDENCY_LOCK_ONLY_BINARY_FALSE")

    for key in ("os_release", "uname", "system_packages"):
        resolve_evidence_file(env["runner"][key], artifact_dir, f"EXECUTION_ENVIRONMENT:{key}")
    freeze_raw = resolve_evidence_file(env["installer"]["pip_freeze"], artifact_dir, "EXECUTION_ENVIRONMENT:pip_freeze")
    require(parse_freeze_bytes(freeze_raw) == env["installed_distributions"], "SAME_TREE_DIFFERENT_EXECUTION_ENVIRONMENT:PIP_FREEZE_REBINDING")

    workflow_text = workflow_path.read_text(encoding="utf-8", errors="strict")
    observed_actions = sorted(
        ({"repository": repo, "commit_sha": sha} for repo, sha in set(USES_RE.findall(workflow_text))),
        key=lambda row: row["repository"],
    )
    require(observed_actions == env["actions"], "SAME_TREE_DIFFERENT_EXECUTION_ENVIRONMENT:ACTION_SET_REBINDING")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--attestation", required=True)
    p.add_argument("--artifact-dir", required=True)
    p.add_argument("--sidecar", required=True)
    args = p.parse_args()

    artifact_dir = Path(args.artifact_dir)
    attestation_path = Path(args.attestation)
    att = load_json_strict(attestation_path)
    require(isinstance(att, dict), "CI_ATTESTATION_NOT_OBJECT")
    validate_protocol_object(att, "AIFC/verifier-ci-attestation/v2")

    require(att["tested_source_commit_sha"] == git("rev-parse", "HEAD"), "DETACHED_CI_PASS_ATTESTATION:SOURCE_COMMIT")
    require(att["tested_tree_sha"] == git("rev-parse", "HEAD^{tree}"), "DETACHED_CI_PASS_ATTESTATION:TREE")

    workflow_path = ROOT / att["workflow"]["path"]
    require(workflow_path.is_file(), "ATTESTED_WORKFLOW_FILE_MISSING")
    require(sha256_bytes(workflow_path.read_bytes()) == att["workflow"]["raw_sha256"], "DETACHED_CI_PASS_ATTESTATION:WORKFLOW_HASH")

    verifier_source = list((ROOT / "reference" / "verifier").glob("*.py")) + [
        ROOT / "reference" / "verifier" / "requirements.txt",
        ROOT / "reference" / "verifier" / "requirements.lock.txt",
    ]
    expected_sets = {
        "schemas": source_set(list((ROOT / "schemas").glob("*.schema.json"))),
        "verifier_source": source_set(verifier_source),
        "test_corpus": source_set(list((ROOT / "reference" / "tests").glob("test_*.py"))),
        "checkers": source_set(checker_paths()),
    }
    for name, expected in expected_sets.items():
        require(att["bound_source_sets"][name] == expected, f"DETACHED_CI_PASS_ATTESTATION:{name.upper()}_SET")

    verify_environment(att, artifact_dir, workflow_path)

    recomputed_exits = []
    unit_output = b""
    for key in ("base_conformance", "preregistration_conformance", "self_audit_conformance", "unittest"):
        exit_code, output = verify_report(att["reports"][key], artifact_dir, key)
        recomputed_exits.append(exit_code)
        if key == "unittest":
            unit_output = output
    recomputed_count = parse_test_count_bytes(unit_output)
    require(recomputed_count == att["reports"]["unittest"]["declared_test_count"], "CI_TEST_COUNT_REBINDING")

    expected_status = "PASS" if recomputed_exits == [0, 0, 0, 0] else "FAIL"
    require(att["overall_status"] == expected_status, "CI_ATTESTATION_STATUS_REPORT_MISMATCH")

    raw = attestation_path.read_bytes()
    side = load_json_strict(args.sidecar)
    require(isinstance(side, dict), "CI_ATTESTATION_SIDECAR_NOT_OBJECT")
    require(side.get("raw_sha256") == sha256_bytes(raw), "CI_ATTESTATION_SIDECAR_RAW_HASH_MISMATCH")
    require(side.get("protocol_content_hash") == hashlib.sha256(ATTESTATION_DOMAIN + raw).hexdigest(), "CI_ATTESTATION_SIDECAR_PROTOCOL_HASH_MISMATCH")

    print(f"CI_ATTESTATION = {att['overall_status']}")
    print(f"TESTED_SOURCE_COMMIT_SHA = {att['tested_source_commit_sha']}")
    print(f"TESTED_TREE_SHA = {att['tested_tree_sha']}")
    print(f"WORKFLOW_RUN_ID = {att['workflow']['run_id']}")
    print(f"WORKFLOW_JOB_ID = {att['workflow']['job_id']}")
    print(f"UNIT_TEST_COUNT_RECOMPUTED = {recomputed_count}")
    print("CI_EXIT_CODE_REBINDING = REJECTED_BY_EVIDENCE_REPLAY")
    print("CI_TEST_COUNT_REBINDING = REJECTED_BY_REPORT_REPLAY")
    print("SAME_TREE_DIFFERENT_EXECUTION_ENVIRONMENT = BOUND_AND_DETECTABLE")
    print("DETACHED_CI_PASS_ATTESTATION = REJECTED_BY_BINDING_CHECKS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AttestationRejected as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(2)
