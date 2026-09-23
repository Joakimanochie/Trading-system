# Quant Trading Agentic OS — Master Plan

> A human-in-the-loop agentic operating system for quantitative trading. Covers research, backtesting, risk management, execution, monitoring, and a dedicated CRT signal agent — all coordinated through a shared orchestration layer, with mandatory human approval gates at every capital-critical decision point.

---

## 1. Vision & Principles

**What this is:** A personal quantitative trading OS — not a SaaS product, not a hedge fund platform. A focused, modular system that lets one person run systematic strategies with the discipline of an institution and the flexibility of a developer.

**Core principles:**
- Human-in-the-loop is structural, not optional. Every agent can propose; only you can commit capital.
- Start manual execution mode. Earn the right to go auto through months of validated live performance.
- Agents handle computation and automation. You handle judgment and risk.
- One asset class first. Build the full loop once before expanding.
- Deterministic math (signal logic, risk sizing) stays in Python. Language tasks (summarisation, reasoning explanations) use OpenRouter API (owl-alpha).
- Specialist signal agents (CRT, Photon) run their own full pipelines independently and feed signals into the shared Risk → Execution layer like any other strategy. They share market infrastructure (MT5 feed, structure utilities, Kaabar pattern engine) from `agents/shared/` — built once, used by all.

---

## 2. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                              HUMAN CONTROL LAYER                                   │
│                  Approve · Override · Set Parameters · Inspect                     │
└─────┬─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬────────────────┘
      │         │         │         │         │         │         │
      ▼         ▼         ▼         ▼         ▼         ▼         ▼
 ┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
 │Research││Backtest││  Risk  ││Executn ││Monitor ││  CRT   ││ Photon │
 │ Agent  ││ Agent  ││ Agent  ││ Agent  ││ Agent  ││ Agent  ││ Agent  │
 └───┬────┘└───┬────┘└───┬────┘└───┬────┘└───┬────┘└───┬────┘└───┬────┘
     │         │         │         │         │         │         │
     └─────────┴─────────┴─────────┴─────────┴─────────┴─────────┘
                                      │
                     ┌────────────────▼────────────────┐
                     │    SHARED MESSAGE BUS + DATA     │
                     │  Signal Queue · Order Log        │
                     │  Market Data · State Store       │
                     │  MT5 OHLC Feed · Pattern Store   │
                     └────────────────┬────────────────┘
                                      │
                     ┌────────────────▼────────────────┐
                     │       ORCHESTRATION LAYER        │
                     │  LangGraph State Machine         │
                     │  Audit Log · Agent Memory        │
                     └────────────────┬────────────────┘
                                      │
                      ┌───────────────▼──────────────┐
                      │        EXECUTION MODES        │
                      │                              │
                ┌─────▼──────┐          ┌────────────▼──────┐
                │   AUTO     │          │  MANUAL REVIEW     │
                │ (direct    │          │  (you approve      │
                │  orders)   │          │   each signal)     │
                └─────┬──────┘          └────────────┬──────┘
                      └──────────────┬───────────────┘
                                     ▼
                     ┌───────────────────────────┐
                     │     BROKER / EXCHANGE      │
                     │  Alpaca · IBKR · Binance   │
                     └───────────────────────────┘
```

---

## 3. Agents — Responsibilities & Boundaries

### 3.1 Research Agent

**Purpose:** Scout for strategy ideas. Not a signal generator — reduces the search space so you can make informed decisions.

**Responsibilities:**
- Crawl arXiv (quant-fin), SSRN, QuantConnect community, academic blogs
- Parse and summarise papers using OpenRouter API (owl-alpha)
- Score ideas against a rubric: Sharpe potential, data availability, implementation complexity, capital requirement, time horizon
- Store ideas in the strategy idea database with status tracking
- Flag ideas that violate known pitfalls (overfitted parameters, no plausible economic rationale)

**What it does NOT do:** Generate live signals. Decide what gets backtested. Allocate any capital.

**Output:** Ranked list of strategy ideas with summaries and scores. ✋ You pick which ones proceed.

**OpenRouter API (owl-alpha) role:** Summarise papers, extract hypothesis + methodology, explain economic rationale in plain English.

---

### 3.2 Backtesting Agent

**Purpose:** Validate or kill strategy ideas through rigorous historical simulation.

**Responsibilities:**
- Execute strategy code against historical data (VectorBT or Backtrader)
- Enforce look-ahead bias prevention: event-driven data feed, one bar at a time
- Apply realistic transaction cost model: commissions + spread + slippage
- Run walk-forward testing across rolling in-sample/out-of-sample windows
- Run Monte Carlo permutation tests to assess statistical significance
- Run parameter sensitivity analysis
- Generate standardised performance report: Sharpe, max drawdown, CAGR, Calmar, win rate, profit factor, avg trade
- Flag overfitting red flags: too many parameters, pre-cost Sharpe > 3, curve-fitted equity curve

**What it does NOT do:** Approve strategies for live trading. Set position sizes.

**Output:** Full backtest report per strategy. ✋ You review and approve/reject before any capital allocation.

**OpenRouter API (owl-alpha) role:** Explain backtest results in plain English, flag anomalies, summarise key risks.

---

### 3.3 Risk Management Agent

**Purpose:** Size positions and enforce limits. The most critical agent — never bypass it.

**Responsibilities:**
- Calculate optimal leverage per strategy using Kelly criterion
- Apply fractional Kelly (25–50% of full Kelly) to account for parameter estimation error
- Allocate capital across multiple strategies using covariance of returns
- Enforce hard limits: max drawdown, daily loss limit, position concentration limit, leverage cap
- Calculate per-trade stop loss (percentage of entry or ATR-based)
- Run tail risk check: position must survive a 5-sigma adverse move
- Maintain live risk dashboard: current leverage, live drawdown, portfolio VaR, per-strategy exposure
- Auto-pause a strategy when its live drawdown breaches the configured threshold

**What it does NOT do:** Override its own limits. Self-approve breaches.

**Output:** Position size + risk metadata attached to every signal. ✋ You set and confirm all hard limits before go-live.

**OpenRouter API (owl-alpha) role:** Explain risk metrics in plain English. Summarise portfolio risk state in natural language for the approval UI.

---

### 3.4 Execution Agent

**Purpose:** Route orders to the broker. The only agent that touches real money.

**Responsibilities:**
- Maintain broker API connection (Alpaca REST, IBKR ibapi, or Binance)
- Support two execution modes: AUTO (fires on signal) and MANUAL (queues for human approval)
- Manage order lifecycle: submit, track status, handle partial fills and rejections
- Implement order retry logic with exponential backoff
- Track execution quality: theoretical fill vs actual fill (slippage measurement)
- Reconcile broker positions with internal state every 5 minutes
- Expose kill switch: single command halts all orders and can flatten all positions

**What it does NOT do:** Generate signals. Override risk limits. Execute in AUTO mode without passing through the Risk Agent.

**Output:** Order confirmations, fill records, slippage log. ✋ Paper trade for minimum 4 weeks before live capital. Live switch requires your explicit go-ahead.

---

### 3.5 Monitoring Agent

**Purpose:** Watch everything 24/7. Surface problems before they become disasters.

**Responsibilities:**
- Track live P&L per strategy and portfolio-wide
- Detect regime shifts: volatility, correlation, and return distribution drift from backtest conditions
- Alert on strategy degradation: live Sharpe significantly below backtest Sharpe
- Send alerts via Telegram/email: daily summary, risk limit breaches, execution errors, drawdown warnings
- Log every trade with entry/exit reasoning, signal source, expected vs actual P&L
- Generate automated weekly performance report every Sunday
- Monitor system health: agent uptime, data feed freshness, broker connection status

**Output:** Dashboard, alerts, weekly reports. ✋ You review the 30-day live report and decide to scale, pause, or kill each strategy.

---

### 3.6 CRT Agent (Candle Range Theory Signal Agent)

**Purpose:** A specialist signal agent that implements the full CRT/AMD/ICT multi-timeframe playbook. Operates independently from the general research pipeline — it has its own data feed, pattern detection engine, and signal pipeline, and injects signals into the shared execution layer.

#### What it is

The CRT Agent combines two frameworks into a single automated system:

**Candle Range Theory (CRT):** Treats every closed HTF candle as a defined range with a ceiling (CRT-High) and floor (CRT-Low). The core rule is: if the market sweeps one extreme of a valid range and closes back inside it, it targets the opposite extreme.

**ICT Power of 3 / AMD (Accumulation, Manipulation, Distribution):** Maps the three phases of institutional price delivery onto the CRT candle — the body is Accumulation, the wick sweep is Manipulation (a liquidity raid), and the directional expansion is Distribution (the true move).

#### Data Source

The CRT Agent connects directly to **MetaTrader 5 (MT5)** using the `MetaTrader5` Python library for OHLC data. This is the canonical data source described in *Mastering Financial Pattern Recognition* (Kaabar). Data is pulled using the book's exact `get_quotes()` / `mass_import()` pipeline:

```python
import MetaTrader5 as mt5
import datetime, pytz, pandas as pd, numpy as np

def get_quotes(time_frame, year, month, day, asset):
    if not mt5.initialize():
        raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")
    timezone = pytz.timezone("Europe/Paris")
    time_from = datetime.datetime(year, month, day, tzinfo=timezone)
    time_to = datetime.datetime.now(timezone) + datetime.timedelta(days=1)
    rates = mt5.copy_rates_range(asset, time_frame, time_from, time_to)
    return pd.DataFrame(rates)

