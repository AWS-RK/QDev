"""
Data models (dataclasses) for each habit category.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class ExerciseLog:
    date: str
    type: str
    duration_min: int
    intensity: str          # 'low' | 'moderate' | 'high'
    calories: Optional[int] = None
    notes: Optional[str] = None
    id: Optional[int] = None

    def validate(self) -> None:
        if self.intensity not in ("low", "moderate", "high"):
            raise ValueError("intensity must be 'low', 'moderate', or 'high'")
        if self.duration_min <= 0:
            raise ValueError("duration_min must be positive")
        _validate_date(self.date)

    @property
    def duration_hours(self) -> float:
        return round(self.duration_min / 60, 2)


@dataclass
class DietLog:
    date: str
    meal: str               # 'breakfast' | 'lunch' | 'dinner' | 'snack'
    description: str
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    notes: Optional[str] = None
    id: Optional[int] = None

    def validate(self) -> None:
        if self.meal not in ("breakfast", "lunch", "dinner", "snack"):
            raise ValueError("meal must be 'breakfast', 'lunch', 'dinner', or 'snack'")
        if not self.description.strip():
            raise ValueError("description cannot be empty")
        _validate_date(self.date)


@dataclass
class WaterLog:
    date: str
    amount_ml: int
    id: Optional[int] = None

    def validate(self) -> None:
        if self.amount_ml <= 0:
            raise ValueError("amount_ml must be positive")
        _validate_date(self.date)

    @property
    def amount_oz(self) -> float:
        return round(self.amount_ml / 29.5735, 1)


@dataclass
class SleepLog:
    date: str
    bedtime: str        # HH:MM (24h)
    wake_time: str      # HH:MM (24h)
    duration_hours: float
    quality: int        # 1-10
    notes: Optional[str] = None
    id: Optional[int] = None

    def validate(self) -> None:
        if not (1 <= self.quality <= 10):
            raise ValueError("quality must be between 1 and 10")
        if self.duration_hours <= 0:
            raise ValueError("duration_hours must be positive")
        _validate_date(self.date)


@dataclass
class MetabolicLog:
    date: str
    weight_kg: Optional[float] = None
    body_fat_pct: Optional[float] = None
    resting_hr: Optional[int] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    blood_glucose: Optional[float] = None
    energy_level: Optional[int] = None   # 1-10
    mood: Optional[int] = None           # 1-10
    notes: Optional[str] = None
    id: Optional[int] = None

    def validate(self) -> None:
        _validate_date(self.date)
        if self.energy_level is not None and not (1 <= self.energy_level <= 10):
            raise ValueError("energy_level must be between 1 and 10")
        if self.mood is not None and not (1 <= self.mood <= 10):
            raise ValueError("mood must be between 1 and 10")
        if self.body_fat_pct is not None and not (0 <= self.body_fat_pct <= 100):
            raise ValueError("body_fat_pct must be between 0 and 100")

    @property
    def bmi(self) -> Optional[float]:
        """Requires weight_kg to be set; height must be provided externally."""
        return None  # BMI calculation requires height; see reports module

    @property
    def blood_pressure(self) -> Optional[str]:
        if self.systolic_bp and self.diastolic_bp:
            return f"{self.systolic_bp}/{self.diastolic_bp}"
        return None


def _validate_date(date_str: str) -> None:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"date must be in YYYY-MM-DD format, got: {date_str!r}")


def today() -> str:
    return date.today().isoformat()
