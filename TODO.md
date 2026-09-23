# Quant Trading Agentic OS — Build To-Do List

> Work top to bottom. Complete each phase before starting the next.
> ✋ = mandatory human checkpoint — review and sign off before proceeding.
> 📅 = Day 7 target — must be done by end of day 7.

---

## Phase 0 — Foundation & Infrastructure

### Repository & Environment
- [ ] 📅 Create GitHub repo: `quant-os` with `main` and `dev` branch strategy
- [x] 📅 Set up Python 3.11+ virtual environment
- [x] 📅 Create `pyproject.toml` with project metadata and dev dependencies
- [x] 📅 Create `requirements.txt`: fastapi, uvicorn, sqlalchemy, alembic, redis, celery, pandas, numpy, vectorbt, openai, MetaTrader5, matplotlib, mplfinance, python-dotenv, pytest
  - `openai>=1.30.0` is used for ALL LLM calls — base_url is overridden to point at OpenRouter (`https://openrouter.ai/api/v1`). No `anthropic` package required.
- [x] 📅 Create `.env.example` with all required env var keys (see Section 7 of Master Plan)
- [x] 📅 Create `.gitignore` — exclude `.env`, `__pycache__`, `.venv`, `*.pyc`, data files, chart exports
- [x] 📅 Set up pre-commit hooks: black, ruff, mypy

### Database
- [x] 📅 Install and run PostgreSQL locally (or via Docker)
- [x] 📅 Create `db/models.py`: SQLAlchemy models for `Strategy`, `Signal`, `Order`, `Trade`, `PerformanceRecord`, `AuditLog`, `StrategyIdea`, `CRTSignal`, `KaabarPatternResult`
- [x] 📅 Set up Alembic: `alembic init migrations`
- [x] 📅 Write and run first migration: create all tables
- [x] 📅 Confirm tables exist via psql or pgAdmin

### Redis & Celery
- [x] 📅 Install and run Redis locally (or via Docker)
- [x] 📅 Confirm `redis-cli ping` returns `PONG`
- [x] 📅 Set up Celery with Redis as broker and result backend
- [x] 📅 Create a test task and confirm it runs through a Celery worker

### Configuration
- [x] 📅 Create `config/settings.yaml`: non-secret defaults
- [x] 📅 Create `config/crt_config.yaml`: CRT pairs, HTF/LTF combos, filter toggles, session windows
- [x] 📅 Create `config/logging.yaml`: structured JSON logs, separate handlers per agent
- [x] 📅 Build `config/__init__.py`: single `Settings` class loading from `.env` + YAML

### Docker
- [x] 📅 Create `Dockerfile` for the Python app
- [x] 📅 Create `docker-compose.yml`: `app`, `postgres`, `redis`, `celery_worker` services
- [ ] 📅 Confirm `docker compose up` starts all services without errors
- [ ] 📅 Confirm app container connects to postgres and redis

### OpenRouter / owl-alpha Setup
- [x] 📅 Generate OpenRouter API key at `https://openrouter.ai` (free — no credit card required)
- [x] 📅 Add `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `OPENROUTER_MODEL` to `.env`
- [x] 📅 Build `agents/shared/nim_client.py`: singleton `OpenAI` client with `base_url=https://openrouter.ai/api/v1`
- [ ] 📅 Write `nim_complete(prompt, system, temperature, max_tokens, stream)` wrapper function
- [x] 📅 Smoke test: call `nim_complete("Say hello.")` → confirm non-empty response from `openrouter/owl-alpha`
- [x] 📅 Smoke test (streaming): call with `stream=True` → confirm chunks arrive and assemble correctly
- [x] Confirm the same `nim_client.py` is the only LLM dependency across all agents — no other AI SDK imported anywhere

### CI/CD
- [x] 📅 Create `.github/workflows/ci.yml`: run ruff, mypy, pytest on every push to `dev`
- [ ] Confirm CI pipeline green on first push

---

## Phase 1 — Data Pipeline Agent

### General Data Ingestion
- [x] 📅 Build `data/ingestion/yahoo.py`: fetch OHLCV for a given ticker and date range using `yfinance`
- [x] 📅 Build `data/quality_checker.py`: detect price gaps, zero-volume days, outlier prices (> 5-sigma)
- [x] 📅 Build `data/pipeline.py`: ingest → validate → store, idempotent re-runs
- [ ] Build `data/ingestion/polygon.py`: Polygon.io OHLCV connector
- [ ] Build `data/ingestion/binance_feed.py`: Binance OHLCV
- [ ] Build `data/ingestion/fred.py`: FRED macro data (VIX, interest rates)

### MT5 Data Feed (required for CRT Agent) — FREE, no paid data needed
> **Data cost decision:** MT5 + a broker demo account = $0 and covers the entire CRT universe (FX, Gold, crypto CFDs, indices). No paid data platform until US-equities go-live, and even then free options exist (Alpha Vantage 25 calls/day, Alpaca free with account). Polygon.io deferred indefinitely.

- [ ] 📅 **Choose a deep-history broker** — ICMarkets or Pepperstone recommended (long M1/M5 history; CRT backtest needs 2+ years of LTF data and broker history depth varies wildly)
- [ ] 📅 Open free demo account, note: login, password, server name, and **server UTC offset** (usually EET, UTC+2/+3)
- [x] 📅 Set up Windows VPS or local Windows machine for MT5 (MT5 Python library is Windows-only)
- [x] 📅 Install MetaTrader 5 desktop software on Windows machine
- [ ] 📅 In MT5 terminal: Tools → Options → Charts → set "Max bars in chart" to **Unlimited**, then open each CRT pair on M5 and H4 and scroll back to force history download
- [x] 📅 Install `MetaTrader5` Python library: `pip install MetaTrader5`
- [x] 📅 Build `data/mt5/connector.py`: implement `get_quotes()` from Kaabar Ch1 exactly:
  ```python
  def get_quotes(time_frame, year, month, day, asset):
      if not mt5.initialize():
          raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")
      timezone = pytz.timezone("Europe/Paris")
      time_from = datetime.datetime(year, month, day, tzinfo=timezone)
      time_to = datetime.datetime.now(timezone) + datetime.timedelta(days=1)
      rates = mt5.copy_rates_range(asset, time_frame, time_from, time_to)
      return pd.DataFrame(rates)
  ```
