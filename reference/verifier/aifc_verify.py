#!/usr/bin/env python3
"""Command-line entry point for AIFC Verifier A frontier v0.1.

This CLI exposes only implemented frontier checks. It intentionally cannot emit
IMPLEMENTATION_A_PASS or any physical interpretation.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

from frontier import (
    experiment_genesis_hash,
    validate_candidate_generation_profile,
    validate_canonical_rational,
    validate_registry_transition,
    validate_registry_transition_set,
    validate_release_manifest_structure,
    validate_target_derivation_bindings,
)


def load(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def emit(result, *, extra=None) -> int:
    payload = {
        "schema": "AIFC/verifier-a-frontier-result/v0.1",
        "verifier_id": "AIFC-Verifier-A",
        "verifier_version": "0.1.0-frontier",
        "check": asdict(result),
        "implementation_a_pass": "NOT_ESTABLISHED",
        "aifc_v1_frozen": False,
        "physical_interpretation": "NO_AUTOMATIC_PHYSICAL_RETROCAUSALITY_CLAIM",
    }
    if extra is not None:
        payload["extra"] = extra
    print(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    return 0 if result.ok else 2


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="AIFC Verifier A frontier core v0.1")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("genesis", help="compute deterministic experiment genesis predecessor")
    p.add_argument("experiment_id")

    p = sub.add_parser("rational", help="validate canonical exact-rational probability bound")
    p.add_argument("json_file")

    p = sub.add_parser("candidate", help="validate candidate-generation provenance frontier")
    p.add_argument("json_file")

    p = sub.add_parser("target-bindings", help="validate frozen target-derivation bindings")
    p.add_argument("profile_hash")
    p.add_argument("profile")
    p.add_argument("pre_return")
    p.add_argument("entropy_profile")
    p.add_argument("target_evidence")

    p = sub.add_parser("registry-transition", help="validate one structural joint registry transition")
    p.add_argument("json_file")

    p = sub.add_parser("registry-transition-set", help="validate transition set and reject configuration forks")
    p.add_argument("json_file", help="JSON array of transition certificates")

    p = sub.add_parser("release-manifest", help="validate structural proof-carrying release manifest")
    p.add_argument("manifest")
    p.add_argument("release_gate")

    args = parser.parse_args(argv)

    if args.command == "genesis":
        value = experiment_genesis_hash(args.experiment_id)
        print(json.dumps({
            "schema": "AIFC/verifier-a-frontier-genesis/v0.1",
            "experiment_id": args.experiment_id,
            "previous_event_hash": value,
            "implementation_a_pass": "NOT_ESTABLISHED",
            "aifc_v1_frozen": False,
        }, sort_keys=True, separators=(",", ":")))
        return 0

    if args.command == "rational":
        result, value = validate_canonical_rational(load(args.json_file))
        extra = None if value is None else {"numerator": value.numerator, "denominator": value.denominator}
        return emit(result, extra=extra)

    if args.command == "candidate":
        return emit(validate_candidate_generation_profile(load(args.json_file)))

    if args.command == "target-bindings":
        return emit(validate_target_derivation_bindings(
            args.profile_hash,
            load(args.profile),
            load(args.pre_return),
            load(args.entropy_profile),
            load(args.target_evidence),
        ))

    if args.command == "registry-transition":
        return emit(validate_registry_transition(load(args.json_file)))

    if args.command == "registry-transition-set":
        obj = load(args.json_file)
        if not isinstance(obj, list):
            raise SystemExit("registry-transition-set input must be a JSON array")
        return emit(validate_registry_transition_set(obj))

    if args.command == "release-manifest":
        gate = load(args.release_gate)
        required = [row["id"] for row in gate.get("required_checks", []) if row.get("required") is True]
        return emit(validate_release_manifest_structure(load(args.manifest), required))

    raise AssertionError("unreachable")


if __name__ == "__main__":
    sys.exit(main())
