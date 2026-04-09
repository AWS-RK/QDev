#!/usr/bin/env python3
"""
Mobile entry point for Habit Tracker.

Launches the interactive menu-driven UI — no flags needed.
Designed for Termux (Android) and a-Shell (iPhone).

Usage:
    python mobile.py
"""

import sys
import argparse
from habit_tracker.database import DEFAULT_DB_PATH
from habit_tracker.interactive import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Habit Tracker — mobile interactive mode.")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, metavar="PATH",
                        help="Path to the SQLite database file.")
    args = parser.parse_args()
    run(db_path=args.db)
