"""
Reports and analytics: daily summaries, weekly reports, and trend charts.
"""

from datetime import datetime, timedelta
from typing import Optional

from .tracker import HabitTracker
from .models import today as _today


def _monday_of(date_str: str) -> str:
    d = datetime.strptime(date_str, "%Y-%m-%d")
    monday = d - timedelta(days=d.weekday())
    return monday.strftime("%Y-%m-%d")


def _add_days(date_str: str, n: int) -> str:
    d = datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=n)
    return d.strftime("%Y-%m-%d")


class DailySummary:
    def __init__(self, tracker: HabitTracker, date: str):
        self.tracker = tracker
        self.date = date

    def print(self) -> None:
        t = self.tracker
        d = self.date

        print(f"\n{'='*50}")
        print(f"  Daily Summary for {d}")
        print(f"{'='*50}")

        # Exercise
        ex_logs = t.get_exercise(d)
        total_ex_min = sum(l.duration_min for l in ex_logs)
        total_ex_cal = sum(l.calories or 0 for l in ex_logs)
        print(f"\nExercise  ({len(ex_logs)} session{'s' if len(ex_logs) != 1 else ''})")
        if ex_logs:
            for l in ex_logs:
                print(f"  - {l.type} {l.duration_min} min [{l.intensity}]"
                      + (f", {l.calories} kcal" if l.calories else ""))
            print(f"  Total: {total_ex_min} min burned  ~{total_ex_cal} kcal")
        else:
            print("  No exercise recorded.")

        # Diet
        diet_logs = t.get_diet(d)
        total_cal = sum(l.calories or 0 for l in diet_logs)
        total_p   = sum(l.protein_g or 0 for l in diet_logs)
        total_c   = sum(l.carbs_g or 0 for l in diet_logs)
        total_f   = sum(l.fat_g or 0 for l in diet_logs)
        print(f"\nDiet  ({len(diet_logs)} meal{'s' if len(diet_logs) != 1 else ''})")
        if diet_logs:
            for l in diet_logs:
                print(f"  - {l.meal.capitalize()}: {l.description}"
                      + (f"  [{l.calories} kcal]" if l.calories else ""))
            print(f"  Totals: {total_cal} kcal | P:{total_p:.1f}g C:{total_c:.1f}g F:{total_f:.1f}g")
        else:
            print("  No meals recorded.")

        # Water
        water_ml = t.get_water_total(d)
        goal_ml = 2000
        pct = min(water_ml / goal_ml * 100, 100)
        bar_filled = int(pct / 5)
        bar = "#" * bar_filled + "-" * (20 - bar_filled)
        print(f"\nWater")
        print(f"  {water_ml} ml / {goal_ml} ml  [{bar}] {pct:.0f}%")

        # Sleep
        sleep = t.get_sleep(d)
        print(f"\nSleep")
        if sleep:
            stars = "*" * sleep.quality + " " * (10 - sleep.quality)
            print(f"  {sleep.duration_hours:.1f} h  ({sleep.bedtime} → {sleep.wake_time})")
            print(f"  Quality: [{stars}] {sleep.quality}/10")
        else:
            print("  No sleep recorded.")

        # Metabolic
        met = t.get_metabolic(d)
        print(f"\nMetabolic")
        if met:
            fields = [
                ("Weight",        met.weight_kg,       " kg",   1),
                ("Body Fat",      met.body_fat_pct,    "%",     1),
                ("Resting HR",    met.resting_hr,      " bpm",  0),
                ("Blood Glucose", met.blood_glucose,   " mg/dL",1),
                ("Energy",        met.energy_level,    "/10",   0),
                ("Mood",          met.mood,            "/10",   0),
            ]
            printed = False
            for label, val, suffix, dec in fields:
                if val is not None:
                    if dec:
                        print(f"  {label}: {val:.{dec}f}{suffix}")
                    else:
                        print(f"  {label}: {val}{suffix}")
                    printed = True
            bp = met.blood_pressure
            if bp:
                print(f"  Blood Pressure: {bp} mmHg")
                printed = True
            if not printed:
                print("  No measurements recorded.")
        else:
            print("  No measurements recorded.")

        print(f"\n{'='*50}\n")


