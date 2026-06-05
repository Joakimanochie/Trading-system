from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db import get_db
from db.models import Strategy, StrategyIdea

router = APIRouter()


@router.get("/")
def list_strategies(db: Session = Depends(get_db)):
    return db.query(Strategy).all()


@router.get("/ideas")
def list_ideas(db: Session = Depends(get_db)):
    return db.query(StrategyIdea).all()


@router.post("/ideas/{idea_id}/approve")
def approve_idea(idea_id: int, db: Session = Depends(get_db)):
    from db.models import IdeaStatus
    idea = db.query(StrategyIdea).filter(StrategyIdea.id == idea_id).first()
    if not idea:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Idea not found")
    idea.status = IdeaStatus.APPROVED
    db.commit()
    return {"id": idea_id, "status": "approved"}