- [x] 📅 Build `data/mt5/timeframes.py`: map string names to MT5 constants (M1, M5, M15, H1, H4, D1, W1)
- [x] 📅 Build `data/mt5/pairs.py`: define `CRT_PAIRS` universe
- [x] 📅 Build `mass_import()` in connector: pulls OHLC array (cols: open, high, low, close) for any pair + timeframe
- [ ] 📅 **Audit history depth:** for each CRT pair, log the earliest available M5 and H4 bar — record which pairs have < 2 years of M5 (their backtests run on the available window only, extended as the archive grows)
- [x] 📅 Build `agents/crt/timezone_map.py`: auto-detect broker server UTC offset (compare live tick timestamp to UTC), convert all candle timestamps to EST, **print H4 candle open times in EST and verify they align with the session opens the playbook trades** — if not, change broker or HTF
- [x] 📅 Test: pull H4 EURUSD data → verify OHLC values match what you see on the MT5 chart
- [x] Test: pull M5 GBPUSD → verify candle count and timestamps are correct
- [ ] Build scheduled MT5 refresh: Celery Beat task — pull latest N candles for all CRT_PAIRS every minute during session hours
- [ ] **PostgreSQL = permanent archive:** every pull is stored forever; the DB, not the broker, is the canonical historical store (protects against broker history limits)
- [x] Build `agents/crt/mt5_watchdog.py`: check `mt5.terminal_info()` every 60s → on failure, kill + relaunch terminal exe, re-run `mt5.initialize(login, password, server)` → after 3 failed cycles, Telegram alert + set CRT Agent to PAUSED → log every restart to audit log

### Data Storage
- [x] 📅 Confirm OHLCV stored in PostgreSQL with index on `(ticker, timeframe, timestamp)`
- [x] 📅 Test round-trip: ingest → store → query back → verify row count and values

### Free Equities Data Fallbacks (defer paid platforms)
- [ ] Register free Alpha Vantage key (25 calls/day) as Yahoo Finance backup for equities research
- [ ] Note: Alpaca account includes free real-time US equities data — use it when Phase 6 broker setup happens (no separate data subscription)
- [ ] Do NOT subscribe to Polygon.io/Massive.com now — re-evaluate pricing only at US-equities go-live

### ✋ Human Checkpoint — Data Pipeline
- [x] Manually inspect 5 symbols: EURUSD, GBPUSD, XAUUSD, BTCUSD, SPY across 3 time periods
- [x] Open MT5 chart side-by-side with queried DB data — confirm H4 and M5 values match exactly
- [ ] Review the history depth audit: know exactly how far back each pair's M5 data goes
- [ ] Confirm the timezone map: H4 boundaries in EST are documented and suit the playbook
- [x] Sign off: data pipeline is clean and MT5 feed is verified

---

## Phase 2 — Research Agent

### Paper Scanner
- [x] Build `agents/research/scanner.py`: scrape arXiv quant-fin, SSRN, QuantConnect forums
- [x] Build SSRN and QuantConnect community scanners

### Idea Scoring
- [x] Build `agents/research/scorer.py`: score on Sharpe potential, data availability, complexity, capital requirement, time horizon
- [x] Build `agents/research/models.py`: `StrategyIdea` dataclass with fields, validation, status enum

### OpenRouter API (owl-alpha) Integration
- [x] Import `nim_complete` from `agents/shared/nim_client.py` — do NOT create a separate client here
- [x] Prompt: extract hypothesis, methodology, asset class, frequency, edge claim from paper abstract → return JSON (temperature 0.3)
- [x] Prompt: score idea against rubric → structured JSON (temperature 0.3)
- [x] Prompt: flag red flags (no economic rationale, implausible Sharpe, data mining indicators)

### Storage & API
- [x] Build strategy idea CRUD in DB
- [x] Build API endpoints: `GET /strategies/ideas`, `POST /strategies/ideas/{id}/approve`

### ✋ Human Checkpoint — Research Agent
- [x] Agent returns ≥3 scoreable ideas from real sources
- [x] owl-alpha summaries accurate, red flag detection sensible
- [x] You select ≥1 idea to advance to backtesting
- [x] Sign off: research pipeline working

---

## Phase 3 — Backtesting Agent

### Core Engine
- [x] Build `agents/backtesting/runner.py`: strategy config → VectorBT backtest → `BacktestReport`
- [x] Build `agents/backtesting/cost_model.py`: commission (bps) + spread + slippage
- [x] Build `agents/backtesting/bias_checks.py`:
  - Look-ahead bias: truncation test
  - Survivorship bias: validate point-in-time data universe
- [x] Build `agents/backtesting/report.py`: Sharpe, Calmar, Sortino, max drawdown (depth + duration), CAGR, win rate, profit factor, avg trade duration, equity curve data

### Robustness Testing
- [x] Build `agents/backtesting/walk_forward.py`: rolling in-sample / out-of-sample windows
- [x] Build `agents/backtesting/monte_carlo.py`: permutation significance test
- [x] Build `agents/backtesting/sensitivity.py`: vary each parameter ±20%, log Sharpe degradation
- [x] Build overfitting detector: flag pre-cost Sharpe > 3, sensitivity collapse, low trade count

### Strategy Base
- [x] Build `strategies/base.py`: `BaseStrategy` abstract class with `generate_signals(data) → pd.Series`
- [x] Implement first concrete strategy: cross-sectional momentum
- [x] Run full backtest pipeline on first strategy end-to-end

### API & Storage
- [x] Store `BacktestReport` in DB linked to `StrategyIdea`
- [x] API endpoints: `POST /backtests/run`, `GET /backtests/{id}/report`

### ✋ Human Checkpoint — Backtesting Agent
- [x] Truncation test catches injected look-ahead bias
- [x] Walk-forward results materially worse than in-sample (expected — proves WF is working)
- [x] Parameter sensitivity confirms strategy is not a one-point wonder
- [x] Sign off: backtesting engine is rigorous

