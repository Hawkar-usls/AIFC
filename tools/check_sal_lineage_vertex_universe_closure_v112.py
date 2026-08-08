#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference/verifier"))

from sal_lineage_vertex_universe_closure_checker_v112 import main

if __name__ == "__main__":
    main()
