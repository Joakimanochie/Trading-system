"""Risk management API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import settings
from agents.risk.limits import RiskLimits

router = APIRouter()


class RiskLimitsUpdate(BaseModel):
    max_drawdown_pct: float | None = None
    daily_loss_limit_pct: float | None = None
    max_leverage: float | None = None
    max_position_concentration: float | None = None
    confirm: bool = False


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
    return RiskLimits.from_settings().__dict__


@router.put("/limits")
def update_risk_limits(update: RiskLimitsUpdate):
    if not update.confirm:
        raise HTTPException(status_code=400, detail="Must set confirm=true to update risk limits")
    updated = {}
    if update.max_drawdown_pct is not None:
        settings.risk_max_drawdown_pct = update.max_drawdown_pct
        updated["max_drawdown_pct"] = update.max_drawdown_pct
    if update.daily_loss_limit_pct is not None:
        settings.risk_daily_loss_limit_pct = update.daily_loss_limit_pct
        updated["daily_loss_limit_pct"] = update.daily_loss_limit_pct
    if update.max_leverage is not None:
        settings.risk_max_leverage = update.max_leverage
        updated["max_leverage"] = update.max_leverage
    if update.max_position_concentration is not None:
        settings.risk_max_position_concentration = update.max_position_concentration
        updated["max_position_concentration"] = update.max_position_concentration
    return {"updated": updated, "current": RiskLimits.from_settings().__dict__}
