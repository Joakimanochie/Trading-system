# Day 1 Setup Checklist

## STATUS: Day 1 / Phase 0 infra COMPLETE (2026-06-15)
- PostgreSQL 16 running natively, role `quant`/`quant_pass`, db `quant_os`
- Alembic migration applied — all 11 tables created
- Redis (winget Redis.Redis 3.0.504) running, PONG confirmed
  - NOTE: pinned `redis==4.6.0` in requirements.txt — redis-py>=5 sends HELLO/RESP3 which this old Redis build rejects
- Celery worker starts clean, `health_check` task returns `{'status': 'ok'}`
- Seed data loaded: SPY/AAPL/MSFT, 1620 rows each in `ohlcv` table
- `.env` created from `.env.example`, DATABASE_URL points to native postgres (quant:quant_pass@localhost:5432/quant_os)
- Run with: `$env:PYTHONPATH="."` before any python/celery/alembic command (no PYTHONPATH set globally)
- pg_hba.conf: `host all all 127.0.0.1/32` set to `trust` (user did this manually, admin-elevated) — needed since native postgres password mgmt has no easy non-interactive path on Windows

- LLM provider switched to OpenRouter owl-alpha (was NVIDIA NIM GLM-5.1). Smoke test pending re-run with new API key.
- MT5 creds added to `.env` (login 52920995, server ICMarketsSC-Demo), `MetaTrader5` pip package installed (5.0.5735), uncommented in requirements.txt

- MT5 connector verified: `initialize_mt5()` → True, `get_quotes(H4, EURUSD)` returned live candles through 2026-06-15. (Root cause of earlier IPC timeout: server name resolved to wrong broker entry — user fixed via MT5 login dialog.)

## Remaining before Phase 1
- Docker Desktop installed but unverified/unused (going native instead)
- git push not yet done
- Day 1 human checkpoint: inspect seeded data vs Yahoo Finance, sign off

## Already completed (by Claude Code session)
- [x] Python 3.11.9 installed (`C:\Users\Hp\AppData\Local\Programs\Python\Python311\python.exe`)
- [x] Virtual environment created (`.venv\`)
- [x] Core Python packages installed (fastapi, sqlalchemy, alembic, celery, redis, pandas, numpy, yfinance, openai, etc.)
- [x] All project files scaffolded (see folder structure in MASTER_PLAN.md)
- [x] All 9 unit tests passing
- [x] `.env.example` created
- [x] Docker Compose file ready
- [x] Alembic migration `0001_initial_schema.py` ready
- [x] GitHub CI workflow ready (`.github/workflows/ci.yml`)
- [x] Pre-commit config ready (`.pre-commit-config.yaml`)

## Still needed (install in progress / manual steps)

### 1. Copy .env.example → .env and fill in values
```
cp .env.example .env
# Edit .env — fill in OPENROUTER_API_KEY (get from https://openrouter.ai), DATABASE_URL, etc.
```

### 2. Docker Desktop (for PostgreSQL + Redis) 
- Docker Desktop should be installing now. Once done, restart your terminal.
- Verify: `docker --version`

### 3. Start PostgreSQL + Redis
```
docker compose up postgres redis -d
```

### 4. Run database migration
```
.venv\Scripts\alembic upgrade head
```
Verify tables created: `docker exec -it trading-system-postgres-1 psql -U quant -d quant_os -c "\dt"`

### 5. Test Redis
```
docker exec -it trading-system-redis-1 redis-cli ping
# Should return: PONG
```

### 6. Start Celery worker
```
.venv\Scripts\celery -A tasks.celery_app worker --loglevel=info
```
In another terminal:
```
.venv\Scripts\python -c "from tasks.data_tasks import health_check; r = health_check.delay(); print(r.get(timeout=10))"
# Should return: {'status': 'ok'}
```

### 7. Seed Yahoo Finance data
```
.venv\Scripts\python scripts\seed_data.py
```
Checks: SPY, AAPL, MSFT OHLCV stored in DB.

### 8. Start the API
```
.venv\Scripts\uvicorn api.main:app --reload
# Visit http://localhost:8000/docs to see the API
```

### 9. MetaTrader 5 (CRT Agent data source)
- Download and install MT5 from your broker (ICMarkets, Pepperstone, etc.)
- MT5 Python library only works on Windows (you're on Windows ✓)
- Install: `.venv\Scripts\pip install MetaTrader5`
- Then uncomment `MetaTrader5>=5.0` in requirements.txt
- Configure MT5_LOGIN, MT5_PASSWORD, MT5_SERVER in .env
- Test: `python scripts/run_crt_scan.py`

### 10. OpenRouter API key
- Go to https://openrouter.ai
- Sign up and generate an API key
- Add to .env as OPENROUTER_API_KEY

### 11. Push to GitHub
```
git add .
git commit -m "Phase 0 complete — full infrastructure scaffold"
git push
```
CI will run on push to dev/main.

### 12. Human checkpoint ✋ (Data pipeline)
Once data is seeded:
- Manually inspect 5 symbols in DB and compare to Yahoo Finance
- Sign off before proceeding to Phase 1 (Research Agent)
