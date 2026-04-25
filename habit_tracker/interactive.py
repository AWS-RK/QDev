"""
Interactive menu-driven interface optimised for mobile (Termux / a-Shell).
No flags or long commands — everything is driven by numbered prompts.
"""

import sys
from datetime import datetime, timedelta
from typing import Optional

from .database import initialize_db, DEFAULT_DB_PATH
from .models import ExerciseLog, DietLog, WaterLog, SleepLog, MetabolicLog, today as _today
from .tracker import HabitTracker
from .reports import DailySummary, WeeklySummary, generate_trend


# ------------------------------------------------------------------ #
#  Terminal helpers                                                    #
# ------------------------------------------------------------------ #

def _clear():
    print("\n" * 2)


def _header(title: str):
    width = 38
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def _prompt(label: str, default=None, cast=str):
    """Prompt the user, returning cast(value) or default on empty input."""
    hint = f" [{default}]" if default is not None else ""
    while True:
        raw = input(f"  {label}{hint}: ").strip()
        if raw == "" and default is not None:
            return default
        if raw == "" and default is None:
            print("  ! This field is required.")
            continue
        try:
            return cast(raw)
        except (ValueError, TypeError):
            print(f"  ! Invalid input, expected {cast.__name__}.")


def _choose(options: list, label: str = "Choice") -> int:
    """Print a numbered list and return the 0-based index chosen."""
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        raw = input(f"  {label}: ").strip()
        try:
            n = int(raw)
            if 1 <= n <= len(options):
                return n - 1
        except ValueError:
            pass
        print(f"  ! Enter a number between 1 and {len(options)}.")


def _confirm(msg: str = "Confirm?") -> bool:
    return input(f"  {msg} (y/n): ").strip().lower() in ("y", "yes")


def _pause():
    input("\n  Press Enter to continue...")


