#!/usr/bin/env python3
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here if (here / "gara_workflow").is_dir() else here.parents[2]))
from gara_workflow.health import main

if __name__ == "__main__":
    raise SystemExit(main())