def mass_import(asset, time_frame):
    tf_map = {
        'M1': mt5.TIMEFRAME_M1, 'M5': mt5.TIMEFRAME_M5,
        'M15': mt5.TIMEFRAME_M15, 'H1': mt5.TIMEFRAME_H1,
        'H4': mt5.TIMEFRAME_H4, 'D1': mt5.TIMEFRAME_D1,
    }
    data = get_quotes(tf_map[time_frame], 2020, 1, 1, asset=asset)
    return data.iloc[:, 1:5].values.round(decimals=5)  # OHLC array
```

#### Data Cost & Sufficiency Decision

**MT5 is free and is the ONLY data source the CRT Agent needs.** The software costs nothing; any broker demo account (ICMarkets, Pepperstone, Exness) provides free historical and live data for all CRT pairs — FX, Gold, crypto CFDs, indices. **No paid data platform is required until the system expands to live US equities trading** (a separate, later concern for the Research/Backtesting agents). Free interim options for equities research: Yahoo Finance (yfinance), Alpha Vantage (25 calls/day free), Alpaca (free real-time US equities data with account). Polygon.io is deferred indefinitely — budget for it only at equities go-live, and re-verify its pricing then (its free tier status has been in flux since the Massive.com rebrand).

**History depth caveat (the one real MT5 limitation):** brokers limit available history, especially on LTFs — H4 typically goes back years, but M5/M1 may only go back months. The CRT backtest needs 2+ years of LTF data. Mitigations, in order:
1. Choose a deep-history broker (ICMarkets and Pepperstone are known for long M1/M5 history)
2. In the MT5 terminal: Tools → Options → Charts → set "Max bars in chart" to Unlimited, then force-download history per pair/TF before first import
3. **PostgreSQL is the permanent archive:** from day one, every pull is stored; the DB accumulates LTF history forward forever, so even a shallow broker becomes a deep dataset within months. The DB — not the broker — is the canonical historical store.
4. If a pair's LTF history is too shallow for the full backtest window, run the backtest on the available window and extend it as the archive grows — never silently backtest H4-only logic and call it validated

**Demo vs live feed note:** demo-account prices occasionally differ slightly from live (spreads, weekend gaps). Acceptable for backtesting and paper trading; before go-live, switch the MT5 terminal to a live account login for feed parity.

#### MT5 Reliability — Watchdog Required

The Python library only works while the **MT5 terminal application is running and logged in** on the Windows machine. If the terminal crashes, auto-updates, or the broker session expires, the feed dies silently. `mt5_watchdog.py` (runs as its own process/service):
- Calls `mt5.terminal_info()` every 60s — if it fails, kill and relaunch the terminal executable, re-run `mt5.initialize(login=…, password=…, server=…)`
- After 3 failed restart cycles: alert via Telegram and set CRT Agent status to PAUSED (a stale feed must never feed the signal pipeline — see failure conditions in Section 8)
- Logs every restart event to the audit log

#### Asset Universe

Runs on all of the following pairs simultaneously (matching Kaabar's backtested universe plus Forex focus for CRT):

```python
CRT_PAIRS = [
    'EURUSD', 'GBPUSD', 'USDCHF', 'USDCAD',   # Major FX
    'AUDUSD', 'USDJPY', 'NZDUSD',               # Additional majors
    'XAUUSD',                                    # Gold
    'BTCUSD', 'ETHUSD',                          # Crypto (session filter disabled — 24/7 market)
    'US500', 'UK100',                            # Indices (if available on MT5 broker)
]
```

#### Timezone Handling (read this before anything else)

Three timezones collide in this system and must be explicitly mapped, or the agent will anchor to the wrong candles:

- **MT5 server time:** most brokers run EET (UTC+2, UTC+3 in summer). All candle timestamps from `copy_rates_range` are in server time. **H4 candle boundaries are defined by server time** — an "H4 candle" on an EET broker opens at 1:00, 5:00, 9:00 AM EST etc. only if the broker's offset makes it so.
- **Session macros:** defined in EST (New York time) per the playbook.
- **Kaabar's code:** uses Europe/Paris in `get_quotes()` — keep for data pulls but never for session logic.

The `timezone_map.py` module resolves this: it stores the broker's server UTC offset (auto-detected by comparing a live tick timestamp to UTC), converts every candle timestamp to EST before session-macro evaluation, and documents which H4 boundaries this broker produces in EST. **Verify at setup: print the H4 candle open times in EST and confirm they align with the session opens you intend to trade. If they don't, the broker's H4 grid doesn't suit the playbook — change brokers or change HTF.**

#### CRT Playbook Implementation (5 Steps)

**Step 1 — Anchor Candle Selection**
- Pull the most recently closed candle on the HTF (D1, H4, or H1 depending on config)
- Record `CRT_HIGH = candle.high` and `CRT_LOW = candle.low`
- These are drawn as horizontal lines on the chart: the ceiling and floor of the range

**Step 2 — Liquidity Raid Detection (Manipulation) — INTRA-CANDLE, not on close**

This is the most important implementation detail in the agent. The sweep must be detected *while the HTF candle is forming* — waiting for the H4 close makes signals up to 4 hours late and destroys the edge. But `mass_import()` only returns closed candles. The resolution:

- `live_candle.py` reconstructs the **forming HTF candle** from closed LTF bars on every scan tick: `live_high = max(ltf_highs since HTF open)`, `live_low = min(ltf_lows)`, `live_close = last ltf close`
- **Sweep event (bullish):** `live_low < CRT_LOW` (raid has occurred) AND the most recent *closed LTF candle* closes back above `CRT_LOW` (reclaim confirmed on LTF close — this is the playbook's own confirmation unit, available in real time)
- **Sweep event (bearish):** mirror logic above `CRT_HIGH`
- **Invalidation (live):** a closed LTF candle closes beyond the sweep extreme by more than `CRT_INVALIDATION_ATR_MULT × ATR(LTF)` — price is trending out, not sweeping
- **Invalidation (final):** if the HTF candle ultimately *closes* outside the range, the setup is void regardless of LTF state — await next anchor
- **3-Candle Rule:** if the sweep candle (C2) closes and the following HTF candle (C3) does not trigger an entry, the setup expires

**Backtest parity rule:** the backtest must replay LTF bars *inside* each HTF candle in chronological order and apply exactly the logic above. It must never use the HTF candle's close to qualify a sweep and then "enter" at a price inside that same candle — that is look-ahead bias and will inflate results. One code path for live and backtest (`sweep_detector.py` consuming an LTF bar stream) guarantees parity.

**Step 3 — Drop to LTF for Nested CRT**
- Once the HTF sweep event fires, evaluate the execution TF (M15/M5/M1)
- On the LTF, identify a micro candle range (a second, nested CRT) around the sweep zone
- Confirm: LTF candle sweeps its own minor high/low in the same direction as the HTF bias and closes back inside the LTF range

**Step 4 — Market Structure Shift (MSS) Confirmation — parameterised**

All three detection thresholds are explicit config values, not vibes:

- **Swing definition:** fractal — a swing high is a bar whose high exceeds the highs of `CRT_SWING_FRACTAL_N` bars on each side (default 2); mirror for swing lows
- **Displacement:** the breaking candle's range must exceed `CRT_DISPLACEMENT_ATR_MULT × ATR(LTF, 14)` (default 1.5) — a weak drift through a swing point is not displacement
- **FVG:** a three-candle imbalance where candle 1's high < candle 3's low (bullish; mirror for bearish), with gap size ≥ `CRT_FVG_MIN_ATR_MULT × ATR(LTF, 14)` (default 0.25) — micro-gaps don't count
- MSS confirmed = displacement candle breaks the most recent swing (in bias direction) AND leaves a qualifying FVG. Record the FVG zone `(fvg_high, fvg_low)` and any order block (last opposite-colour candle before displacement)

**Step 5 — Entry, SL, TP Calculation — entry comes from the FVG, not a fixed offset**

```python
def calculate_crt_levels(crt_high, crt_low, direction, mss_result,
                         sl_mode='conservative', ltf_sweep_extreme=None,
                         htf_sweep_extreme=None):
    """
    Entry is the midpoint of the MSS-created FVG zone (the playbook's retest level).
    If an order block was recorded, its open is an alternative entry (config choice).
    The old `low + range*0.15` formula is FALLBACK ONLY when no FVG qualifies,
    and such signals are tagged entry_basis='fallback' and scored lower.
    """
    range_size = crt_high - crt_low
    eq_50 = crt_low + range_size * 0.5            # TP1: 50% equilibrium of HTF range

    if mss_result.fvg is not None:
        entry = (mss_result.fvg.high + mss_result.fvg.low) / 2
        entry_basis = 'fvg_midpoint'
    elif mss_result.order_block is not None:
        entry = mss_result.order_block.open
        entry_basis = 'order_block'
    else:
        entry = (crt_low + range_size * 0.15) if direction == 'LONG' \
                else (crt_high - range_size * 0.15)
        entry_basis = 'fallback'                  # flagged lower-conviction

    if direction == 'LONG':
        # Conservative: below the absolute low of the HTF manipulation wick
        # Aggressive: below the LTF sweep candle's low
        sl = (htf_sweep_extreme if sl_mode == 'conservative'
              else ltf_sweep_extreme)
        sl -= atr_buffer(pair)                    # small ATR-based buffer beyond the wick
        tp1, tp2 = eq_50, crt_high
    else:  # SHORT
        sl = (htf_sweep_extreme if sl_mode == 'conservative'
              else ltf_sweep_extreme)
        sl += atr_buffer(pair)
        tp1, tp2 = eq_50, crt_low

    return {'entry': entry, 'entry_basis': entry_basis,
            'sl': sl, 'tp1': tp1, 'tp2': tp2}
