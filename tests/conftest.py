"""Pytest configuration for moonraker tests."""

import os
import sys

# Force headless backend for matplotlib in tests.
os.environ.setdefault("MPLBACKEND", "Agg")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
for _path in (SRC,):
    if _path not in sys.path:
        sys.path.insert(0, _path)
