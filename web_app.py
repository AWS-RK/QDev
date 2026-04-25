#!/usr/bin/env python3
"""
Web entry point for Habit Tracker.

Usage:
    python web_app.py [--db PATH] [--port PORT] [--host HOST]
"""

import argparse
from habit_tracker.database import DEFAULT_DB_PATH
from habit_tracker.web import create_app

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Habit Tracker — web UI.")
    parser.add_argument("--db",   default=DEFAULT_DB_PATH, metavar="PATH")
    parser.add_argument("--port", default=5000, type=int)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    app = create_app(db_path=args.db)
    print(f"\n  Habit Tracker running at http://{args.host}:{args.port}\n")
    app.run(host=args.host, port=args.port, debug=False)
