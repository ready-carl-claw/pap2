#!/usr/bin/env python3
"""Compatibility wrapper for pap2.

This skill's canonical helper is scripts/pap2.py.
This wrapper exists only to avoid confusion if an older reference accidentally calls pap.py.
"""

from pathlib import Path
import runpy

if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).with_name("pap2.py")), run_name="__main__")