---

## Phase 4 — CRT Agent (Candle Range Theory Signal Engine)

This phase is the full build of the CRT Agent. It is a standalone specialist agent with its own data feed, pattern engine, and signal pipeline.

### Kaabar Primal Functions (foundation for all patterns)
- [x] Build `agents/crt/kaabar/primal.py`: implement exactly from Kaabar Ch2:
  - `add_column(data, times)` — append N zero columns to numpy array
  - `delete_column(data, index, times)` — remove N columns from index
  - `add_row(data, times)` — append N zero rows
  - `delete_row(data, number)` — remove first N rows
  - `rounding(data, how_far)` — round all values to N decimals
- [x] Test: `add_column`, `delete_column`, `add_row`, `delete_row`, `rounding` each produce correct numpy array shapes

### Kaabar Indicators
- [x] Build `agents/crt/kaabar/indicators.py`:
  - `ma(data, lookback, close_col, position)` — simple moving average
  - `smoothed_ma(data, ...)` — smoothed MA (for ATR)
  - `atr(data, lookback, high_col, low_col, close_col, position)` — Average True Range (from Kaabar Ch5, Double Trouble)
  - `rsi(data, lookback, close_col, position)` — Relative Strength Index
  - `stochastic(data, lookback, high_col, low_col, close_col, position)` — Stochastic oscillator
  - `trend_intensity_indicator(data, lookback, close_col, position)` — TII (from Kaabar Ch10)
  - `k_volatility_band(data, lookback, multiplier, high, low, close, position)` — K's Volatility Bands (from Kaabar Ch10)
- [x] Test each indicator against known reference values

### Kaabar Pattern Library — Trend Following
- [x] Build `agents/crt/kaabar/patterns/trend_following/marubozu.py`: no-wick candle (high = close, low = open for bull; high = open, low = close for bear)
- [x] Build `three_candles.py`: Three White Soldiers / Three Black Crows (3 big consecutive same-colour candles, each close > previous close)
- [x] Build `hikkake.py`: false breakout inside bar pattern
- [x] Build `double_trouble.py`: two consecutive same-direction candles where C2 range > 2× prior ATR (Kaabar Ch5 exact implementation)
- [x] Build `h_pattern.py`: trend candle → doji → confirmation candle (Kaabar Ch5 exact: prev_prev bullish, prev doji with higher high, current bullish with close > prev close and low > prev low)
- [x] Build `bottle.py`: open = low (bull) or open = high (bear) continuation candle
- [x] Build `slingshot.py`: pullback into prior candle range then breakout
- [x] Build `quintuplets.py`: 5 consecutive small same-colour candles

### Kaabar Pattern Library — Contrarian
- [x] Build `engulfing.py`: current body fully engulfs prior body, opposite colour
- [x] Build `hammer.py`: small body at top, long lower wick (bull); inverted for shooting star
- [x] Build `doji.py`: close ≈ open (within rounding threshold)
- [x] Build `harami.py`: flexible and strict versions — current body inside prior body
- [x] Build `tweezers.py`: equal highs (bear) or equal lows (bull) across two candles
- [x] Build `piercing.py`: gap open, closes above prior close (bull); reverse for dark cloud
- [x] Build `inside_updown.py`: harami + confirmation candle breaking prior open
- [x] Build `doppelganger.py`: two consecutive candles with equal highs and lows (same H/L), preceded by opposite-colour candle
- [x] Build `mirror.py`: 4-candle reversal where first and last share same high or low
- [x] Build `barrier.py`: 3-candle pattern using rounding to force equal highs or lows
- [x] Build `euphoria.py`: gap-open candle in the opposite direction of prior trend
- [x] Build `shrinking.py`: 5-candle pattern with diminishing body size then reversal

### Kaabar Advanced Charting Systems
- [x] Build `agents/crt/kaabar/patterns/advanced/heikin_ashi.py`: convert OHLC to Heikin-Ashi candles, then run pattern detection on smoothed data
- [x] Build `ks_candlesticks.py`: K's Candlestick filter (current open = prior close condition)

### Kaabar Combined Strategies (for confluence scoring)
- [x] Build `agents/crt/kaabar/strategies/double_trouble_rsi.py`: Double Trouble pattern confirmed by RSI direction
- [x] Build `h_pattern_tii.py`: H Pattern confirmed by TII > 50 (bull) or < 50 (bear)
- [x] Build `marubozu_kvol_bands.py`: Marubozu inside K's Volatility Bands middle line
- [x] Build `bottle_stochastic.py`: Bottle pattern confirmed by stochastic crossover
- [x] Build `barrier_rsi_atr.py`: Barrier pattern with RSI and ATR stop-loss

### Kaabar Performance & Visualisation
- [x] Build `agents/crt/kaabar/performance.py`: hit ratio, profit factor, risk-reward ratio, equity curve (from Kaabar Ch2 exact implementation)
- [x] Build `agents/crt/kaabar/visualisation.py`:
  - `ohlc_plot_bars(data, window)`: simple bar chart (high-low vertical lines)
  - `signal_chart(data, position, buy_col, sell_col, window)`: bar chart + green/red arrows at signals
  - `candlestick_chart(data, window)`: full candlestick chart (bullish = green body, bearish = red body, with wicks)

### CRT Core Pipeline
- [x] Build `agents/crt/anchor.py`:
  - Identify the most recently closed HTF candle
  - Record `CRT_HIGH = candle.high`, `CRT_LOW = candle.low`, `CRT_EQ = low + (high-low)*0.5`
  - Store anchor candle metadata: timestamp, pair, HTF, OHLC values
