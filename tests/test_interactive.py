"""
Tests for the interactive mobile UI module.
Focuses on the pure-logic helpers and menu flows that can be exercised
without a real TTY by patching builtins.input.
"""

import os
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from habit_tracker.database import initialize_db
from habit_tracker.models import today as _today
from habit_tracker.tracker import HabitTracker
from habit_tracker import interactive as ui


class TestPickDate(unittest.TestCase):
    def test_today(self):
        with patch("builtins.input", return_value="1"):
            result = ui._pick_date()
        self.assertEqual(result, _today())

    def test_yesterday(self):
        with patch("builtins.input", return_value="2"):
            result = ui._pick_date()
        expected = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        self.assertEqual(result, expected)

    def test_custom_valid_date(self):
        inputs = iter(["3", "2024-06-15"])
        with patch("builtins.input", side_effect=inputs):
            result = ui._pick_date()
        self.assertEqual(result, "2024-06-15")

    def test_custom_invalid_then_valid(self):
        inputs = iter(["3", "not-a-date", "2024-06-15"])
        with patch("builtins.input", side_effect=inputs):
            result = ui._pick_date()
        self.assertEqual(result, "2024-06-15")


class TestPrompt(unittest.TestCase):
    def test_uses_default_on_empty(self):
        with patch("builtins.input", return_value=""):
            result = ui._prompt("Label", default="hello")
        self.assertEqual(result, "hello")

    def test_casts_to_int(self):
        with patch("builtins.input", return_value="42"):
            result = ui._prompt("Label", cast=int)
        self.assertEqual(result, 42)

    def test_retries_on_bad_cast(self):
        inputs = iter(["abc", "7"])
        with patch("builtins.input", side_effect=inputs):
            result = ui._prompt("Label", cast=int)
        self.assertEqual(result, 7)

    def test_required_field_retries_on_empty(self):
        inputs = iter(["", "hello"])
        with patch("builtins.input", side_effect=inputs):
            result = ui._prompt("Label")
        self.assertEqual(result, "hello")


class TestChoose(unittest.TestCase):
    def test_valid_choice(self):
        with patch("builtins.input", return_value="2"):
            result = ui._choose(["A", "B", "C"])
        self.assertEqual(result, 1)  # 0-based

    def test_out_of_range_then_valid(self):
        inputs = iter(["0", "5", "3"])
        with patch("builtins.input", side_effect=inputs):
            result = ui._choose(["A", "B", "C"])
        self.assertEqual(result, 2)

    def test_non_numeric_then_valid(self):
        inputs = iter(["x", "1"])
        with patch("builtins.input", side_effect=inputs):
            result = ui._choose(["A", "B"])
        self.assertEqual(result, 0)


class TestConfirm(unittest.TestCase):
    def test_yes(self):
        for ans in ("y", "Y", "yes", "YES"):
            with patch("builtins.input", return_value=ans):
                self.assertTrue(ui._confirm())

    def test_no(self):
        for ans in ("n", "N", "no", ""):
            with patch("builtins.input", return_value=ans):
                self.assertFalse(ui._confirm())


class TestExerciseFlow(unittest.TestCase):
    def setUp(self):
        fd, self.db = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        initialize_db(self.db)
        self.tracker = HabitTracker(self.db)

    def tearDown(self):
        os.unlink(self.db)

    def test_log_exercise(self):
        # Simulate: today, type=Running, duration=30, intensity=moderate(2), no cal, no notes, pause
        inputs = iter(["1",       # date: today
                       "Running", # type
                       "30",      # duration
                       "2",       # intensity: moderate
                       "",        # calories: skip
                       "",        # notes: skip
                       ""])       # pause
        with patch("builtins.input", side_effect=inputs):
            ui._exercise_log(self.tracker)

        logs = self.tracker.get_exercise(_today())
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].type, "Running")
        self.assertEqual(logs[0].duration_min, 30)
        self.assertEqual(logs[0].intensity, "moderate")
        self.assertIsNone(logs[0].calories)

    def test_log_exercise_with_calories(self):
        inputs = iter(["1", "Cycling", "45", "3", "350", "", ""])
        with patch("builtins.input", side_effect=inputs):
            ui._exercise_log(self.tracker)

        logs = self.tracker.get_exercise(_today())
        self.assertEqual(logs[0].calories, 350)

    def test_view_exercise_no_data(self):
        inputs = iter(["1", ""])  # today, then pause
        with patch("builtins.input", side_effect=inputs):
            # Should not raise even with no data
            ui._exercise_view(self.tracker)


