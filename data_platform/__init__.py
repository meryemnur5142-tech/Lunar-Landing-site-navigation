"""Importable alias for the data-platform package (hyphens are not valid Python identifiers).

The canonical source lives in ``data-platform/``.  This directory provides an
underscore-named package so it is importable when the repo root is on sys.path
(e.g. during tests or when running the dev server without ``pip install -e .``).
"""
