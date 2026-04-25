"""
Core tracker: CRUD operations for all habit categories.
"""

from typing import List, Optional
from .database import db_session, DEFAULT_DB_PATH
from .models import ExerciseLog, DietLog, WaterLog, SleepLog, MetabolicLog


class HabitTracker:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path

    # ------------------------------------------------------------------ #
    #  Exercise                                                            #
    # ------------------------------------------------------------------ #

    def log_exercise(self, log: ExerciseLog) -> int:
        log.validate()
        with db_session(self.db_path) as conn:
            cur = conn.execute(
                """INSERT INTO exercise_logs
                   (date, type, duration_min, intensity, calories, notes)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (log.date, log.type, log.duration_min, log.intensity,
                 log.calories, log.notes),
            )
            return cur.lastrowid

    def get_exercise(self, date: str) -> List[ExerciseLog]:
        with db_session(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM exercise_logs WHERE date = ? ORDER BY id", (date,)
            ).fetchall()
        return [_row_to_exercise(r) for r in rows]

    def get_exercise_range(self, start: str, end: str) -> List[ExerciseLog]:
        with db_session(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM exercise_logs WHERE date BETWEEN ? AND ? ORDER BY date, id",
                (start, end),
            ).fetchall()
        return [_row_to_exercise(r) for r in rows]

    def delete_exercise(self, log_id: int) -> bool:
        with db_session(self.db_path) as conn:
            cur = conn.execute("DELETE FROM exercise_logs WHERE id = ?", (log_id,))
            return cur.rowcount > 0

    # ------------------------------------------------------------------ #
    #  Diet                                                                #
    # ------------------------------------------------------------------ #

    def log_diet(self, log: DietLog) -> int:
        log.validate()
        with db_session(self.db_path) as conn:
            cur = conn.execute(
                """INSERT INTO diet_logs
                   (date, meal, description, calories, protein_g, carbs_g, fat_g, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (log.date, log.meal, log.description, log.calories,
                 log.protein_g, log.carbs_g, log.fat_g, log.notes),
            )
            return cur.lastrowid

    def get_diet(self, date: str) -> List[DietLog]:
        with db_session(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM diet_logs WHERE date = ? ORDER BY id", (date,)
            ).fetchall()
        return [_row_to_diet(r) for r in rows]

    def get_diet_range(self, start: str, end: str) -> List[DietLog]:
        with db_session(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM diet_logs WHERE date BETWEEN ? AND ? ORDER BY date, id",
                (start, end),
            ).fetchall()
        return [_row_to_diet(r) for r in rows]

    def delete_diet(self, log_id: int) -> bool:
        with db_session(self.db_path) as conn:
            cur = conn.execute("DELETE FROM diet_logs WHERE id = ?", (log_id,))
            return cur.rowcount > 0

    # ------------------------------------------------------------------ #
    #  Water                                                               #
    # ------------------------------------------------------------------ #

    def log_water(self, log: WaterLog) -> int:
        log.validate()
        with db_session(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO water_logs (date, amount_ml) VALUES (?, ?)",
                (log.date, log.amount_ml),
            )
            return cur.lastrowid

    def get_water_total(self, date: str) -> int:
        """Returns total ml consumed on a given date."""
        with db_session(self.db_path) as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(amount_ml), 0) FROM water_logs WHERE date = ?",
                (date,),
            ).fetchone()
        return int(row[0])

    def get_water_range(self, start: str, end: str) -> dict:
        """Returns {date: total_ml} for the date range."""
        with db_session(self.db_path) as conn:
            rows = conn.execute(
                """SELECT date, SUM(amount_ml) as total
                   FROM water_logs WHERE date BETWEEN ? AND ?
                   GROUP BY date ORDER BY date""",
                (start, end),
            ).fetchall()
        return {r["date"]: r["total"] for r in rows}

    # ------------------------------------------------------------------ #
    #  Sleep                                                               #
    # ------------------------------------------------------------------ #

    def log_sleep(self, log: SleepLog) -> int:
        log.validate()
        with db_session(self.db_path) as conn:
            cur = conn.execute(
                """INSERT INTO sleep_logs
                   (date, bedtime, wake_time, duration_hours, quality, notes)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(date) DO UPDATE SET
                     bedtime=excluded.bedtime,
                     wake_time=excluded.wake_time,
                     duration_hours=excluded.duration_hours,
                     quality=excluded.quality,
                     notes=excluded.notes""",
                (log.date, log.bedtime, log.wake_time,
                 log.duration_hours, log.quality, log.notes),
            )
            return cur.lastrowid

    def get_sleep(self, date: str) -> Optional[SleepLog]:
        with db_session(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM sleep_logs WHERE date = ?", (date,)
            ).fetchone()
        return _row_to_sleep(row) if row else None

    def get_sleep_range(self, start: str, end: str) -> List[SleepLog]:
        with db_session(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM sleep_logs WHERE date BETWEEN ? AND ? ORDER BY date",
                (start, end),
            ).fetchall()
        return [_row_to_sleep(r) for r in rows]

    # ------------------------------------------------------------------ #
    #  Metabolic                                                           #
    # ------------------------------------------------------------------ #

    def log_metabolic(self, log: MetabolicLog) -> int:
        log.validate()
        with db_session(self.db_path) as conn:
            cur = conn.execute(
                """INSERT INTO metabolic_logs
                   (date, weight_kg, body_fat_pct, resting_hr,
                    systolic_bp, diastolic_bp, blood_glucose,
                    energy_level, mood, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(date) DO UPDATE SET
                     weight_kg=excluded.weight_kg,
                     body_fat_pct=excluded.body_fat_pct,
                     resting_hr=excluded.resting_hr,
                     systolic_bp=excluded.systolic_bp,
                     diastolic_bp=excluded.diastolic_bp,
                     blood_glucose=excluded.blood_glucose,
                     energy_level=excluded.energy_level,
                     mood=excluded.mood,
                     notes=excluded.notes""",
                (log.date, log.weight_kg, log.body_fat_pct, log.resting_hr,
                 log.systolic_bp, log.diastolic_bp, log.blood_glucose,
                 log.energy_level, log.mood, log.notes),
            )
            return cur.lastrowid

    def get_metabolic(self, date: str) -> Optional[MetabolicLog]:
        with db_session(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM metabolic_logs WHERE date = ?", (date,)
            ).fetchone()
        return _row_to_metabolic(row) if row else None

    def get_metabolic_range(self, start: str, end: str) -> List[MetabolicLog]:
        with db_session(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM metabolic_logs WHERE date BETWEEN ? AND ? ORDER BY date",
                (start, end),
            ).fetchall()
        return [_row_to_metabolic(r) for r in rows]