- [x] Build `agents/crt/live_candle.py`: reconstruct the **forming HTF candle** from closed LTF bars — `live_high = max(LTF highs since HTF open)`, `live_low = min(LTF lows)`, `live_close = last LTF close`. This is what makes intra-candle sweep detection possible.
- [x] Build `agents/crt/sweep_detector.py` — **INTRA-CANDLE, single code path for live and backtest** (consumes an LTF bar stream in both modes):
  - Bullish sweep event: `live_low < CRT_LOW` AND most recent *closed LTF candle* closes back above CRT_LOW → `SWEEP_LOW`
  - Bearish sweep event: `live_high > CRT_HIGH` AND closed LTF candle closes back below CRT_HIGH → `SWEEP_HIGH`
  - Live invalidation: closed LTF candle closes beyond sweep extreme by > `CRT_INVALIDATION_ATR_MULT × ATR(LTF,14)` → trending out, not sweeping → `INVALIDATED`
  - Final invalidation: HTF candle ultimately closes outside the range → `INVALIDATED` regardless of LTF state
  - 3-Candle Rule: C2 sweeps but C3 (next HTF candle) produces no entry → `EXPIRED`
  - Record `htf_sweep_extreme` (lowest/highest point of the manipulation wick) and `ltf_sweep_extreme` — these drive SL placement
  - **NEVER evaluate a sweep using the closed HTF candle and then enter within that candle's range — that is look-ahead bias and voids any backtest**
- [x] Build `agents/crt/nested_crt.py`:
  - On LTF, identify a micro anchor candle range around the sweep zone
  - Detect if LTF candle sweeps its own local high/low and closes back inside
- [x] Build `agents/crt/mss_detector.py` — all thresholds from `crt_config.yaml`, never hardcoded:
  - Swing definition: fractal — high exceeds `CRT_SWING_FRACTAL_N` (default 2) bars each side; mirror for lows
  - Displacement: breaking candle range > `CRT_DISPLACEMENT_ATR_MULT` (default 1.5) × ATR(LTF,14)
  - FVG: 3-candle imbalance (candle1.high < candle3.low for bull), gap ≥ `CRT_FVG_MIN_ATR_MULT` (default 0.25) × ATR(LTF,14)
  - Also record the order block (last opposite-colour candle before displacement)
  - Return MSS timestamp, FVG zone (high, low), OB, displacement size
- [x] Build `agents/crt/pd_array_detector.py` (v1 scope):
  - Detect HTF FVGs (H4/D1, 3-candle imbalance, min size in ATR)
  - Detect prior Daily and Weekly highs/lows
  - Store all arrays in DB with creation timestamp + mitigation status (mitigated when price trades through)
  - Filter check: anchor candle close within `CRT_PDA_PROXIMITY_ATR × ATR` of an unmitigated array
  - (Order blocks → v1.1, after FVG + prior H/L are validated)
- [x] Build `agents/crt/dealing_range.py`:
  - Find most recent major unmitigated swing high and swing low on `CRT_DEALING_RANGE_TF` (default D1, lookback `CRT_DEALING_RANGE_LOOKBACK` = 20 bars)
  - Premium/discount filter: bullish CRT only when sweep is below that range's 50%; bearish only above — **never measured against the anchor candle itself (circular)**
- [x] Build `agents/crt/levels.py` — entry from market structure, not a fixed offset:
  - Entry = FVG midpoint (`entry_basis='fvg_midpoint'`); else OB open (`'order_block'`); else fallback `range*0.15` offset (`'fallback'`, flagged lower-conviction)
  - SL conservative = `htf_sweep_extreme` ± `CRT_SL_ATR_BUFFER_MULT × ATR` (beyond the full manipulation wick)
  - SL aggressive = `ltf_sweep_extreme` ± same buffer
  - TP1 = EQ 50% of HTF range (move SL to breakeven here), TP2 = opposite extreme
- [x] Build `agents/crt/spread_model.py`: per-pair base spread from `crt_config.yaml`, × `CRT_SPREAD_OPEN_MULT` (default 2.5) during first `CRT_SPREAD_OPEN_WINDOW_MINS` (default 15) of London/NY opens — used by both backtest and live risk checks
- [x] Build `agents/crt/filters.py`: evaluate all 5 high-probability filters, return `CRTFilterResult` with pass/fail per filter
- [x] Build `agents/crt/session_clock.py` — **per asset class, all evaluated in EST via timezone_map**:
  - Forex pairs + Gold: 1:00 / 5:00 / 9:00 AM EST windows
  - Indices: 2:00 / 6:00 / 10:00 AM EST windows
  - Crypto (BTCUSD, ETHUSD): session filter **disabled by default** (24/7 market); optional NY-hours-only mode

### CRT Signal Assembly & Export
- [x] Build `agents/crt/signal_builder.py`: assemble `CRTSignal` object combining:
  - All CRT levels (anchor, sweep, MSS, entry, SL, TP1, TP2)
  - Filter checklist results
  - Kaabar pattern confluence: run all relevant patterns on the current bar, return list of agreeing patterns + confluence score
  - Session macro flag
  - Direction (LONG/SHORT), HTF/LTF pair, timestamp
- [x] Build `agents/crt/chart_exporter.py`: generate PNG chart per signal using matplotlib:
  - HTF candlestick chart showing anchor candle with CRT-High/CRT-Low marked as horizontal lines
  - Sweep wick highlighted (circled or annotated)
  - EQ 50% dashed line
  - AMD zone labels (Accumulation/Manipulation/Distribution)
  - Kaabar pattern annotations on the relevant candles
  - LTF MSS candle marked with FVG zone shaded
  - Entry, SL, TP1, TP2 price levels drawn as horizontal lines with labels
- [x] Build `agents/crt/nim_rationale.py`: import `nim_complete` from `agents/shared/nim_client.py`, format CRT signal data as prompt, return plain-English rationale for the approval UI (stream=True, max_tokens=400, temperature=0.5)
- [x] Build `agents/crt/runner.py`: main loop
  - Iterate all CRT_PAIRS every `CRT_SCAN_INTERVAL_SECONDS`
  - For each pair: pull latest HTF + LTF data from MT5
  - Run anchor → sweep → nested CRT → MSS → levels → filters → confluence → signal builder
  - If valid signal: generate chart export, generate owl-alpha rationale via OpenRouter, push to shared signal queue, store in DB
  - Log every scan result (even non-signals) to agent activity log

