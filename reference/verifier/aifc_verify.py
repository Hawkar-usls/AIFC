#!/usr/bin/env python3
"""AIFC Verifier A standalone evidence replay CLI v0.2."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from canonical import CanonicalizationError, canonical_json_bytes, load_json_strict
from replay import verify_replay_manifest
from resolver import EvidenceResolutionError, EvidenceResolver


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aifc-verify",
        description=(
            "Replay an AIFC content-addressed evidence package. The verifier resolves "
            "exact bytes and recomputes protocol identities instead of trusting producer hashes."
        ),
    )
    parser.add_argument("--package", required=True, help="AIFC/replay-package/v0.2 JSON")
    parser.add_argument("--store-index", required=True, help="AIFC/evidence-store-index/v1 JSON")
    parser.add_argument("--store-root", required=True, help="Root containing exact evidence files")
    parser.add_argument("--output", help="Optional path for canonical verifier-result JSON")
    return parser


def cli_failure(detail: str) -> dict:
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
    args = build_parser().parse_args(argv)
    try:
        package = load_json_strict(args.package)
        index = load_json_strict(args.store_index)
        if not isinstance(package, dict):
            raise CanonicalizationError("replay package must be a JSON object")
        if not isinstance(index, dict):
            raise CanonicalizationError("evidence-store index must be a JSON object")
        resolver = EvidenceResolver(args.store_root, index)
        result = verify_replay_manifest(package, resolver)
    except (CanonicalizationError, EvidenceResolutionError, OSError, ValueError) as exc:
        result = cli_failure(str(exc))

    rendered = canonical_json_bytes(result)
    sys.stdout.buffer.write(rendered + b"\n")
    if args.output:
        Path(args.output).write_bytes(rendered)
    return 0 if result.get("terminal_grade") != "INVALIDATED_EVIDENCE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
