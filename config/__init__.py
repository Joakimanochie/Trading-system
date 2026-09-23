"""
Single Settings class loading from .env + YAML.
Usage:
    from config import settings
    print(settings.database_url)
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_CONFIG_DIR = Path(__file__).parent
_ROOT_DIR = _CONFIG_DIR.parent


def _load_yaml(filename: str) -> dict[str, Any]:
    path = _CONFIG_DIR / filename
    if not path.exists():
        return {}
    with path.open() as f:
        return yaml.safe_load(f) or {}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    app_secret_key: str = "change-me-in-production"
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/quant_os"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # OpenRouter / owl-alpha
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openrouter/owl-alpha"
    openrouter_max_tokens: int = 16384
    openrouter_temperature: float = 0.6
    openrouter_stream: bool = True

    # Broker — Alpaca
    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""
    alpaca_base_url: str = "https://paper-api.alpaca.markets"
    alpaca_data_url: str = "https://data.alpaca.markets"

    # Broker — IBKR
    ibkr_host: str = "127.0.0.1"
    ibkr_port: int = 7497
    ibkr_client_id: int = 1

    # Broker — Binance
    binance_api_key: str = ""
    binance_secret_key: str = ""
    binance_testnet: bool = True

    # MT5
    mt5_login: str = ""
    mt5_password: str = ""
    mt5_server: str = ""
    mt5_timezone: str = "Europe/Paris"
    mt5_enabled: bool = False

    # CRT Agent
    crt_htf: str = "H4"
    crt_ltf: str = "M5"
    crt_pairs: str = "EURUSD,GBPUSD,USDCHF,USDCAD,AUDUSD,USDJPY,NZDUSD,XAUUSD,BTCUSD,ETHUSD"
    crt_filter_pd_array: bool = True
    crt_filter_session_macro: bool = True
    crt_filter_premium_discount: bool = True
    crt_filter_nested_ltf: bool = True
    crt_filter_mss_fvg: bool = True
    crt_scan_interval_seconds: int = 60
    crt_sl_mode: str = "conservative"
    crt_min_confluence_score: int = 0

    # Photon Agent
    photon_pairs: str = "EURUSD,GBPUSD,USDCHF,USDCAD,AUDUSD,USDJPY,NZDUSD,XAUUSD"

    # Data providers
    polygon_api_key: str = ""
    fred_api_key: str = ""
    yahoo_finance_enabled: bool = True

    # Notifications
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    email_smtp_host: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_alert_recipient: str = ""

    # Risk
    risk_max_drawdown_pct: float = 0.15
    risk_daily_loss_limit_pct: float = 0.02
    risk_max_leverage: float = 2.0
    risk_max_position_concentration: float = 0.20
    risk_kelly_fraction: float = 0.50

    # Execution
    execution_mode: str = "MANUAL"
    signal_approval_timeout_mins: int = 30
    paper_trade_min_weeks: int = 4

    # Backtesting
    backtest_engine: str = "vectorbt"
    backtest_commission_bps: int = 5
    backtest_slippage_bps: int = 2
    backtest_min_trades: int = 100

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    @field_validator("crt_pairs", mode="before")
    @classmethod
    def parse_crt_pairs(cls, v: Any) -> Any:
        return v  # kept as comma-separated string; use .split(",") at call site

    @property
    def crt_pairs_list(self) -> list[str]:
        return [p.strip() for p in self.crt_pairs.split(",") if p.strip()]

    @property
    def photon_pairs_list(self) -> list[str]:
        return [p.strip() for p in self.photon_pairs.split(",") if p.strip()]

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Module-level singleton for convenient import
settings = get_settings()
