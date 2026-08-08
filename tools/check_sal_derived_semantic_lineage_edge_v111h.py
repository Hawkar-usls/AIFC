#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT/"reference/verifier/sal_derived_semantic_lineage_edge_checker_v111h.py"),run_name="__main__")
