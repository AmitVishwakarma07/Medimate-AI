"""Request/response shapes and input validation (Pydantic).
NOTE: the numeric ranges below only reject impossible typing mistakes
(e.g. a heart rate of 9999). They are NOT medical thresholds."""
import re
from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .passwords import check_password_strength

RecordType = Literal["heart_rate", "blood_pressure", "sleep", "water", "weight", "activity"]
UNITS = {
    "heart_rate": "bpm", "blood_pressure": "mmHg", "sleep": "hours",
    "water": "litres", "weight": "kg", "activity": "minutes",
}
INPUT_LIMITS = {
    "heart_rate": (20, 250), "blood_pressure": (50, 260), "sleep": (0, 24),
    "water": (0, 10), "weight": (1, 500), "activity": (0, 1440),
}
GOALS = ["better_sleep", "hydration", "be_active", "balanced_diet", "manage_stress"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------- auth / profile ----------
class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: str = Field(max_length=255)
    password: str = Field(min_length=10, max_length=72)

    @field_validator("email")
    @classmethod
    def check_email(cls, v):
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("Enter a valid email address")
        return v

    @field_validator("name")
    @classmethod
    def clean_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        return v

    @field_validator("password")
    @classmethod
    def check_password(cls, v):
        if len(v.encode("utf-8")) > 72:  # bcrypt only uses the first 72 bytes
            raise ValueError("Password is too long (max 72 bytes)")
        return v

    @model_validator(mode="after")
    def check_strength(self):
        problem = check_password_strength(self.password, self.email)
        if problem:
            raise ValueError(problem)
        return self


class LoginIn(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def norm_email(cls, v):
        return v.strip().lower()


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    goals: List[str] = []
    activity_level: Optional[str] = None
    has_restrictions: bool = False
    ai_consent: bool = False


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    goals: Optional[List[Literal["better_sleep", "hydration", "be_active", "balanced_diet", "manage_stress"]]] = None
    activity_level: Optional[Literal["sedentary", "light", "moderate", "active"]] = None
    has_restrictions: Optional[bool] = None
    ai_consent: Optional[bool] = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: ProfileOut


# ---------- health records ----------
class RecordIn(BaseModel):
    record_type: RecordType
    value: float
    value2: Optional[float] = None  # diastolic, only for blood_pressure
    recorded_date: date
    notes: Optional[str] = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def check_values(self):
        lo, hi = INPUT_LIMITS[self.record_type]
        if not (lo <= self.value <= hi):
            raise ValueError(f"value must be between {lo} and {hi} {UNITS[self.record_type]}")
        if self.record_type == "blood_pressure":
            if self.value2 is None:
                raise ValueError("Blood pressure needs both systolic (value) and diastolic (value2)")
            if not (30 <= self.value2 <= 200) or self.value2 >= self.value:
                raise ValueError("Diastolic must be between 30 and 200 and lower than systolic")
        elif self.value2 is not None:
            raise ValueError("value2 is only used for blood_pressure")
        if self.recorded_date > date.today():
            raise ValueError("recorded_date cannot be in the future")
        return self


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    record_type: str
    value: float
    value2: Optional[float]
    unit: str
    recorded_date: date
    notes: Optional[str]
    is_sample: bool


# ---------- appointments ----------
class AppointmentIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    provider: str = Field(min_length=1, max_length=120)
    appt_date: date
    appt_time: str
    notes: Optional[str] = Field(default=None, max_length=500)
    status: Literal["scheduled", "completed", "cancelled"] = "scheduled"

    @field_validator("appt_time")
    @classmethod
    def check_time(cls, v):
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError("Time must be in HH:MM (24-hour) format")
        return v

    @field_validator("title", "provider")
    @classmethod
    def strip_text(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("This field cannot be empty")
        return v


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    provider: str
    appt_date: date
    appt_time: str
    notes: Optional[str]
    status: str


# ---------- chat / recommendations ----------
class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class ChatOut(BaseModel):
    reply: str
    source: Literal["rule_based", "llm"]
    emergency: bool = False
    disclaimer: str


class RecProgressIn(BaseModel):
    completed: bool


# ---------- account & privacy ----------
class DeleteAccountIn(BaseModel):
    password: str


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=10, max_length=72)