```

Note the SL change: stops are placed relative to the **actual sweep wick extremes** (the playbook's rule) plus a small ATR buffer — not a percentage of range, which ignored where the manipulation actually travelled.

#### Kaabar Pattern Engine Integration

The CRT Agent also embeds the full Kaabar candlestick pattern recognition engine from *Mastering Financial Pattern Recognition*. Every CRT signal is cross-referenced against Kaabar patterns to add confluence. Patterns are implemented using the book's exact `signal()` function structure (primal functions + add_column/delete_column/rounding):

| Pattern Category | Patterns Used as CRT Confluence |
|---|---|
| Classic Trend-Following | Marubozu, Three White Soldiers / Three Black Crows, Hikkake |
| Modern Trend-Following | Double Trouble (ATR-based range expansion), H Pattern, Bottle, Slingshot, Quintuplets |
| Classic Contrarian | Engulfing, Hammer, Doji, Harami, Tweezers, Piercing, Inside Up/Down |
| Modern Contrarian | Doppelgänger, Mirror, Barrier, Euphoria, Shrinking, Blockade |
| Advanced Systems | Heikin-Ashi filter (smoothed candle direction), K's Candlesticks (open = prior close filter) |
| Combined Strategies | Double Trouble + RSI, H Pattern + TII, Marubozu + K's Volatility Bands, Bottle + Stochastic |

A CRT signal gains **confluence score +1** for each Kaabar pattern that agrees with the direction on the same or adjacent bars. Signals with 0 confluence are still valid CRT setups but flagged as lower conviction.

**Confluence is an unproven hypothesis until backtested.** Kaabar validated these patterns standalone, mostly on hourly data — nobody has tested whether they add lift on top of CRT setups at H4/M5. The CRT backtest must measure hit-rate lift per pattern (signals with pattern X present vs absent). Keep `CRT_MIN_CONFLUENCE_SCORE=0` until that analysis shows which patterns actually help; only then consider raising the threshold.

#### CRT-Specific Cost Model (session-aware spreads)

The general backtest cost model (flat 5bps + 2bps) was designed for equities and **understates CRT costs**, because CRT deliberately trades session opens — exactly when FX spreads widen 2–5×. The CRT backtest and live risk checks use a per-pair, session-aware spread model instead:
- Base spread per pair stored in `crt_config.yaml` (e.g., EURUSD 0.8 pips, XAUUSD 25 cents, BTCUSD broker-dependent)
- Multiplied by `CRT_SPREAD_OPEN_MULT` (default 2.5) during the first `CRT_SPREAD_OPEN_WINDOW_MINS` (default 15) of London and NY opens
- Multiplied further during scheduled high-impact news windows if a news calendar is later integrated (v2)
- The live Execution Agent records actual spread at fill time so the model can be calibrated against reality after the first weeks of paper trading

#### High-Probability Filters (all configurable)

| Filter | Implementation | Status |
|---|---|---|
| PD Array confluence | `pd_array_detector.py` programmatically detects HTF PD arrays: Fair Value Gaps (3-candle imbalance on H4/D1), Order Blocks (last opposite candle before displacement), and prior Daily/Weekly highs/lows. Anchor candle must close within `CRT_PDA_PROXIMITY_ATR` of a detected array. Arrays stored in DB with creation time and mitigation status. | v1 — FVG + prior H/L; OB in v1.1 |
| Session macro timing | **Per asset class** via `session_clock.py` + `timezone_map.py` (all evaluated in EST after server-time conversion): Forex 1:00/5:00/9:00 AM; Indices 2:00/6:00/10:00 AM; **Crypto: filter disabled by default** (24/7 market, no session opens) — optional NY-hours-only mode | v1 |
| Premium/Discount zone | Measured against a **higher-timeframe dealing range**, NOT the anchor candle itself (a sweep below CRT-Low is trivially below the anchor's EQ — circular). Dealing range = the range between the most recent unmitigated major swing high and swing low on `CRT_DEALING_RANGE_TF` (default D1, lookback `CRT_DEALING_RANGE_LOOKBACK` = 20 bars). Bullish CRT valid only when the sweep occurs below that range's 50%; bearish only above. | v1 |
| 3-Candle Rule | Setup must complete within 3 HTF candles: C1 = anchor, C2 = sweep, C3 = entry trigger. Expires otherwise. | v1 |
| Nested LTF CRT | LTF micro-structure must confirm before entry is triggered | v1 |
| MSS + FVG | Structural displacement with qualifying FVG (parameterised: fractal N, displacement ATR multiple, min FVG size) | v1 |

#### CRT Agent Outputs

- **CRT Signal objects:** pushed to the shared signal queue with all levels pre-calculated (entry, SL conservative, SL aggressive, TP1, TP2), direction, HTF/LTF pair, session macro flag, Kaabar pattern confluence score, filter checklist
- **CRT Chart exports:** PNG exports of the signal chart per pair showing: HTF candle with CRT-High/CRT-Low marked, sweep wick highlighted, LTF MSS candle annotated, Kaabar pattern overlay, all price levels drawn
- **Signal log entries:** every signal timestamped and stored in DB with full metadata

**What it does NOT do:** Size positions (that belongs to the Risk Agent). Submit orders (that belongs to the Execution Agent). Operate without data from MT5.

**OpenRouter API (owl-alpha) role:** Generate a plain-English signal rationale for the approval UI: "On H4 EURUSD, a bullish CRT formed at 1.0842. The anchor candle closed at a Daily Order Block. C2 swept sell-side liquidity below 1.0812 and closed back inside the range. An M5 MSS with FVG confirmed re-entry. Kaabar Double Trouble pattern present (bullish). Entry near 1.0820, SL at 1.0800, TP1 at 1.0876 (EQ), TP2 at 1.0910 (CRT-High)."

---

---

### 3.7 Photon Agent (Expectational Orderflow / SMC Signal Agent)

**Purpose:** A second specialist signal agent implementing the Photon Trading framework — top-down multi-timeframe structural analysis, Expectational Orderflow (EOF), institutional Points of Interest, liquidity mapping, and a mechanical LTF-BOS entry model. Like the CRT Agent, it runs its own independent pipeline and injects signals into the shared Risk → Execution layer.

#### What it is, and how it differs from the CRT Agent

The two agents are complementary lenses on the same institutional behaviour:

| | CRT Agent | Photon Agent |
|---|---|---|
| Unit of analysis | A single HTF candle treated as a range | Market structure across D1 → H4 → M15 → M1 |
| Core trigger | Sweep of the anchor candle's extreme + reclaim | Price arrival at a pre-identified POI + liquidity sweep + LTF BOS |
| Posture | Reactive within the candle's lifecycle | **Anticipatory** — the expectation is built before price arrives (EOF) |
| Typical hold | Within 1–3 HTF candles | Structural leg (hours to days) |
| Shared | MT5 feed, timezone map, live candle reconstruction, spread model, Kaabar confluence engine, Risk → Execution pipeline | same |

Both run as independent processes; every signal is tagged with its source agent for separate performance attribution.

#### The Photon Pipeline (11 phases → deterministic modules)

**Module 1 — Structure Engine (`structure_engine.py`)**
- Fractal swing detection: swing high = high exceeding `PHOTON_SWING_FRACTAL_N` (default 2) bars each side; mirror for lows
- Label every swing per timeframe: HH / HL / LH / LL
- **Strong/Weak classification (Photon's filter):** a Strong Low is a low that produced a subsequent Higher High (institutions defended it); a Weak Low failed to produce a new HH. Mirror for highs. Only Strong levels qualify as tradeable POIs in trend direction.

**Module 2 — BOS / CHoCH Detector (`bos_choch.py`)**
- **BOS (Break of Structure):** price breaks a swing point in the SAME direction as the current trend → continuation signal
- **CHoCH (Change of Character):** the FIRST break against the current trend → bias warning, not an entry signal
- Break confirmation mode: `PHOTON_BOS_CONFIRM=close` (candle close beyond the level, default) or `wick`
- Every BOS/CHoCH event is logged per timeframe with timestamp and level

**Module 3 — Trend State Machine (`trend_state.py`)**
- Per-timeframe state: BULLISH / BEARISH / RANGING, derived from the structure engine + last BOS/CHoCH event
- The H4 state is the **narrative**; D1 is **perspective**; M15 is **immediate bias**; M1/M5 is **timing** — exactly Photon's table

**Module 4 — POI Detector (`poi_detector.py`)**
- Supply/demand zones qualified by ALL of:
  - Impulsive departure: departure candle range > `PHOTON_POI_DEPARTURE_ATR_MULT` (default 1.5) × ATR(TF,14)
  - Compact base: ≤ `PHOTON_POI_MAX_BASE_CANDLES` (default 5) candles in the base
  - Freshness: zone untested since creation (`PHOTON_POI_FRESH_ONLY=true`)
  - Strong/Weak filter: zone anchored at a Strong level only
  - Embedded FVG recorded if present (gap ≥ `PHOTON_FVG_MIN_ATR_MULT` × ATR) — becomes the precision entry
- Zones stored in DB with creation time, timeframe, strength class, and mitigation status

**Module 5 — Liquidity Map (`liquidity_map.py`)**
- **BSL:** equal highs (within `PHOTON_EQUAL_LEVEL_TOLERANCE_ATR` (default 0.1) × ATR) + recent swing highs
- **SSL:** equal lows + recent swing lows
- Sweep detection: wick through a pool followed by close back (the trap springing)
- Pre-entry checks the playbook requires: nearest pool between entry and target (potential stall), and whether the entry zone's pool has already been swept (confirmation)

**Module 6 — EOF Engine (`eof_engine.py`) — the signature Photon step**
- When a new structural extreme forms on H4 (e.g., new Lower Low in a bearish trend), create an **Expectation object**: the LTFs should now turn counter-trend to pull back toward the next structural level (the next Lower High), which will form at the previous Strong H4 high → that POI
- Expectation = {pair, direction, anticipated_zone (POI ref), created_at, status: PENDING → PRICE_ARRIVED → TRIGGERED / EXPIRED}
- Expectations expire if structure invalidates them (e.g., CHoCH against the premise) before price arrives
- This is what makes the agent anticipatory: the zone is identified and stored **before** price travels there

**Module 7 — MTF Alignment (`mtf_alignment.py`)**
- Checklist evaluated at signal time: D1 perspective ✓/✗, H4 narrative ✓/✗, M15 bias confirming ✓/✗, LTF trigger ✓/✗
- Produces an alignment score (0–4); `PHOTON_MIN_ALIGNMENT=3` by default (D1 may be neutral, H4 + M15 + LTF must agree)

**Module 8 — Entry Engine (`entry_engine.py`) — the mechanical sequence**
1. Price arrives inside a PENDING expectation's POI
2. Liquidity sweep confirmed at/around the zone (from Module 5)
3. LTF (M1/M5) BOS in the trade direction — orderflow has shifted; this is the trigger
4. Entry = midpoint of the FVG inside the POI (`entry_basis='fvg_in_poi'`); else LTF BOS candle close (`'bos_close'`); else limit at zone boundary (`'zone_limit'`)
- All three conditions are hard requirements — no sweep or no LTF BOS means no signal, regardless of how good the zone looks

**Module 9 — Trade Levels (`trade_levels.py`)**
- SL: beyond the POI extreme / sweep extreme + `PHOTON_SL_ATR_BUFFER_MULT` (default 0.3) × ATR(LTF,14)
- TP1: nearest opposing liquidity pool (BSL for longs, SSL for shorts) — partial + move SL to breakeven
- TP2: next significant POI / structural target
- **Hard R:R gate:** computed R:R to TP1 must be ≥ `PHOTON_MIN_RR` (default 2.0) or the signal is rejected and logged (Photon aims for 5:1 on clean setups — that's the target, 2:1 is the floor)

**Module 10 — News Filter (`news_filter.py`)**
- v1: manual weekly schedule of high-impact events in `photon_config.yaml`; entries blocked `PHOTON_NEWS_BLACKOUT_MINS` (default 15) before each, re-allowed after the spike window
- v2: automated economic calendar feed
- Shared with the CRT Agent once built (CRT's spread model references the same news windows)

**Module 11 — Runner, Charts, Rationale**
- `runner.py`: every scan tick — update structure/trend per TF, refresh POIs and liquidity, create/expire expectations, check entry sequence on PRICE_ARRIVED expectations, emit signals
- `chart_exporter.py`: PNG per signal — structure labels (HH/HL/LH/LL), BOS/CHoCH marks, POI zones shaded, liquidity pools marked, the expectation arrow (where the level was anticipated vs where price triggered), entry/SL/TP lines
- `nim_rationale.py`: owl-alpha plain-English rationale, e.g. *"H4 GBPUSD is bearish (LH/LL). After the new H4 low at 1.2581, an expectation was created for the next Lower High at the previous Strong high zone 1.2640–1.2655. Price arrived, swept the equal highs at 1.2648 (BSL), and M5 broke structure bearish with displacement. Entry 1.2643 (FVG in POI), SL 1.2661, TP1 1.2598 (SSL pool, 2.5R), TP2 1.2560."*

#### Photon Backtesting Requirements

Same parity discipline as CRT: the backtest replays LTF bars through the exact live code path — structure, expectations, sweeps, and LTF BOS must all be evaluated on information available at that moment. Additionally, Photon's own Phase 9 rule is encoded as a gate: **minimum 50–100 recorded setups across the pair universe before live consideration**, with win rate, average R:R, and expectancy reported per pair and per entry_basis.

#### Photon Agent Outputs

- **PhotonSignal objects:** expectation id, POI reference, MTF alignment score, liquidity context (pools swept / pools in path), entry_basis, all levels, computed R:R — pushed to the shared signal queue
- **Chart exports:** annotated PNGs as above
- **Expectation board state:** all PENDING/PRICE_ARRIVED expectations per pair (drives Screen 8)

**What it does NOT do:** Size positions. Submit orders. Trade Weak levels. Enter without the sweep + LTF BOS sequence. Operate on stale MT5 data.

#### The Human-Side Phases (1, 10, 11) — where they live in the OS

Three phases of the playbook are disciplines, not detection code, and map onto existing OS structures rather than Photon modules:

- **Phase 1 (Theoretical foundation — Auction Market Theory, microstructure, orderflow):** your reading, not the agent's. *Trading and Exchanges* (Harris) in the project library covers the microstructure half. The owl-alpha rationale text deliberately narrates signals in orderflow language so every approval decision reinforces the framework rather than becoming pattern-matching.
- **Phase 10 (Living trade plan):** this entire MASTER_PLAN + the `photon_config.yaml` parameters ARE the written trade plan — bias rules, POI qualification, entry rules, and risk rules all live in version-controlled config, not in your head. The journalling requirement maps to the Monitoring Agent's `trade_journal.py` (every trade logged with chart export, rationale, expected vs actual) and `weekly_report.py` (the mandated weekly review).
- **Phase 11 (Psychology / +EV mindset):** structurally enforced rather than willed — the backtest gate (≥50 setups before live) builds the statistical conviction the playbook describes; expectancy is reported per strategy in the weekly report so success is measured in long-run EV, not per-trade outcomes; and MANUAL mode with the approval queue removes the impulse-execution failure mode entirely.


---

## 4. Orchestration Layer

**Engine:** LangGraph state machine.

### 4.1 Strategy Lifecycle State Machine

```
IDEA_PROPOSED
    │  ✋ Human selects idea for testing
    ▼
