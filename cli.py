#!/usr/bin/env python3
"""CLI entry point for D6 Browser Forensics."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "firmware"))
from browser import main

if __name__ == "__main__":
    main()
