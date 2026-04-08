"""
Unit tests for the Habit Tracker application.
"""

import os
import tempfile
import unittest

from habit_tracker.database import initialize_db
from habit_tracker.models import (
    ExerciseLog, DietLog, WaterLog, SleepLog, MetabolicLog, today
)
from habit_tracker.tracker import HabitTracker


class TestBase(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        initialize_db(self.db_path)
        self.tracker = HabitTracker(self.db_path)

    def tearDown(self):
        os.unlink(self.db_path)


# ------------------------------------------------------------------ #
#  Exercise                                                            #
# ------------------------------------------------------------------ #

class TestExercise(TestBase):
    def _make_log(self, **kw):
        defaults = dict(date="2024-03-01", type="Running",
                        duration_min=30, intensity="moderate")
        defaults.update(kw)
        return ExerciseLog(**defaults)

    def test_log_and_retrieve(self):
        log = self._make_log(calories=300, notes="Morning run")
        log_id = self.tracker.log_exercise(log)
        self.assertIsInstance(log_id, int)
        result = self.tracker.get_exercise("2024-03-01")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].type, "Running")
        self.assertEqual(result[0].duration_min, 30)
        self.assertEqual(result[0].calories, 300)

    def test_multiple_sessions_same_day(self):
        self.tracker.log_exercise(self._make_log(type="Running", duration_min=30))
        self.tracker.log_exercise(self._make_log(type="Cycling", duration_min=45))
        result = self.tracker.get_exercise("2024-03-01")
        self.assertEqual(len(result), 2)

    def test_range_query(self):
        self.tracker.log_exercise(self._make_log(date="2024-03-01"))
        self.tracker.log_exercise(self._make_log(date="2024-03-03"))
        self.tracker.log_exercise(self._make_log(date="2024-03-10"))
        result = self.tracker.get_exercise_range("2024-03-01", "2024-03-05")
        self.assertEqual(len(result), 2)

    def test_delete(self):
        log_id = self.tracker.log_exercise(self._make_log())
        self.assertTrue(self.tracker.delete_exercise(log_id))
        self.assertEqual(self.tracker.get_exercise("2024-03-01"), [])

    def test_invalid_intensity(self):
        with self.assertRaises(ValueError):
            self._make_log(intensity="extreme").validate()

    def test_invalid_duration(self):
        with self.assertRaises(ValueError):
            self._make_log(duration_min=0).validate()

    def test_duration_hours_property(self):
        log = self._make_log(duration_min=90)
        self.assertAlmostEqual(log.duration_hours, 1.5)


# ------------------------------------------------------------------ #
#  Diet                                                                #
# ------------------------------------------------------------------ #

class TestDiet(TestBase):
    def _make_log(self, **kw):
        defaults = dict(date="2024-03-01", meal="lunch",
                        description="Chicken salad", calories=450,
                        protein_g=35, carbs_g=20, fat_g=15)
        defaults.update(kw)
        return DietLog(**defaults)

    def test_log_and_retrieve(self):
        log_id = self.tracker.log_diet(self._make_log())
        self.assertIsInstance(log_id, int)
        result = self.tracker.get_diet("2024-03-01")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].meal, "lunch")

    def test_multiple_meals(self):
        for meal in ("breakfast", "lunch", "dinner"):
            self.tracker.log_diet(self._make_log(meal=meal))
        result = self.tracker.get_diet("2024-03-01")
        self.assertEqual(len(result), 3)

    def test_invalid_meal(self):
        with self.assertRaises(ValueError):
            self._make_log(meal="brunch").validate()

    def test_empty_description(self):
        with self.assertRaises(ValueError):
            self._make_log(description="  ").validate()

    def test_delete(self):
        log_id = self.tracker.log_diet(self._make_log())
        self.assertTrue(self.tracker.delete_diet(log_id))
        self.assertEqual(self.tracker.get_diet("2024-03-01"), [])


# ------------------------------------------------------------------ #
#  Water                                                               #
# ------------------------------------------------------------------ #

class TestWater(TestBase):
    def test_log_and_total(self):
        self.tracker.log_water(WaterLog(date="2024-03-01", amount_ml=500))
        self.tracker.log_water(WaterLog(date="2024-03-01", amount_ml=750))
        total = self.tracker.get_water_total("2024-03-01")
        self.assertEqual(total, 1250)

    def test_empty_date_returns_zero(self):
        total = self.tracker.get_water_total("2024-01-01")
        self.assertEqual(total, 0)

    def test_invalid_amount(self):
        with self.assertRaises(ValueError):
            WaterLog(date="2024-03-01", amount_ml=0).validate()

    def test_amount_oz_property(self):
        w = WaterLog(date="2024-03-01", amount_ml=296)
        self.assertAlmostEqual(w.amount_oz, 10.0, places=0)

    def test_range_query(self):
        self.tracker.log_water(WaterLog(date="2024-03-01", amount_ml=1000))
        self.tracker.log_water(WaterLog(date="2024-03-02", amount_ml=1500))
        self.tracker.log_water(WaterLog(date="2024-03-05", amount_ml=2000))
        result = self.tracker.get_water_range("2024-03-01", "2024-03-03")
        self.assertEqual(len(result), 2)
        self.assertEqual(result["2024-03-01"], 1000)