BACKTESTING
    │  ✋ Human reviews backtest report → approve / reject
    ▼
RISK_REVIEW
    │  ✋ Human confirms risk parameters + position sizing
    ▼
PAPER_TRADING          ← minimum 4 weeks
    │  ✋ Human reviews paper trade performance → go live / kill
    ▼
LIVE_TRADING
    │  Monitoring agent watches continuously
    │  ✋ Human reviews 30-day report
    ▼
SCALING / PAUSED / RETIRED
```

Note: Specialist signal agents (CRT, Photon) bypass the Research Agent stage — they are fully-specified strategies with known playbooks. Each enters the lifecycle at BACKTESTING (historical validation) then follows the same gate sequence as every other strategy, independently.

### 4.2 Signal Lifecycle

```
Signal generated (CRT Agent or other strategy agent)
    │
    ▼
Risk Agent validates + sizes position
    │
    ▼
Execution mode check:
    ├── AUTO: order submitted immediately
    └── MANUAL: signal queued in approval UI
              │  ✋ Human reviews: signal, rationale (owl-alpha generated),
              │     CRT levels, Kaabar confluence, risk metrics, filter checklist
              └── APPROVE → order submitted
                  REJECT  → signal discarded, logged
                  MODIFY  → human adjusts size/price → submitted