# ------------------------------------------------------------------ #
#  Row → Model helpers                                                #
# ------------------------------------------------------------------ #

def _row_to_exercise(r) -> ExerciseLog:
    return ExerciseLog(
        id=r["id"], date=r["date"], type=r["type"],
        duration_min=r["duration_min"], intensity=r["intensity"],
        calories=r["calories"], notes=r["notes"],
    )


def _row_to_diet(r) -> DietLog:
    return DietLog(
        id=r["id"], date=r["date"], meal=r["meal"],
        description=r["description"], calories=r["calories"],
        protein_g=r["protein_g"], carbs_g=r["carbs_g"],
        fat_g=r["fat_g"], notes=r["notes"],
    )


def _row_to_sleep(r) -> SleepLog:
    return SleepLog(
        id=r["id"], date=r["date"], bedtime=r["bedtime"],
        wake_time=r["wake_time"], duration_hours=r["duration_hours"],
        quality=r["quality"], notes=r["notes"],
    )


def _row_to_metabolic(r) -> MetabolicLog:
    return MetabolicLog(
        id=r["id"], date=r["date"], weight_kg=r["weight_kg"],
        body_fat_pct=r["body_fat_pct"], resting_hr=r["resting_hr"],
        systolic_bp=r["systolic_bp"], diastolic_bp=r["diastolic_bp"],
        blood_glucose=r["blood_glucose"], energy_level=r["energy_level"],
        mood=r["mood"], notes=r["notes"],
    )
