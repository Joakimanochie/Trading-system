"""SQLAlchemy ORM models for quant-os."""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


# ─── Enums ────────────────────────────────────────────────────────────────────


class StrategyStatus(str, enum.Enum):
    IDEA_PROPOSED = "IDEA_PROPOSED"
    BACKTESTING = "BACKTESTING"
    RISK_REVIEW = "RISK_REVIEW"
    PAPER_TRADING = "PAPER_TRADING"
    LIVE_TRADING = "LIVE_TRADING"
    PAUSED = "PAUSED"
    RETIRED = "RETIRED"


class SignalDirection(str, enum.Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class OrderSide(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class IdeaStatus(str, enum.Enum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    BACKTESTING = "BACKTESTING"


# ─── Core Strategy ────────────────────────────────────────────────────────────


class Strategy(Base):
    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    asset_class: Mapped[str | None] = mapped_column(String(50))
    frequency: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[StrategyStatus] = mapped_column(
        Enum(StrategyStatus), default=StrategyStatus.IDEA_PROPOSED, nullable=False
    )
    parameters: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    signals: Mapped[list[Signal]] = relationship("Signal", back_populates="strategy")
    performance_records: Mapped[list[PerformanceRecord]] = relationship(
        "PerformanceRecord", back_populates="strategy"
    )


# ─── Signals ──────────────────────────────────────────────────────────────────


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    strategy_id: Mapped[int | None] = mapped_column(ForeignKey("strategies.id"))
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[SignalDirection] = mapped_column(Enum(SignalDirection), nullable=False)
    entry_price: Mapped[float | None] = mapped_column(Float)
    stop_loss: Mapped[float | None] = mapped_column(Float)
    take_profit_1: Mapped[float | None] = mapped_column(Float)
    take_profit_2: Mapped[float | None] = mapped_column(Float)
    position_size: Mapped[float | None] = mapped_column(Float)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    approved: Mapped[bool | None] = mapped_column(Boolean)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    strategy: Mapped[Strategy | None] = relationship("Strategy", back_populates="signals")
    orders: Mapped[list[Order]] = relationship("Order", back_populates="signal")

    __table_args__ = (Index("ix_signals_ticker_created", "ticker", "created_at"),)


# ─── CRT Signal ───────────────────────────────────────────────────────────────


class CRTSignal(Base):
    __tablename__ = "crt_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pair: Mapped[str] = mapped_column(String(20), nullable=False)
    htf: Mapped[str] = mapped_column(String(10), nullable=False)
    ltf: Mapped[str] = mapped_column(String(10), nullable=False)
    direction: Mapped[SignalDirection] = mapped_column(Enum(SignalDirection), nullable=False)

    # Anchor candle
    anchor_timestamp: Mapped[datetime | None] = mapped_column(DateTime)
    crt_high: Mapped[float] = mapped_column(Float, nullable=False)
    crt_low: Mapped[float] = mapped_column(Float, nullable=False)
    eq_50: Mapped[float] = mapped_column(Float, nullable=False)

    # Levels
    entry: Mapped[float | None] = mapped_column(Float)
    sl_conservative: Mapped[float | None] = mapped_column(Float)
    sl_aggressive: Mapped[float | None] = mapped_column(Float)
    tp1: Mapped[float | None] = mapped_column(Float)
    tp2: Mapped[float | None] = mapped_column(Float)

    # Pipeline step metadata
    sweep_timestamp: Mapped[datetime | None] = mapped_column(DateTime)
    mss_timestamp: Mapped[datetime | None] = mapped_column(DateTime)
    fvg_high: Mapped[float | None] = mapped_column(Float)
    fvg_low: Mapped[float | None] = mapped_column(Float)

    # Filters
    filter_pd_array: Mapped[bool] = mapped_column(Boolean, default=False)
    filter_session_macro: Mapped[bool] = mapped_column(Boolean, default=False)
    filter_premium_discount: Mapped[bool] = mapped_column(Boolean, default=False)
    filter_nested_ltf: Mapped[bool] = mapped_column(Boolean, default=False)
    filter_mss_fvg: Mapped[bool] = mapped_column(Boolean, default=False)
    filters_passed_count: Mapped[int] = mapped_column(Integer, default=0)

    # Kaabar confluence
    kaabar_patterns: Mapped[list | None] = mapped_column(JSON)
    confluence_score: Mapped[int] = mapped_column(Integer, default=0)

    # Outcome tracking
    tp1_hit: Mapped[bool | None] = mapped_column(Boolean)
    tp2_hit: Mapped[bool | None] = mapped_column(Boolean)
    sl_hit: Mapped[bool | None] = mapped_column(Boolean)
    expired: Mapped[bool] = mapped_column(Boolean, default=False)

    # Rationale from GLM-5.1
    nim_rationale: Mapped[str | None] = mapped_column(Text)

    # Chart export path
    chart_path: Mapped[str | None] = mapped_column(String(500))

    approved: Mapped[bool | None] = mapped_column(Boolean)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (Index("ix_crt_signals_pair_created", "pair", "created_at"),)


# ─── Kaabar Pattern Results ───────────────────────────────────────────────────


class KaabarPatternResult(Base):
    __tablename__ = "kaabar_pattern_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    crt_signal_id: Mapped[int | None] = mapped_column(ForeignKey("crt_signals.id"))
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    pattern_name: Mapped[str] = mapped_column(String(100), nullable=False)
    pattern_category: Mapped[str | None] = mapped_column(String(50))
    direction: Mapped[SignalDirection | None] = mapped_column(Enum(SignalDirection))
    candle_timestamp: Mapped[datetime | None] = mapped_column(DateTime)
    signal_value: Mapped[int | None] = mapped_column(Integer)  # +1 bull, -1 bear
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_kaabar_ticker_tf_pattern", "ticker", "timeframe", "pattern_name"),
    )


# ─── Orders ───────────────────────────────────────────────────────────────────


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    signal_id: Mapped[int | None] = mapped_column(ForeignKey("signals.id"))
    broker_order_id: Mapped[str | None] = mapped_column(String(100))
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    side: Mapped[OrderSide] = mapped_column(Enum(OrderSide), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    order_type: Mapped[str] = mapped_column(String(20), default="MARKET")
    limit_price: Mapped[float | None] = mapped_column(Float)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False
    )
    filled_quantity: Mapped[float] = mapped_column(Float, default=0.0)
    avg_fill_price: Mapped[float | None] = mapped_column(Float)
    theoretical_price: Mapped[float | None] = mapped_column(Float)
    slippage_bps: Mapped[float | None] = mapped_column(Float)
    broker: Mapped[str | None] = mapped_column(String(50))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)
    filled_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    signal: Mapped[Signal | None] = relationship("Signal", back_populates="orders")
    trade: Mapped[Trade | None] = relationship("Trade", back_populates="order", uselist=False)


# ─── Trades ───────────────────────────────────────────────────────────────────


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"))
    strategy_id: Mapped[int | None] = mapped_column(ForeignKey("strategies.id"))
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[SignalDirection] = mapped_column(Enum(SignalDirection), nullable=False)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    exit_price: Mapped[float | None] = mapped_column(Float)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    pnl: Mapped[float | None] = mapped_column(Float)
    pnl_pct: Mapped[float | None] = mapped_column(Float)
    commission: Mapped[float] = mapped_column(Float, default=0.0)
    entry_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    exit_at: Mapped[datetime | None] = mapped_column(DateTime)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    order: Mapped[Order | None] = relationship("Order", back_populates="trade")

    __table_args__ = (Index("ix_trades_ticker_entry", "ticker", "entry_at"),)


# ─── Performance Records ──────────────────────────────────────────────────────


class PerformanceRecord(Base):
    __tablename__ = "performance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    strategy_id: Mapped[int] = mapped_column(ForeignKey("strategies.id"), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    sharpe_ratio: Mapped[float | None] = mapped_column(Float)
    calmar_ratio: Mapped[float | None] = mapped_column(Float)
    sortino_ratio: Mapped[float | None] = mapped_column(Float)
    max_drawdown_pct: Mapped[float | None] = mapped_column(Float)
    max_drawdown_duration_days: Mapped[int | None] = mapped_column(Integer)
    cagr: Mapped[float | None] = mapped_column(Float)
    win_rate: Mapped[float | None] = mapped_column(Float)
    profit_factor: Mapped[float | None] = mapped_column(Float)
    avg_trade_duration_mins: Mapped[float | None] = mapped_column(Float)
    total_trades: Mapped[int | None] = mapped_column(Integer)
    equity_curve: Mapped[list | None] = mapped_column(JSON)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    record_type: Mapped[str] = mapped_column(String(20), default="backtest")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    strategy: Mapped[Strategy] = relationship("Strategy", back_populates="performance_records")


# ─── Strategy Ideas ───────────────────────────────────────────────────────────


class StrategyIdea(Base):
    __tablename__ = "strategy_ideas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500))
    source_type: Mapped[str | None] = mapped_column(String(50))  # arxiv | ssrn | quantconnect
    abstract: Mapped[str | None] = mapped_column(Text)
    hypothesis: Mapped[str | None] = mapped_column(Text)
    methodology: Mapped[str | None] = mapped_column(Text)
    asset_class: Mapped[str | None] = mapped_column(String(50))
    edge_claim: Mapped[str | None] = mapped_column(Text)
    red_flags: Mapped[list | None] = mapped_column(JSON)
    score_sharpe_potential: Mapped[float | None] = mapped_column(Float)
    score_data_availability: Mapped[float | None] = mapped_column(Float)
    score_complexity: Mapped[float | None] = mapped_column(Float)
    score_capital_requirement: Mapped[float | None] = mapped_column(Float)
    score_time_horizon: Mapped[float | None] = mapped_column(Float)
    total_score: Mapped[float | None] = mapped_column(Float)
    status: Mapped[IdeaStatus] = mapped_column(
        Enum(IdeaStatus), default=IdeaStatus.PROPOSED, nullable=False
    )
    nim_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


# ─── Audit Log ────────────────────────────────────────────────────────────────


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    strategy_id: Mapped[str | None] = mapped_column(String(100))
    details: Mapped[dict | None] = mapped_column(JSON)
    outcome: Mapped[str | None] = mapped_column(String(50))

    __table_args__ = (Index("ix_audit_logs_timestamp_actor", "timestamp", "actor"),)
