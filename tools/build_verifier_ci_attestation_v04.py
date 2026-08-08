#!/usr/bin/env python3
"""Build AIFC/verifier-ci-attestation/v2 with environment and report evidence bindings."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import os
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


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def raw_sha(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def source_set(paths: Iterable[Path]) -> dict:
    rows = []
    for path in sorted({p.resolve() for p in paths}):
        rows.append({"path": path.relative_to(ROOT.resolve()).as_posix(), "raw_sha256": raw_sha(path)})
    payload = canonical_json_bytes({"schema": "AIFC/source-set-manifest/v1", "files": rows})
    return {
        "manifest_sha256": hashlib.sha256(b"AIFC:SOURCE_SET_MANIFEST:v1\x00" + payload).hexdigest(),
        "file_count": len(rows),
    }


def evidence_file(path: Path) -> dict:
    raw = path.read_bytes()
    return {
        "path": path.name,
        "raw_sha256": sha256_bytes(raw),
        "aifc_raw_evidence_hash": raw_evidence_hash(raw),
    }


def read_exit_code(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="strict").strip()
    if not re.fullmatch(r"[0-9]{1,3}", text):
        raise ValueError(f"invalid exit evidence in {path}: {text!r}")
    value = int(text, 10)
    if value < 0 or value > 255:
        raise ValueError(f"exit code out of range in {path}: {value}")
    return value


def test_count(path: Path) -> int:
    text = path.read_text(encoding="utf-8", errors="strict")
    matches = re.findall(r"^Ran\s+(\d+)\s+tests?\s+in\s+.+$", text, flags=re.MULTILINE)
    if len(matches) != 1:
        raise ValueError(f"unittest report must contain exactly one 'Ran N tests' summary, found {len(matches)}")
    return int(matches[0], 10)


def report(output: Path, exit_evidence: Path) -> dict:
    return {
        "output": evidence_file(output),
        "exit_evidence": evidence_file(exit_evidence),
        "declared_exit_code": read_exit_code(exit_evidence),
    }


def content_bound_environment(path: Path) -> dict:
    env = load_json_strict(path)
    if not isinstance(env, dict):
        raise ValueError("execution environment manifest must be an object")
    validate_protocol_object(env, "AIFC/execution-environment-manifest/v1")
    raw = path.read_bytes()
    return {
        "path": path.name,
        "raw_sha256": sha256_bytes(raw),
        "aifc_raw_evidence_hash": raw_evidence_hash(raw),
        "protocol_content_hash": hashlib.sha256(ENV_DOMAIN + raw).hexdigest(),
    }


def checker_paths() -> list[Path]:
    return [
        ROOT / "tools" / "check_repo_conformance.py",
        ROOT / "tools" / "check_preregistration_conformance.py",
        ROOT / "tools" / "check_self_audit_conformance.py",
        ROOT / "tools" / "check_sal_conformance_v12.py",
        ROOT / "tools" / "check_sal_root_closure_v13.py",
        ROOT / "tools" / "check_sal_lineage_activation_v14.py",
        ROOT / "tools" / "check_sal_authority_closure_v15.py",
        ROOT / "tools" / "build_execution_environment_manifest.py",
        ROOT / "tools" / "build_verifier_ci_attestation_v04.py",
        ROOT / "tools" / "verify_verifier_ci_attestation_v04.py",
        ROOT / "tools" / "build_ci_platform_receipt.py",
        ROOT / "tools" / "verify_ci_platform_receipt.py",
    ]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--workflow-path", required=True)
    p.add_argument("--environment-manifest", required=True)
    p.add_argument("--base-report", required=True)
    p.add_argument("--base-exit", required=True)
    p.add_argument("--prereg-report", required=True)
    p.add_argument("--prereg-exit", required=True)
    p.add_argument("--self-audit-report", required=True)
    p.add_argument("--self-audit-exit", required=True)
    p.add_argument("--unittest-report", required=True)
    p.add_argument("--unittest-exit", required=True)
    p.add_argument("--job-id", required=True, type=int)
    p.add_argument("--job-name", required=True)
    p.add_argument("--output-dir", required=True)
    args = p.parse_args()

    workflow = ROOT / args.workflow_path
    env_path = Path(args.environment_manifest)
    base = report(Path(args.base_report), Path(args.base_exit))
    prereg = report(Path(args.prereg_report), Path(args.prereg_exit))
    self_audit = report(Path(args.self_audit_report), Path(args.self_audit_exit))
    unit = report(Path(args.unittest_report), Path(args.unittest_exit))
    unit["declared_test_count"] = test_count(Path(args.unittest_report))

    verifier_source = list((ROOT / "reference" / "verifier").glob("*.py")) + [
        ROOT / "reference" / "verifier" / "requirements.txt",
        ROOT / "reference" / "verifier" / "requirements.lock.txt",
    ]
    reports = {
        "base_conformance": base,
        "preregistration_conformance": prereg,
        "self_audit_conformance": self_audit,
        "unittest": unit,
    }
    exits = [row["declared_exit_code"] for row in reports.values()]
    status = "PASS" if exits == [0, 0, 0, 0] else "FAIL"

    attestation = {
        "schema": "AIFC/verifier-ci-attestation/v2",
        "verifier_id": "AIFC-Verifier-A",
        "verifier_version": "0.4.0-environment-self-audit",
        "repository": "Hawkar-usls/AIFC",
        "tested_source_commit_sha": git("rev-parse", "HEAD"),
        "tested_tree_sha": git("rev-parse", "HEAD^{tree}"),
        "workflow": {
            "path": args.workflow_path,
            "raw_sha256": raw_sha(workflow),
            "run_id": int(os.environ["GITHUB_RUN_ID"]),
            "run_attempt": int(os.environ.get("GITHUB_RUN_ATTEMPT", "1")),
            "job_id": args.job_id,
            "job_name": args.job_name,
            "event_name": os.environ.get("GITHUB_EVENT_NAME", "unknown"),
        },
        "execution_environment": content_bound_environment(env_path),
        "bound_source_sets": {
            "schemas": source_set(list((ROOT / "schemas").glob("*.schema.json"))),
            "verifier_source": source_set(verifier_source),
            "test_corpus": source_set(list((ROOT / "reference" / "tests").glob("test_*.py"))),
            "checkers": source_set(checker_paths()),
        },
        "reports": reports,
        "overall_status": status,
        "claim_ceiling": {
            "implementation_a_pass": False,
            "aifc_v1_frozen": False,
            "physical_retrocausality": "NOT_OBSERVED",
        },
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    validate_protocol_object(attestation, "AIFC/verifier-ci-attestation/v2")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "verifier-ci-attestation-v2.json"
    out.write_bytes(canonical_json_bytes(attestation))
    raw = out.read_bytes()
    raw_digest = sha256_bytes(raw)
    protocol_digest = hashlib.sha256(ATTESTATION_DOMAIN + raw).hexdigest()
    sidecar = {
        "schema": "AIFC/verifier-ci-attestation-sidecar/v2",
        "raw_sha256": raw_digest,
        "protocol_content_hash": protocol_digest,
    }
    (out_dir / "verifier-ci-attestation-v2.sha256.json").write_bytes(canonical_json_bytes(sidecar))
    print(f"CI_ATTESTATION_STATUS = {status}")
    print(f"TESTED_SOURCE_COMMIT_SHA = {attestation['tested_source_commit_sha']}")
    print(f"TESTED_TREE_SHA = {attestation['tested_tree_sha']}")
    print(f"RECOMPUTABLE_DECLARED_TEST_COUNT = {unit['declared_test_count']}")
    print(f"ATTESTATION_RAW_SHA256 = {raw_digest}")
    print(f"ATTESTATION_PROTOCOL_HASH = {protocol_digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
