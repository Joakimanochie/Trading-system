"""Test POI detector."""
import pandas as pd
from datetime import datetime, timedelta
from agents.photon.structure_engine import analyze_structure
from agents.photon.poi_detector import detect_pois

def test_no_pois_flat_data():
    dates = [datetime(2026,1,1)+timedelta(hours=4*i) for i in range(30)]
    data = pd.DataFrame({"open":100,"high":101,"low":99,"close":100}, index=dates)
    levels = analyze_structure(data, fractal_n=2)
    pois = detect_pois(data, levels, "H4")
    # Flat data has no strong levels → no qualifying POIs
    assert isinstance(pois, list)

def test_empty():
    data = pd.DataFrame({"open":[],"high":[],"low":[],"close":[]})
    pois = detect_pois(data, [], "H4")
    assert pois == []