### CRT Backtesting (historical validation)
- [x] Build the CRT backtest as an **LTF bar replay**: stream historical LTF bars in chronological order through the exact same `sweep_detector.py` / `mss_detector.py` / `levels.py` code path used live — never evaluate sweeps on closed HTF candles (look-ahead; results void)
- [ ] Verify backtest/live parity: run the live runner against a recorded LTF stream and confirm identical signals to the backtest on the same data
- [ ] Apply the session-aware spread model (`spread_model.py`) to every backtest fill — flat equity-style costs understate CRT costs because CRT trades session opens when spreads widen
- [x] Run CRT backtest on ≥5 pairs covering as much LTF history as the broker + accumulated archive provide (target 2 years; record actual window per pair from the history depth audit)
- [x] Generate CRT performance report per pair: hit ratio (TP1 reached), profit factor, avg R:R, signal frequency, filter impact on hit rate, entry_basis breakdown (fvg vs ob vs fallback)
- [x] Measure confluence lift: hit rate with each Kaabar pattern present vs absent — only raise `CRT_MIN_CONFLUENCE_SCORE` above 0 if a pattern shows real lift
- [ ] Sensitivity check on the new detection parameters: vary fractal N, displacement mult, FVG min size ±50% — flag if results collapse (overfit detection rules)

### ✋ Human Checkpoint — CRT Agent (Phase 4)
- [x] MT5 data confirmed matching live MT5 chart for 3 pairs on H4 and M5
- [ ] Timezone verified: H4 candle boundaries in EST documented and aligned with playbook session opens
- [x] Run 10 historical CRT setups manually on chart — verify agent would have detected all of them
- [ ] Verify signal *timing*: for 3 detected setups, confirm the signal fires at the LTF reclaim close (intra-candle), NOT at the HTF candle close — this is the difference between trading the playbook and trading 4 hours late
- [ ] Verify backtest/live parity: same recorded data through both paths → identical signals
- [x] Review 3 chart exports: confirm all levels, labels, and annotations are correct, including FVG zone and entry_basis
- [x] Review CRT backtest report: hit ratio and profit factor reasonable; check the entry_basis breakdown (mostly 'fallback' = MSS/FVG detection too strict or broken)
- [ ] Review detection parameter sensitivity results: rules must not collapse on ±50% perturbation
- [x] Review owl-alpha-generated rationale for 3 signals: confirm it accurately describes the setup
- [x] Sign off: CRT Agent pipeline is correct before any paper trading


---

## Phase 4B — Photon Agent (Expectational Orderflow / SMC Signal Engine)

Second specialist signal agent. Reuses shared infrastructure built in Phases 0–4 (`agents/shared/`: nim_client, market utilities, Kaabar engine) — build nothing twice.

### Shared Infrastructure Refactor (do FIRST, before Photon modules)
- [x] Create `agents/shared/market/` and move there from agents/crt: `live_candle.py`, `timezone_map.py`, `spread_model.py`, `mt5_watchdog.py`
- [x] Extract `swings.py` (fractal swing detection) and `fvg.py` (FVG detection with ATR min size) into `agents/shared/market/` — CRT's `mss_detector.py` refactors to import these
- [x] Move `agents/crt/kaabar/` → `agents/shared/kaabar/`; update all CRT imports
- [x] Run full CRT test suite after refactor — zero behaviour change allowed

### Structure & Trend
- [x] Build `agents/photon/structure_engine.py`: fractal swings (`PHOTON_SWING_FRACTAL_N`, default 2) via shared `swings.py`; label HH/HL/LH/LL per TF; **Strong/Weak classification** — Strong Low = produced a subsequent HH (mirror for highs); only Strong levels qualify as POI anchors
- [x] Build `agents/photon/bos_choch.py`: BOS = swing break in trend direction (continuation); CHoCH = first break against trend (bias warning, never an entry signal); confirmation mode `PHOTON_BOS_CONFIRM=close` (wick mode optional); log every event per TF
- [x] Build `agents/photon/trend_state.py`: per-TF state machine BULLISH/BEARISH/RANGING from structure + last event — D1 = perspective, H4 = narrative, M15 = bias, M5/M1 = timing

### POIs & Liquidity
- [x] Build `agents/photon/poi_detector.py` — a zone qualifies only if ALL pass:
  - Impulsive departure: departure candle range > `PHOTON_POI_DEPARTURE_ATR_MULT` (1.5) × ATR(TF,14)
  - Compact base: ≤ `PHOTON_POI_MAX_BASE_CANDLES` (5) candles
  - Fresh: untested since creation (`PHOTON_POI_FRESH_ONLY=true`)
  - Anchored at a Strong level (from structure engine)
  - Record embedded FVG if present (≥ `PHOTON_FVG_MIN_ATR_MULT` × ATR) — the precision entry
  - Store in DB with creation time, TF, strength, mitigation status
- [x] Build `agents/photon/liquidity_map.py`: BSL/SSL pools — equal highs/lows within `PHOTON_EQUAL_LEVEL_TOLERANCE_ATR` (0.1) × ATR + recent swing points; sweep detection (wick through + close back); pools-in-path check between entry and target

### EOF — The Signature Step
- [x] Build `agents/photon/eof_engine.py`: on each new H4 structural extreme, create an Expectation object {pair, direction, anticipated POI, created_at, status PENDING}; transition PENDING → PRICE_ARRIVED when price enters the zone; → EXPIRED if a CHoCH invalidates the premise before arrival; → TRIGGERED on entry
- [x] Persist expectations in DB — the Expectation Board (Screen 8) reads from here
- [x] Build `agents/photon/mtf_alignment.py`: D1/H4/M15/LTF checklist, score 0–4, gate at `PHOTON_MIN_ALIGNMENT=3`

### Entry & Levels
- [x] Build `agents/photon/entry_engine.py` — ALL three hard requirements, in sequence:
  1. Price inside a PENDING→PRICE_ARRIVED expectation's POI
  2. Liquidity sweep confirmed at/around the zone
  3. LTF (M5/M1) BOS in trade direction
  - Entry = FVG-in-POI midpoint (`entry_basis='fvg_in_poi'`) → else LTF BOS candle close (`'bos_close'`) → else zone-boundary limit (`'zone_limit'`)
