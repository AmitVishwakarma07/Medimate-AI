"""Privacy features: download all my data, change password, delete my account and everything in it."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..auth import clear_session_cookie, get_current_user, hash_password, verify_password
from ..database import get_db
from ..models import Appointment, HealthRecord, RecommendationProgress, User
from ..schemas import AppointmentOut, ChangePasswordIn, DeleteAccountIn, RecordOut
from ..passwords import check_password_strength
from ..security import log, login_fail_limiter, raise_if_blocked
from .auth import profile_out

router = APIRouter(prefix="/api/account", tags=["Account & privacy"])


def _check_current_password(user: User, password: str):
    """Re-checks the password; wrong guesses count towards the same lock-out as login."""
    key = f"user:{user.id}"
    raise_if_blocked(login_fail_limiter, key, "Too many wrong passwords. Please try again later.")
    if not verify_password(password, user.password_hash):
        login_fail_limiter.hit(key)
        raise HTTPException(403, "Incorrect password")
    login_fail_limiter.reset(key)


@router.get("/export")
def export_my_data(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Everything stored about this user, as a JSON download (right of access / portability)."""
    records = db.query(HealthRecord).filter(HealthRecord.user_id == user.id).order_by(HealthRecord.recorded_date).all()
    appts = db.query(Appointment).filter(Appointment.user_id == user.id).order_by(Appointment.appt_date).all()
    progress = db.query(RecommendationProgress).filter(RecommendationProgress.user_id == user.id).all()
    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "profile": profile_out(user).model_dump(),
        "health_records": [RecordOut.model_validate(r).model_dump(mode="json") for r in records],
        "appointments": [AppointmentOut.model_validate(a).model_dump(mode="json") for a in appts],
        "recommendation_progress": [{"key": p.rec_key, "completed": p.completed} for p in progress],
    }
    return JSONResponse(payload, headers={"Content-Disposition": "attachment; filename=medimate_my_data.json"})


@router.put("/password")
def change_password(data: ChangePasswordIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _check_current_password(user, data.current_password)
    problem = check_password_strength(data.new_password, user.email)
    if problem:
        raise HTTPException(422, problem)
    user.password_hash = hash_password(data.new_password)
    db.commit()
    log.info("password changed user_id=%s", user.id)
    return {"message": "Password changed"}


@router.delete("", status_code=204)
def delete_account(data: DeleteAccountIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Permanently deletes the user and ALL their data (right of erasure)."""
    _check_current_password(user, data.password)
    for model in (HealthRecord, Appointment, RecommendationProgress):
        db.query(model).filter(model.user_id == user.id).delete()
    db.delete(user)
    db.commit()
    log.info("account deleted user_id=%s", user.id)
    resp = Response(status_code=204)
    clear_session_cookie(resp)
    return resp
