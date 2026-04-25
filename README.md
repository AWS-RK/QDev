# Habit Tracker

A Python CLI application for tracking daily habits including exercise, diet, water intake, sleep, and metabolic factors.

## Features

- **Exercise** – log sessions with type, duration, intensity, and calories burned
- **Diet** – log meals (breakfast, lunch, dinner, snacks) with macros (protein, carbs, fat)
- **Water** – track daily hydration with a visual progress bar
- **Sleep** – record bedtime, wake time, duration, and quality score
- **Metabolic** – log weight, body fat %, resting heart rate, blood pressure, blood glucose, energy, and mood
- **Daily Summary** – full snapshot of all metrics for any given day
- **Weekly Report** – aggregated stats across a 7-day window
- **Trend Charts** – ASCII sparkline charts for any tracked metric

## Data Storage

All data is stored in a local SQLite database at `~/.habit_tracker.db`. You can override this with `--db <path>`.

## Usage

```bash
python main.py <command> [options]
```

### Exercise

```bash
# Log a session
python main.py exercise log -t Running -m 30 -i moderate -c 320 -n "Morning jog"

# View today's exercise
python main.py exercise view

# View a specific date
python main.py exercise view -d 2024-03-15
```

### Diet

```bash
# Log a meal
python main.py diet log -m breakfast -D "Oatmeal with berries" -c 380 -p 12 -C 65 -f 8

# View today's meals
python main.py diet view
```

### Water

```bash
# Log water intake (in ml)
python main.py water log -a 500

# View today's total
python main.py water view
```

### Sleep

```bash
# Log last night's sleep
python main.py sleep log -b 22:30 -w 06:30 -D 8.0 -q 8

# View sleep for a date
python main.py sleep view -d yesterday
```

### Metabolic

```bash
# Log measurements
python main.py metabolic log -w 75.2 -r 58 -s 118 -p 76 -e 8 -m 7

# View today's data
python main.py metabolic view
```

### Reports

```bash
# Full daily summary
python main.py summary
python main.py summary -d 2024-03-15

# Weekly report (defaults to current week starting Monday)
python main.py weekly
python main.py weekly -s 2024-03-11

# Trend chart (last 14 days by default)
python main.py trend weight
python main.py trend sleep_duration -D 30
python main.py trend exercise_min
```

Available trend metrics: `weight`, `sleep_duration`, `sleep_quality`, `exercise_min`, `calories_in`, `water`, `energy`, `mood`, `resting_hr`

### Date shorthand

All `-d` / `--date` flags accept:
- `YYYY-MM-DD` (e.g. `2024-03-15`)
- `today` (default)
- `yesterday`

## Project Structure

```
habit_tracker/
  __init__.py     Package init
  database.py     SQLite schema and connection management
  models.py       Dataclasses: ExerciseLog, DietLog, WaterLog, SleepLog, MetabolicLog
  tracker.py      CRUD operations via HabitTracker class
  cli.py          argparse-based CLI commands
  reports.py      DailySummary, WeeklySummary, trend charts

main.py           Entry point
tests/
  test_habit_tracker.py   33 unit tests
```

## Running Tests

```bash
python -m unittest tests/test_habit_tracker.py -v
```
