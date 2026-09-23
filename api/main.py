"""FastAPI application entry point."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings

app = FastAPI(
    title="Quant OS API",
    description="Quant Trading Agentic OS — REST & WebSocket API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
from api.routers import backtests, crt, performance, photon, risk, signals, strategies, system  # noqa: E402

app.include_router(backtests.router, prefix="/backtests", tags=["backtests"])
app.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
app.include_router(signals.router, prefix="/signals", tags=["signals"])
app.include_router(crt.router, prefix="/crt", tags=["crt"])
app.include_router(photon.router, prefix="/photon", tags=["photon"])
app.include_router(risk.router, prefix="/risk", tags=["risk"])
app.include_router(performance.router, prefix="/performance", tags=["performance"])
app.include_router(system.router, prefix="/system", tags=["system"])


# ── WebSocket ────────────────────────────────────────────────────────────────
from api.websockets import ws_endpoint  # noqa: E402

app.websocket("/ws")(ws_endpoint)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
