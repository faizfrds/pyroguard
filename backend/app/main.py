"""FastAPI Main Server for PyroGuard AI.

Exposes REST APIs and a real-time WebSocket endpoint for the ReAct Agent,
GEE multi-sensor pipelines, active hotspots, and ONNX wildfire risk forecasting.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.domain.indonesia import REGIONS_REGISTRY, resolve_region
from app.services.geospatial import init_earth_engine, get_gee_status
from app.services.hotspots import fetch_active_hotspots
from app.ml.inference import get_onnx_session
from app.agent.engine import PyroGuardAgentEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("pyroguard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing PyroGuard AI Backend Services...")
    # Initialize GEE
    init_earth_engine()
    # Pre-warm ONNX inference session
    try:
        get_onnx_session()
    except Exception as e:
        logger.warning(f"ONNX warm-up notice: {e}")
    yield
    logger.info("Shutting down PyroGuard AI Backend Services...")


app = FastAPI(
    title="PyroGuard AI - Indonesia Wildfire & Peatland Intelligence API",
    description="Real-time multi-sensor radar & optical wildfire risk forecasting system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health_check():
    gee_info = get_gee_status()
    firms_key = os.getenv("FIRMS_MAP_KEY", "")
    has_firms_key = bool(firms_key and firms_key != "your_firms_map_key")
    
    return {
        "status": "online",
        "service": "PyroGuard AI",
        "version": "1.0.0",
        "google_earth_engine": gee_info,
        "nasa_firms_configured": has_firms_key,
        "onnx_model_ready": get_onnx_session() is not None
    }


@app.get("/api/v1/regions")
def list_regions(q: Optional[str] = None):
    """Returns supported Indonesian fire-prone regencies and KHG peatland zones."""
    results = []
    for key, reg in REGIONS_REGISTRY.items():
        if not q or q.lower() in reg["name"].lower() or q.lower() in reg["province"].lower() or q.lower() in reg["indonesian_name"].lower():
            results.append({
                "id": reg["id"],
                "name": reg["name"],
                "indonesian_name": reg["indonesian_name"],
                "province": reg["province"],
                "center": reg["center"],
                "bbox": reg["bbox"],
                "area_ha": reg["area_ha"],
                "peatland_pct": reg["peatland_pct"],
                "khg_units": reg["khg_units"]
            })
    return results


@app.get("/api/v1/hotspots/feed")
async def get_hotspots_feed(
    region: str = Query("Kapuas Regency", description="Target Indonesian regency"),
    lookback_days: int = Query(3, ge=1, le=7)
):
    """Fetches active thermal anomalies with KHG peatland classification."""
    return await fetch_active_hotspots(region_name=region, lookback_days=lookback_days)


class AgentQueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default_session"


@app.post("/api/v1/agent/query")
async def execute_agent_query(request: AgentQueryRequest):
    """Programmatic REST endpoint for executing an agent query."""
    engine = PyroGuardAgentEngine()
    result = await engine.execute_query(request.query, session_id=request.session_id)
    return result


@app.websocket("/ws/agent")
async def websocket_agent_endpoint(websocket: WebSocket):
    """
    Bidirectional streaming WebSocket endpoint.
    Emits real-time agent thoughts, tool start/results, dynamic tile URLs, and final report.
    """
    await websocket.accept()
    logger.info("Client connected to PyroGuard Agent WebSocket.")
    
    async def stream_callback(event: Dict[str, Any]):
        await websocket.send_json(event)
        
    engine = PyroGuardAgentEngine(stream_callback=stream_callback)
    
    try:
        while True:
            data_text = await websocket.receive_text()
            try:
                message = json.loads(data_text)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "agent_error", "payload": {"message": "Invalid JSON format."}})
                continue
                
            msg_type = message.get("type", "user_query")
            
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue
                
            if msg_type == "user_query":
                payload = message.get("payload", {})
                query_str = payload.get("query", "")
                session_id = message.get("session_id", "default_session")
                
                if not query_str.strip():
                    await websocket.send_json({
                        "type": "agent_error",
                        "payload": {"message": "Empty query received."}
                    })
                    continue
                    
                await engine.execute_query(query_str, session_id=session_id)
                
    except WebSocketDisconnect:
        logger.info("Client disconnected from PyroGuard Agent WebSocket.")
    except Exception as e:
        logger.error(f"WebSocket unhandled error: {e}")

