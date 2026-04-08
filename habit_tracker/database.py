"""
Database setup and connection management using SQLite.
"""

import sqlite3
import os
from contextlib import contextmanager


DEFAULT_DB_PATH = os.path.join(os.path.expanduser("~"), ".habit_tracker.db")


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session(db_path: str = DEFAULT_DB_PATH):
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Create all tables if they don't exist."""
    with db_session(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS exercise_logs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT NOT NULL,
                type        TEXT NOT NULL,
                duration_min INTEGER NOT NULL,
                intensity   TEXT CHECK(intensity IN ('low','moderate','high')) NOT NULL,
                calories    INTEGER,
                notes       TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS diet_logs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT NOT NULL,
                meal        TEXT CHECK(meal IN ('breakfast','lunch','dinner','snack')) NOT NULL,
                description TEXT NOT NULL,
                calories    INTEGER,
                protein_g   REAL,
                carbs_g     REAL,
                fat_g       REAL,
                notes       TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS water_logs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT NOT NULL,
                amount_ml   INTEGER NOT NULL,
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS sleep_logs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                date            TEXT NOT NULL UNIQUE,
                bedtime         TEXT NOT NULL,
                wake_time       TEXT NOT NULL,
                duration_hours  REAL NOT NULL,
                quality         INTEGER CHECK(quality BETWEEN 1 AND 10) NOT NULL,
                notes           TEXT,
                created_at      TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS metabolic_logs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                date            TEXT NOT NULL UNIQUE,
                weight_kg       REAL,
                body_fat_pct    REAL,
                resting_hr      INTEGER,
                systolic_bp     INTEGER,
                diastolic_bp    INTEGER,
                blood_glucose   REAL,
                energy_level    INTEGER CHECK(energy_level BETWEEN 1 AND 10),
                mood            INTEGER CHECK(mood BETWEEN 1 AND 10),
                notes           TEXT,
                created_at      TEXT DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_exercise_date   ON exercise_logs(date);
            CREATE INDEX IF NOT EXISTS idx_diet_date       ON diet_logs(date);
            CREATE INDEX IF NOT EXISTS idx_water_date      ON water_logs(date);
            CREATE INDEX IF NOT EXISTS idx_sleep_date      ON sleep_logs(date);
            CREATE INDEX IF NOT EXISTS idx_metabolic_date  ON metabolic_logs(date);
        """)