class WeeklySummary:
    def __init__(self, tracker: HabitTracker, week_start: Optional[str] = None):
        self.tracker = tracker
        self.week_start = week_start or _monday_of(_today())
        self.week_end = _add_days(self.week_start, 6)

    def print(self) -> None:
        t = self.tracker
        ws, we = self.week_start, self.week_end

        ex_logs  = t.get_exercise_range(ws, we)
        diet_logs = t.get_diet_range(ws, we)
        water_map = t.get_water_range(ws, we)
        sleep_logs = t.get_sleep_range(ws, we)
        met_logs = t.get_metabolic_range(ws, we)

        print(f"\n{'='*55}")
        print(f"  Weekly Summary  {ws}  →  {we}")
        print(f"{'='*55}")

        # Exercise
        days_with_ex = len({l.date for l in ex_logs})
        total_ex_min = sum(l.duration_min for l in ex_logs)
        print(f"\nExercise")
        print(f"  Sessions: {len(ex_logs)} across {days_with_ex} day(s)")
        print(f"  Total time: {total_ex_min} min ({total_ex_min/60:.1f} h)")
        if ex_logs:
            types = {}
            for l in ex_logs:
                types[l.type] = types.get(l.type, 0) + l.duration_min
            for etype, mins in sorted(types.items(), key=lambda x: -x[1]):
                print(f"    {etype}: {mins} min")

        # Diet
        days_with_diet = len({l.date for l in diet_logs})
        total_cal = sum(l.calories or 0 for l in diet_logs)
        avg_cal = total_cal / days_with_diet if days_with_diet else 0
        print(f"\nDiet  ({days_with_diet} day(s) logged)")
        print(f"  Total calories: {total_cal} kcal  |  Avg/day: {avg_cal:.0f} kcal")

        # Water
        total_water = sum(water_map.values()) if water_map else 0
        days_with_water = len(water_map)
        avg_water = total_water / days_with_water if days_with_water else 0
        print(f"\nWater  ({days_with_water} day(s) logged)")
        print(f"  Total: {total_water} ml  |  Avg/day: {avg_water:.0f} ml")

        # Sleep
        print(f"\nSleep  ({len(sleep_logs)} night(s) logged)")
        if sleep_logs:
            avg_dur = sum(s.duration_hours for s in sleep_logs) / len(sleep_logs)
            avg_qual = sum(s.quality for s in sleep_logs) / len(sleep_logs)
            print(f"  Avg duration: {avg_dur:.1f} h")
            print(f"  Avg quality:  {avg_qual:.1f}/10")

        # Metabolic
        print(f"\nMetabolic  ({len(met_logs)} day(s) logged)")
        if met_logs:
            weights = [m.weight_kg for m in met_logs if m.weight_kg is not None]
            energies = [m.energy_level for m in met_logs if m.energy_level is not None]
            moods = [m.mood for m in met_logs if m.mood is not None]
            if weights:
                print(f"  Weight: {min(weights):.1f}–{max(weights):.1f} kg  (last: {weights[-1]:.1f} kg)")
            if energies:
                print(f"  Avg energy: {sum(energies)/len(energies):.1f}/10")
            if moods:
                print(f"  Avg mood:   {sum(moods)/len(moods):.1f}/10")

        print(f"\n{'='*55}\n")


def generate_trend(tracker: HabitTracker, metric: str, days: int = 14) -> None:
    """Print a simple ASCII sparkline for the chosen metric over the last N days."""
    end = _today()
    start = _add_days(end, -(days - 1))

    data = {}  # date -> value

    if metric == "weight":
        for m in tracker.get_metabolic_range(start, end):
            if m.weight_kg is not None:
                data[m.date] = m.weight_kg
    elif metric == "sleep_duration":
        for s in tracker.get_sleep_range(start, end):
            data[s.date] = s.duration_hours
    elif metric == "sleep_quality":
        for s in tracker.get_sleep_range(start, end):
            data[s.date] = s.quality
    elif metric == "exercise_min":
        for ex in tracker.get_exercise_range(start, end):
            data[ex.date] = data.get(ex.date, 0) + ex.duration_min
    elif metric == "calories_in":
        for d in tracker.get_diet_range(start, end):
            if d.calories:
                data[d.date] = data.get(d.date, 0) + d.calories
    elif metric == "water":
        water_map = tracker.get_water_range(start, end)
        data = water_map
    elif metric == "energy":
        for m in tracker.get_metabolic_range(start, end):
            if m.energy_level is not None:
                data[m.date] = m.energy_level
    elif metric == "mood":
        for m in tracker.get_metabolic_range(start, end):
            if m.mood is not None:
                data[m.date] = m.mood
    elif metric == "resting_hr":
        for m in tracker.get_metabolic_range(start, end):
            if m.resting_hr is not None:
                data[m.date] = m.resting_hr

    # Build ordered list
    dates = [_add_days(start, i) for i in range(days)]
    values = [data.get(d) for d in dates]

    present = [v for v in values if v is not None]
    if not present:
        print(f"No data for '{metric}' in the last {days} days.")
        return

    vmin, vmax = min(present), max(present)
    height = 8
    labels = {
        "weight": ("kg", 1),
        "sleep_duration": ("h", 1),
        "sleep_quality": ("/10", 0),
        "exercise_min": ("min", 0),
        "calories_in": ("kcal", 0),
        "water": ("ml", 0),
        "energy": ("/10", 0),
        "mood": ("/10", 0),
        "resting_hr": ("bpm", 0),
    }
    unit, dec = labels.get(metric, ("", 0))

    print(f"\n--- Trend: {metric} (last {days} days) ---")

    # Build sparkline rows (top = high)
    rows = []
    for row in range(height, 0, -1):
        threshold = vmin + (vmax - vmin) * (row - 1) / (height - 1) if vmax > vmin else vmin
        line = ""
        for v in values:
            if v is None:
                line += "  "
            elif v >= threshold:
                line += "* "
            else:
                line += "  "
        label_val = vmin + (vmax - vmin) * (row - 1) / (height - 1) if vmax > vmin else vmin
        if dec:
            rows.append(f"  {label_val:{5}.{dec}f}{unit} |{line}")
        else:
            rows.append(f"  {label_val:{5}.0f}{unit} |{line}")

    for r in rows:
        print(r)

    # x-axis
    print("         " + "+-" * len(dates))

    # Date labels (every 2 days)
    date_line = "         "
    for i, d in enumerate(dates):
        if i % 2 == 0:
            date_line += d[5:]  # MM-DD
        else:
            date_line += "  "
    print(date_line)
    print()