```

### 4.3 Human Approval Gates (non-negotiable)

| Gate | Trigger | What you see | Actions |
|---|---|---|---|
| Idea approval | Research agent proposes idea | Hypothesis, source, score | Approve / Reject |
| CRT backtest approval | CRT historical validation complete | Hit ratio, profit factor, walk-forward, per-pair breakdown | Approve / Reject |
| Photon backtest approval | ≥50–100 recorded setups complete | Win rate, avg R:R, expectancy per pair + per entry_basis, alignment-score impact | Approve / Reject |
| Risk parameter sign-off | Before paper or live trading | Kelly sizing, drawdown limits, stop levels | Confirm / Adjust |
| Paper → Live approval | 4+ weeks paper trade complete | Execution quality, slippage, P&L vs expectation | Go Live / Kill |
| Signal approval (manual mode) | New signal generated | Signal + CRT rationale + levels + confluence score | Approve / Reject / Modify |
| Limit change approval | Any change to risk limits | Old limit, new limit, reason | Confirm / Cancel |
| 30-day live review | Monthly | Strategy P&L, regime analysis, degradation flags | Scale / Pause / Kill |

### 4.4 Audit Log

Every agent action, every decision, every approval is written to the audit log:

```json
{
  "timestamp": "2026-06-01T09:32:11Z",
  "actor": "crt_agent | risk_agent | human:tobechukwu | execution_agent",
  "action": "crt_signal_generated | position_sized | signal_approved | order_submitted",
  "strategy_id": "crt_eurusd_h4_001",
  "details": {
    "pair": "EURUSD",
    "htf": "H4", "ltf": "M5",
    "direction": "LONG",
    "crt_high": 1.0910, "crt_low": 1.0812,
    "entry": 1.0820, "sl": 1.0800, "tp1": 1.0861, "tp2": 1.0910,
    "filters_passed": ["pd_array", "session_macro", "nested_ltf_crt", "mss_fvg"],
    "kaabar_confluence": ["double_trouble_bull"],
    "confluence_score": 1
  },
  "outcome": "approved"
}
```

---

## 5. Folder Structure

```
quant_os/
│
├── agents/
│   ├── shared/                     # ← SHARED INFRASTRUCTURE (built once, used by all agents)
│   │   ├── __init__.py
│   │   ├── nim_client.py           # singleton OpenAI client → OpenRouter (owl-alpha); the ONLY LLM dependency
│   │   ├── market/
│   │   │   ├── __init__.py
│   │   │   ├── live_candle.py      # reconstruct forming HTF candle from closed LTF bars (CRT + Photon)
│   │   │   ├── timezone_map.py     # broker server-time → EST conversion; H4 boundary verification
│   │   │   ├── swings.py           # fractal swing detection (shared by CRT MSS + Photon structure engine)
│   │   │   ├── fvg.py              # FVG detection w/ ATR-based min size (shared by CRT + Photon)
│   │   │   ├── atr.py              # ATR utilities
│   │   │   ├── spread_model.py     # per-pair session-aware spread model (backtests + live risk checks)
│   │   │   └── mt5_watchdog.py     # terminal health check, auto-restart, alert + PAUSE after 3 failures
│   │   └── kaabar/                 # Kaabar pattern engine (Mastering Financial Pattern Recognition) — imported by CRT (confluence) and Photon (optional confluence)
│   │       ├── __init__.py
│   │       ├── primal.py           # add_column, delete_column, add_row, delete_row, rounding
│   │       ├── indicators.py       # ATR, moving average, RSI, stochastic, TII, K's volatility bands
│   │       ├── patterns/
│   │       │   ├── __init__.py
│   │       │   ├── trend_following/
│   │       │   │   ├── marubozu.py         # Marubozu (no-wick, full-range candle)
│   │       │   │   ├── three_candles.py    # Three White Soldiers / Three Black Crows
│   │       │   │   ├── hikkake.py          # Hikkake (false breakout)
│   │       │   │   ├── double_trouble.py   # Double Trouble (ATR-based range expansion)
│   │       │   │   ├── h_pattern.py        # H Pattern (trend continuation via doji pivot)
│   │       │   │   ├── bottle.py           # Bottle (open = low/high continuation)
│   │       │   │   ├── slingshot.py        # Slingshot (pullback breakout)
│   │       │   │   └── quintuplets.py      # Quintuplets (5 small same-colour candles)
│   │       │   ├── contrarian/
│   │       │   │   ├── engulfing.py        # Engulfing (body fully engulfs prior body)
│   │       │   │   ├── hammer.py           # Hammer / Shooting Star
│   │       │   │   ├── doji.py             # Doji (open ≈ close)
│   │       │   │   ├── harami.py           # Harami (flexible + strict)
│   │       │   │   ├── tweezers.py         # Tweezers (equal highs/lows)
│   │       │   │   ├── piercing.py         # Piercing / Dark Cloud Cover
│   │       │   │   ├── inside_updown.py    # Inside Up / Inside Down
│   │       │   │   ├── doppelganger.py     # Doppelgänger (twin candles reversal)
│   │       │   │   ├── mirror.py           # Mirror (reflection reversal)
│   │       │   │   ├── barrier.py          # Barrier (equal highs or lows with rounding)
│   │       │   │   ├── euphoria.py         # Euphoria (gap-open reversal)
│   │       │   │   └── shrinking.py        # Shrinking (diminishing body reversal)
│   │       │   └── advanced/
│   │       │   │   ├── heikin_ashi.py      # Heikin-Ashi smoothed candle system
│   │       │   │   └── ks_candlesticks.py  # K's Candlesticks (open = prior close filter)
│   │       ├── strategies/
│   │       │   ├── double_trouble_rsi.py       # Double Trouble + RSI
│   │       │   ├── h_pattern_tii.py            # H Pattern + Trend Intensity Index
│   │       │   ├── marubozu_kvol_bands.py      # Marubozu + K's Volatility Bands
│   │       │   ├── bottle_stochastic.py        # Bottle + Stochastic Oscillator
│   │       │   └── barrier_rsi_atr.py          # Barrier + RSI/ATR combo
│   │       ├── performance.py      # hit ratio, profit factor, risk-reward, equity curve
│   │       └── visualisation.py    # ohlc_plot_bars, signal_chart, candlestick chart
│   │
│   ├── research/
│   │   ├── __init__.py
│   │   ├── scanner.py              # paper/blog scraper
│   │   ├── scorer.py               # idea scoring rubric
│   │   ├── nim_client.py        # OpenRouter API (owl-alpha) calls for summarisation
│   │   └── models.py               # StrategyIdea dataclass
│   │
│   ├── backtesting/
│   │   ├── __init__.py
│   │   ├── runner.py               # backtest execution engine
│   │   ├── bias_checks.py          # look-ahead, survivorship bias guards
│   │   ├── cost_model.py           # commissions, spread, slippage
│   │   ├── walk_forward.py         # rolling WF test
│   │   ├── monte_carlo.py          # permutation significance test
│   │   └── report.py               # generate BacktestReport
│   │
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── kelly.py                # Kelly + fractional Kelly calculator
│   │   ├── sizer.py                # position sizing logic
│   │   ├── limits.py               # drawdown, daily loss, concentration limits
│   │   ├── stop_loss.py            # ATR-based and percentage stop engine
│   │   ├── tail_risk.py            # 5-sigma stress check
│   │   └── dashboard.py            # live risk state aggregator
│   │
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── broker/
│   │   │   ├── alpaca.py           # Alpaca REST connector
│   │   │   ├── ibkr.py             # IBKR ibapi connector
│   │   │   └── binance.py          # Binance connector
│   │   ├── order_manager.py        # order lifecycle (submit/track/retry)
│   │   ├── modes.py                # AUTO vs MANUAL mode logic
│   │   ├── reconciler.py           # sync broker state with internal state
│   │   ├── kill_switch.py          # emergency halt
│   │   └── slippage_tracker.py     # theoretical vs actual fill tracker
│   │
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── pnl_tracker.py          # live P&L aggregation
│   │   ├── regime_detector.py      # volatility + correlation regime analysis
│   │   ├── degradation.py          # strategy live vs backtest Sharpe drift
│   │   ├── alerts.py               # Telegram + email alert dispatcher
│   │   ├── trade_journal.py        # per-trade log with reasoning
│   │   └── weekly_report.py        # auto-generated Sunday report
│   │
│   ├── crt/                        # ← CRT AGENT (specialist signal agent #1)
│   │   # imports from agents/shared/: nim_client, market/{live_candle, timezone_map, swings, fvg, atr, spread_model, mt5_watchdog}, kaabar
│       ├── __init__.py
│       ├── mt5_feed.py             # MT5 connector: get_quotes() + mass_import()
│       ├── anchor.py               # HTF anchor candle selection + CRT-High/Low marking
│       ├── sweep_detector.py       # Step 2: INTRA-CANDLE raid detection + LTF-close reclaim + invalidation — single code path for live AND backtest
│       ├── nested_crt.py           # Step 3: LTF nested CRT micro-structure detection
│       ├── mss_detector.py         # Step 4: MSS + FVG (fractal N, displacement ATR mult, min FVG size — all from crt_config.yaml)
│       ├── pd_array_detector.py    # HTF PD arrays: FVGs + prior daily/weekly highs/lows (v1); order blocks (v1.1); stored in DB w/ mitigation status
│       ├── dealing_range.py        # higher-TF dealing range (major swing high↔low on D1) for premium/discount filter
│       ├── levels.py               # Step 5: entry = FVG midpoint / OB open (fallback: range offset, flagged); SL = sweep wick + ATR buffer; TP1/TP2
│       ├── filters.py              # high-probability filter checklist (PD array, session, premium/discount vs dealing range)
│       ├── session_clock.py        # session macros per asset class (crypto disabled by default); evaluated in EST
│       ├── signal_builder.py       # assembles CRTSignal object from all components
│       ├── chart_exporter.py       # generates PNG signal chart with all levels annotated
│       ├── nim_rationale.py        # OpenRouter API (owl-alpha): generate plain-English signal explanation
│       ├── runner.py               # main loop: iterates all CRT_PAIRS, HTF/LTF combos
│       └── models.py               # CRTSignal dataclass, CRTLevel, CRTFilterResult
│
│   └── photon/                     # ← PHOTON AGENT (specialist signal agent #2 — Expectational Orderflow / SMC)
│       # imports from agents/shared/: nim_client, market/{live_candle, timezone_map, swings, fvg, atr, spread_model}, kaabar (optional confluence)
│       ├── __init__.py
│       ├── structure_engine.py     # fractal swings, HH/HL/LH/LL labelling, Strong/Weak high-low classification
│       ├── bos_choch.py            # BOS (with-trend break) vs CHoCH (first counter-trend break); close- or wick-confirm
│       ├── trend_state.py          # per-TF state machine: BULLISH / BEARISH / RANGING (D1 perspective, H4 narrative, M15 bias)
│       ├── poi_detector.py         # supply/demand zones: impulsive departure, compact base, freshness, Strong filter, embedded FVG
│       ├── liquidity_map.py        # BSL/SSL pools (equal highs/lows + swings), sweep detection, pools-in-path check
│       ├── eof_engine.py           # Expectational Orderflow: pre-build Expectation objects (PENDING → PRICE_ARRIVED → TRIGGERED/EXPIRED)
│       ├── mtf_alignment.py        # D1/H4/M15/LTF alignment checklist + score (min 3/4 to trade)
│       ├── entry_engine.py         # mechanical sequence: POI arrival → sweep confirmed → LTF BOS → entry (FVG-in-POI / BOS close / zone limit)
│       ├── trade_levels.py         # SL beyond POI+sweep extreme + ATR buffer; TP1 = nearest opposing pool; TP2 = next POI; hard min-R:R gate
│       ├── news_filter.py          # v1: manual red-news schedule, blackout window; v2: automated calendar (shared with CRT)
│       ├── signal_builder.py       # assembles PhotonSignal (expectation id, POI ref, alignment score, liquidity context, levels)
│       ├── chart_exporter.py       # PNG: structure labels, BOS/CHoCH marks, POI zones, liquidity pools, expectation arrow, levels
│       ├── nim_rationale.py        # owl-alpha plain-English setup narrative for the approval UI
│       ├── runner.py               # scan loop: update structure → POIs → liquidity → expectations → entry checks → emit signals
│       └── models.py               # PhotonSignal, POI, LiquidityPool, Expectation, AlignmentResult dataclasses
│
├── orchestrator/
│   ├── __init__.py
│   ├── state_machine.py            # LangGraph strategy lifecycle FSM
│   ├── signal_router.py            # all agent signals → Risk → Execution
│   ├── approval_queue.py           # pending human decisions (Redis-backed)
│   ├── audit_log.py                # immutable append-only action log
│   └── health_monitor.py           # agent heartbeat + feed freshness watchdog
│
├── data/
│   ├── __init__.py
│   ├── ingestion/
│   │   ├── yahoo.py                # Yahoo Finance OHLCV
│   │   ├── polygon.py              # Polygon.io paid feed
│   │   ├── binance_feed.py         # Binance public market data
│   │   └── fred.py                 # FRED macro data
│   ├── mt5/
│   │   ├── connector.py            # MT5 Python library wrapper
│   │   ├── timeframes.py           # MT5 timeframe constants + mapping
│   │   └── pairs.py                # CRT_PAIRS universe definition
│   ├── pipeline.py                 # clean, adjust, validate, store
│   ├── quality_checker.py          # gap detection, outlier flagging
│   ├── realtime_feed.py            # WebSocket / REST polling live feed
│   └── universe.py                 # point-in-time symbol universe management
│
├── strategies/
│   ├── __init__.py
│   ├── base.py                     # BaseStrategy abstract class
│   ├── mean_reversion/
│   │   └── pairs_trading.py
│   ├── momentum/
│   │   └── cross_sectional.py
│   └── factor/
│       └── quality_value.py
│
├── db/
│   ├── models.py                   # SQLAlchemy models: Strategy, Signal, Order, Trade,
│   │                               #   CRTSignal, KaabarPatternResult, PhotonSignal, POI,
│   │                               #   LiquidityPool, Expectation, PerformanceRecord, AuditLog
│   ├── migrations/
│   └── seeds/
│
├── api/
│   ├── __init__.py
│   ├── main.py
│   ├── routers/
│   │   ├── strategies.py
│   │   ├── signals.py
│   │   ├── crt.py                  # CRT-specific endpoints: signals, charts, pair scan
│   │   ├── photon.py               # Photon endpoints: expectations board, POIs, liquidity map, signals
│   │   ├── risk.py
│   │   ├── performance.py
│   │   └── system.py
│   └── websockets.py
│
├── ui/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx           # Screen 1
│   │   │   ├── Signals.jsx             # Screen 2
│   │   │   ├── Strategies.jsx          # Screen 3
│   │   │   ├── RiskControls.jsx        # Screen 4
│   │   │   ├── Performance.jsx         # Screen 5
│   │   │   ├── SystemLogs.jsx          # Screen 6
│   │   │   ├── CRTScanner.jsx          # Screen 7 — CRT Agent screen
│   │   │   └── PhotonScanner.jsx       # Screen 8 — Photon Agent screen (expectation board)
│   │   └── components/
│   └── package.json
│
├── tests/
│   ├── unit/
│   │   ├── test_kelly.py
│   │   ├── test_cost_model.py
│   │   ├── test_bias_checks.py
│   │   ├── test_order_manager.py
│   │   ├── test_crt_levels.py          # CRT level calculation accuracy
│   │   ├── test_sweep_detector.py      # sweep detection logic
│   │   ├── test_kaabar_patterns.py     # all Kaabar pattern signal functions
│   │   ├── test_mss_detector.py        # MSS + FVG detection
│   │   ├── test_structure_engine.py    # swing labelling + Strong/Weak classification
│   │   ├── test_bos_choch.py           # BOS vs CHoCH event classification
│   │   ├── test_poi_detector.py        # zone qualification rules
│   │   ├── test_liquidity_map.py       # equal-level pools + sweep detection
│   │   ├── test_eof_engine.py          # expectation lifecycle (PENDING→ARRIVED→TRIGGERED/EXPIRED)
│   │   └── test_trade_levels.py        # SL/TP placement + min-R:R rejection
│   ├── integration/
│   │   ├── test_signal_to_order_flow.py
│   │   ├── test_data_pipeline.py
│   │   ├── test_crt_full_pipeline.py   # end-to-end CRT: MT5 → signal → approval queue
│   │   └── test_photon_full_pipeline.py # end-to-end Photon: structure → expectation → entry → approval queue
│   └── stress/
│       ├── test_crash_scenarios.py
│       └── test_broker_disconnect.py
│
├── scripts/
│   ├── run_backtest.py
│   ├── run_crt_scan.py             # CLI: run CRT scan across all pairs + print signals
│   ├── run_photon_scan.py          # CLI: run Photon scan — print structure states, expectations, signals
│   ├── seed_data.py
│   └── generate_report.py
│
├── config/
│   ├── settings.yaml
│   ├── crt_config.yaml             # CRT-specific config: pairs, HTF/LTF combos, filter toggles
│   ├── photon_config.yaml          # Photon config: pairs, TF stack, POI/structure params, news schedule, min R:R
│   └── logging.yaml
│
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 6. UI Screens

