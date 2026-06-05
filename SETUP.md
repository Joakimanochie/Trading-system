# Day 1 Setup Checklist

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
# Edit .env — fill in NVIDIA_API_KEY (get from https://build.nvidia.com), DATABASE_URL, etc.
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

### 10. NVIDIA NIM API key
- Go to https://build.nvidia.com/z-ai/glm-5.1
- Sign up (free, no credit card)
- Generate API key → add to .env as NVIDIA_API_KEY

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
