"""Unit Tests for Peatland Drying Index (PDI) and Indonesian Domain Calculations."""

import pytest
from app.domain.indonesia import (
    compute_peatland_drying_index,
    simulate_haze_dispersion_cones,
    evaluate_macro_climate,
    resolve_region,
    REGIONS_REGISTRY
)


def test_resolve_region_exact_and_fuzzy():
    # Exact name
    reg = resolve_region("Kapuas Regency")
    assert reg["id"] == "ID-62-03"
    assert reg["province"] == "Central Kalimantan"
    
    # Indonesian informal term
    reg_id = resolve_region("Kabupaten Pulang Pisau")
    assert reg_id["id"] == "ID-62-11"
    
    # Province match
    reg_riau = resolve_region("Riau")
    assert reg_riau["province"] == "Riau"

    # Mount Bromo National Park match (East Java)
    reg_bromo = resolve_region("Mount Bromo National Park")
    assert reg_bromo["id"] == "ID-35-TNBTS"
    assert reg_bromo["province"] == "East Java"
    assert reg_bromo["peatland_pct"] == 0.0
    assert reg_bromo["center"] == [112.953, -7.942]


def test_pdi_saturated_conditions():
    # Saturated peat: baseline SAR VV, normal LST, heavy recent rain (80mm)
    res = compute_peatland_drying_index(
        sar_vv=-7.8,
        sar_wet_baseline=-7.8,
        lst=28.0,
        lst_baseline=28.5,
        rain_14d_mm=80.0
    )
    assert res["pdi_score"] < 0.20
    assert res["status"] == "SATURATED_MOIST"
    assert res["estimated_water_table_cm"] > -30.0


def test_pdi_critical_drawdown_conditions():
    # Severe desiccation: SAR VV drop of 3.2 dB, LST anomaly +4.0C, 0mm rain
    res = compute_peatland_drying_index(
        sar_vv=-11.0,
        sar_wet_baseline=-7.8,
        lst=32.5,
        lst_baseline=28.5,
        rain_14d_mm=0.0
    )
    assert res["pdi_score"] >= 0.70
    assert res["status"] == "CRITICAL_DRAWDOWN"
    assert res["estimated_water_table_cm"] <= -40.0
    assert "statutory 40cm limit" in res["advisory"]


def test_simulate_haze_dispersion_cones():
    hotspots = [
        {"id": "test_1", "latitude": -2.5, "longitude": 114.2, "frp_mw": 25.0, "is_peatland": True},
        {"id": "test_2", "latitude": -2.8, "longitude": 114.5, "frp_mw": 12.0, "is_peatland": False}
    ]
    geojson = simulate_haze_dispersion_cones(hotspots, wind_speed_ms=5.0, wind_direction_deg=120.0)
    
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 2
    
    # Check cone geometry
    feat = geojson["features"][0]
    assert feat["geometry"]["type"] == "Polygon"
    assert len(feat["geometry"]["coordinates"][0]) >= 5  # Closed cone polygon
    assert feat["properties"]["is_peatland"] is True
    assert feat["properties"]["severity"] == "CRITICAL"


def test_evaluate_macro_climate_compound():
    # El Nino + Positive IOD
    res = evaluate_macro_climate(oni=1.4, dmi=0.6)
    assert res["phase"] == "COMPOUND_DROUGHT_EXTREME"
    assert res["risk_multiplier"] > 1.20
    
    # Neutral
    res_neutral = evaluate_macro_climate(oni=0.1, dmi=0.1)
    assert res_neutral["phase"] == "NEUTRAL"
    assert res_neutral["risk_multiplier"] == 1.0