class TestDietFlow(unittest.TestCase):
    def setUp(self):
        fd, self.db = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        initialize_db(self.db)
        self.tracker = HabitTracker(self.db)

    def tearDown(self):
        os.unlink(self.db)

    def test_log_diet_minimal(self):
        # date=today, meal=lunch(2), desc, no macros, pause
        inputs = iter(["1", "2", "Chicken salad", "", "", "", "", ""])
        with patch("builtins.input", side_effect=inputs):
            ui._diet_log(self.tracker)

        logs = self.tracker.get_diet(_today())
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].meal, "lunch")
        self.assertEqual(logs[0].description, "Chicken salad")

    def test_log_diet_with_macros(self):
        inputs = iter(["1", "1", "Oatmeal", "350", "10", "55", "8", ""])
        with patch("builtins.input", side_effect=inputs):
            ui._diet_log(self.tracker)

        logs = self.tracker.get_diet(_today())
        self.assertEqual(logs[0].calories, 350)
        self.assertAlmostEqual(logs[0].protein_g, 10)
        self.assertAlmostEqual(logs[0].carbs_g, 55)
        self.assertAlmostEqual(logs[0].fat_g, 8)


class TestWaterFlow(unittest.TestCase):
    def setUp(self):
        fd, self.db = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        initialize_db(self.db)
        self.tracker = HabitTracker(self.db)

    def tearDown(self):
        os.unlink(self.db)

    def test_log_preset_amount(self):
        # date=today, choose "Large glass (500 ml)" = option 3, then pause
        inputs = iter(["1", "3", ""])
        with patch("builtins.input", side_effect=inputs):
            ui._water_log(self.tracker)
        self.assertEqual(self.tracker.get_water_total(_today()), 500)

    def test_log_custom_amount(self):
        # date=today, choose "Custom amount" = option 6, enter 650, then pause
        inputs = iter(["1", "6", "650", ""])
        with patch("builtins.input", side_effect=inputs):
            ui._water_log(self.tracker)
        self.assertEqual(self.tracker.get_water_total(_today()), 650)


class TestSleepFlow(unittest.TestCase):
    def setUp(self):
        fd, self.db = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        initialize_db(self.db)
        self.tracker = HabitTracker(self.db)

    def tearDown(self):
        os.unlink(self.db)

    def test_log_sleep_auto_duration(self):
        # date=today, bedtime=22:30, wake=06:30, accept auto duration(8.0), quality=8, pause
        inputs = iter(["1", "22:30", "06:30", "", "8", ""])
        with patch("builtins.input", side_effect=inputs):
            ui._sleep_log(self.tracker)

        log = self.tracker.get_sleep(_today())
        self.assertIsNotNone(log)
        self.assertAlmostEqual(log.duration_hours, 8.0)
        self.assertEqual(log.quality, 8)

    def test_log_sleep_manual_duration(self):
        inputs = iter(["1", "23:00", "07:00", "7.5", "7", ""])
        with patch("builtins.input", side_effect=inputs):
            ui._sleep_log(self.tracker)

        log = self.tracker.get_sleep(_today())
        self.assertAlmostEqual(log.duration_hours, 7.5)


class TestMetabolicFlow(unittest.TestCase):
    def setUp(self):
        fd, self.db = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        initialize_db(self.db)
        self.tracker = HabitTracker(self.db)

    def tearDown(self):
        os.unlink(self.db)

    def test_log_metabolic_all_fields(self):
        inputs = iter(["1",    # today
                       "75.5", # weight
                       "18.2", # body fat
                       "58",   # resting HR
                       "118",  # systolic
                       "76",   # diastolic
                       "91.0", # glucose
                       "8",    # energy
                       "9",    # mood
                       ""])    # pause
        with patch("builtins.input", side_effect=inputs):
            ui._metabolic_log(self.tracker)

        log = self.tracker.get_metabolic(_today())
        self.assertIsNotNone(log)
        self.assertAlmostEqual(log.weight_kg, 75.5)
        self.assertEqual(log.resting_hr, 58)
        self.assertEqual(log.energy_level, 8)

    def test_log_metabolic_skipped_fields(self):
        inputs = iter(["1", "", "", "", "", "", "", "", "", ""])
        with patch("builtins.input", side_effect=inputs):
            ui._metabolic_log(self.tracker)

        log = self.tracker.get_metabolic(_today())
        self.assertIsNotNone(log)
        self.assertIsNone(log.weight_kg)
        self.assertIsNone(log.energy_level)


if __name__ == "__main__":
    unittest.main()
