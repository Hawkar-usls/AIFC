#!/usr/bin/env python3
"""Build AIFC/ci-platform-receipt/v1 after the verifier artifact has been uploaded."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

from canonical import canonical_json_bytes  # noqa: E402
from schema_runtime import validate_protocol_object  # noqa: E402

API_VERSION = "2022-11-28"
DOMAIN = b"AIFC:CI_PLATFORM_RECEIPT:v1\x00"


def api_json(url: str, token: str) -> dict:
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
    })
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", type=int, required=True)
    p.add_argument("--job-id", type=int, required=True)
    p.add_argument("--artifact-id", type=int, required=True)
    p.add_argument("--tested-source-commit", required=True)
    p.add_argument("--attestation-raw-sha256", required=True)
    p.add_argument("--attestation-protocol-hash", required=True)
    p.add_argument("--output-dir", required=True)
    args = p.parse_args()

    token = os.environ.get("GH_TOKEN")
    repository = os.environ.get("GITHUB_REPOSITORY", "Hawkar-usls/AIFC")
    require(bool(token), "GH_TOKEN is required")
    require(repository == "Hawkar-usls/AIFC", f"unexpected repository: {repository}")
    base = f"https://api.github.com/repos/{repository}"

    run = api_json(f"{base}/actions/runs/{args.run_id}", token)
    job = api_json(f"{base}/actions/jobs/{args.job_id}", token)
    artifact = api_json(f"{base}/actions/artifacts/{args.artifact_id}", token)

    require(run.get("id") == args.run_id, "PLATFORM_RUN_ID_MISMATCH")
    require(run.get("head_sha") == args.tested_source_commit, "PLATFORM_HEAD_SHA_MISMATCH")
    require(job.get("id") == args.job_id, "PLATFORM_JOB_ID_MISMATCH")
    require(job.get("run_id") == args.run_id, "PLATFORM_JOB_RUN_REBINDING")
    require(job.get("name") == "Verifier A environment self-audit", "PLATFORM_JOB_NAME_MISMATCH")
    require(job.get("status") == "completed", "PLATFORM_JOB_NOT_COMPLETED")
    require(job.get("conclusion") == "success", "PLATFORM_JOB_NOT_SUCCESS")
    require(artifact.get("id") == args.artifact_id, "PLATFORM_ARTIFACT_ID_MISMATCH")
    require(artifact.get("expired") is False, "PLATFORM_ARTIFACT_EXPIRED")
    require(isinstance(artifact.get("digest"), str) and artifact["digest"].startswith("sha256:"), "PLATFORM_ARTIFACT_DIGEST_MISSING")
    workflow_run = artifact.get("workflow_run") or {}
    require(workflow_run.get("id") == args.run_id, "PLATFORM_ARTIFACT_RUN_REBINDING")
    require(workflow_run.get("head_sha") in (None, args.tested_source_commit), "PLATFORM_ARTIFACT_HEAD_REBINDING")

    receipt = {
        "schema": "AIFC/ci-platform-receipt/v1",
        "platform": "GITHUB_ACTIONS",
        "repository": repository,
        "tested_source_commit_sha": args.tested_source_commit,
        "workflow_run": {
            "run_id": args.run_id,
            "run_attempt": int(run.get("run_attempt", 1)),
            "workflow_id": int(run["workflow_id"]),
            "event_name": str(run["event"]),
            "head_sha": str(run["head_sha"]),
            "head_branch": run.get("head_branch"),
        },
        "verifier_job": {
            "job_id": args.job_id,
            "name": str(job["name"]),
            "status": str(job["status"]),
            "conclusion": str(job["conclusion"]),
        },
        "attestation_artifact": {
            "artifact_id": args.artifact_id,
            "name": str(artifact["name"]),
            "digest": str(artifact["digest"]),
            "size_in_bytes": int(artifact["size_in_bytes"]),
            "expired": bool(artifact["expired"]),
        },
        "attestation_binding": {
            "attestation_raw_sha256": args.attestation_raw_sha256,
            "attestation_protocol_hash": args.attestation_protocol_hash,
        },
        "api_observation": {
            "api_version": API_VERSION,
            "observed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        },
        "scope": "ATTESTS_EXISTENCE_AND_PLATFORM_METADATA_OF_THE_VERIFIER_JOB_AND_ITS_ALREADY_UPLOADED_ATTESTATION_ARTIFACT;DOES_NOT_SELF_BIND_THIS_PLATFORM_RECEIPTS_OWN_ARTIFACT_ID_OR_DIGEST",
        "claim_ceiling": {
            "implementation_a_pass": False,
            "aifc_v1_frozen": False,
            "platform_trust_proven": False,
        },
    }
    validate_protocol_object(receipt, "AIFC/ci-platform-receipt/v1")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "ci-platform-receipt.json"
    out.write_bytes(canonical_json_bytes(receipt))
    raw = out.read_bytes()
    raw_sha = hashlib.sha256(raw).hexdigest()
    protocol_hash = hashlib.sha256(DOMAIN + raw).hexdigest()
    sidecar = {
        "schema": "AIFC/ci-platform-receipt-sidecar/v1",
        "raw_sha256": raw_sha,
        "protocol_content_hash": protocol_hash,
    }
    (out_dir / "ci-platform-receipt.sha256.json").write_bytes(canonical_json_bytes(sidecar))
    print("CI_PLATFORM_RECEIPT_BUILD = PASS")
    print(f"PLATFORM_RUN_ID = {args.run_id}")
    print(f"PLATFORM_JOB_ID = {args.job_id}")
    print(f"ATTESTATION_ARTIFACT_ID = {args.artifact_id}")
    print(f"ATTESTATION_ARTIFACT_DIGEST = {artifact['digest']}")
    print(f"CI_PLATFORM_RECEIPT_RAW_SHA256 = {raw_sha}")
    print(f"CI_PLATFORM_RECEIPT_PROTOCOL_HASH = {protocol_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
