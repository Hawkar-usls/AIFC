#!/usr/bin/env python3
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).resolve().parents[1]/"reference/verifier/sal_lineage_edge_universe_checker_v111u.py"),run_name="__main__")
