#!/usr/bin/env python3
"""Online verifier for AIFC/ci-platform-receipt/v1 using GitHub Actions API."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

from canonical import load_json_strict  # noqa: E402
from schema_runtime import validate_protocol_object  # noqa: E402

API_VERSION = "2022-11-28"
ATTESTATION_DOMAIN = b"AIFC:VERIFIER_CI_ATTESTATION:v2\x00"
PLATFORM_DOMAIN = b"AIFC:CI_PLATFORM_RECEIPT:v1\x00"


class PlatformReceiptRejected(ValueError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise PlatformReceiptRejected(code)


def request(url: str, token: str, accept: str = "application/vnd.github+json") -> bytes:
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": accept,
        "X-GitHub-Api-Version": API_VERSION,
    })
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def api_json(url: str, token: str) -> dict:
    return json.loads(request(url, token).decode("utf-8", errors="strict"))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--receipt", required=True)
    p.add_argument("--sidecar", required=True)
    args = p.parse_args()

    token = os.environ.get("GH_TOKEN")
    require(bool(token), "GH_TOKEN_REQUIRED")
    receipt_path = Path(args.receipt)
    receipt = load_json_strict(receipt_path)
    require(isinstance(receipt, dict), "CI_PLATFORM_RECEIPT_NOT_OBJECT")
    validate_protocol_object(receipt, "AIFC/ci-platform-receipt/v1")
    repository = receipt["repository"]
    require(repository == "Hawkar-usls/AIFC", "CI_PLATFORM_RECEIPT_REPOSITORY")
    base = f"https://api.github.com/repos/{repository}"

    run_id = receipt["workflow_run"]["run_id"]
    job_id = receipt["verifier_job"]["job_id"]
    artifact_id = receipt["attestation_artifact"]["artifact_id"]
    run = api_json(f"{base}/actions/runs/{run_id}", token)
    job = api_json(f"{base}/actions/jobs/{job_id}", token)
    artifact = api_json(f"{base}/actions/artifacts/{artifact_id}", token)

    require(run.get("id") == run_id, "CI_PLATFORM_RUN_ID_REBINDING")
    require(run.get("head_sha") == receipt["tested_source_commit_sha"], "CI_PLATFORM_HEAD_SHA_REBINDING")
    require(int(run.get("run_attempt", 1)) == receipt["workflow_run"]["run_attempt"], "CI_PLATFORM_RUN_ATTEMPT_REBINDING")
    require(int(run.get("workflow_id")) == receipt["workflow_run"]["workflow_id"], "CI_PLATFORM_WORKFLOW_ID_REBINDING")
    require(str(run.get("event")) == receipt["workflow_run"]["event_name"], "CI_PLATFORM_EVENT_REBINDING")
    require(run.get("head_branch") == receipt["workflow_run"]["head_branch"], "CI_PLATFORM_HEAD_BRANCH_REBINDING")

    require(job.get("id") == job_id, "CI_PLATFORM_JOB_ID_REBINDING")
    require(job.get("run_id") == run_id, "CI_PLATFORM_JOB_RUN_REBINDING")
    require(job.get("name") == receipt["verifier_job"]["name"], "CI_PLATFORM_JOB_NAME_REBINDING")
    require(job.get("status") == "completed", "CI_PLATFORM_JOB_NOT_COMPLETED")
    require(job.get("conclusion") == "success", "CI_PLATFORM_JOB_NOT_SUCCESS")

    require(artifact.get("id") == artifact_id, "CI_PLATFORM_ARTIFACT_ID_REBINDING")
    require(artifact.get("name") == receipt["attestation_artifact"]["name"], "CI_PLATFORM_ARTIFACT_NAME_REBINDING")
    require(artifact.get("digest") == receipt["attestation_artifact"]["digest"], "CI_PLATFORM_ARTIFACT_DIGEST_REBINDING")
    require(int(artifact.get("size_in_bytes")) == receipt["attestation_artifact"]["size_in_bytes"], "CI_PLATFORM_ARTIFACT_SIZE_REBINDING")
    require(artifact.get("expired") is False, "CI_PLATFORM_ARTIFACT_EXPIRED")
    artifact_run = artifact.get("workflow_run") or {}
    require(artifact_run.get("id") == run_id, "CI_PLATFORM_ARTIFACT_RUN_REBINDING")
    require(artifact_run.get("head_sha") in (None, receipt["tested_source_commit_sha"]), "CI_PLATFORM_ARTIFACT_HEAD_REBINDING")

    zip_raw = request(f"{base}/actions/artifacts/{artifact_id}/zip", token, accept="application/octet-stream")
    try:
        with zipfile.ZipFile(io.BytesIO(zip_raw), "r") as zf:
            names = set(zf.namelist())
            attestation_name = next((n for n in names if n.endswith("verifier-ci-attestation-v2.json")), None)
            sidecar_name = next((n for n in names if n.endswith("verifier-ci-attestation-v2.sha256.json")), None)
            require(attestation_name is not None, "CI_PLATFORM_ARTIFACT_ATTESTATION_MISSING")
            require(sidecar_name is not None, "CI_PLATFORM_ARTIFACT_ATTESTATION_SIDECAR_MISSING")
            attestation_raw = zf.read(attestation_name)
            sidecar_raw = zf.read(sidecar_name)
    except zipfile.BadZipFile as exc:
        raise PlatformReceiptRejected("CI_PLATFORM_ARTIFACT_BAD_ZIP") from exc

    att_raw_sha = hashlib.sha256(attestation_raw).hexdigest()
    att_protocol = hashlib.sha256(ATTESTATION_DOMAIN + attestation_raw).hexdigest()
    require(att_raw_sha == receipt["attestation_binding"]["attestation_raw_sha256"], "CI_PLATFORM_ARTIFACT_ATTESTATION_RAW_REBINDING")
    require(att_protocol == receipt["attestation_binding"]["attestation_protocol_hash"], "CI_PLATFORM_ARTIFACT_ATTESTATION_PROTOCOL_REBINDING")
    side = json.loads(sidecar_raw.decode("utf-8", errors="strict"))
    require(side.get("raw_sha256") == att_raw_sha, "CI_PLATFORM_ARTIFACT_SIDECAR_RAW_MISMATCH")
    require(side.get("protocol_content_hash") == att_protocol, "CI_PLATFORM_ARTIFACT_SIDECAR_PROTOCOL_MISMATCH")

    receipt_raw = receipt_path.read_bytes()
    sidecar = load_json_strict(args.sidecar)
    require(isinstance(sidecar, dict), "CI_PLATFORM_SIDECAR_NOT_OBJECT")
    require(sidecar.get("raw_sha256") == hashlib.sha256(receipt_raw).hexdigest(), "CI_PLATFORM_RECEIPT_SIDECAR_RAW_MISMATCH")
    require(sidecar.get("protocol_content_hash") == hashlib.sha256(PLATFORM_DOMAIN + receipt_raw).hexdigest(), "CI_PLATFORM_RECEIPT_SIDECAR_PROTOCOL_MISMATCH")

    print("CI_PLATFORM_RECEIPT = PASS")
    print(f"TESTED_SOURCE_COMMIT_SHA = {receipt['tested_source_commit_sha']}")
    print(f"WORKFLOW_RUN_ID = {run_id}")
    print(f"VERIFIER_JOB_ID = {job_id}")
    print(f"ATTESTATION_ARTIFACT_ID = {artifact_id}")
    print(f"ATTESTATION_ARTIFACT_DIGEST = {artifact['digest']}")
    print("CI_PLATFORM_JOB_SUCCESS = API_CONFIRMED")
    print("CI_PLATFORM_ARTIFACT_BYTES = DOWNLOADED_AND_BOUND")
    print("PLATFORM_TRUST_PROVEN = FALSE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PlatformReceiptRejected as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(2)
