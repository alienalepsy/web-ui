#!/usr/bin/env python3
"""
TESL Tracker - Application Launcher

Quick launcher script for the TESL Balance Tracker application.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tesl_tracker.app import main

if __name__ == "__main__":
    main()
