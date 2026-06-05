from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db import get_db
from db.models import Signal

router = APIRouter()


@router.get("/")
def list_signals(approved: bool | None = None, db: Session = Depends(get_db)):
    q = db.query(Signal)
    if approved is not None:
        q = q.filter(Signal.approved == approved)
    return q.order_by(Signal.created_at.desc()).limit(100).all()
