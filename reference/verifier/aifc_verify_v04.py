#!/usr/bin/env python3
"""AIFC Verifier A standalone replay CLI v0.4 with explicit exit taxonomy."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from canonical import CanonicalizationError, canonical_json_bytes, load_json_strict
from full_admission_v03 import verify_replay_manifest
from resolver import EvidenceResolutionError
from resolver_v02 import EvidenceResolverV02
from schema_runtime import validate_protocol_object

ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_PATH = ROOT / "conformance" / "CLI-EXIT-TAXONOMY-v1.json"


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="aifc-verify-v04",
        description=(
            "Resolve exact evidence bytes, enforce runtime Draft 2020-12 schemas, "
            "replay current pre-crypto AIFC semantics, and return a nonzero process "
            "status for NOT_ADMITTED or STRUCTURAL_MATCH_ONLY outcomes."
        ),
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
        "verifier_version": "0.4.0-environment-self-audit",
        "evidence_bundle_hash": "0" * 64,
        "gate_results": {"CLI_INPUT": "FAIL"},
        "exact_match": False,
        "terminal_grade": "INVALIDATED_EVIDENCE",
        "failure_codes": [f"CLI_INPUT_REJECTED:{detail}"],
        "physical_interpretation": "NO_AUTOMATIC_PHYSICAL_RETROCAUSALITY_CLAIM",
        "fail_open": False,
    }


def load_exit_taxonomy() -> dict:
    taxonomy = load_json_strict(TAXONOMY_PATH)
    if not isinstance(taxonomy, dict):
        raise CanonicalizationError("CLI exit taxonomy must be a JSON object")
    validate_protocol_object(taxonomy, "AIFC/cli-exit-taxonomy/v1")
    return taxonomy


def exit_code_for_result(result: dict, taxonomy: dict | None = None) -> int:
    taxonomy = taxonomy or load_exit_taxonomy()
    grade = result.get("terminal_grade")
    mapping = taxonomy["terminal_grade_exit_codes"]
    if grade not in mapping:
        raise CanonicalizationError(f"terminal grade missing from CLI taxonomy: {grade!r}")
    return int(mapping[grade])


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        taxonomy = load_exit_taxonomy()
        package = load_json_strict(args.package)
        index = load_json_strict(args.store_index)
        if not isinstance(package, dict) or not isinstance(index, dict):
            raise CanonicalizationError("package and evidence-store index must be JSON objects")
        resolver = EvidenceResolverV02(args.store_root, index)
        result = verify_replay_manifest(package, resolver)
    except (CanonicalizationError, EvidenceResolutionError, OSError, ValueError) as exc:
        taxonomy = load_exit_taxonomy()
        result = invalid(str(exc))

    rendered = canonical_json_bytes(result)
    sys.stdout.buffer.write(rendered + b"\n")
    if args.output:
        Path(args.output).write_bytes(rendered)
    return exit_code_for_result(result, taxonomy)


if __name__ == "__main__":
    raise SystemExit(main())
