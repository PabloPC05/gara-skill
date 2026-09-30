#!/usr/bin/env python3
"""Resolve the bundled runtime and assets relative to this skill."""

import sys
from pathlib import Path

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here if (here / "gara_workflow").is_dir() else here.parents[2]))
from gara_workflow.pdf import main

if __name__ == "__main__":
    arguments = sys.argv[1:]
    if "--assets" not in arguments:
        arguments += ["--assets", str(here.parent / "assets")]
    raise SystemExit(main(arguments))
