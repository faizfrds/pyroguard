"""Integration Tests for Agent Tools and Autonomous ReAct Execution."""

import pytest
from app.agent.tools import (
    tool_extract_regional_fire_metrics,
    tool_fetch_active_hotspots,
    tool_forecast_wildfire_risk,
    tool_generate_gee_tile_layer
)
from app.agent.engine import PyroGuardAgentEngine


@pytest.mark.asyncio
async def test_tool_extract_regional_fire_metrics():
    metrics = await tool_extract_regional_fire_metrics(region_name="Kapuas Regency", lookback_days=30)
    assert metrics["region_name"] == "Kapuas Regency"
    assert "delta_14d" in metrics
    assert "peatland_drying_index" in metrics
    assert len(metrics["time_series"]) == 30
    assert metrics["boundary_geojson"]["geometry"]["type"] == "Polygon"


@pytest.mark.asyncio
async def test_tool_fetch_active_hotspots():
    hotspots = await tool_fetch_active_hotspots(region_name="Kapuas Regency", lookback_days=3)
    assert hotspots["total_hotspots"] >= 1
    assert "geojson" in hotspots
    assert "haze_dispersion_cones" in hotspots
    assert hotspots["geojson"]["type"] == "FeatureCollection"
    assert hotspots["haze_dispersion_cones"]["type"] == "FeatureCollection"


@pytest.mark.asyncio
async def test_tool_forecast_wildfire_risk():
    metrics = await tool_extract_regional_fire_metrics(region_name="Pulang Pisau", lookback_days=30)
    forecast = await tool_forecast_wildfire_risk(metrics_payload=metrics, forecast_horizon_days=14)
    
    assert 0.0 <= forecast["wildfire_vulnerability_index"] <= 1.0
    assert forecast["risk_tier"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    assert len(forecast["trajectory_14d"]) == 14
    assert "macro_climate" in forecast
    assert "weather_summary" in forecast


@pytest.mark.asyncio
async def test_tool_generate_gee_tile_layer():
    tile = await tool_generate_gee_tile_layer(layer_type="ndwi_stress", region_name="Kapuas Regency")
    assert tile["layer_type"] == "ndwi_stress"
    assert "tile_url_template" in tile
    assert "{z}" in tile["tile_url_template"]
    assert "legend" in tile


@pytest.mark.asyncio
async def test_agent_engine_react_streaming():
    events_collected = []
    
    async def capture_stream(event):
        events_collected.append(event)
        
    engine = PyroGuardAgentEngine(stream_callback=capture_stream)
    query = "Evaluate fire risk in Kapuas Regency, Central Kalimantan near peatland zones"
    
    final_payload = await engine.execute_query(query=query, session_id="test_sess_001")
    
    # Assert return structure
    assert final_payload["region_name"] == "Kapuas Regency"
    assert final_payload["province"] == "Central Kalimantan"
    assert final_payload["risk_score"] > 0.0
    assert "report_markdown" in final_payload
    assert len(final_payload["telemetry_chart_data"]) == 30
    
    # Assert streamed event types
    event_types = [e["type"] for e in events_collected]
    assert "agent_thought" in event_types
    assert "tool_start" in event_types
    assert "tool_result" in event_types
    assert "hotspots_update" in event_types
    assert "haze_vectors_update" in event_types
    assert "map_layer_update" in event_types
    assert "agent_final_response" in event_types

