#!/usr/bin/env python3
"""Compatibility entry point for the former regex-based page splitter.

The canonical compiler reads original sources, never the already-generated
Jekyll artifact. Use site_core.py directly for all new builds.
"""
from site_core import main

if __name__ == '__main__':
    main()
