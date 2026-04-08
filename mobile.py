#!/usr/bin/env python3
"""
Mobile entry point for Habit Tracker.

Launches the interactive menu-driven UI — no flags needed.
Designed for Termux (Android) and a-Shell (iPhone).

Usage:
    python mobile.py
"""

import sys
from habit_tracker.interactive import run

if __name__ == "__main__":
    run()
