from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import HealthRecord, RecommendationProgress, User
from ..schemas import RecProgressIn
from ..services import recommendation_service as svc

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])
VALID_KEYS = set(svc.CATALOG) | {"see_professional_restrictions"}


@router.get("")
def get_recommendations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    since = date.today() - timedelta(days=14)
    recent = (db.query(HealthRecord).filter(HealthRecord.user_id == user.id,
                                            HealthRecord.recorded_date >= since).all())
    done = {p.rec_key for p in db.query(RecommendationProgress)
            .filter(RecommendationProgress.user_id == user.id, RecommendationProgress.completed.is_(True))}
    goals = [g for g in (user.goals or "").split(",") if g]
    return svc.build(goals, user.activity_level, bool(user.has_restrictions), svc.compute_stats(recent), done)


@router.put("/{key}")
def mark_recommendation(key: str, data: RecProgressIn, user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    if key not in VALID_KEYS:
        raise HTTPException(404, "Unknown recommendation")
    row = (db.query(RecommendationProgress)
           .filter(RecommendationProgress.user_id == user.id, RecommendationProgress.rec_key == key).first())
    if row is None:
        row = RecommendationProgress(user_id=user.id, rec_key=key)
        db.add(row)
    row.completed = data.completed
    db.commit()
    return {"key": key, "completed": row.completed}