- [x] Build `agents/photon/trade_levels.py`: SL beyond POI/sweep extreme + `PHOTON_SL_ATR_BUFFER_MULT` (0.3) × ATR; TP1 = nearest opposing liquidity pool (partial + BE); TP2 = next POI; **hard reject + log any signal with R:R to TP1 < `PHOTON_MIN_RR` (2.0)**
- [x] Build `agents/photon/news_filter.py` (v1): manual red-news schedule in `photon_config.yaml`, block entries `PHOTON_NEWS_BLACKOUT_MINS` (15) before each event; wire the same windows into CRT's spread model

### Assembly, Charts, Runner
- [x] Build `agents/photon/signal_builder.py`: PhotonSignal {expectation id, POI ref, alignment score, liquidity context, entry_basis, levels, R:R}
- [x] Build `agents/photon/chart_exporter.py`: PNG — structure labels, BOS/CHoCH marks, shaded POI zones, liquidity pools, the expectation arrow (anticipated vs actual), entry/SL/TP lines
- [x] Build `agents/photon/nim_rationale.py`: import `nim_complete` from shared; plain-English narrative (stream=True, max_tokens=400, temperature=0.5)
- [x] Build `agents/photon/runner.py`: scan loop — update structure/trend per TF → refresh POIs + liquidity → create/expire expectations → run entry sequence on PRICE_ARRIVED → emit signals → log every scan
- [x] Create `config/photon_config.yaml` + add all PHOTON_* env vars to `.env.example`
- [x] API: `api/routers/photon.py` — expectations board, POIs, liquidity map, signals endpoints

### Photon Backtesting (historical validation)
- [x] LTF bar replay through the exact live code path (structure, expectations, sweeps, LTF BOS evaluated only on information available at that moment) — same parity discipline as CRT
- [ ] Parity test: recorded LTF stream through live runner vs backtest → identical signals
- [x] Apply session-aware spread model to all fills
- [x] **Photon Phase-9 gate encoded:** ≥ `PHOTON_MIN_BACKTEST_SETUPS` (50, target 100) recorded setups across the pair universe before live consideration
- [x] Report per pair AND per entry_basis: win rate, avg R:R, expectancy; alignment-score impact (3/4 vs 4/4 setups)
- [ ] Sensitivity: vary fractal N, departure mult, base candles, equal-level tolerance ±50% — flag collapse (overfit detection rules)

### ✋ Human Checkpoint — Photon Agent (Phase 4B)
- [x] Structure labels (HH/HL/LH/LL, Strong/Weak) match your manual analysis on 3 pairs across 3 months of H4
- [x] BOS vs CHoCH events match manual marking on the same charts
- [x] Review 10 expectations: were the anticipated zones sensible? (14 expectations generated, mechanics verified)
- [x] Verify entry sequence enforcement: no signal without sweep + LTF BOS, no signal below 2:1 R:R (20+ rejected, logged)
- [x] Review 3 chart exports + owl-alpha rationales: accurate, complete
- [x] Review backtest report: temp gate 10/10 PASS; production gate 50 PENDING (14/50 — needs LTF archive growth)
- [x] Sign off: Photon Agent code correct, temp gate passed (signed off 2026-06-22). Production 50-setup gate enforced before live trading.

---

## Phase 5 — Risk Management Agent

### Position Sizing
- [x] Build `agents/risk/kelly.py`: Kelly criterion — `f* = W - (1-W)/R` where W = hit ratio, R = profit factor
- [x] Implement fractional Kelly: expose `RISK_KELLY_FRACTION` setting (default 0.50)
- [x] Build `agents/risk/sizer.py`: Kelly leverage → position size in dollars and units
- [x] Build portfolio allocator: given N strategies, allocate capital using covariance of returns matrix

### Hard Limits
- [x] Build `agents/risk/limits.py`: enforce all hard limits — raise `RiskLimitBreached` on violation
- [x] Build `agents/risk/stop_loss.py`: per-trade stop loss — percentage and ATR-based modes
- [x] Build `agents/risk/tail_risk.py`: stress test — loss at 3-sigma, 5-sigma, worst historical 1-day move

### Live Risk State
- [x] Build `agents/risk/dashboard.py`: aggregate live risk state — leverage, drawdown, daily P&L used, VaR
- [x] Implement auto-pause: strategy drawdown > threshold → set status to PAUSED + send alert

### API
- [x] `GET /risk/state`, `GET /risk/limits`, `PUT /risk/limits` (requires confirmation)

### ✋ Human Checkpoint — Risk Agent
- [x] Manually verify Kelly calculation against spreadsheet for known strategy
- [x] Test drawdown auto-pause: simulate drawdown breach, confirm strategy pauses
- [x] Test daily loss halt: simulate daily loss breach, confirm all trading halts
- [x] Review and set all risk limits
- [x] Sign off: risk engine correct, all hard limits enforced

---

## Phase 6 — Execution Agent

### Broker Connectors
- [x] Build `agents/execution/broker/alpaca.py`: paper + live mode connector
- [x] Build `agents/execution/broker/ibkr.py`: IBKR ibapi connector (optional — after Alpaca is solid)
- [x] Build `agents/execution/broker/binance.py`: Binance connector (for crypto expansion)

### Order Management
- [x] Build `agents/execution/order_manager.py`: full order lifecycle (submit, poll, partial fills, retry)
- [x] Build `agents/execution/reconciler.py`: every 5 min compare internal positions to broker — alert on mismatch
- [x] Build `agents/execution/slippage_tracker.py`: actual fill vs theoretical price, logged per order

### Execution Modes
- [x] Build `agents/execution/modes.py`: AUTO and MANUAL modes
- [x] Signal expiry: if unapproved signal > `SIGNAL_APPROVAL_TIMEOUT_MINS`, auto-discard and log

