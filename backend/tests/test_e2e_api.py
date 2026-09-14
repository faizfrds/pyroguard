"""End-to-End API and WebSocket Testing for PyroGuard AI FastAPI Server."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_api_health_endpoint():
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["service"] == "PyroGuard AI"
    assert "google_earth_engine" in data
    assert data["onnx_model_ready"] is True


def test_api_regions_endpoint():
    client = TestClient(app)
    response = client.get("/api/v1/regions?q=Kapuas")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "Kapuas Regency"
    assert "khg_units" in data[0]


def test_api_hotspots_feed_endpoint():
    client = TestClient(app)
    response = client.get("/api/v1/hotspots/feed?region=Kapuas%20Regency&lookback_days=3")
    assert response.status_code == 200
    data = response.json()
    assert data["total_hotspots"] >= 1
    assert "geojson" in data


def test_api_agent_query_post_endpoint():
    client = TestClient(app)
    payload = {
        "query": "What is the wildfire vulnerability in Kapuas Regency?",
        "session_id": "test_rest_session"
    }
    response = client.post("/api/v1/agent/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["region_name"] == "Kapuas Regency"
    assert 0.0 <= data["risk_score"] <= 1.0
    assert "report_markdown" in data


def test_websocket_agent_streaming():
    client = TestClient(app)
    with client.websocket_connect("/ws/agent") as websocket:
        # Send query
        query_msg = {
            "type": "user_query",
            "session_id": "test_ws_001",
            "payload": {
                "query": "Evaluate fire risk in Kapuas Regency, Central Kalimantan"
            }
        }
        websocket.send_json(query_msg)
        
        # Read streaming packets until final response
        events = []
        for _ in range(25):
            msg = websocket.receive_json()
            events.append(msg)
            if msg.get("type") == "agent_final_response":
                break
                
        event_types = [e.get("type") for e in events]
        assert "agent_thought" in event_types
        assert "tool_start" in event_types
        assert "tool_result" in event_types
        assert "agent_final_response" in event_types
        
        final_event = next(e for e in events if e.get("type") == "agent_final_response")
        assert final_event["payload"]["region_name"] == "Kapuas Regency"
        assert final_event["payload"]["risk_score"] > 0
