"""API endpoints for backtesting."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from db.models import PerformanceRecord, Strategy, StrategyStatus

router = APIRouter()


class BacktestRequest(BaseModel):
    ticker: str = "SPY"
    lookback: int = 20
    strategy_name: str = "momentum_sma_crossover"


@router.post("/run")
def run_backtest_endpoint(req: BacktestRequest, db: Session = Depends(get_db)):
    """Run a backtest for a given strategy and ticker using data from the DB."""
    import pandas as pd
    from db.models import OHLCV

    rows = (
        db.query(OHLCV)
        .filter(OHLCV.ticker == req.ticker)
        .order_by(OHLCV.timestamp)
        .all()
    )
    if len(rows) < 50:
        raise HTTPException(status_code=400, detail=f"Not enough data for {req.ticker} ({len(rows)} rows)")

    data = pd.DataFrame(
        [{"open": r.open, "high": r.high, "low": r.low, "close": r.close, "volume": r.volume} for r in rows],
        index=pd.DatetimeIndex([r.timestamp for r in rows]),
    )

    from strategies.momentum import MomentumStrategy
    from agents.backtesting.runner import run_backtest

    strategy = MomentumStrategy(lookback=req.lookback)
    result = run_backtest(strategy, data, ticker=req.ticker, parameters={"lookback": float(req.lookback)})

    strat = db.query(Strategy).filter(Strategy.name == req.strategy_name).first()
    if not strat:
        strat = Strategy(name=req.strategy_name, description=strategy.description, status=StrategyStatus.BACKTESTING)
        db.add(strat)
        db.flush()

    record = PerformanceRecord(
        strategy_id=strat.id,
        period_start=result.report.period_start,
        period_end=result.report.period_end,
        sharpe_ratio=result.report.sharpe_ratio,
        calmar_ratio=result.report.calmar_ratio,
        sortino_ratio=result.report.sortino_ratio,
        max_drawdown_pct=result.report.max_drawdown_pct,
        max_drawdown_duration_days=result.report.max_drawdown_duration_days,
        cagr=result.report.cagr,
        win_rate=result.report.win_rate,
        profit_factor=result.report.profit_factor,
        avg_trade_duration_mins=result.report.avg_trade_duration_mins,
        total_trades=result.report.total_trades,
        equity_curve=result.report.equity_curve,
        record_type="backtest",
        metadata_json={
            "ticker": req.ticker,
            "lookback": req.lookback,
            "bias_checks": {
                "look_ahead": result.bias_checks.look_ahead_passed,
                "survivorship": result.bias_checks.survivorship_passed,
            },
            "walk_forward": {
                "avg_is_sharpe": result.walk_forward.avg_is_sharpe,
                "avg_oos_sharpe": result.walk_forward.avg_oos_sharpe,
                "degradation_pct": result.walk_forward.degradation_pct,
            },
            "monte_carlo": {
                "p_value": result.monte_carlo.p_value,
                "significant": result.monte_carlo.significant,
            },
            "overfitting_flags": result.overfitting_flags,
        },
    )
    db.add(record)
    db.commit()

    return {
        "id": record.id,
        "strategy": req.strategy_name,
        "ticker": req.ticker,
        "sharpe": result.report.sharpe_ratio,
        "total_return": f"{result.report.total_return * 100:.2f}%",
        "total_trades": result.report.total_trades,
        "max_drawdown": f"{result.report.max_drawdown_pct * 100:.2f}%",
        "walk_forward_degradation": f"{result.walk_forward.degradation_pct:.1f}%",
        "monte_carlo_p_value": result.monte_carlo.p_value,
        "overfitting_flags": result.overfitting_flags,
    }


@router.get("/{backtest_id}/report")
def get_backtest_report(backtest_id: int, db: Session = Depends(get_db)):
    record = db.query(PerformanceRecord).filter(PerformanceRecord.id == backtest_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return record
