"""Photon Agent API endpoints: expectations board, POIs, liquidity map, signals."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/expectations")
def get_expectations():
    """Get all active expectations across pairs."""
    from agents.photon.runner import _eof_engines
    all_expectations = []
    for pair, engine in _eof_engines.items():
        for exp in engine.get_active(pair):
            all_expectations.append({
                "id": exp.id,
                "pair": exp.pair,
                "direction": exp.direction,
                "zone": exp.anticipated_price_zone,
                "status": exp.status.value,
                "created_at": str(exp.created_at),
                "arrived_at": str(exp.arrived_at) if exp.arrived_at else None,
            })
    return all_expectations


@router.get("/signals")
def get_photon_signals():
    """Placeholder for active Photon signals."""
    return {"signals": [], "note": "Run scan_all_pairs to generate signals"}


@router.get("/config")
def get_photon_config():
    """Return current Photon configuration."""
    import yaml
    from pathlib import Path
    config_path = Path("config/photon_config.yaml")
    if config_path.exists():
        with config_path.open() as f:
            return yaml.safe_load(f)
    return {"error": "photon_config.yaml not found"}
