import csv
import io
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from ..auth import get_current_user
from .. import config
from ..database import get_db
from ..models import HealthRecord, User
from ..schemas import UNITS, RecordIn, RecordOut, RecordType

router = APIRouter(prefix="/api/health-records", tags=["Health records"])


def _own_query(db: Session, user: User):
    """Every query is restricted to the logged-in user's rows."""
    return db.query(HealthRecord).filter(HealthRecord.user_id == user.id)


def _get_own(db: Session, user: User, record_id: int) -> HealthRecord:
    rec = _own_query(db, user).filter(HealthRecord.id == record_id).first()
    if rec is None:  # 404 (not 403) so other users' ids are not revealed
        raise HTTPException(404, "Record not found")
    return rec


@router.get("", response_model=List[RecordOut])
def list_records(
    record_type: Optional[RecordType] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(500, ge=1, le=2000),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = _own_query(db, user)
    if record_type:
        q = q.filter(HealthRecord.record_type == record_type)
    if start_date:
        q = q.filter(HealthRecord.recorded_date >= start_date)
    if end_date:
        q = q.filter(HealthRecord.recorded_date <= end_date)
    return q.order_by(HealthRecord.recorded_date.desc(), HealthRecord.id.desc()).limit(limit).all()


@router.get("/summary")
def summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Dashboard numbers: total entries + latest record of each type."""
    latest = {}
    for rtype in UNITS:
        rec = (_own_query(db, user).filter(HealthRecord.record_type == rtype)
               .order_by(HealthRecord.recorded_date.desc(), HealthRecord.id.desc()).first())
        if rec:
            latest[rtype] = RecordOut.model_validate(rec)
    return {
        "total": _own_query(db, user).count(),
        "has_sample_data": _own_query(db, user).filter(HealthRecord.is_sample.is_(True)).count() > 0,
        "latest": latest,
    }


@router.get("/export.csv")
def export_csv(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = _own_query(db, user).order_by(HealthRecord.recorded_date, HealthRecord.id).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "type", "value", "value2_diastolic", "unit", "notes", "is_sample"])

    def safe(text):  # stop spreadsheet formula injection (=, +, -, @ at the start)
        text = text or ""
        return "'" + text if text[:1] in ("=", "+", "-", "@") else text

    for r in rows:
        writer.writerow([r.recorded_date.isoformat(), r.record_type, r.value,
                         "" if r.value2 is None else r.value2, r.unit, safe(r.notes), r.is_sample])
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=medimate_records.csv"})


@router.post("/demo-data", status_code=201)
def load_demo_data(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Demo mode only: add 14 days of clearly labelled SAMPLE records."""
    if not config.DEMO_MODE:
        raise HTTPException(403, "Demo mode is turned off")
    _own_query(db, user).filter(HealthRecord.is_sample.is_(True)).delete()
    hr = [72, 75, 70, 78, 74, 71, 73, 76, 72, 69, 74, 77, 71, 73]
    sys_ = [118, 121, 119, 122, 120, 117, 121, 123, 119, 118, 120, 122, 119, 121]
    dia = [78, 80, 79, 81, 79, 77, 80, 82, 78, 78, 79, 81, 78, 80]
    sleep = [7.2, 6.5, 7.8, 6.9, 7.1, 8.0, 6.2, 7.4, 7.0, 6.8, 7.5, 7.9, 6.6, 7.3]
    water = [1.8, 2.0, 1.5, 2.2, 1.9, 2.4, 1.6, 2.1, 1.7, 2.0, 2.3, 1.8, 1.9, 2.2]
    today = date.today()
    for i in range(14):
        d = today - timedelta(days=13 - i)
        for rtype, v, v2 in [("heart_rate", hr[i], None), ("blood_pressure", sys_[i], dia[i]),
                             ("sleep", sleep[i], None), ("water", water[i], None)]:
            db.add(HealthRecord(user_id=user.id, record_type=rtype, value=v, value2=v2,
                                unit=UNITS[rtype], recorded_date=d, notes="SAMPLE DATA", is_sample=True))
    db.commit()
    return {"added": 56, "message": "Sample data loaded. It is fictional demo data."}


@router.delete("/demo-data")
def clear_demo_data(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    n = _own_query(db, user).filter(HealthRecord.is_sample.is_(True)).delete()
    db.commit()
    return {"removed": n}


@router.post("", response_model=RecordOut, status_code=201)
def create_record(data: RecordIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rec = HealthRecord(user_id=user.id, record_type=data.record_type, value=data.value, value2=data.value2,
                       unit=UNITS[data.record_type], recorded_date=data.recorded_date, notes=data.notes)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


@router.put("/{record_id}", response_model=RecordOut)
def update_record(record_id: int, data: RecordIn, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    rec = _get_own(db, user, record_id)
    rec.record_type, rec.value, rec.value2 = data.record_type, data.value, data.value2
    rec.unit, rec.recorded_date, rec.notes = UNITS[data.record_type], data.recorded_date, data.notes
    rec.is_sample = False  # edited by the user, so it is no longer pure sample data
    db.commit()
    db.refresh(rec)
    return rec


@router.delete("/{record_id}", status_code=204)
def delete_record(record_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(_get_own(db, user, record_id))
    db.commit()
    return Response(status_code=204)