### Screen 1 — Dashboard (home)

**Purpose:** Instant situational awareness.

**Shows:**
- Portfolio P&L today, week, month (with vs benchmark comparison)
- Active strategies count + status badges (live / paper / paused)
- CRT active signals badge: number of live CRT setups across all pairs
- Pending signals awaiting approval (badge count)
- System health strip: data feed ✓, MT5 connection ✓, broker connection ✓, agent statuses ✓
- Top-level risk panel: current leverage, current max drawdown, daily loss used
- Kill switch button (always visible, top right)

---

### Screen 2 — Signal Review (manual mode inbox)

**Purpose:** Your decision queue.

**Shows per signal:**
- Strategy name + signal direction (LONG/SHORT) + ticker + suggested size
- For CRT signals: pair, HTF/LTF, CRT-High, CRT-Low, EQ 50%, step completion checklist, filter status, Kaabar confluence patterns
- Rationale section (OpenRouter API (owl-alpha) generated): plain-English explanation of why the signal fired
- Risk metrics: position size, stop loss level, max loss $, current portfolio exposure
- CRT chart PNG export showing all annotated levels
- **Approve / Reject / Modify** buttons
- Signal expiry countdown (signals expire after configurable timeout)

---

### Screen 3 — Strategy Manager

**Purpose:** Manage the full lifecycle of every strategy.

**Shows:**
- Strategy list with lifecycle status column
- CRT Agent listed as a permanent strategy with sub-rows per active pair
- Per-strategy: name, asset class, frequency, live Sharpe, current drawdown, last signal
- Actions: view backtest report, view live performance, pause, retire, edit parameters
- Lifecycle timeline per strategy

---

### Screen 4 — Risk Controls

**Purpose:** Set and monitor all risk limits.

**Shows:**
- Risk limit table (editable, with confirmation modal)
- Live risk gauges: leverage, drawdown, daily loss
- Per-strategy Kelly allocation breakdown (including CRT Agent allocation)
- Tail risk section: 3-sigma, 5-sigma, worst historical drawdown
- Emergency kill switch

---

### Screen 5 — Performance Analytics

**Purpose:** Deep-dive into strategy performance over time.

**Shows:**
- Portfolio equity curve with benchmark overlay
- Per-strategy Sharpe, Calmar, max drawdown, CAGR table
- CRT Agent breakdown: per-pair hit ratio, profit factor, signal frequency
- Monthly returns heatmap
- Backtest vs live comparison
- Trade distribution histogram
- Weekly report download

---

### Screen 6 — System Logs & Health

**Purpose:** Debug and audit.

**Shows:**
- Real-time agent activity log (filterable by agent, level, strategy)
- MT5 connection status: last heartbeat, feed latency, pairs active
- Audit trail: every human decision + timestamp
- Order log, broker connection status, system alerts history

---

### Screen 7 — CRT Scanner (new)

**Purpose:** The dedicated CRT Agent control centre and live scan view.

**Shows:**
- Live pair scan grid: all CRT_PAIRS with current HTF/LTF status, whether an anchor candle is active, whether a sweep has occurred, and whether a signal is pending
- Per-pair detail panel: CRT range visualisation (CRT-High, EQ 50%, CRT-Low), sweep wick highlighted, AMD zone labels, step completion pipeline (Steps 1–5)
- Kaabar pattern confluence overlay: which patterns are present on the current signal
- Session macro timing strip: London/NY/Futures windows with live clock
- Active signals queue: signals generated but not yet acted on
- Historical CRT trades log: past CRT signals with outcome (hit TP1/TP2, hit SL, or expired)
- Filter panel: toggle each high-probability filter on/off across all pairs
- MT5 connection status + last data refresh timestamp
- CRT Agent config: HTF/LTF combos, pairs enabled, filter toggles, session windows

