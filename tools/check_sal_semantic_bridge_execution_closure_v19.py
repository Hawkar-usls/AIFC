#!/usr/bin/env python3
"""Convenience wrapper for the attested SAL v1.9 verifier checker."""
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(
    str(ROOT / "reference" / "verifier" / "sal_semantic_bridge_execution_closure_checker_v19.py"),
    run_name="__main__",
)
