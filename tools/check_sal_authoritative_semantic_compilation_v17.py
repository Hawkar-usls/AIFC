#!/usr/bin/env python3
"""Convenience wrapper for the attested SAL v1.7 checker implementation."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "reference" / "verifier"
sys.path.insert(0, str(VERIFIER))

from sal_authoritative_semantic_compilation_checker_v17 import main  # noqa: E402
from scientific_assurance_lineage_v17 import ScientificAssuranceLineageV17Error  # noqa: E402


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ScientificAssuranceLineageV17Error as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(2)