# ------------------------------------------------------------------ #
#  Sleep                                                               #
# ------------------------------------------------------------------ #

class TestSleep(TestBase):
    def _make_log(self, **kw):
        defaults = dict(date="2024-03-01", bedtime="22:30",
                        wake_time="06:30", duration_hours=8.0, quality=7)
        defaults.update(kw)
        return SleepLog(**defaults)

    def test_log_and_retrieve(self):
        log_id = self.tracker.log_sleep(self._make_log())
        self.assertIsInstance(log_id, int)
        result = self.tracker.get_sleep("2024-03-01")
        self.assertIsNotNone(result)
        self.assertEqual(result.duration_hours, 8.0)
        self.assertEqual(result.quality, 7)

    def test_upsert_same_date(self):
        self.tracker.log_sleep(self._make_log(quality=5))
        self.tracker.log_sleep(self._make_log(quality=8))
        result = self.tracker.get_sleep("2024-03-01")
        self.assertEqual(result.quality, 8)

    def test_not_found_returns_none(self):
        result = self.tracker.get_sleep("2000-01-01")
        self.assertIsNone(result)

    def test_invalid_quality(self):
        with self.assertRaises(ValueError):
            self._make_log(quality=11).validate()

    def test_range_query(self):
        self.tracker.log_sleep(self._make_log(date="2024-03-01"))
        self.tracker.log_sleep(self._make_log(date="2024-03-02"))
        self.tracker.log_sleep(self._make_log(date="2024-03-10"))
        result = self.tracker.get_sleep_range("2024-03-01", "2024-03-05")
        self.assertEqual(len(result), 2)


# ------------------------------------------------------------------ #
#  Metabolic                                                           #
# ------------------------------------------------------------------ #

class TestMetabolic(TestBase):
    def _make_log(self, **kw):
        defaults = dict(date="2024-03-01", weight_kg=75.5, resting_hr=60,
                        systolic_bp=120, diastolic_bp=80, energy_level=7, mood=8)
        defaults.update(kw)
        return MetabolicLog(**defaults)

    def test_log_and_retrieve(self):
        log_id = self.tracker.log_metabolic(self._make_log())
        self.assertIsInstance(log_id, int)
        result = self.tracker.get_metabolic("2024-03-01")
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result.weight_kg, 75.5)
        self.assertEqual(result.resting_hr, 60)

    def test_upsert_same_date(self):
        self.tracker.log_metabolic(self._make_log(weight_kg=75.5))
        self.tracker.log_metabolic(self._make_log(weight_kg=74.8))
        result = self.tracker.get_metabolic("2024-03-01")
        self.assertAlmostEqual(result.weight_kg, 74.8)

    def test_blood_pressure_property(self):
        log = self._make_log(systolic_bp=120, diastolic_bp=80)
        self.assertEqual(log.blood_pressure, "120/80")

    def test_blood_pressure_none(self):
        log = MetabolicLog(date="2024-03-01")
        self.assertIsNone(log.blood_pressure)

    def test_invalid_energy_level(self):
        with self.assertRaises(ValueError):
            self._make_log(energy_level=0).validate()

    def test_invalid_mood(self):
        with self.assertRaises(ValueError):
            self._make_log(mood=11).validate()

    def test_invalid_body_fat(self):
        with self.assertRaises(ValueError):
            self._make_log(body_fat_pct=105).validate()

    def test_not_found_returns_none(self):
        result = self.tracker.get_metabolic("2000-01-01")
        self.assertIsNone(result)

    def test_range_query(self):
        self.tracker.log_metabolic(self._make_log(date="2024-03-01"))
        self.tracker.log_metabolic(self._make_log(date="2024-03-03"))
        self.tracker.log_metabolic(self._make_log(date="2024-03-10"))
        result = self.tracker.get_metabolic_range("2024-03-01", "2024-03-05")
        self.assertEqual(len(result), 2)


# ------------------------------------------------------------------ #
#  Model validation                                                    #
# ------------------------------------------------------------------ #

class TestModelValidation(unittest.TestCase):
    def test_invalid_date_format(self):
        from habit_tracker.models import _validate_date
        with self.assertRaises(ValueError):
            _validate_date("01/03/2024")
        with self.assertRaises(ValueError):
            _validate_date("not-a-date")

    def test_valid_date(self):
        from habit_tracker.models import _validate_date
        _validate_date("2024-03-01")  # should not raise


if __name__ == "__main__":
    unittest.main()