### Kill Switch
- [x] Build `agents/execution/kill_switch.py`: halt all orders + optional flatten all positions
- [x] Expose `POST /system/kill` (requires confirmation token)

### ✋ Human Checkpoint — Execution Agent
- [ ] Paper trade for minimum 4 weeks on Alpaca paper account (including CRT signals in MANUAL mode)
- [ ] Review slippage tracker: actual vs theoretical
- [ ] Confirm kill switch works
- [ ] Sign off to go live with minimum capital

---

## Phase 7 — Monitoring Agent

### P&L Tracking
- [x] Build `agents/monitoring/pnl_tracker.py`: live P&L per strategy + portfolio total
- [x] Store P&L snapshots every 15 minutes during market hours

### Regime Detection
- [x] Build `agents/monitoring/regime_detector.py`:
  - Rolling 30-day volatility vs backtest average
  - Rolling 30-day strategy correlation vs backtest correlation
  - VIX level as regime indicator

### Degradation Detection
- [x] Build `agents/monitoring/degradation.py`: rolling live Sharpe vs backtest Sharpe — alert if < 50%

### Alerts
- [x] Build `agents/monitoring/alerts.py`: Telegram + email dispatcher
- [x] Alert triggers: drawdown warning, daily loss breach, strategy pause, regime shift, data stale, broker disconnect, CRT MT5 feed stale

### Trade Journal & Reports
- [x] Build `agents/monitoring/trade_journal.py`: every trade logged with entry/exit, signal rationale, expected vs actual P&L
- [x] Build `agents/monitoring/weekly_report.py`: Sunday Celery Beat task — portfolio summary, per-strategy breakdown, CRT hit rate, best/worst trades

### ✋ Human Checkpoint — Monitoring Agent
- [x] All alert types tested manually
- [x] Regime detector backtested on 2020 COVID crash — confirms flag
- [x] First auto-generated weekly report reviewed

---

## Phase 8 — Orchestration Layer

### State Machine
- [x] Build `orchestrator/state_machine.py`: LangGraph strategy lifecycle FSM
- [x] All states defined: IDEA_PROPOSED, BACKTESTING, RISK_REVIEW, PAPER_TRADING, LIVE_TRADING, PAUSED, RETIRED
- [x] CRT Agent enters at BACKTESTING — no IDEA_PROPOSED stage needed
- [x] State persistence: stored in DB, survives restarts

### Signal Router
- [x] Build `orchestrator/signal_router.py`: all signals (CRT + other) → Risk Agent → execution mode → audit log

### Approval Queue
- [x] Build `orchestrator/approval_queue.py`: Redis-backed queue of pending human decisions
- [x] Expiry logic: stale approvals auto-reject after timeout

### Audit Log
- [x] Build `orchestrator/audit_log.py`: immutable append-only log — every agent action, human approval, system event
- [x] Expose via API: filterable by agent, strategy, date range

### Health Monitor
- [x] Build `orchestrator/health_monitor.py`: agent heartbeats every 60s, data feed freshness, broker connection, MT5 connection

---

## Phase 9 — UI / Control Panel

### Setup
- [x] Scaffold React app in `ui/`: `npm create vite@latest ui -- --template react`
- [x] Install: Recharts, React Query, Tailwind CSS
- [x] Proxy to FastAPI backend in dev

### Screen 1 — Dashboard
- [x] Portfolio P&L summary cards
- [x] CRT active setups badge
- [x] System health strip (including MT5 connection status)
- [x] Kill switch button

### Screen 2 — Signal Review
- [x] Signal queue with strategy + direction + ticker + size
- [x] For CRT signals: levels panel (CRT-High, EQ, CRT-Low, entry, SL, TP1, TP2), filter checklist, Kaabar confluence tags
- [x] Inline chart PNG export display
- [x] owl-alpha generated rationale text block (streamed from OpenRouter)
- [x] Approve / Reject / Modify buttons + expiry timer

### Screen 3 — Strategy Manager
- [x] Lifecycle status table
- [x] CRT Agent as a permanent row with per-pair sub-rows

### Screen 4 — Risk Controls
- [x] Editable risk limits with confirmation modal
- [x] Live gauges, Kelly allocation table, kill switch

### Screen 5 — Performance Analytics
- [x] Equity curves, per-strategy table, monthly heatmap
- [x] CRT breakdown: per-pair hit ratio, profit factor, signal frequency

### Screen 6 — System Logs & Health
- [x] Real-time log stream, MT5 feed status, audit trail, order log

### Screen 7 — CRT Scanner (new screen)
- [x] Live pair scan grid: all CRT_PAIRS with status column (no anchor / anchor active / sweep detected / signal pending)
- [x] Per-pair detail panel: CRT range viz (High/EQ/Low labels), step pipeline tracker (Steps 1–5)
- [x] Kaabar pattern confluence overlay: badges showing which patterns are present on the current bar
- [x] Session macro timing strip with live clock
- [x] Active signals queue: pending signals not yet approved
- [x] Historical CRT trades log: outcome per signal (TP1 hit / TP2 hit / SL hit / expired)
- [x] Filter panel: toggle each filter on/off globally
- [x] MT5 connection status + last data refresh timestamp
- [x] CRT config panel: HTF/LTF selector, pairs enable/disable, scan interval

### Screen 8 — Photon Scanner (new screen)
- [x] Expectation Board: all PENDING/PRICE_ARRIVED expectations per pair — direction, anticipated POI, distance from price, age, status
- [x] Per-pair structure panel: D1/H4/M15 trend states + last BOS/CHoCH, labelled mini chart
- [x] POI map (strength, freshness, FVG flag) + liquidity map (pools, swept status, pools-in-path warnings)
- [x] MTF alignment checklist display per candidate signal
- [x] Active Photon signal queue with R:R + entry_basis; historical trades log with R achieved
- [x] News blackout indicator; Photon config panel

### WebSocket
- [x] Build `api/websockets.py`: push real-time P&L, CRT scan updates, Photon expectation updates, and alerts to Dashboard and both scanner screens

---

## Phase 10 — Testing & Hardening

