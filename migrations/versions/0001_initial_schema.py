"""Initial schema — all tables

Revision ID: 0001
Revises:
Create Date: 2026-06-05

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # strategies
    op.create_table(
        "strategies",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("asset_class", sa.String(50)),
        sa.Column("frequency", sa.String(20)),
        sa.Column("status", sa.String(30), nullable=False, server_default="IDEA_PROPOSED"),
        sa.Column("parameters", sa.JSON),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # strategy_ideas
    op.create_table(
        "strategy_ideas",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("source_url", sa.String(500)),
        sa.Column("source_type", sa.String(50)),
        sa.Column("abstract", sa.Text),
        sa.Column("hypothesis", sa.Text),
        sa.Column("methodology", sa.Text),
        sa.Column("asset_class", sa.String(50)),
        sa.Column("edge_claim", sa.Text),
        sa.Column("red_flags", sa.JSON),
        sa.Column("score_sharpe_potential", sa.Float),
        sa.Column("score_data_availability", sa.Float),
        sa.Column("score_complexity", sa.Float),
        sa.Column("score_capital_requirement", sa.Float),
        sa.Column("score_time_horizon", sa.Float),
        sa.Column("total_score", sa.Float),
        sa.Column("status", sa.String(30), nullable=False, server_default="PROPOSED"),
        sa.Column("nim_summary", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # signals
    op.create_table(
        "signals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("strategy_id", sa.Integer, sa.ForeignKey("strategies.id")),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("entry_price", sa.Float),
        sa.Column("stop_loss", sa.Float),
        sa.Column("take_profit_1", sa.Float),
        sa.Column("take_profit_2", sa.Float),
        sa.Column("position_size", sa.Float),
        sa.Column("metadata_json", sa.JSON),
        sa.Column("approved", sa.Boolean),
        sa.Column("approved_at", sa.DateTime),
        sa.Column("expires_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_signals_ticker_created", "signals", ["ticker", "created_at"])

    # crt_signals
    op.create_table(
        "crt_signals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("pair", sa.String(20), nullable=False),
        sa.Column("htf", sa.String(10), nullable=False),
        sa.Column("ltf", sa.String(10), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("anchor_timestamp", sa.DateTime),
        sa.Column("crt_high", sa.Float, nullable=False),
        sa.Column("crt_low", sa.Float, nullable=False),
        sa.Column("eq_50", sa.Float, nullable=False),
        sa.Column("entry", sa.Float),
        sa.Column("sl_conservative", sa.Float),
        sa.Column("sl_aggressive", sa.Float),
        sa.Column("tp1", sa.Float),
        sa.Column("tp2", sa.Float),
        sa.Column("sweep_timestamp", sa.DateTime),
        sa.Column("mss_timestamp", sa.DateTime),
        sa.Column("fvg_high", sa.Float),
        sa.Column("fvg_low", sa.Float),
        sa.Column("filter_pd_array", sa.Boolean, server_default="false"),
        sa.Column("filter_session_macro", sa.Boolean, server_default="false"),
        sa.Column("filter_premium_discount", sa.Boolean, server_default="false"),
        sa.Column("filter_nested_ltf", sa.Boolean, server_default="false"),
        sa.Column("filter_mss_fvg", sa.Boolean, server_default="false"),
        sa.Column("filters_passed_count", sa.Integer, server_default="0"),
        sa.Column("kaabar_patterns", sa.JSON),
        sa.Column("confluence_score", sa.Integer, server_default="0"),
        sa.Column("tp1_hit", sa.Boolean),
        sa.Column("tp2_hit", sa.Boolean),
        sa.Column("sl_hit", sa.Boolean),
        sa.Column("expired", sa.Boolean, server_default="false"),
        sa.Column("nim_rationale", sa.Text),
        sa.Column("chart_path", sa.String(500)),
        sa.Column("approved", sa.Boolean),
        sa.Column("approved_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_crt_signals_pair_created", "crt_signals", ["pair", "created_at"])

    # kaabar_pattern_results
    op.create_table(
        "kaabar_pattern_results",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("crt_signal_id", sa.Integer, sa.ForeignKey("crt_signals.id")),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("timeframe", sa.String(10), nullable=False),
        sa.Column("pattern_name", sa.String(100), nullable=False),
        sa.Column("pattern_category", sa.String(50)),
        sa.Column("direction", sa.String(10)),
        sa.Column("candle_timestamp", sa.DateTime),
        sa.Column("signal_value", sa.Integer),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_kaabar_ticker_tf_pattern",
        "kaabar_pattern_results",
        ["ticker", "timeframe", "pattern_name"],
    )

    # orders
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("signal_id", sa.Integer, sa.ForeignKey("signals.id")),
        sa.Column("broker_order_id", sa.String(100)),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("side", sa.String(10), nullable=False),
        sa.Column("quantity", sa.Float, nullable=False),
        sa.Column("order_type", sa.String(20), server_default="MARKET"),
        sa.Column("limit_price", sa.Float),
        sa.Column("status", sa.String(20), server_default="PENDING", nullable=False),
        sa.Column("filled_quantity", sa.Float, server_default="0"),
        sa.Column("avg_fill_price", sa.Float),
        sa.Column("theoretical_price", sa.Float),
        sa.Column("slippage_bps", sa.Float),
        sa.Column("broker", sa.String(50)),
        sa.Column("submitted_at", sa.DateTime),
        sa.Column("filled_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # trades
    op.create_table(
        "trades",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("order_id", sa.Integer, sa.ForeignKey("orders.id")),
        sa.Column("strategy_id", sa.Integer, sa.ForeignKey("strategies.id")),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("entry_price", sa.Float, nullable=False),
        sa.Column("exit_price", sa.Float),
        sa.Column("quantity", sa.Float, nullable=False),
        sa.Column("pnl", sa.Float),
        sa.Column("pnl_pct", sa.Float),
        sa.Column("commission", sa.Float, server_default="0"),
        sa.Column("entry_at", sa.DateTime, nullable=False),
        sa.Column("exit_at", sa.DateTime),
        sa.Column("duration_minutes", sa.Integer),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_trades_ticker_entry", "trades", ["ticker", "entry_at"])

    # performance_records
    op.create_table(
        "performance_records",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("strategy_id", sa.Integer, sa.ForeignKey("strategies.id"), nullable=False),
        sa.Column("period_start", sa.DateTime, nullable=False),
        sa.Column("period_end", sa.DateTime, nullable=False),
        sa.Column("sharpe_ratio", sa.Float),
        sa.Column("calmar_ratio", sa.Float),
        sa.Column("sortino_ratio", sa.Float),
        sa.Column("max_drawdown_pct", sa.Float),
        sa.Column("max_drawdown_duration_days", sa.Integer),
        sa.Column("cagr", sa.Float),
        sa.Column("win_rate", sa.Float),
        sa.Column("profit_factor", sa.Float),
        sa.Column("avg_trade_duration_mins", sa.Float),
        sa.Column("total_trades", sa.Integer),
        sa.Column("equity_curve", sa.JSON),
        sa.Column("metadata_json", sa.JSON),
        sa.Column("record_type", sa.String(20), server_default="backtest"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("timestamp", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("strategy_id", sa.String(100)),
        sa.Column("details", sa.JSON),
        sa.Column("outcome", sa.String(50)),
    )
    op.create_index("ix_audit_logs_timestamp_actor", "audit_logs", ["timestamp", "actor"])

    # ohlcv
    op.create_table(
        "ohlcv",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("timeframe", sa.String(10), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Float, nullable=False),
        sa.Column("high", sa.Float, nullable=False),
        sa.Column("low", sa.Float, nullable=False),
        sa.Column("close", sa.Float, nullable=False),
        sa.Column("volume", sa.Float),
        sa.UniqueConstraint("ticker", "timeframe", "timestamp", name="uq_ohlcv_ticker_tf_ts"),
    )
    op.create_index("ix_ohlcv_ticker_tf_ts", "ohlcv", ["ticker", "timeframe", "timestamp"])


def downgrade() -> None:
    op.drop_table("ohlcv")
    op.drop_table("audit_logs")
    op.drop_table("performance_records")
    op.drop_table("trades")
    op.drop_table("orders")
    op.drop_table("kaabar_pattern_results")
    op.drop_table("crt_signals")
    op.drop_table("signals")
    op.drop_table("strategy_ideas")
    op.drop_table("strategies")