---

### Screen 8 — Photon Scanner (new)

**Purpose:** The Photon Agent control centre — built around the Expectation Board, which is the heart of the EOF methodology.

**Shows:**
- **Expectation Board:** every PENDING and PRICE_ARRIVED expectation per pair — anticipated direction, the POI where the next structural level is expected to form, distance from current price, age, and status. This is the "where we are waiting and why" view.
- Per-pair structure panel: D1/H4/M15 trend states with last BOS/CHoCH event marked, HH/HL/LH/LL labels on a mini chart
- POI map: all unmitigated zones per pair with strength class (Strong/Weak), freshness, and embedded FVG flag
- Liquidity map: BSL/SSL pools with swept/unswept status, pools-in-path warnings for active expectations
- MTF alignment checklist for any candidate signal (D1 ✓ H4 ✓ M15 ✓ LTF ✓ + score)
- Active Photon signals queue (pending approval) with computed R:R and entry_basis
- Historical Photon trades log: outcome, R achieved, expectation-to-trigger time
- News blackout indicator: current/upcoming blocked windows
- Photon config panel: TF stack, pairs, structure/POI parameters, min R:R, news schedule

---

## 7. Environment Variables

```bash
# ── Application ──────────────────────────────────────────────
APP_ENV=development
APP_SECRET_KEY=your_secret_key_here
LOG_LEVEL=INFO

# ── Database ─────────────────────────────────────────────────
DATABASE_URL=postgresql://user:password@localhost:5432/quant_os
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# ── Redis ────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ── OpenRouter API — owl-alpha ─────────────────────────────────────────────
# Endpoint: https://openrouter.ai/api/v1  (OpenAI-compatible)
# Model card: https://openrouter.ai/openrouter/owl-alpha
# SDK: openai Python library (base_url override) — no Anthropic SDK required
OPENROUTER_API_KEY=sk-or-your_key_here        # generate at openrouter.ai
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openrouter/owl-alpha
OPENROUTER_MAX_TOKENS=16384               # owl-alpha max context window
OPENROUTER_TEMPERATURE=0.6               # lower = more deterministic for signal rationale
OPENROUTER_TOP_P=0.9
OPENROUTER_STREAM=true                   # use streaming for long rationale responses

# ── Broker: Alpaca ───────────────────────────────────────────
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPACA_DATA_URL=https://data.alpaca.markets

# ── Broker: Interactive Brokers ──────────────────────────────
IBKR_HOST=127.0.0.1
IBKR_PORT=7497
IBKR_CLIENT_ID=1

# ── Broker: Binance ──────────────────────────────────────────
BINANCE_API_KEY=your_binance_key
BINANCE_SECRET_KEY=your_binance_secret
BINANCE_TESTNET=true

# ── MetaTrader 5 (CRT Agent data source) ─────────────────────
MT5_LOGIN=your_mt5_account_number
MT5_PASSWORD=your_mt5_password
MT5_SERVER=your_broker_mt5_server    # e.g. ICMarkets-Demo
MT5_TIMEZONE=Europe/Paris            # timezone used in get_quotes()
MT5_ENABLED=true

# ── CRT Agent Config ─────────────────────────────────────────
CRT_HTF=H4                           # H1 | H4 | D1
CRT_LTF=M5                           # M1 | M5 | M15
CRT_PAIRS=EURUSD,GBPUSD,USDCHF,USDCAD,AUDUSD,USDJPY,NZDUSD,XAUUSD,BTCUSD,ETHUSD
CRT_FILTER_PD_ARRAY=true
CRT_FILTER_SESSION_MACRO=true
CRT_FILTER_PREMIUM_DISCOUNT=true
CRT_FILTER_NESTED_LTF=true
CRT_FILTER_MSS_FVG=true
CRT_SCAN_INTERVAL_SECONDS=60         # how often the runner checks for new setups
CRT_SL_MODE=conservative             # conservative (HTF sweep wick) | aggressive (LTF sweep wick)
CRT_MIN_CONFLUENCE_SCORE=0           # 0 = accept all CRT signals; raise only after backtest proves pattern lift

# ── CRT detection parameters (the difference between deterministic and vibes) ──
CRT_SWING_FRACTAL_N=2                # swing high/low = exceeds N bars on each side
CRT_DISPLACEMENT_ATR_MULT=1.5        # MSS candle range must exceed this × ATR(LTF,14)
CRT_FVG_MIN_ATR_MULT=0.25            # FVG gap must be ≥ this × ATR(LTF,14) to qualify
CRT_INVALIDATION_ATR_MULT=1.0        # LTF close beyond sweep extreme by this × ATR = trend, not sweep
CRT_SL_ATR_BUFFER_MULT=0.3           # SL buffer beyond sweep wick, in ATR(LTF,14) multiples
CRT_PDA_PROXIMITY_ATR=1.0            # anchor must close within this × ATR of a PD array
CRT_DEALING_RANGE_TF=D1              # timeframe for premium/discount dealing range
CRT_DEALING_RANGE_LOOKBACK=20        # bars to scan for major swing high/low

# ── CRT session-aware spread model ───────────────────────────
CRT_SPREAD_OPEN_MULT=2.5             # spread multiplier during session-open windows
CRT_SPREAD_OPEN_WINDOW_MINS=15       # minutes after London/NY open with widened spread
# per-pair base spreads live in config/crt_config.yaml

# ── Photon Agent Config ──────────────────────────────────────
PHOTON_PAIRS=EURUSD,GBPUSD,USDCHF,USDCAD,AUDUSD,USDJPY,NZDUSD,XAUUSD
PHOTON_TF_PERSPECTIVE=D1             # structural direction + major POIs
PHOTON_TF_NARRATIVE=H4               # continuation vs pullback narrative
PHOTON_TF_BIAS=M15                   # immediate bias confirm/reverse
PHOTON_TF_ENTRY=M5                   # M1 | M5 — LTF BOS entry timing
PHOTON_SCAN_INTERVAL_SECONDS=60
PHOTON_SWING_FRACTAL_N=2             # swing = exceeds N bars each side
PHOTON_BOS_CONFIRM=close             # close | wick — break confirmation mode
PHOTON_POI_DEPARTURE_ATR_MULT=1.5    # impulsive departure threshold
PHOTON_POI_MAX_BASE_CANDLES=5        # compact base requirement
PHOTON_POI_FRESH_ONLY=true           # untested zones only
PHOTON_EQUAL_LEVEL_TOLERANCE_ATR=0.1 # equal highs/lows tolerance for liquidity pools
PHOTON_FVG_MIN_ATR_MULT=0.25         # min FVG size inside POI
PHOTON_MIN_ALIGNMENT=3               # of 4 timeframes must agree
PHOTON_MIN_RR=2.0                    # hard floor — signals below are rejected (target 5:1)
PHOTON_SL_ATR_BUFFER_MULT=0.3        # SL buffer beyond POI/sweep extreme
PHOTON_NEWS_BLACKOUT_MINS=15         # no entries this close to red news
PHOTON_MIN_BACKTEST_SETUPS=50        # Photon Phase-9 rule: 50–100 setups before live consideration

# ── Data Providers ───────────────────────────────────────────
POLYGON_API_KEY=your_polygon_key
FRED_API_KEY=your_fred_key
YAHOO_FINANCE_ENABLED=true

# ── Notifications ────────────────────────────────────────────
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_ALERT_RECIPIENT=your_email@gmail.com

# ── Risk Defaults ────────────────────────────────────────────
RISK_MAX_DRAWDOWN_PCT=0.15
RISK_DAILY_LOSS_LIMIT_PCT=0.02
RISK_MAX_LEVERAGE=2.0
RISK_MAX_POSITION_CONCENTRATION=0.20
RISK_KELLY_FRACTION=0.50

# ── Execution ────────────────────────────────────────────────
EXECUTION_MODE=MANUAL
SIGNAL_APPROVAL_TIMEOUT_MINS=30
PAPER_TRADE_MIN_WEEKS=4

# ── Backtesting ──────────────────────────────────────────────
BACKTEST_ENGINE=vectorbt
BACKTEST_COMMISSION_BPS=5
BACKTEST_SLIPPAGE_BPS=2
BACKTEST_MIN_TRADES=100

# ── Deployment ───────────────────────────────────────────────
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000
```

---

## 8. Success Criteria

### Phase completion criteria