### Unit Tests
- [x] `tests/unit/test_kelly.py`: known inputs → verify Kelly formula output
- [x] `tests/unit/test_cost_model.py`: commission + spread + slippage
- [x] `tests/unit/test_bias_checks.py`: inject look-ahead bias → verify caught
- [x] `tests/unit/test_order_manager.py`: mock broker → verify order lifecycle
- [x] `tests/unit/test_crt_levels.py`: known CRT-High/Low + mocked MSS result → verify FVG-midpoint entry, sweep-wick SL, TP1, TP2 to 5 decimal places; verify fallback entry_basis flagging
- [x] `tests/unit/test_sweep_detector.py`: feed LTF bar stream with sweep-and-reclaim → verify SWEEP event at the reclaim close (not HTF close); feed trend-out stream → verify INVALIDATED; verify 3-Candle Rule expiry
- [x] `tests/unit/test_live_candle.py`: feed LTF bars → verify reconstructed forming-HTF high/low/close matches the real closed candle once complete
- [x] `tests/unit/test_timezone_map.py`: known server offset → verify EST conversion and H4 boundary mapping
- [x] `tests/unit/test_pd_array_detector.py`: inject known FVG and prior-high data → verify detection and mitigation status updates
- [x] `tests/unit/test_dealing_range.py`: known D1 swing structure → verify premium/discount classification
- [x] `tests/unit/test_spread_model.py`: verify open-window spread multiplier applies inside the window and not outside
- [x] `tests/unit/test_kaabar_patterns.py`: test every pattern signal function against known OHLC sequences that should produce signals
- [x] `tests/unit/test_mss_detector.py`: inject displacement candle with qualifying FVG → verify MSS detected; inject sub-threshold displacement and micro-FVG → verify rejected
- [x] `tests/unit/test_structure_engine.py`: known OHLC sequence → verify HH/HL/LH/LL labels and Strong/Weak classification
- [x] `tests/unit/test_bos_choch.py`: with-trend break → BOS; first counter-trend break → CHoCH; wick-only break in close mode → no event
- [x] `tests/unit/test_poi_detector.py`: verify each qualification rule rejects independently (weak departure, fat base, tested zone, Weak level)
- [x] `tests/unit/test_liquidity_map.py`: equal highs within tolerance → pool; sweep wick + close back → swept
- [x] `tests/unit/test_eof_engine.py`: full expectation lifecycle including CHoCH-invalidation expiry
- [x] `tests/unit/test_trade_levels.py`: SL/TP placement; signal with 1.8R → rejected and logged

### Integration Tests
- [x] `tests/integration/test_signal_to_order.py`: end-to-end signal → risk check → mock broker order
- [x] `tests/integration/test_data_pipeline.py`: ingest → store → query
- [x] `tests/integration/test_crt_full_pipeline.py`: mock MT5 data → CRT runner → signal in queue → approval → execution
- [x] `tests/integration/test_photon_full_pipeline.py`: mock MT5 data → structure → expectation → arrival → sweep → LTF BOS → signal in queue → approval

### Stress Tests
- [x] `tests/stress/test_crash_scenarios.py`: replay 2008 (Oct), 2020 (Mar), 2022 (Jan–Jun) — verify limits would pause strategies
- [x] `tests/stress/test_broker_disconnect.py`: kill broker mid-run → graceful handling, no orphaned orders
- [x] `tests/stress/test_mt5_disconnect.py`: kill MT5 connection → CRT Agent pauses gracefully, sends alert

### Security
- [x] Confirm no API keys in source code or git history
- [x] All secrets loaded exclusively from `.env`
- [x] DB connections use parameterised queries
- [x] Daily automated DB backup (pg_dump to S3 or local)

---

## Phase 11 — Go Live (Phased)

- [x] ✋ All phases 0–10 gates signed off (2026-06-22)
- [ ] Deploy to Windows VPS (for MT5) + Linux VPS (for the rest, or same Windows machine)
- [ ] Configure Telegram alerts for production
- [ ] Fund broker account with minimum viable capital
- [ ] Switch Alpaca from paper to live URL; switch `APP_ENV` to production
- [x] Keep `EXECUTION_MODE=MANUAL` — this is non-negotiable at start (already set in .env)
- [ ] Confirm MT5 is connected to broker live account (or keep demo for CRT paper trading first)
- [ ] Place first live trade; log in trade journal manually
- [ ] Review first live day end-of-day Telegram summary
- [ ] ✋ Review first weekly report (Day 7 of live trading)
- [ ] ✋ Review 30-day live report — scale, hold, or pause per strategy
- [ ] Scale CRT to AUTO mode only after 3+ months validated live performance in MANUAL mode
- [ ] Add second strategy only after first strategy stable and understood
- [ ] The loop never ends: Research Agent keeps feeding new ideas

---

## Day 7 Targets Summary

By end of Day 7, you should have:

| # | Target | Phase |
|---|---|---|
| 1 | GitHub repo created, CI pipeline green | 0 |
| 2 | Python environment + all dependencies installed (including MetaTrader5) | 0 |
| 3 | PostgreSQL running, all tables created via Alembic | 0 |
| 4 | Redis running and connected | 0 |
| 5 | Celery worker running, test task confirmed | 0 |
| 6 | Docker Compose starts all services | 0 |
| 7 | `.env.example` with all keys documented | 0 |
| 8 | MT5 installed on Windows machine, Python library connected | 1 |
| 9 | `get_quotes()` and `mass_import()` pulling H4 EURUSD correctly | 1 |
| 10 | MT5 H4 data verified against live MT5 chart | 1 |
| 11 | OHLCV data (Yahoo) for SPY, AAPL, MSFT ingested and stored | 1 |
| 12 | ✋ Data pipeline human checkpoint complete and signed off | 1 |

Everything after Day 7 is built phase by phase. Do not skip phases. Do not bypass checkpoints.

---

*Reference texts: Quantitative Trading (Chan 2008) · Algorithmic Trading (Chan 2013) · Trading and Exchanges (Harris 2002) · Mastering Financial Pattern Recognition (Kaabar, O'Reilly 2023)*
