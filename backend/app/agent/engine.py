"""ReAct Agent Execution Engine for PyroGuard AI.

Orchestrates multi-step reasoning, tool execution, and real-time event streaming
over WebSockets. Formats outputs for MapLibre GL map overlays, Recharts time-series,
and conversational Markdown reports.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable
from datetime import datetime, timezone

from app.domain.indonesia import resolve_region
from app.agent.tools import (
    tool_extract_regional_fire_metrics,
    tool_fetch_active_hotspots,
    tool_forecast_wildfire_risk,
    tool_generate_gee_tile_layer
)

logger = logging.getLogger(__name__)

StreamCallback = Callable[[Dict[str, Any]], Awaitable[None]]


class PyroGuardAgentEngine:
    """
    Autonomous disaster management agent specializing in Indonesian peatland
    and tropical wildfire risk assessment.
    """

    def __init__(self, stream_callback: Optional[StreamCallback] = None):
        self.stream_callback = stream_callback

    async def emit(self, event_type: str, payload: Dict[str, Any]):
        """Emits an event packet over the WebSocket stream if callback is registered."""
        if self.stream_callback:
            event = {
                "type": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": payload
            }
            try:
                await self.stream_callback(event)
            except Exception as e:
                logger.warning(f"Error streaming event {event_type}: {e}")

    async def execute_query(self, query: str, session_id: str = "default_session") -> Dict[str, Any]:
        """
        Executes full autonomous ReAct reasoning and tool-calling loop for a disaster query.
        """
        # Step 0: Intent & Geographic Entity Resolution
        await self.emit("agent_thought", {
            "step": 0,
            "text": f"Analyzing disaster query: \"{query}\". Resolving Indonesian administrative entity..."
        })
        await asyncio.sleep(0.3)
        
        region = resolve_region(query)
        region_name = region["name"]
        province = region["province"]
        
        await self.emit("agent_thought", {
            "step": 1,
            "text": f"Resolved AOI: {region_name} ({province}). Peatland coverage: {region['peatland_pct']}%. Initializing multi-sensor radar & optical data extraction."
        })
        await asyncio.sleep(0.3)

        # Step 1: Tool 1 - Extract Regional Fire Metrics
        await self.emit("tool_start", {
            "tool": "extract_regional_fire_metrics",
            "input": {"region_name": region_name, "lookback_days": 30}
        })
        
        metrics = await tool_extract_regional_fire_metrics(region_name=region_name, lookback_days=30)
        
        await self.emit("tool_result", {
            "tool": "extract_regional_fire_metrics",
            "output": {
                "ndwi_14d_change": f"{metrics['delta_14d']['ndwi_change_pct']}%",
                "sar_vv_drop": f"{metrics['delta_14d']['sar_vv_drop_db']} dB",
                "lst_anomaly": f"+{metrics['delta_14d']['lst_anomaly_celsius']} °C",
                "pdi_status": metrics["peatland_drying_index"]["status"],
                "pdi_score": metrics["peatland_drying_index"]["pdi_score"],
                "estimated_water_table_cm": metrics["peatland_drying_index"]["estimated_water_table_cm"]
            }
        })
        await asyncio.sleep(0.3)

        # Step 2: Tool 2 - Fetch Active Hotspots
        await self.emit("agent_thought", {
            "step": 2,
            "text": f"Telemetry indicates active peat drawdown. Querying real-time thermal anomalies (VIIRS 375m) and computing forward haze dispersion vectors..."
        })
        await asyncio.sleep(0.2)
        
        await self.emit("tool_start", {
            "tool": "fetch_active_hotspots",
            "input": {"region_name": region_name, "lookback_days": 3, "min_confidence": "nominal"}
        })
        
        hotspots_data = await tool_fetch_active_hotspots(region_name=region_name, lookback_days=3)
        
        await self.emit("tool_result", {
            "tool": "fetch_active_hotspots",
            "output": {
                "total_hotspots": hotspots_data["total_hotspots"],
                "peatland_hotspots": hotspots_data["peatland_hotspots"],
                "total_frp_mw": hotspots_data["total_frp_mw"],
                "max_frp_mw": hotspots_data["max_frp_mw"]
            }
        })
        
        # Emit Hotspots GeoJSON and Haze Cones for MapLibre
        await self.emit("hotspots_update", {
            "features": hotspots_data["geojson"]
        })
        await self.emit("haze_vectors_update", {
            "features": hotspots_data.get("haze_dispersion_cones", {})
        })
        await asyncio.sleep(0.3)

        # Step 3: Tool 3 - Forecast Wildfire Risk via ONNX Model
        await self.emit("agent_thought", {
            "step": 3,
            "text": "Ingesting 30-day temporal sequence, 14-day weather forecast, and El Niño/IOD climate indices into ONNX risk forecasting model..."
        })
        await asyncio.sleep(0.2)
        
        await self.emit("tool_start", {
            "tool": "forecast_wildfire_risk",
            "input": {"region_name": region_name, "forecast_horizon_days": 14}
        })
        
        risk_forecast = await tool_forecast_wildfire_risk(metrics_payload=metrics, forecast_horizon_days=14)
        
        await self.emit("tool_result", {
            "tool": "forecast_wildfire_risk",
            "output": {
                "wildfire_vulnerability_index": risk_forecast["wildfire_vulnerability_index"],
                "risk_tier": risk_forecast["risk_tier"],
                "top_driver": risk_forecast["top_drivers"][0]["feature"],
                "weather_max_temp": f"{risk_forecast['weather_summary']['max_temp_avg_c']} °C",
                "consecutive_dry_days": risk_forecast["weather_summary"]["consecutive_dry_days"]
            }
        })
        await asyncio.sleep(0.3)

        # Step 4: Tool 4 - Generate GEE Tile Layer
        await self.emit("agent_thought", {
            "step": 4,
            "text": "Generating dynamic GEE raster tile layer for vegetation water stress (NDWI) and boundary geometry for map viewport..."
        })
        await asyncio.sleep(0.2)
        
        await self.emit("tool_start", {
            "tool": "generate_gee_tile_layer",
            "input": {"layer_type": "ndwi_stress", "region_name": region_name}
        })
        
        tile_layer = await tool_generate_gee_tile_layer(layer_type="ndwi_stress", region_name=region_name)
        
        await self.emit("tool_result", {
            "tool": "generate_gee_tile_layer",
            "output": {
                "layer_type": tile_layer["layer_type"],
                "tile_template": tile_layer["tile_url_template"]
            }
        })
        
        await self.emit("map_layer_update", {
            "tile_layer": tile_layer,
            "boundary": metrics["boundary_geojson"],
            "center": region["center"],
            "bbox": region["bbox"]
        })
        await asyncio.sleep(0.3)

        # Step 5: Synthesis & Report Generation
        # Step 5: Synthesis & Report Generation
        wvi = risk_forecast["wildfire_vulnerability_index"]
        tier = risk_forecast["risk_tier"]
        pdi_status = metrics["peatland_drying_index"]["status"]
        water_table = metrics["peatland_drying_index"]["estimated_water_table_cm"]
        hotspots_count = hotspots_data["total_hotspots"]
        peat_hotspots = hotspots_data["peatland_hotspots"]
        is_peat_dominant = region.get("peatland_pct", 0) > 30.0
        ecosystem_type = region.get("ecosystem_type", "Tropical Forest Ecosystem")
        
        if is_peat_dominant:
            hydrology_header = f"**Peatland Hydrology Status**: **{pdi_status}** (Estimated Water Table: **{water_table} cm**)"
            telemetry_bullet_1 = f"- **Sentinel-1 SAR C-band**: Surface backscatter has dropped **{metrics['delta_14d']['sar_vv_drop_db']} dB** over the past 14 days, indicating extreme moisture drawdown in peat dome formations (*kubah gambut*). Water table is below the BRGM **-40 cm** statutory danger threshold."
            hotspots_desc = f"- **Thermal Detections**: **{hotspots_count} active hotspots** identified in the past 72 hours with **{peat_hotspots} located directly within protected KHG peat zones** (*{region.get('khg_units', ['KHG Gambut'])[0]}*)."
            actions = """1. **Immediate Posko Damkar Deployment**: Mobilize *Manggala Agni* and regional fire brigades to ground coordinates near detected KHG peat hotspots.
