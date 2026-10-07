#!/usr/bin/env python3
"""Genera el PDF con los assets de esta skill."""

import sys
from pathlib import Path

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here))
from pdf import main

if __name__ == "__main__":
    arguments = sys.argv[1:]
    if "--assets" not in arguments:
        arguments += ["--assets", str(here.parent / "assets")]
    raise SystemExit(main(arguments))
