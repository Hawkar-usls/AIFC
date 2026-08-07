#!/usr/bin/env python3
"""Build a content-bound AIFC verifier execution-environment manifest."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

from canonical import canonical_json_bytes, raw_evidence_hash  # noqa: E402
from schema_runtime import validate_protocol_object  # noqa: E402

DOMAIN = b"AIFC:EXECUTION_ENVIRONMENT_MANIFEST:v1\x00"
ACTION_RE = re.compile(r"^([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)=([0-9a-f]{40})$")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def evidence_file(path: Path) -> dict:
    raw = path.read_bytes()
    return {
        "path": path.name,
        "raw_sha256": sha256_bytes(raw),
        "aifc_raw_evidence_hash": raw_evidence_hash(raw),
    }


def parse_freeze(path: Path) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for line in path.read_text(encoding="utf-8", errors="strict").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "==" not in stripped:
            raise ValueError(f"non-exact pip freeze row: {stripped}")
        name, version = stripped.split("==", 1)
        if not name or not version or " " in name:
            raise ValueError(f"invalid pip freeze row: {stripped}")
        key = name.lower().replace("_", "-")
        if key in seen:
            raise ValueError(f"duplicate installed distribution: {name}")
        seen.add(key)
        rows.append({"name": name, "version": version})
    if not rows:
        raise ValueError("empty pip freeze evidence")
    return sorted(rows, key=lambda row: row["name"].lower().replace("_", "-"))


def parse_actions(values: list[str]) -> list[dict]:
    rows = []
    seen = set()
    for value in values:
        match = ACTION_RE.fullmatch(value)
        if not match:
            raise ValueError(f"invalid --action value: {value}")
        repository, commit_sha = match.groups()
        if repository in seen:
            raise ValueError(f"duplicate action repository: {repository}")
        seen.add(repository)
        rows.append({"repository": repository, "commit_sha": commit_sha})
    return sorted(rows, key=lambda row: row["repository"])


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def pip_version() -> str:
    text = subprocess.check_output([sys.executable, "-m", "pip", "--version"], text=True).strip()
    parts = text.split()
    if len(parts) < 2 or parts[0] != "pip":
        raise ValueError(f"unrecognized pip --version output: {text}")
    return parts[1]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--artifact-dir", required=True)
    p.add_argument("--os-release", required=True)
    p.add_argument("--uname", required=True)
    p.add_argument("--system-packages", required=True)
    p.add_argument("--pip-freeze", required=True)
    p.add_argument("--dependency-lock", default="reference/verifier/requirements.lock.txt")
    p.add_argument("--action", action="append", default=[])
    args = p.parse_args()

    artifact_dir = Path(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    os_release = Path(args.os_release)
    uname = Path(args.uname)
    system_packages = Path(args.system_packages)
    pip_freeze = Path(args.pip_freeze)
    lock = ROOT / args.dependency_lock
    if len(args.action) < 3:
        raise ValueError("at least three pinned GitHub Actions are required")

    lock_raw = lock.read_bytes()
    manifest = {
        "schema": "AIFC/execution-environment-manifest/v1",
        "platform": "GITHUB_ACTIONS",
        "repository": "Hawkar-usls/AIFC",
        "tested_source_commit_sha": git("rev-parse", "HEAD"),
        "runner": {
            "os": os.environ.get("RUNNER_OS", "UNKNOWN_NOT_EXPOSED"),
            "arch": os.environ.get("RUNNER_ARCH", "UNKNOWN_NOT_EXPOSED"),
            "image_os": os.environ.get("ImageOS", os.environ.get("IMAGE_OS", "UNKNOWN_NOT_EXPOSED")),
            "image_version": os.environ.get("ImageVersion", os.environ.get("IMAGE_VERSION", "UNKNOWN_NOT_EXPOSED")),
            "os_release": evidence_file(os_release),
            "uname": evidence_file(uname),
            "system_packages": evidence_file(system_packages),
        },
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
        },
        "installer": {
            "pip_version": pip_version(),
            "pip_freeze": evidence_file(pip_freeze),
        },
        "dependency_lock": {
            "path": args.dependency_lock,
            "raw_sha256": sha256_bytes(lock_raw),
            "require_hashes": True,
            "only_binary": True,
        },
        "installed_distributions": parse_freeze(pip_freeze),
        "actions": parse_actions(args.action),
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    validate_protocol_object(manifest, "AIFC/execution-environment-manifest/v1")

    out = artifact_dir / "execution-environment-manifest.json"
    out.write_bytes(canonical_json_bytes(manifest))
    raw = out.read_bytes()
    raw_digest = sha256_bytes(raw)
    protocol_digest = hashlib.sha256(DOMAIN + raw).hexdigest()
    sidecar = {
        "schema": "AIFC/execution-environment-manifest-sidecar/v1",
        "raw_sha256": raw_digest,
        "protocol_content_hash": protocol_digest,
    }
    (artifact_dir / "execution-environment-manifest.sha256.json").write_bytes(canonical_json_bytes(sidecar))
    print(f"EXECUTION_ENVIRONMENT_MANIFEST_RAW_SHA256 = {raw_digest}")
    print(f"EXECUTION_ENVIRONMENT_MANIFEST_PROTOCOL_HASH = {protocol_digest}")
    print(f"RUNNER_IMAGE_OS = {manifest['runner']['image_os']}")
    print(f"RUNNER_IMAGE_VERSION = {manifest['runner']['image_version']}")
    print(f"INSTALLED_DISTRIBUTION_COUNT = {len(manifest['installed_distributions'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
