from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db import get_db
from db.models import CRTSignal

router = APIRouter()


@router.get("/signals")
def list_crt_signals(pair: str | None = None, db: Session = Depends(get_db)):
    q = db.query(CRTSignal)
    if pair:
        q = q.filter(CRTSignal.pair == pair)
    return q.order_by(CRTSignal.created_at.desc()).limit(50).all()


@router.post("/signals/{signal_id}/approve")
def approve_crt_signal(signal_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    from datetime import datetime, timezone

    sig = db.query(CRTSignal).filter(CRTSignal.id == signal_id).first()
    if not sig:
        raise HTTPException(status_code=404, detail="CRT signal not found")
    sig.approved = True
    sig.approved_at = datetime.now(timezone.utc)
    db.commit()
    return {"id": signal_id, "status": "approved"}


@router.post("/signals/{signal_id}/reject")
def reject_crt_signal(signal_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    from datetime import datetime, timezone

    sig = db.query(CRTSignal).filter(CRTSignal.id == signal_id).first()
    if not sig:
        raise HTTPException(status_code=404, detail="CRT signal not found")
    sig.approved = False
    sig.approved_at = datetime.now(timezone.utc)
    db.commit()
    return {"id": signal_id, "status": "rejected"}
