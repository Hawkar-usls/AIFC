#!/usr/bin/env python3
"""Convenience wrapper for the attested SAL v1.8 verifier checker."""
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT / "reference" / "verifier" / "sal_semantic_abstraction_closure_checker_v18.py"), run_name="__main__")
