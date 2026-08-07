#!/usr/bin/env python3
"""AIFC Verifier A authoritative standalone replay CLI v0.2."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from canonical import CanonicalizationError, canonical_json_bytes, load_json_strict
from full_admission_v02 import verify_replay_manifest
from resolver import EvidenceResolutionError
from resolver_v02 import EvidenceResolverV02


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="aifc-verify-v02",
        description="Resolve exact AIFC evidence bytes, verify plan preregistration, and replay admitted v0.2 evidence structure.",
    )
    p.add_argument("--package", required=True)
    p.add_argument("--store-index", required=True)
    p.add_argument("--store-root", required=True)
    p.add_argument("--output")
    return p


def invalid(detail: str) -> dict:
    return {
        "schema": "AIFC/verifier-result/v1",
        "experiment_id": "UNKNOWN",
        "trial_index": 1,
        "verifier_id": "AIFC-Verifier-A",
        "verifier_version": "0.2.0-replay",
        "evidence_bundle_hash": "0" * 64,
        "gate_results": {"CLI_INPUT": "FAIL"},
        "exact_match": False,
        "terminal_grade": "INVALIDATED_EVIDENCE",
        "failure_codes": [f"CLI_INPUT_REJECTED:{detail}"],
        "physical_interpretation": "NO_AUTOMATIC_PHYSICAL_RETROCAUSALITY_CLAIM",
        "fail_open": False,
    }


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        package = load_json_strict(args.package)
        index = load_json_strict(args.store_index)
        if not isinstance(package, dict) or not isinstance(index, dict):
            raise CanonicalizationError("package and evidence-store index must be JSON objects")
        resolver = EvidenceResolverV02(args.store_root, index)
        result = verify_replay_manifest(package, resolver)
    except (CanonicalizationError, EvidenceResolutionError, OSError, ValueError) as exc:
        result = invalid(str(exc))
    rendered = canonical_json_bytes(result)
    sys.stdout.buffer.write(rendered + b"\n")
    if args.output:
        Path(args.output).write_bytes(rendered)
    return 0 if result.get("terminal_grade") != "INVALIDATED_EVIDENCE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
