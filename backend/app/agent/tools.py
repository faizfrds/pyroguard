"""Core Tool Specifications and Declarations for PyroGuard AI Agent.

Implements the 4 foundational tools:
1. extract_regional_fire_metrics (GEE zonal radar/optical time-series & PDI)
2. fetch_active_hotspots (NASA FIRMS / VIIRS thermal anomalies + KHG cross-ref)
3. forecast_wildfire_risk (ONNX 14-day risk model inference)
4. generate_gee_tile_layer (Dynamic XYZ raster overlay for MapLibre)
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.services.geospatial import (
    extract_regional_fire_metrics as service_extract_metrics,
    generate_gee_tile_layer as service_generate_tile
)
from app.services.hotspots import fetch_active_hotspots as service_fetch_hotspots
from app.services.weather import fetch_weather_forecast
from app.ml.inference import predict_wildfire_risk
from app.domain.indonesia import simulate_haze_dispersion_cones, evaluate_macro_climate, resolve_region


# Tool 1: extract_regional_fire_metrics
class ExtractMetricsArgs(BaseModel):
    region_name: str = Field(..., description="Name of the Indonesian regency or province (e.g., 'Kapuas Regency', 'Pulang Pisau', 'Riau').")
    lookback_days: int = Field(30, description="Historical lookback window in days (default: 30).")


async def tool_extract_regional_fire_metrics(region_name: str, lookback_days: int = 30) -> Dict[str, Any]:
    """
    Executes GEE / radar reductions over the region boundary to calculate 30-day time-series
    of NDWI canopy moisture, SAR VV/VH backscatter, LST anomalies, and Peatland Drying Index.
    """
    return service_extract_metrics(region_name=region_name, lookback_days=lookback_days)


# Tool 2: fetch_active_hotspots
class FetchHotspotsArgs(BaseModel):
    region_name: str = Field(..., description="Target Indonesian regency name.")
    lookback_days: int = Field(3, description="Lookback window in days (1 to 7, default: 3).")
    min_confidence: str = Field("nominal", description="Minimum confidence filter: 'low', 'nominal', or 'high'.")


async def tool_fetch_active_hotspots(region_name: str, lookback_days: int = 3, min_confidence: str = "nominal") -> Dict[str, Any]:
    """
    Queries real-time thermal anomalies from NASA FIRMS (VIIRS 375m) and flags intersection with KHG peatland zones.
    Also computes forward smoke/haze dispersion cones based on hotspot Fire Radiative Power (FRP).
    """
    hotspots_result = await service_fetch_hotspots(region_name=region_name, lookback_days=lookback_days, min_confidence=min_confidence)
    
    # Compute forward haze cones
    hotspots_list = hotspots_result.get("hotspots", [])
    haze_cones = simulate_haze_dispersion_cones(hotspots_list)
    hotspots_result["haze_dispersion_cones"] = haze_cones
    
    return hotspots_result


# Tool 3: forecast_wildfire_risk
class ForecastRiskArgs(BaseModel):
    metrics_payload: Dict[str, Any] = Field(..., description="Payload returned by extract_regional_fire_metrics.")
    forecast_horizon_days: int = Field(14, description="Forecast horizon in days (default: 14).")


async def tool_forecast_wildfire_risk(metrics_payload: Dict[str, Any], forecast_horizon_days: int = 14) -> Dict[str, Any]:
    """
    Runs ONNX risk model inference to predict the Wildfire Vulnerability Index (0.0 to 1.0),
    14-day daily trajectory, and key contributing drivers. Ingests real-time 14-day weather forecasts.
    """
    center = metrics_payload.get("center", [114.386, -2.015])
    lon, lat = center[0], center[1]
    
    # Fetch 14-day meteorological conditions
    weather_payload = await fetch_weather_forecast(latitude=lat, longitude=lon, forecast_days=forecast_horizon_days)
    
    # Evaluate macro climate
    macro = evaluate_macro_climate(oni=1.2, dmi=0.5)
    
    prediction = predict_wildfire_risk(
        metrics_payload=metrics_payload,
        weather_payload=weather_payload,
        oni_index=macro["oni_nino34"],
        dmi_index=macro["dmi_iod"]
    )
    
    prediction["macro_climate"] = macro
    prediction["weather_summary"] = {
        "max_temp_avg_c": weather_payload.get("max_temp_avg"),
        "consecutive_dry_days": weather_payload.get("consecutive_dry_days"),
        "total_forecast_rain_mm": weather_payload.get("total_forecast_rain_mm"),
        "avg_wind_speed_ms": weather_payload.get("avg_wind_speed_ms")
    }
    return prediction


# Tool 4: generate_gee_tile_layer
class GenerateTileArgs(BaseModel):
    layer_type: str = Field(..., description="Layer type: 'ndwi_stress', 'sar_moisture_anomaly', 'lst_thermal', or 'peat_vulnerability'.")
    region_name: str = Field(..., description="Target Indonesian regency name.")


async def tool_generate_gee_tile_layer(layer_type: str, region_name: str) -> Dict[str, Any]:
    """
    Generates dynamic Earth Engine / XYZ raster tile URL template and palette metadata for frontend MapLibre GL.
    """
    return service_generate_tile(layer_type=layer_type, region_name=region_name)


# Registry of tools available to the ReAct agent
AGENT_TOOLS_METADATA = [
    {
        "name": "extract_regional_fire_metrics",
        "description": "Calculates 30-day time series of Sentinel-2 NDWI, Sentinel-1 SAR VV/VH backscatter, LST anomalies, and Peatland Drying Index across an Indonesian regency or boundary.",
        "parameters": ExtractMetricsArgs.model_json_schema()
    },
    {
        "name": "fetch_active_hotspots",
        "description": "Fetches near-real-time thermal detections from NASA FIRMS (VIIRS 375m) within target regency, cross-referencing KHG peatland zones and generating forward haze dispersion cones.",
        "parameters": FetchHotspotsArgs.model_json_schema()
    },
    {
        "name": "forecast_wildfire_risk",
        "description": "Runs ONNX neural network inference to predict the 14-day Wildfire Vulnerability Index (0.0 to 1.0), trajectory, and key contributing drivers using radar/optical telemetry and weather forecasts.",
        "parameters": ForecastRiskArgs.model_json_schema()
    },
    {
        "name": "generate_gee_tile_layer",
        "description": "Generates dynamic Earth Engine / XYZ raster tile URL template and legend for visualization layers (ndwi_stress, sar_moisture_anomaly, lst_thermal, peat_vulnerability).",
        "parameters": GenerateTileArgs.model_json_schema()
    }
]

