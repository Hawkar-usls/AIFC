#!/usr/bin/env python3
"""Build AIFC/ci-platform-receipt/v1 from GitHub state after verifier artifact upload.

No identifiers or attestation digests are accepted from the verifier job output channel.
The builder independently discovers the verifier job and artifact by frozen names,
downloads the artifact, and derives the attestation bindings from those stored bytes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

from canonical import canonical_json_bytes, loads_strict  # noqa: E402
from schema_runtime import validate_protocol_object  # noqa: E402

API_VERSION = "2022-11-28"
DOMAIN = b"AIFC:CI_PLATFORM_RECEIPT:v1\x00"
ATTESTATION_DOMAIN = b"AIFC:VERIFIER_CI_ATTESTATION:v2\x00"
VERIFIER_JOB_NAME = "Verifier A environment self-audit"
ARTIFACT_PREFIX = "verifier-a-v04-ci-attestation-"


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


def strict_json_bytes(raw: bytes):
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("PLATFORM_ARTIFACT_JSON_UTF8_BOM_FORBIDDEN")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(f"PLATFORM_ARTIFACT_JSON_INVALID_UTF8:{exc}") from exc
    return loads_strict(text)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def unique_named(rows: list[dict], predicate, code: str) -> dict:
    matches = [row for row in rows if predicate(row)]
    require(len(matches) == 1, f"{code}:EXPECTED_ONE_FOUND_{len(matches)}")
    return matches[0]


def attestation_from_artifact(base: str, artifact_id: int, token: str) -> tuple[dict, str, str]:
    zip_raw = request(f"{base}/actions/artifacts/{artifact_id}/zip", token, accept="application/octet-stream")
    try:
        with zipfile.ZipFile(io.BytesIO(zip_raw), "r") as zf:
            names = set(zf.namelist())
            attestation_name = next((n for n in names if n.endswith("verifier-ci-attestation-v2.json")), None)
            sidecar_name = next((n for n in names if n.endswith("verifier-ci-attestation-v2.sha256.json")), None)
            require(attestation_name is not None, "PLATFORM_ARTIFACT_ATTESTATION_MISSING")
            require(sidecar_name is not None, "PLATFORM_ARTIFACT_ATTESTATION_SIDECAR_MISSING")
            attestation_raw = zf.read(attestation_name)
            sidecar_raw = zf.read(sidecar_name)
    except zipfile.BadZipFile as exc:
        raise ValueError("PLATFORM_ARTIFACT_BAD_ZIP") from exc

    attestation = strict_json_bytes(attestation_raw)
    sidecar = strict_json_bytes(sidecar_raw)
    require(isinstance(attestation, dict), "PLATFORM_ARTIFACT_ATTESTATION_NOT_OBJECT")
    require(isinstance(sidecar, dict), "PLATFORM_ARTIFACT_ATTESTATION_SIDECAR_NOT_OBJECT")
    validate_protocol_object(attestation, "AIFC/verifier-ci-attestation/v2")
    raw_sha = hashlib.sha256(attestation_raw).hexdigest()
    protocol_hash = hashlib.sha256(ATTESTATION_DOMAIN + attestation_raw).hexdigest()
    require(sidecar.get("raw_sha256") == raw_sha, "PLATFORM_ARTIFACT_ATTESTATION_SIDECAR_RAW_MISMATCH")
    require(sidecar.get("protocol_content_hash") == protocol_hash, "PLATFORM_ARTIFACT_ATTESTATION_SIDECAR_PROTOCOL_MISMATCH")
    return attestation, raw_sha, protocol_hash


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--run-id", type=int, required=True)
    p.add_argument("--output-dir", required=True)
    args = p.parse_args()

    token = os.environ.get("GH_TOKEN")
    repository = os.environ.get("GITHUB_REPOSITORY", "Hawkar-usls/AIFC")
    require(bool(token), "GH_TOKEN is required")
    require(repository == "Hawkar-usls/AIFC", f"unexpected repository: {repository}")
    base = f"https://api.github.com/repos/{repository}"

    run = api_json(f"{base}/actions/runs/{args.run_id}", token)
    jobs = api_json(f"{base}/actions/runs/{args.run_id}/jobs?per_page=100", token).get("jobs", [])
    artifacts = api_json(f"{base}/actions/runs/{args.run_id}/artifacts?per_page=100", token).get("artifacts", [])
    job = unique_named(jobs, lambda row: row.get("name") == VERIFIER_JOB_NAME, "PLATFORM_VERIFIER_JOB_LOOKUP")
    expected_artifact_name = f"{ARTIFACT_PREFIX}{args.run_id}"
    artifact = unique_named(artifacts, lambda row: row.get("name") == expected_artifact_name, "PLATFORM_ATTESTATION_ARTIFACT_LOOKUP")

    require(run.get("id") == args.run_id, "PLATFORM_RUN_ID_MISMATCH")
    require(job.get("run_id") == args.run_id, "PLATFORM_JOB_RUN_REBINDING")
    require(job.get("status") == "completed", "PLATFORM_JOB_NOT_COMPLETED")
    require(job.get("conclusion") == "success", "PLATFORM_JOB_NOT_SUCCESS")
    require(artifact.get("expired") is False, "PLATFORM_ARTIFACT_EXPIRED")
    require(isinstance(artifact.get("digest"), str) and artifact["digest"].startswith("sha256:"), "PLATFORM_ARTIFACT_DIGEST_MISSING")
    artifact_run = artifact.get("workflow_run") or {}
    require(artifact_run.get("id") == args.run_id, "PLATFORM_ARTIFACT_RUN_REBINDING")

    attestation, attestation_raw_sha, attestation_protocol_hash = attestation_from_artifact(
        base, int(artifact["id"]), token
    )
    tested_source_commit = attestation["tested_source_commit_sha"]
    require(run.get("head_sha") == tested_source_commit, "PLATFORM_HEAD_SHA_MISMATCH")
    require(git("rev-parse", "HEAD") == tested_source_commit, "PLATFORM_CHECKOUT_HEAD_MISMATCH")
    require(attestation["workflow"]["run_id"] == args.run_id, "PLATFORM_ATTESTATION_RUN_REBINDING")
    require(attestation["workflow"]["job_id"] == int(job["id"]), "PLATFORM_ATTESTATION_JOB_REBINDING")
    require(artifact_run.get("head_sha") in (None, tested_source_commit), "PLATFORM_ARTIFACT_HEAD_REBINDING")

    receipt = {
        "schema": "AIFC/ci-platform-receipt/v1",
        "platform": "GITHUB_ACTIONS",
        "repository": repository,
        "tested_source_commit_sha": tested_source_commit,
        "workflow_run": {
            "run_id": args.run_id,
            "run_attempt": int(run.get("run_attempt", 1)),
            "workflow_id": int(run["workflow_id"]),
            "event_name": str(run["event"]),
            "head_sha": str(run["head_sha"]),
            "head_branch": run.get("head_branch"),
        },
        "verifier_job": {
            "job_id": int(job["id"]),
            "name": str(job["name"]),
            "status": str(job["status"]),
            "conclusion": str(job["conclusion"]),
        },
        "attestation_artifact": {
            "artifact_id": int(artifact["id"]),
            "name": str(artifact["name"]),
            "digest": str(artifact["digest"]),
            "size_in_bytes": int(artifact["size_in_bytes"]),
            "expired": bool(artifact["expired"]),
        },
        "attestation_binding": {
            "attestation_raw_sha256": attestation_raw_sha,
            "attestation_protocol_hash": attestation_protocol_hash,
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
    print(f"PLATFORM_JOB_ID = {job['id']}")
    print(f"ATTESTATION_ARTIFACT_ID = {artifact['id']}")
    print(f"ATTESTATION_ARTIFACT_DIGEST = {artifact['digest']}")
    print(f"ATTESTATION_RAW_SHA256 = {attestation_raw_sha}")
    print(f"ATTESTATION_PROTOCOL_HASH = {attestation_protocol_hash}")
    print(f"CI_PLATFORM_RECEIPT_RAW_SHA256 = {raw_sha}")
    print(f"CI_PLATFORM_RECEIPT_PROTOCOL_HASH = {protocol_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
