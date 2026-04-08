#!/usr/bin/env python3
"""
Habit Tracker - entry point.

Usage:
    python main.py <command> [options]

Run `python main.py --help` for the full command reference.
"""

import sys
from habit_tracker.cli import main

if __name__ == "__main__":
    sys.exit(main())