| Phase | Gate | Pass criteria |
|---|---|---|
| 0 — Infrastructure | Manual | DB migrations clean. Redis connects. Docker Compose starts all services. CI green. |
| 1 — Data pipeline | Human ✋ | 5 symbols manually inspected. Adjustments correct. No gaps in 5-year history. |
| 1b — MT5 feed | Human ✋ | MT5 connects. OHLC data pulls correctly for 3 pairs on H4 and M5. Data matches chart. |
| 2 — Research agent | Human ✋ | Agent surfaces ≥3 scoreable ideas. owl-alpha summaries accurate. You select ≥1 to test. |
| 3 — Backtesting agent | Human ✋ | Backtest report passes look-ahead bias check. Transaction costs included. Walk-forward run. |
| 3b — CRT backtest | Human ✋ | CRT strategy backtested on ≥5 pairs across 2+ years. Profit factor ≥ 1.0 on majority. You approve. |
| 4 — Risk agent | Human ✋ | Kelly sizes correct. All hard limits enforced. Risk dashboard live. You sign off limits. |
| 5 — CRT Agent | Human ✋ | Agent detects ≥3 valid CRT setups from historical data. Chart exports correct. Levels accurate. |
| 5c — Photon Agent | Human ✋ | Structure labels match manual analysis on 3 pairs. ≥50 backtested setups recorded. Expectancy positive. Min-R:R gate enforced. You approve. |
| 5b — Execution agent | Human ✋ | Paper trading ≥4 weeks. Slippage < 2× model estimate. Fill rate > 95%. You authorise live. |
| 6 — Monitoring | Automatic | Alerts firing. Regime detector tested on 2020/2022 data. Weekly report generated. |
| 7 — Orchestration | Manual | Full flow: idea → backtest → risk → paper → CRT signal → approval queue → execution. |
| 8 — UI | Manual | All 8 screens functional. Screen 7 (CRT Scanner) shows live pair grid. Screen 8 (Photon) shows the expectation board. Kill switch tested. |
| 9 — Hardening | Automated | All unit + integration tests pass. Crash scenarios handled. No secrets in code. |
| 10 — Go live | Human ✋ | First live trade. First weekly report reviewed. |

### Live trading success criteria (30/60/90-day gates)

**30 days:** Live Sharpe ≥ 50% of backtest Sharpe. No drawdown limit breaches. CRT Agent generating ≥2 signals/week across the pair universe.

**60 days:** Live Sharpe within 25% of backtest. Regime detector has flagged at least one shift. CRT hit rate on TP1 ≥ 45% (statistical baseline).

**90 days:** Consistent live performance. Second strategy candidate ready. Capital scaling decision made.

### Non-negotiable failure conditions

- Live drawdown exceeds configured max drawdown limit
- Any day with P&L below daily loss limit
- Broker reconciliation mismatch: internal state ≠ broker state
- Data feed gap > 1 hour during market hours
- Any order submitted without passing through Risk Agent
- MT5 feed stale > 2 candles during active session, or watchdog fails 3 restart cycles (CRT Agent auto-pauses; no stale-feed signal may ever enter the pipeline)
- Any CRT backtest result produced by code that evaluates sweeps on closed HTF candles instead of replaying LTF bars (look-ahead — results are void)

---

## 9. Technology Stack

| Layer | Choice | Rationale |
|---|---|---|
| Language | Python 3.11+ | Best quant ecosystem, agent frameworks, all broker APIs |
| LLM Client | `openai` Python SDK | owl-alpha uses an OpenAI-compatible endpoint — no separate SDK needed. See integration pattern below. |
| MT5 Integration | MetaTrader5 Python library | Official MT5 Python API; Windows-native (use Windows VPS or VM for MT5) |
| Database | PostgreSQL | Relational, reliable, good time-series support |
| Cache / Queue | Redis + Celery | Fast in-memory state, async task queue |
| Backtesting | VectorBT (start) | Vectorised, fast iteration. Kaabar patterns implemented as numpy signal functions |
| Pattern Library | Custom (Kaabar) | Ported from *Mastering Financial Pattern Recognition* — all patterns as Python functions |
| Broker API | Alpaca (start) | Simplest REST API, paper trading sandbox, US equities |
| AI / Agents | owl-alpha via OpenRouter | OpenAI-compatible endpoint at `integrate.api.nvidia.com/v1`. MoE architecture, 16K context, strong tool use and agentic reasoning. Free tier via `openrouter.ai`. Used for: signal rationale, paper summaries, backtest explanations. |
| Orchestration | LangGraph | State machine for agent workflows with human-in-the-loop support |
| API | FastAPI | Async, fast, auto docs, WebSocket support |
| UI | React + Recharts | Equity curves, drawdown charts, CRT range visualisation |
| Chart Exports | matplotlib | CRT signal chart PNG exports (Kaabar's ohlc_plot_bars + signal_chart) |
| Notifications | Telegram Bot | Instant mobile alerts, approve/reject via bot |
| Containerisation | Docker Compose | Local dev parity with production |
| Deployment | Hetzner VPS (Windows) or AWS EC2 (Windows) | MT5 Python library requires Windows; use a Windows VM or VPS |
| CI/CD | GitHub Actions | Lint + test on every push, deploy on merge to main |

---

## 10. Key Decisions

| Decision | Recommendation | Reason |
|---|---|---|
| Asset class | FX pairs + Gold via MT5 (CRT); US equities via Alpaca (other strategies) | CRT is most established in FX. MT5 covers FX, Gold, Indices natively. |
| CRT data source | MetaTrader 5 via Python library | Book's canonical pipeline. MT5 is the industry standard for FX retail. |
| Execution mode default | MANUAL | You must earn AUTO through validated performance. Start with full visibility. |
| Kelly fraction | 50% (fractional Kelly) | Full Kelly is too aggressive given parameter estimation error. |
| Backtest engine | VectorBT | Fast vectorised backtesting for rapid iteration. Kaabar patterns are numpy-compatible. |
| Data provider (non-MT5) | Free only for now: Yahoo Finance + Alpha Vantage (25 calls/day) + Alpaca (free with account) | MT5 covers the entire CRT universe for $0. Paid data (Polygon.io / Massive.com) is deferred until live US-equities trading — re-verify its pricing then, as the free tier has been in flux since the rebrand. |
| OpenRouter API (owl-alpha) scope | Signal rationale, pattern confluence explanations, backtest summaries, research paper parsing | Never use owl-alpha for signal generation or risk math. Deterministic logic stays in Python. owl-alpha chosen for: OpenAI-compatible API (no new SDK), MoE efficiency, strong agentic/tool-use capability, free tier at openrouter.ai. |
| MT5 deployment | Windows VPS (Hetzner CX22 or similar) | MT5 Python library is Windows-only. Run the CRT Agent on a cheap Windows VPS. |
| Minimum paper trade duration | 4 weeks | Minimum to observe realistic market conditions across different sessions and regimes. |
| Photon vs CRT rollout order | CRT first, then Photon (Phase 4 → 4B) | Photon reuses shared infrastructure proven by the CRT build (MT5 feed, swings, FVG, spread model). The shared refactor happens at the start of 4B. |
| Photon live gate | ≥50 backtested setups + positive expectancy + min 2:1 R:R enforced | Photon's own Phase-9 rule: prove the edge statistically before risking capital. |

---

---

## 11. OpenRouter / owl-alpha Integration Pattern

All language-task calls across every agent (research summaries, backtest explanations, CRT signal rationale, risk plain-English) use this single shared client. No Anthropic SDK. No separate dependency beyond `openai`.

```python
# agents/shared/nim_client.py
from openai import OpenAI
import os

_client = None

def get_nim_client() -> OpenAI:
    """Return a singleton OpenAI client pointed at OpenRouter."""
    global _client
    if _client is None:
        _client = OpenAI(
            base_url=os.environ["OPENROUTER_BASE_URL"],   # https://openrouter.ai/api/v1
            api_key=os.environ["OPENROUTER_API_KEY"],          # sk-or-...
        )
    return _client

def nim_complete(
    prompt: str,
    system: str = "",
    temperature: float = 0.6,
    max_tokens: int = 2048,
    stream: bool = False,
) -> str:
    """Single-turn completion via owl-alpha. Returns full text response."""
    client = get_nim_client()
    model = os.environ.get("OPENROUTER_MODEL", "openrouter/owl-alpha")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    if stream:
        response_text = ""
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=float(os.environ.get("OPENROUTER_TOP_P", "0.9")),
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in completion:
            if not getattr(chunk, "choices", None):
                continue
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and getattr(delta, "content", None):
                response_text += delta.content
        return response_text
    else:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=float(os.environ.get("OPENROUTER_TOP_P", "0.9")),
            max_tokens=max_tokens,
        )
        return completion.choices[0].message.content
```

**Usage examples across agents:**

```python
# Research Agent — summarise paper abstract
from agents.shared.nim_client import nim_complete

summary = nim_complete(
    prompt=f"Extract: hypothesis, methodology, asset class, edge claim, red flags.\n\nAbstract:\n{abstract}",
    system="You are a quantitative research analyst. Return structured JSON only.",
    temperature=0.3,
)

# CRT Agent — generate signal rationale for approval UI
rationale = nim_complete(
    prompt=f"""Generate a plain-English trading rationale for this CRT signal:
Pair: {signal.pair}, Direction: {signal.direction}, HTF: {signal.htf}, LTF: {signal.ltf}
CRT-High: {signal.crt_high}, CRT-Low: {signal.crt_low}, EQ: {signal.eq}
Entry: {signal.entry}, SL: {signal.sl}, TP1: {signal.tp1}, TP2: {signal.tp2}
Filters passed: {signal.filters_passed}
Kaabar patterns: {signal.kaabar_patterns}
""",
    system="You are a professional FX trader explaining a setup to yourself before executing. Be concise and factual.",
    temperature=0.5,
    max_tokens=400,
)

# Risk Agent — explain current portfolio risk state in natural language
risk_summary = nim_complete(
    prompt=f"Current portfolio risk state: {risk_state_json}. Explain in 3 sentences.",
    temperature=0.3,
    max_tokens=200,
)
```

**pip dependency (no change to current stack):**
```
openai>=1.30.0   # already required for OpenAI-compatible SDKs
```

---

*Reference texts: Quantitative Trading (Chan 2008) · Algorithmic Trading (Chan 2013) · Trading and Exchanges (Harris 2002) · Mastering Financial Pattern Recognition (Kaabar, O'Reilly 2023)*
