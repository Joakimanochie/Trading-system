from fastapi import APIRouter
from config import settings

router = APIRouter()


@router.get("/state")
def get_risk_state():
    return {
        "max_drawdown_pct": settings.risk_max_drawdown_pct,
        "daily_loss_limit_pct": settings.risk_daily_loss_limit_pct,
        "max_leverage": settings.risk_max_leverage,
        "max_position_concentration": settings.risk_max_position_concentration,
        "kelly_fraction": settings.risk_kelly_fraction,
    }


@router.get("/limits")
def get_risk_limits():
    return get_risk_state()
