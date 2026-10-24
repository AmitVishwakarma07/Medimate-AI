"""Database tables (SQLAlchemy)."""
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint

from .database import Base


def now_utc():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # bcrypt hash, never the password
    created_at = Column(DateTime(timezone=True), default=now_utc)
    # Optional lifestyle info used by the recommendation engine
    goals = Column(String(200), default="")               # comma-separated goal keys
    activity_level = Column(String(20), nullable=True)    # sedentary / light / moderate / active
    has_restrictions = Column(Boolean, default=False)     # dietary/medical restrictions exist
    ai_consent = Column(Boolean, default=False)           # allow chat text to go to an external AI


class HealthRecord(Base):
    __tablename__ = "health_records"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    record_type = Column(String(30), index=True, nullable=False)
    value = Column(Float, nullable=False)                 # for blood pressure: systolic
    value2 = Column(Float, nullable=True)                 # for blood pressure: diastolic
    unit = Column(String(20), nullable=False)
    recorded_date = Column(Date, index=True, nullable=False)
    notes = Column(String(500), nullable=True)
    is_sample = Column(Boolean, default=False)            # True only for demo-mode sample rows
    created_at = Column(DateTime(timezone=True), default=now_utc)


class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    title = Column(String(120), nullable=False)
    provider = Column(String(120), nullable=False)        # doctor or clinic name (demo only)
    appt_date = Column(Date, nullable=False)
    appt_time = Column(String(5), nullable=False)         # "HH:MM"
    notes = Column(String(500), nullable=True)
    status = Column(String(20), default="scheduled")      # scheduled / completed / cancelled
    created_at = Column(DateTime(timezone=True), default=now_utc)


class RecommendationProgress(Base):
    __tablename__ = "recommendation_progress"
    __table_args__ = (UniqueConstraint("user_id", "rec_key"),)
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    rec_key = Column(String(50), nullable=False)
    completed = Column(Boolean, default=False)