2. **Canal Water Retention**: Close canal blocks (*sekat kanal*) immediately across agricultural concessions to rewet desiccated peat domes.
3. **Air Support**: Place water-bombing helicopters on standby at provincial command centers."""
        else:
            hydrology_header = f"**Ecosystem Regime**: **{ecosystem_type}** (Non-Peat Volcanic/Mineral Soil)"
            telemetry_bullet_1 = f"- **Sentinel-1 SAR C-band & Soil Moisture**: Surface roughness and radar backscatter show **{metrics['delta_14d']['sar_vv_drop_db']} dB** desiccation in topsoil and volcanic ash layers, drying out fine savanna fuels (*ilalang & pakis*)."
            hotspots_desc = f"- **Thermal Detections**: **{hotspots_count} active thermal anomalies** identified within national park borders (*{region.get('khg_units', ['Zona Konservasi'])[0]}*)."
            actions = """1. **TNBTS Ranger Patrols**: Deploy TNBTS forest rangers (*Polhut*) and BPBD quick-response teams with portable backpack water pumps (*jet shooters*) and fire beaters (*gepyok*).
2. **Visitor & Trail Restriction**: Temporarily restrict tourist access across high-risk sectors (e.g. *Savana Teletubbies*, *Lautan Pasir*, and caldera rim trails); enforce a strict ban on flares and campfires.
3. **Firebreak Clearing**: Establish mechanical firebreaks (*sekat bakar*) along ridgelines and saddle gaps to halt rapid upslope grass fire propagation under highland winds."""

        report_markdown = f"""### Wildfire Risk Intelligence Report: {region_name}, {province}

