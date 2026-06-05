from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db import get_db
from db.models import PerformanceRecord

router = APIRouter()


@router.get("/")
def list_performance(strategy_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(PerformanceRecord)
    if strategy_id:
        q = q.filter(PerformanceRecord.strategy_id == strategy_id)
    return q.order_by(PerformanceRecord.created_at.desc()).limit(50).all()
