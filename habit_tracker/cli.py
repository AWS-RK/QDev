"""
Command-line interface for the Habit Tracker.
"""

import argparse
import sys
from datetime import datetime, timedelta

from .database import initialize_db, DEFAULT_DB_PATH
from .models import ExerciseLog, DietLog, WaterLog, SleepLog, MetabolicLog, today
from .tracker import HabitTracker
from .reports import DailySummary, WeeklySummary, generate_trend


def _parse_date(s: str) -> str:
    if s == "today":
        return today()
    if s == "yesterday":
        return (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return s
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date '{s}'. Use YYYY-MM-DD, 'today', or 'yesterday'.")


def _fmt_optional(val, suffix="", decimals=None) -> str:
    if val is None:
        return "-"
    if decimals is not None:
        return f"{val:.{decimals}f}{suffix}"
    return f"{val}{suffix}"


# ------------------------------------------------------------------ #
#  Sub-command handlers                                               #
# ------------------------------------------------------------------ #

def cmd_exercise_log(args, tracker: HabitTracker) -> None:
    log = ExerciseLog(
        date=args.date,
        type=args.type,
        duration_min=args.duration,
        intensity=args.intensity,
        calories=args.calories,
        notes=args.notes,
    )
    log_id = tracker.log_exercise(log)
    print(f"Exercise logged (id={log_id}): {args.duration} min of {args.type} on {args.date}.")


def cmd_exercise_view(args, tracker: HabitTracker) -> None:
    logs = tracker.get_exercise(args.date)
    if not logs:
        print(f"No exercise logged for {args.date}.")
        return
    total_min = sum(l.duration_min for l in logs)
    print(f"\n--- Exercise on {args.date} ---")
    for l in logs:
        cal = f", {l.calories} kcal" if l.calories else ""
        print(f"  [{l.id}] {l.type} | {l.duration_min} min | {l.intensity}{cal}")
        if l.notes:
            print(f"       Notes: {l.notes}")
    print(f"  Total: {total_min} min ({total_min/60:.1f} h)")


def cmd_diet_log(args, tracker: HabitTracker) -> None:
    log = DietLog(
        date=args.date,
        meal=args.meal,
        description=args.description,
        calories=args.calories,
        protein_g=args.protein,
        carbs_g=args.carbs,
        fat_g=args.fat,
        notes=args.notes,
    )
    log_id = tracker.log_diet(log)
    print(f"Diet logged (id={log_id}): {args.meal} on {args.date}.")


def cmd_diet_view(args, tracker: HabitTracker) -> None:
    logs = tracker.get_diet(args.date)
    if not logs:
        print(f"No diet logged for {args.date}.")
        return
    total_cal = sum(l.calories or 0 for l in logs)
    total_p = sum(l.protein_g or 0 for l in logs)
    total_c = sum(l.carbs_g or 0 for l in logs)
    total_f = sum(l.fat_g or 0 for l in logs)
    print(f"\n--- Diet on {args.date} ---")
    for l in logs:
        cal = f" | {l.calories} kcal" if l.calories else ""
        macros = []
        if l.protein_g: macros.append(f"P:{l.protein_g}g")
        if l.carbs_g:   macros.append(f"C:{l.carbs_g}g")
        if l.fat_g:     macros.append(f"F:{l.fat_g}g")
        macro_str = " | " + " ".join(macros) if macros else ""
        print(f"  [{l.id}] {l.meal.capitalize()}: {l.description}{cal}{macro_str}")
        if l.notes:
            print(f"       Notes: {l.notes}")
    print(f"  Totals: {total_cal} kcal | P:{total_p:.1f}g C:{total_c:.1f}g F:{total_f:.1f}g")


def cmd_water_log(args, tracker: HabitTracker) -> None:
    log = WaterLog(date=args.date, amount_ml=args.amount)
    tracker.log_water(log)
    total = tracker.get_water_total(args.date)
    print(f"Water logged: {args.amount} ml. Daily total: {total} ml ({total/1000:.2f} L).")


def cmd_water_view(args, tracker: HabitTracker) -> None:
    total = tracker.get_water_total(args.date)
    goal = 2000  # ml
    pct = total / goal * 100
    bar_len = 20
    filled = int(bar_len * min(total, goal) / goal)
    bar = "#" * filled + "-" * (bar_len - filled)
    print(f"\n--- Water on {args.date} ---")
    print(f"  Consumed: {total} ml ({total/1000:.2f} L)")
    print(f"  Goal:     {goal} ml  [{bar}] {pct:.0f}%")


def cmd_sleep_log(args, tracker: HabitTracker) -> None:
    log = SleepLog(
        date=args.date,
        bedtime=args.bedtime,
        wake_time=args.wake,
        duration_hours=args.duration,
        quality=args.quality,
        notes=args.notes,
    )
    log_id = tracker.log_sleep(log)
    print(f"Sleep logged (id={log_id}): {args.duration:.1f} h, quality {args.quality}/10 on {args.date}.")


def cmd_sleep_view(args, tracker: HabitTracker) -> None:
    log = tracker.get_sleep(args.date)
    if not log:
        print(f"No sleep logged for {args.date}.")
        return
    stars = "*" * log.quality + " " * (10 - log.quality)
    print(f"\n--- Sleep on {args.date} ---")
    print(f"  Bedtime:  {log.bedtime}  |  Wake: {log.wake_time}")
    print(f"  Duration: {log.duration_hours:.1f} h")
    print(f"  Quality:  [{stars}] {log.quality}/10")
    if log.notes:
        print(f"  Notes:    {log.notes}")


def cmd_metabolic_log(args, tracker: HabitTracker) -> None:
    log = MetabolicLog(
        date=args.date,
        weight_kg=args.weight,
        body_fat_pct=args.body_fat,
        resting_hr=args.resting_hr,
        systolic_bp=args.systolic,
        diastolic_bp=args.diastolic,
        blood_glucose=args.glucose,
        energy_level=args.energy,
        mood=args.mood,
        notes=args.notes,
    )
    log_id = tracker.log_metabolic(log)
    print(f"Metabolic data logged (id={log_id}) for {args.date}.")


def cmd_metabolic_view(args, tracker: HabitTracker) -> None:
    log = tracker.get_metabolic(args.date)
    if not log:
        print(f"No metabolic data logged for {args.date}.")
        return
    print(f"\n--- Metabolic on {args.date} ---")
    print(f"  Weight:        {_fmt_optional(log.weight_kg, ' kg', 1)}")
    print(f"  Body Fat:      {_fmt_optional(log.body_fat_pct, '%', 1)}")
    print(f"  Resting HR:    {_fmt_optional(log.resting_hr, ' bpm')}")
    bp = log.blood_pressure
    print(f"  Blood Pressure:{' ' + bp + ' mmHg' if bp else ' -'}")
    print(f"  Blood Glucose: {_fmt_optional(log.blood_glucose, ' mg/dL', 1)}")
    print(f"  Energy:        {_fmt_optional(log.energy_level, '/10')}")
    print(f"  Mood:          {_fmt_optional(log.mood, '/10')}")
    if log.notes:
        print(f"  Notes:         {log.notes}")


def cmd_summary(args, tracker: HabitTracker) -> None:
    summary = DailySummary(tracker, args.date)
    summary.print()


def cmd_weekly(args, tracker: HabitTracker) -> None:
    report = WeeklySummary(tracker, args.week_start)
    report.print()


def cmd_trend(args, tracker: HabitTracker) -> None:
    generate_trend(tracker, args.metric, args.days)


# ------------------------------------------------------------------ #
#  Argument parser                                                    #
# ------------------------------------------------------------------ #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="habit-tracker",
        description="Track daily habits: exercise, diet, sleep, and metabolic factors.",
    )
    parser.add_argument(
        "--db", default=DEFAULT_DB_PATH, metavar="PATH",
        help="Path to the SQLite database file.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ---- exercise ----
    ex = sub.add_parser("exercise", help="Log or view exercise sessions.")
    ex_sub = ex.add_subparsers(dest="action", required=True)

    ex_log = ex_sub.add_parser("log", help="Log an exercise session.")
    ex_log.add_argument("-d", "--date", default=today(), type=_parse_date, help="Date (YYYY-MM-DD, today, yesterday).")
    ex_log.add_argument("-t", "--type", required=True, help="Exercise type (e.g. Running, Cycling).")
    ex_log.add_argument("-m", "--duration", required=True, type=int, metavar="MINUTES", help="Duration in minutes.")
    ex_log.add_argument("-i", "--intensity", required=True, choices=["low", "moderate", "high"])
    ex_log.add_argument("-c", "--calories", type=int, help="Calories burned (optional).")
    ex_log.add_argument("-n", "--notes", help="Optional notes.")

    ex_view = ex_sub.add_parser("view", help="View exercise for a date.")
    ex_view.add_argument("-d", "--date", default=today(), type=_parse_date)

    # ---- diet ----
    diet = sub.add_parser("diet", help="Log or view diet entries.")
    diet_sub = diet.add_subparsers(dest="action", required=True)

    diet_log = diet_sub.add_parser("log", help="Log a meal.")
    diet_log.add_argument("-d", "--date", default=today(), type=_parse_date)
    diet_log.add_argument("-m", "--meal", required=True, choices=["breakfast", "lunch", "dinner", "snack"])
    diet_log.add_argument("-D", "--description", required=True, help="What you ate.")
    diet_log.add_argument("-c", "--calories", type=int)
    diet_log.add_argument("-p", "--protein", type=float, metavar="G")
    diet_log.add_argument("-C", "--carbs", type=float, metavar="G")
    diet_log.add_argument("-f", "--fat", type=float, metavar="G")
    diet_log.add_argument("-n", "--notes")

    diet_view = diet_sub.add_parser("view", help="View diet for a date.")
    diet_view.add_argument("-d", "--date", default=today(), type=_parse_date)

    # ---- water ----
    water = sub.add_parser("water", help="Log or view water intake.")
    water_sub = water.add_subparsers(dest="action", required=True)

    water_log = water_sub.add_parser("log", help="Log water intake.")
    water_log.add_argument("-d", "--date", default=today(), type=_parse_date)
    water_log.add_argument("-a", "--amount", required=True, type=int, metavar="ML", help="Amount in ml.")

    water_view = water_sub.add_parser("view", help="View water intake for a date.")
    water_view.add_argument("-d", "--date", default=today(), type=_parse_date)

    # ---- sleep ----
    slp = sub.add_parser("sleep", help="Log or view sleep data.")
    slp_sub = slp.add_subparsers(dest="action", required=True)

    slp_log = slp_sub.add_parser("log", help="Log a night of sleep.")
    slp_log.add_argument("-d", "--date", default=today(), type=_parse_date,
                         help="Morning date (the day you woke up).")
    slp_log.add_argument("-b", "--bedtime", required=True, metavar="HH:MM", help="Time you went to bed.")
    slp_log.add_argument("-w", "--wake", required=True, metavar="HH:MM", help="Time you woke up.")
    slp_log.add_argument("-D", "--duration", required=True, type=float, metavar="HOURS")
    slp_log.add_argument("-q", "--quality", required=True, type=int, metavar="1-10")
    slp_log.add_argument("-n", "--notes")

    slp_view = slp_sub.add_parser("view", help="View sleep for a date.")
    slp_view.add_argument("-d", "--date", default=today(), type=_parse_date)

    # ---- metabolic ----
    met = sub.add_parser("metabolic", help="Log or view metabolic measurements.")
    met_sub = met.add_subparsers(dest="action", required=True)

    met_log = met_sub.add_parser("log", help="Log metabolic measurements.")
    met_log.add_argument("-d", "--date", default=today(), type=_parse_date)
    met_log.add_argument("-w", "--weight", type=float, metavar="KG")
    met_log.add_argument("-b", "--body-fat", dest="body_fat", type=float, metavar="PCT")
    met_log.add_argument("-r", "--resting-hr", dest="resting_hr", type=int, metavar="BPM")
    met_log.add_argument("-s", "--systolic", type=int, metavar="MMHG")
    met_log.add_argument("-p", "--diastolic", type=int, metavar="MMHG")
    met_log.add_argument("-g", "--glucose", type=float, metavar="MG/DL")
    met_log.add_argument("-e", "--energy", type=int, metavar="1-10")
    met_log.add_argument("-m", "--mood", type=int, metavar="1-10")
    met_log.add_argument("-n", "--notes")

    met_view = met_sub.add_parser("view", help="View metabolic data for a date.")
    met_view.add_argument("-d", "--date", default=today(), type=_parse_date)

    # ---- summary ----
    summ = sub.add_parser("summary", help="Show a full daily summary.")
    summ.add_argument("-d", "--date", default=today(), type=_parse_date)

    # ---- weekly ----
    week = sub.add_parser("weekly", help="Show a weekly summary report.")
    week.add_argument(
        "-s", "--week-start", dest="week_start", default=None,
        type=_parse_date,
        help="Start date of the week (YYYY-MM-DD). Defaults to last Monday.",
    )

    # ---- trend ----
    trend = sub.add_parser("trend", help="Display a trend chart for a metric.")
    trend.add_argument(
        "metric",
        choices=["weight", "sleep_duration", "sleep_quality", "exercise_min",
                 "calories_in", "water", "energy", "mood", "resting_hr"],
        help="Metric to plot.",
    )
    trend.add_argument("-D", "--days", type=int, default=14, metavar="N", help="Number of past days (default 14).")

    return parser


# ------------------------------------------------------------------ #
#  Entry point                                                        #
# ------------------------------------------------------------------ #

def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    initialize_db(args.db)
    tracker = HabitTracker(args.db)

    dispatch = {
        ("exercise",  "log"):  cmd_exercise_log,
        ("exercise",  "view"): cmd_exercise_view,
        ("diet",      "log"):  cmd_diet_log,
        ("diet",      "view"): cmd_diet_view,
        ("water",     "log"):  cmd_water_log,
        ("water",     "view"): cmd_water_view,
        ("sleep",     "log"):  cmd_sleep_log,
        ("sleep",     "view"): cmd_sleep_view,
        ("metabolic", "log"):  cmd_metabolic_log,
        ("metabolic", "view"): cmd_metabolic_view,
        ("summary",   None):   cmd_summary,
        ("weekly",    None):   cmd_weekly,
        ("trend",     None):   cmd_trend,
    }

    action = getattr(args, "action", None)
    handler = dispatch.get((args.command, action))
    if handler is None:
        parser.print_help()
        return 1

    try:
        handler(args, tracker)
        return 0
    except (ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
