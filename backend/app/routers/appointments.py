from datetime import date, datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Appointment, User
from ..schemas import AppointmentIn, AppointmentOut

router = APIRouter(prefix="/api/appointments", tags=["Appointments (personal reminders)"])


def _get_own(db: Session, user: User, appt_id: int) -> Appointment:
    a = db.query(Appointment).filter(Appointment.id == appt_id, Appointment.user_id == user.id).first()
    if a is None:
        raise HTTPException(404, "Appointment not found")
    return a


def _must_be_future(d: date, t: str):
    when = datetime.strptime(f"{d.isoformat()} {t}", "%Y-%m-%d %H:%M")
    if when < datetime.now():
        raise HTTPException(422, "A scheduled appointment must be in the future")


@router.get("", response_model=List[AppointmentOut])
def list_appointments(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (db.query(Appointment).filter(Appointment.user_id == user.id)
            .order_by(Appointment.appt_date, Appointment.appt_time).all())


@router.post("", response_model=AppointmentOut, status_code=201)
def create_appointment(data: AppointmentIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.status == "scheduled":
        _must_be_future(data.appt_date, data.appt_time)
    a = Appointment(user_id=user.id, **data.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.put("/{appointment_id}", response_model=AppointmentOut)
def update_appointment(appointment_id: int, data: AppointmentIn, user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    a = _get_own(db, user, appointment_id)
    changed_when = (a.appt_date, a.appt_time) != (data.appt_date, data.appt_time)
    if data.status == "scheduled" and changed_when:
        _must_be_future(data.appt_date, data.appt_time)
    for field, value in data.model_dump().items():
        setattr(a, field, value)
    db.commit()
    db.refresh(a)
    return a


@router.delete("/{appointment_id}", status_code=204)
def delete_appointment(appointment_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(_get_own(db, user, appointment_id))
    db.commit()
    return Response(status_code=204)