def _pick_date() -> str:
    print()
    print("  1. Today")
    print("  2. Yesterday")
    print("  3. Enter a date")
    idx = _choose(["Today", "Yesterday", "Enter a date"], "Date")
    if idx == 0:
        return _today()
    if idx == 1:
        return (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    while True:
        raw = input("  Date (YYYY-MM-DD): ").strip()
        try:
            datetime.strptime(raw, "%Y-%m-%d")
            return raw
        except ValueError:
            print("  ! Use YYYY-MM-DD format.")


# ------------------------------------------------------------------ #
#  Exercise                                                            #
# ------------------------------------------------------------------ #

def _exercise_menu(tracker: HabitTracker):
    while True:
        _clear()
        _header("Exercise")
        idx = _choose(["Log a session", "View a day", "Back"], "Choice")
        if idx == 0:
            _exercise_log(tracker)
        elif idx == 1:
            _exercise_view(tracker)
        else:
            return


def _exercise_log(tracker: HabitTracker):
    _clear()
    _header("Log Exercise")
    date = _pick_date()
    etype = _prompt("Type (e.g. Running, Cycling, Yoga)")
    duration = _prompt("Duration (minutes)", cast=int)
    print("\n  Intensity:")
    intensity = ["low", "moderate", "high"][_choose(["Low", "Moderate", "High"], "Intensity")]
    calories = _prompt("Calories burned (optional, Enter to skip)", default="", cast=str)
    calories = int(calories) if calories else None
    notes = _prompt("Notes (optional, Enter to skip)", default="", cast=str) or None

    log = ExerciseLog(date=date, type=etype, duration_min=duration,
                      intensity=intensity, calories=calories, notes=notes)
    tracker.log_exercise(log)
    print(f"\n  Saved: {duration} min of {etype} on {date}.")
    _pause()


def _exercise_view(tracker: HabitTracker):
    _clear()
    _header("View Exercise")
    date = _pick_date()
    logs = tracker.get_exercise(date)
    print()
    if not logs:
        print(f"  No exercise logged for {date}.")
    else:
        total = sum(l.duration_min for l in logs)
        for l in logs:
            cal = f"  {l.calories} kcal" if l.calories else ""
            print(f"  {l.type} | {l.duration_min} min | {l.intensity}{cal}")
        print(f"  ----")
        print(f"  Total: {total} min ({total/60:.1f} h)")
    _pause()


# ------------------------------------------------------------------ #
#  Diet                                                                #
# ------------------------------------------------------------------ #

def _diet_menu(tracker: HabitTracker):
    while True:
        _clear()
        _header("Diet")
        idx = _choose(["Log a meal", "View a day", "Back"], "Choice")
        if idx == 0:
            _diet_log(tracker)
        elif idx == 1:
            _diet_view(tracker)
        else:
            return


def _diet_log(tracker: HabitTracker):
    _clear()
    _header("Log Meal")
    date = _pick_date()
    meals = ["breakfast", "lunch", "dinner", "snack"]
    print("\n  Meal:")
    meal = meals[_choose(["Breakfast", "Lunch", "Dinner", "Snack"], "Meal")]
    desc = _prompt("What did you eat?")
    calories = _prompt("Calories (optional)", default="", cast=str)
    calories = int(calories) if calories else None
    protein = _prompt("Protein g (optional)", default="", cast=str)
    protein = float(protein) if protein else None
    carbs = _prompt("Carbs g (optional)", default="", cast=str)
    carbs = float(carbs) if carbs else None
    fat = _prompt("Fat g (optional)", default="", cast=str)
    fat = float(fat) if fat else None

    log = DietLog(date=date, meal=meal, description=desc, calories=calories,
                  protein_g=protein, carbs_g=carbs, fat_g=fat)
    tracker.log_diet(log)
    print(f"\n  Saved: {meal.capitalize()} on {date}.")
    _pause()


def _diet_view(tracker: HabitTracker):
    _clear()
    _header("View Diet")
    date = _pick_date()
    logs = tracker.get_diet(date)
    print()
    if not logs:
        print(f"  No meals logged for {date}.")
    else:
        total_cal = sum(l.calories or 0 for l in logs)
        total_p   = sum(l.protein_g or 0 for l in logs)
        total_c   = sum(l.carbs_g or 0 for l in logs)
        total_f   = sum(l.fat_g or 0 for l in logs)
        for l in logs:
            cal = f"  {l.calories} kcal" if l.calories else ""
            print(f"  {l.meal.capitalize()}: {l.description}{cal}")
        print(f"  ----")
        print(f"  {total_cal} kcal | P:{total_p:.0f}g C:{total_c:.0f}g F:{total_f:.0f}g")
    _pause()


# ------------------------------------------------------------------ #
#  Water                                                               #
# ------------------------------------------------------------------ #

def _water_menu(tracker: HabitTracker):
    while True:
        _clear()
        _header("Water")
        idx = _choose(["Log intake", "View today", "Back"], "Choice")
        if idx == 0:
            _water_log(tracker)
        elif idx == 1:
            _water_view(tracker, _today())
        else:
            return


def _water_log(tracker: HabitTracker):
    _clear()
    _header("Log Water")
    date = _pick_date()
    print("\n  Quick amounts:")
    amounts = [("Small glass (200 ml)", 200), ("Medium glass (300 ml)", 300),
               ("Large glass (500 ml)", 500), ("Bottle (750 ml)", 750),
               ("Large bottle (1000 ml)", 1000), ("Custom amount", 0)]
    idx = _choose([a[0] for a in amounts], "Amount")
    if amounts[idx][1] == 0:
        ml = _prompt("Amount (ml)", cast=int)
    else:
        ml = amounts[idx][1]

    tracker.log_water(WaterLog(date=date, amount_ml=ml))
    total = tracker.get_water_total(date)
    pct = min(total / 2000 * 100, 100)
    bar = "#" * int(pct / 5) + "-" * (20 - int(pct / 5))
    print(f"\n  Added {ml} ml.  Daily total: {total} ml")
    print(f"  [{bar}] {pct:.0f}% of 2 L goal")
    _pause()


def _water_view(tracker: HabitTracker, date: str):
    total = tracker.get_water_total(date)
    goal = 2000
    pct = min(total / goal * 100, 100)
    bar = "#" * int(pct / 5) + "-" * (20 - int(pct / 5))
    print()
    print(f"  Water on {date}")
    print(f"  {total} ml / {goal} ml")
    print(f"  [{bar}] {pct:.0f}%")
    _pause()


# ------------------------------------------------------------------ #
#  Sleep                                                               #
# ------------------------------------------------------------------ #

def _sleep_menu(tracker: HabitTracker):
    while True:
        _clear()
        _header("Sleep")
        idx = _choose(["Log sleep", "View a night", "Back"], "Choice")
        if idx == 0:
            _sleep_log(tracker)
        elif idx == 1:
            _sleep_view(tracker)
        else:
            return


def _sleep_log(tracker: HabitTracker):
    _clear()
    _header("Log Sleep")
    date = _pick_date()
    bedtime  = _prompt("Bedtime (HH:MM)", default="23:00")
    wake     = _prompt("Wake time (HH:MM)", default="07:00")

    # Auto-calculate duration from bedtime/wake
    try:
        bed_dt  = datetime.strptime(bedtime, "%H:%M")
        wake_dt = datetime.strptime(wake, "%H:%M")
        if wake_dt <= bed_dt:
            wake_dt += timedelta(days=1)
        auto_hours = round((wake_dt - bed_dt).seconds / 3600, 2)
    except ValueError:
        auto_hours = 8.0

    duration = _prompt("Duration (hours)", default=auto_hours, cast=float)
    quality  = _prompt("Quality (1-10)", cast=int)

    log = SleepLog(date=date, bedtime=bedtime, wake_time=wake,
                   duration_hours=duration, quality=quality)
    tracker.log_sleep(log)
    stars = "*" * quality + " " * (10 - quality)
    print(f"\n  Saved: {duration:.1f} h  [{stars}] {quality}/10")
    _pause()


def _sleep_view(tracker: HabitTracker):
    _clear()
    _header("View Sleep")
    date = _pick_date()
    log = tracker.get_sleep(date)
    print()
    if not log:
        print(f"  No sleep logged for {date}.")
    else:
        stars = "*" * log.quality + " " * (10 - log.quality)
        print(f"  {log.bedtime} → {log.wake_time}")
        print(f"  Duration : {log.duration_hours:.1f} h")
        print(f"  Quality  : [{stars}] {log.quality}/10")
    _pause()


# ------------------------------------------------------------------ #
#  Metabolic                                                           #
# ------------------------------------------------------------------ #

def _metabolic_menu(tracker: HabitTracker):
    while True:
        _clear()
        _header("Metabolic")
        idx = _choose(["Log measurements", "View a day", "Back"], "Choice")
        if idx == 0:
            _metabolic_log(tracker)
        elif idx == 1:
            _metabolic_view(tracker)
        else:
            return


def _metabolic_log(tracker: HabitTracker):
    _clear()
    _header("Log Metabolic")
    date = _pick_date()
    print("\n  (Press Enter to skip any field)\n")

    def _opt(label, cast=float):
        v = _prompt(label, default="", cast=str)
        return cast(v) if v else None

    weight     = _opt("Weight (kg)")
    body_fat   = _opt("Body fat (%)")
    resting_hr = _opt("Resting HR (bpm)", cast=int)
    systolic   = _opt("Systolic BP (mmHg)", cast=int)
    diastolic  = _opt("Diastolic BP (mmHg)", cast=int)
    glucose    = _opt("Blood glucose (mg/dL)")
    energy     = _opt("Energy level (1-10)", cast=int)
    mood       = _opt("Mood (1-10)", cast=int)

    log = MetabolicLog(date=date, weight_kg=weight, body_fat_pct=body_fat,
                       resting_hr=resting_hr, systolic_bp=systolic,
                       diastolic_bp=diastolic, blood_glucose=glucose,
                       energy_level=energy, mood=mood)
    tracker.log_metabolic(log)
    print(f"\n  Saved metabolic data for {date}.")
    _pause()


def _metabolic_view(tracker: HabitTracker):
    _clear()
    _header("View Metabolic")
    date = _pick_date()
    log = tracker.get_metabolic(date)
    print()
    if not log:
        print(f"  No data logged for {date}.")
    else:
        def _show(label, val, suffix="", dec=1):
            if val is not None:
                fmt = f"{val:.{dec}f}" if dec else str(val)
                print(f"  {label:<16} {fmt}{suffix}")
        _show("Weight",       log.weight_kg,    " kg")
        _show("Body Fat",     log.body_fat_pct, "%")
        _show("Resting HR",   log.resting_hr,   " bpm", dec=0)
        bp = log.blood_pressure
        if bp:
            print(f"  {'Blood Pressure':<16} {bp} mmHg")
        _show("Blood Glucose", log.blood_glucose, " mg/dL")
        _show("Energy",       log.energy_level, "/10", dec=0)
        _show("Mood",         log.mood,         "/10", dec=0)
    _pause()


# ------------------------------------------------------------------ #
#  Reports                                                             #
# ------------------------------------------------------------------ #

def _reports_menu(tracker: HabitTracker):
    while True:
        _clear()
        _header("Reports")
        idx = _choose(["Daily summary", "Weekly report", "Trend chart", "Back"], "Choice")
        if idx == 0:
            _clear()
            date = _pick_date()
            _clear()
            DailySummary(tracker, date).print()
            _pause()
        elif idx == 1:
            _clear()
            WeeklySummary(tracker).print()
            _pause()
        elif idx == 2:
            _trend_menu(tracker)
        else:
            return


def _trend_menu(tracker: HabitTracker):
    _clear()
    _header("Trend Chart")
    metrics = ["weight", "sleep_duration", "sleep_quality", "exercise_min",
               "calories_in", "water", "energy", "mood", "resting_hr"]
    labels  = ["Weight", "Sleep duration", "Sleep quality", "Exercise minutes",
               "Calories in", "Water intake", "Energy level", "Mood", "Resting HR"]
    idx = _choose(labels + ["Back"], "Metric")
    if idx == len(metrics):
        return
    days = _prompt("Days to show", default=14, cast=int)
    _clear()
    generate_trend(tracker, metrics[idx], days)
    _pause()


# ------------------------------------------------------------------ #
#  Main loop                                                           #
# ------------------------------------------------------------------ #

def run(db_path: str = DEFAULT_DB_PATH):
    initialize_db(db_path)
    tracker = HabitTracker(db_path)

    while True:
        _clear()
        _header("Habit Tracker")
        print(f"  {_today()}")
        print()

        # Quick water status on home screen
        water_ml = tracker.get_water_total(_today())
        pct = min(water_ml / 2000 * 100, 100)
        bar = "#" * int(pct / 5) + "-" * (20 - int(pct / 5))
        print(f"  Water  [{bar}] {pct:.0f}%")
        print()

        idx = _choose([
            "Exercise",
            "Diet",
            "Water",
            "Sleep",
            "Metabolic",
            "Reports",
            "Quit",
        ], "Menu")

        if idx == 0:
            _exercise_menu(tracker)
        elif idx == 1:
            _diet_menu(tracker)
        elif idx == 2:
            _water_menu(tracker)
        elif idx == 3:
            _sleep_menu(tracker)
        elif idx == 4:
            _metabolic_menu(tracker)
        elif idx == 5:
            _reports_menu(tracker)
        else:
            print("\n  Goodbye!\n")
            sys.exit(0)
