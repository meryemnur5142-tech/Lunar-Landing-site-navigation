"""
pytest configuration for LUNA-AI.

Inserts the project root directory into sys.path so that all first-party
packages (domain, mission_intelligence, data-platform, etc.) are importable
without an editable install, using the standard ``from package.module import …``
syntax.

This file is discovered automatically by pytest because it lives at the
project root (the same directory as pytest.ini).
"""

import sys
from pathlib import Path

# Project root = the directory that contains this conftest.py
_PROJECT_ROOT = Path(__file__).resolve().parent

if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
