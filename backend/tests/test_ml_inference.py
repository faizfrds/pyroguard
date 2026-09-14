"""Unit Tests for ONNX Wildfire Risk Inference Engine."""

import pytest
import numpy as np
from app.ml.inference import get_onnx_session, predict_wildfire_risk


def test_onnx_session_loads():
    session = get_onnx_session()
    assert session is not None
    inputs = session.get_inputs()
    outputs = session.get_outputs()
    assert len(inputs) == 1
    assert inputs[0].name == "input_features"
    assert inputs[0].shape == ["batch_size", 45]
    assert len(outputs) == 2
    assert outputs[0].name == "wildfire_vulnerability_index"
    assert outputs[1].name == "trajectory_14d"


def test_predict_wildfire_risk_high_vulnerability():
    mock_metrics = {
        "peatland_area_pct": 74.0,
        "current_metrics": {
            "ndwi": 0.28,
            "sar_vv_db": -11.2,
            "sar_vh_db": -17.5,
            "lst_celsius": 33.5
        },
        "delta_14d": {
            "ndwi_change_pct": -24.5,
            "sar_vv_drop_db": 3.4,
            "lst_anomaly_celsius": 4.0,
            "antecedent_rain_14d_mm": 0.0
        },
        "peatland_drying_index": {
            "pdi_score": 0.88,
            "status": "CRITICAL_DRAWDOWN"
        }
    }
    
    mock_weather = {
        "max_temp_avg": 35.0,
        "consecutive_dry_days": 14,
        "total_forecast_rain_mm": 0.0,
        "avg_wind_speed_ms": 5.2
    }
    
    result = predict_wildfire_risk(
        metrics_payload=mock_metrics,
        weather_payload=mock_weather,
        oni_index=1.5,
        dmi_index=0.6
    )
    
    assert 0.0 <= result["wildfire_vulnerability_index"] <= 1.0
    assert result["wildfire_vulnerability_index"] >= 0.70
    assert result["risk_tier"] in ["HIGH", "CRITICAL"]
    assert len(result["trajectory_14d"]) == 14
    assert len(result["top_drivers"]) == 4
    assert result["top_drivers"][0]["contribution_pct"] > 0

