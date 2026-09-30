#!/usr/bin/env python3
"""Run the source checkout or the self-contained helper bundled with the skill."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from gara_workflow.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