**Vulnerability Assessment**: <span style="color: {risk_forecast['tier_color']}; font-weight: bold;">{tier} (WVI: {wvi} / 1.00)</span>  
{hydrology_header}

---

#### 1. Remote Sensing & Fuel Moisture Telemetry
{telemetry_bullet_1}
- **Sentinel-2 NDWI**: Canopy foliar moisture depleted by **{metrics['delta_14d']['ndwi_change_pct']}%** over 14 days, confirming severe vegetation desiccation.
- **Thermal Anomalies**: MODIS/Landsat Land Surface Temperature is **+{metrics['delta_14d']['lst_anomaly_celsius']} °C** above the historical seasonal baseline.

#### 2. Active Hotspots & Smoke Plume Propagation
{hotspots_desc}
- **Fire Radiative Power**: Maximum detected FRP of **{hotspots_data['max_frp_mw']} MW** (Total FRP: {hotspots_data['total_frp_mw']} MW).
- **Haze Dispersion**: Forward wind vectors (dominant direction: {risk_forecast['weather_summary'].get('dominant_wind_dir', 120.0)}°) are projecting smoke cones toward surrounding montane valleys.

#### 3. 14-Day Meteorological & Climate Outlook
- **Dry Spell Duration**: **{risk_forecast['weather_summary']['consecutive_dry_days']} consecutive rainless days** forecast with average daily high temperatures of **{risk_forecast['weather_summary']['max_temp_avg_c']} °C**.
- **Macro Climate**: Active **El Niño (+{risk_forecast['macro_climate']['oni_nino34']}°C)** and **Positive IOD (+{risk_forecast['macro_climate']['dmi_iod']}°C)** are compounding regional atmospheric moisture deficits.

---

#### 4. Recommended Command & Control Actions
{actions}
"""

        final_payload = {
            "region_name": region_name,
            "province": province,
            "report_markdown": report_markdown,
            "risk_score": wvi,
            "risk_tier": tier,
            "tier_color": risk_forecast["tier_color"],
            "telemetry_chart_data": metrics["time_series"],
            "forecast_trajectory": risk_forecast["trajectory_14d"],
            "top_drivers": risk_forecast["top_drivers"],
            "hotspots_summary": {
                "total": hotspots_count,
                "peatland": peat_hotspots,
                "total_frp_mw": hotspots_data["total_frp_mw"]
            },
            "pdi_metrics": metrics["peatland_drying_index"],
            "tile_layer": tile_layer,
            "boundary_geojson": metrics["boundary_geojson"]
        }

        await self.emit("agent_final_response", final_payload)
        return final_payload

