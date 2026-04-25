"""
Flask web application for Habit Tracker.
"""

import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from .database import initialize_db, DEFAULT_DB_PATH
from .models import ExerciseLog, DietLog, WaterLog, SleepLog, MetabolicLog, today as _today
from .tracker import HabitTracker
from .reports import generate_trend


def create_app(db_path: str = DEFAULT_DB_PATH) -> Flask:
    app = Flask(__name__)
    app.secret_key = "habit-tracker-secret"

    initialize_db(db_path)
    tracker = HabitTracker(db_path)

    def _date_or_today(s):
        if not s:
            return _today()
        try:
            datetime.strptime(s, "%Y-%m-%d")
            return s
        except ValueError:
            return _today()

    def _int(v):
        try:
            return int(v) if v else None
        except (ValueError, TypeError):
            return None

    def _float(v):
        try:
            return float(v) if v else None
        except (ValueError, TypeError):
            return None

    # ------------------------------------------------------------------ #
    #  Dashboard                                                           #
    # ------------------------------------------------------------------ #

    @app.route("/")
    def dashboard():
        date = _date_or_today(request.args.get("date"))
        ex_logs   = tracker.get_exercise(date)
        diet_logs = tracker.get_diet(date)
        water_ml  = tracker.get_water_total(date)
        sleep_log = tracker.get_sleep(date)
        met_log   = tracker.get_metabolic(date)

        total_ex_min = sum(l.duration_min for l in ex_logs)
        total_cal_in = sum(l.calories or 0 for l in diet_logs)
        total_cal_burned = sum(l.calories or 0 for l in ex_logs)
        water_pct = min(round(water_ml / 2000 * 100), 100)

        dt      = datetime.strptime(date, "%Y-%m-%d")
        prev_dt = (dt - timedelta(days=1)).strftime("%Y-%m-%d")
        next_dt = (dt + timedelta(days=1)).strftime("%Y-%m-%d")

        return render_template("dashboard.html",
            date=date,
            today=_today(),
            prev_date=prev_dt,
            next_date=next_dt,
            ex_logs=ex_logs,
            diet_logs=diet_logs,
            water_ml=water_ml,
            water_pct=water_pct,
            sleep_log=sleep_log,
            met_log=met_log,
            total_ex_min=total_ex_min,
            total_cal_in=total_cal_in,
            total_cal_burned=total_cal_burned,
        )

    # ------------------------------------------------------------------ #
    #  Exercise                                                            #
    # ------------------------------------------------------------------ #

    @app.route("/exercise", methods=["GET", "POST"])
    def exercise():
        if request.method == "POST":
            try:
                log = ExerciseLog(
                    date=request.form.get("date") or _today(),
                    type=request.form["type"],
                    duration_min=int(request.form["duration_min"]),
                    intensity=request.form["intensity"],
                    calories=_int(request.form.get("calories")),
                    notes=request.form.get("notes") or None,
                )
                log.validate()
                tracker.log_exercise(log)
                flash(f"Logged {log.duration_min} min of {log.type}.", "success")
            except (ValueError, KeyError) as e:
                flash(str(e), "error")
            return redirect(url_for("exercise", date=request.form.get("date") or _today()))

        date = _date_or_today(request.args.get("date"))
        logs = tracker.get_exercise(date)
        total_min = sum(l.duration_min for l in logs)
        return render_template("exercise.html", date=date, logs=logs, total_min=total_min)

    @app.route("/exercise/delete/<int:log_id>", methods=["POST"])
    def exercise_delete(log_id):
        date = request.form.get("date", _today())
        tracker.delete_exercise(log_id)
        flash("Entry deleted.", "success")
        return redirect(url_for("exercise", date=date))

    # ------------------------------------------------------------------ #
    #  Diet                                                                #
    # ------------------------------------------------------------------ #

    @app.route("/diet", methods=["GET", "POST"])
    def diet():
        if request.method == "POST":
            try:
                log = DietLog(
                    date=request.form.get("date") or _today(),
                    meal=request.form["meal"],
                    description=request.form["description"],
                    calories=_int(request.form.get("calories")),
                    protein_g=_float(request.form.get("protein_g")),
                    carbs_g=_float(request.form.get("carbs_g")),
                    fat_g=_float(request.form.get("fat_g")),
                    notes=request.form.get("notes") or None,
                )
                log.validate()
                tracker.log_diet(log)
                flash(f"Logged {log.meal.capitalize()}.", "success")
            except (ValueError, KeyError) as e:
                flash(str(e), "error")
            return redirect(url_for("diet", date=request.form.get("date") or _today()))

        date = _date_or_today(request.args.get("date"))
        logs = tracker.get_diet(date)
        total_cal = sum(l.calories or 0 for l in logs)
        total_p   = sum(l.protein_g or 0 for l in logs)
        total_c   = sum(l.carbs_g or 0 for l in logs)
        total_f   = sum(l.fat_g or 0 for l in logs)
        return render_template("diet.html", date=date, logs=logs,
                               total_cal=total_cal, total_p=total_p,
                               total_c=total_c, total_f=total_f)

    @app.route("/diet/delete/<int:log_id>", methods=["POST"])
    def diet_delete(log_id):
        date = request.form.get("date", _today())
        tracker.delete_diet(log_id)
        flash("Entry deleted.", "success")
        return redirect(url_for("diet", date=date))

    # ------------------------------------------------------------------ #
    #  Water                                                               #
    # ------------------------------------------------------------------ #

    @app.route("/water", methods=["GET", "POST"])
    def water():
        if request.method == "POST":
            try:
                log = WaterLog(
                    date=request.form.get("date") or _today(),
                    amount_ml=int(request.form["amount_ml"]),
                )
                log.validate()
                tracker.log_water(log)
                flash(f"Logged {log.amount_ml} ml.", "success")
            except (ValueError, KeyError) as e:
                flash(str(e), "error")
            return redirect(url_for("water", date=request.form.get("date") or _today()))

        date = _date_or_today(request.args.get("date"))
        total_ml = tracker.get_water_total(date)
        water_pct = min(round(total_ml / 2000 * 100), 100)
        return render_template("water.html", date=date,
                               total_ml=total_ml, water_pct=water_pct)

    # ------------------------------------------------------------------ #
    #  Sleep                                                               #
    # ------------------------------------------------------------------ #

    @app.route("/sleep", methods=["GET", "POST"])
    def sleep():
        if request.method == "POST":
            try:
                bedtime   = request.form["bedtime"]
                wake_time = request.form["wake_time"]
                duration  = _float(request.form.get("duration_hours"))
                if not duration:
                    bed_dt  = datetime.strptime(bedtime, "%H:%M")
                    wake_dt = datetime.strptime(wake_time, "%H:%M")
                    if wake_dt <= bed_dt:
                        wake_dt += timedelta(days=1)
                    duration = round((wake_dt - bed_dt).seconds / 3600, 2)
                log = SleepLog(
                    date=request.form.get("date") or _today(),
                    bedtime=bedtime,
                    wake_time=wake_time,
                    duration_hours=duration,
                    quality=int(request.form["quality"]),
                    notes=request.form.get("notes") or None,
                )
                log.validate()
                tracker.log_sleep(log)
                flash(f"Logged {log.duration_hours:.1f} h sleep.", "success")
            except (ValueError, KeyError) as e:
                flash(str(e), "error")
            return redirect(url_for("sleep", date=request.form.get("date") or _today()))

        date = _date_or_today(request.args.get("date"))
        log = tracker.get_sleep(date)
        return render_template("sleep.html", date=date, log=log)

    # ------------------------------------------------------------------ #
    #  Metabolic                                                           #
    # ------------------------------------------------------------------ #

    @app.route("/metabolic", methods=["GET", "POST"])
    def metabolic():
        if request.method == "POST":
            try:
                log = MetabolicLog(
                    date=request.form.get("date") or _today(),
                    weight_kg=_float(request.form.get("weight_kg")),
                    body_fat_pct=_float(request.form.get("body_fat_pct")),
                    resting_hr=_int(request.form.get("resting_hr")),
                    systolic_bp=_int(request.form.get("systolic_bp")),
                    diastolic_bp=_int(request.form.get("diastolic_bp")),
                    blood_glucose=_float(request.form.get("blood_glucose")),
                    energy_level=_int(request.form.get("energy_level")),
                    mood=_int(request.form.get("mood")),
                    notes=request.form.get("notes") or None,
                )
                log.validate()
                tracker.log_metabolic(log)
                flash("Metabolic data saved.", "success")
            except (ValueError, KeyError) as e:
                flash(str(e), "error")
            return redirect(url_for("metabolic", date=request.form.get("date") or _today()))

        date = _date_or_today(request.args.get("date"))
        log = tracker.get_metabolic(date)
        return render_template("metabolic.html", date=date, log=log)

    # ------------------------------------------------------------------ #
    #  Trends API                                                          #
    # ------------------------------------------------------------------ #

    @app.route("/api/trend/<metric>")
    def api_trend(metric):
        days = int(request.args.get("days", 14))
        end   = _today()
        start = (datetime.strptime(end, "%Y-%m-%d") - timedelta(days=days - 1)).strftime("%Y-%m-%d")
        dates = [(datetime.strptime(start, "%Y-%m-%d") + timedelta(days=i)).strftime("%Y-%m-%d")
                 for i in range(days)]

        data = {}
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
            data = tracker.get_water_range(start, end)
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

        return jsonify({
            "labels": [d[5:] for d in dates],  # MM-DD
            "values": [data.get(d) for d in dates],
        })

    @app.route("/trends")
    def trends():
        return render_template("trends.html")

    return app
