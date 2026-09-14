"use client";

import { useState, useEffect, useRef, useCallback } from "react";

export interface ToolExecution {
  tool: string;
  status: "running" | "completed" | "error";
  input?: any;
  output?: any;
}

export interface HotspotsUpdate {
  type: string;
  features: any[];
}

export interface UseAgentSocketReturn {
  isConnected: boolean;
  isProcessing: boolean;
  thoughts: Array<{ step: number; text: string }>;
  toolExecutions: ToolExecution[];
  hotspotsGeoJSON: any | null;
  hazeConesGeoJSON: any | null;
  tileLayer: any | null;
  boundaryGeoJSON: any | null;
  mapCenter: [number, number];
  finalPayload: any | null;
  error: string | null;
  sendQuery: (query: string) => void;
  clearSession: () => void;
}

export function useAgentSocket(wsUrl: string = "ws://localhost:8000/ws/agent"): UseAgentSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [thoughts, setThoughts] = useState<Array<{ step: number; text: string }>>([]);
  const [toolExecutions, setToolExecutions] = useState<ToolExecution[]>([]);
  const [hotspotsGeoJSON, setHotspotsGeoJSON] = useState<any | null>(null);
  const [hazeConesGeoJSON, setHazeConesGeoJSON] = useState<any | null>(null);
  const [tileLayer, setTileLayer] = useState<any | null>(null);
  const [boundaryGeoJSON, setBoundaryGeoJSON] = useState<any | null>(null);
  const [mapCenter, setMapCenter] = useState<[number, number]>([114.386, -2.015]); // Default Kapuas
  const [finalPayload, setFinalPayload] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    try {
      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        setIsConnected(true);
        setError(null);
      };

      socket.onclose = () => {
        setIsConnected(false);
        // Exponential/delayed reconnect
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };

      socket.onerror = () => {
        setError("WebSocket connection failed. Ensure backend server is running on port 8000.");
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const type = data.type;
          const payload = data.payload || {};

          switch (type) {
            case "agent_thought":
              setThoughts((prev) => [...prev, payload]);
              break;

            case "tool_start":
              setToolExecutions((prev) => [
                ...prev.filter((t) => t.tool !== payload.tool),
                { tool: payload.tool, status: "running", input: payload.input }
              ]);
              break;

            case "tool_result":
              setToolExecutions((prev) =>
                prev.map((t) =>
                  t.tool === payload.tool
                    ? { ...t, status: "completed", output: payload.output }
                    : t
                )
              );
              break;

            case "hotspots_update":
              setHotspotsGeoJSON(payload.features);
              break;

            case "haze_vectors_update":
              setHazeConesGeoJSON(payload.features);
              break;

            case "map_layer_update":
              if (payload.tile_layer) setTileLayer(payload.tile_layer);
              if (payload.boundary) setBoundaryGeoJSON(payload.boundary);
              if (payload.center) setMapCenter(payload.center);
              break;

            case "agent_final_response":
              setFinalPayload(payload);
              setIsProcessing(false);
              break;

            case "agent_error":
              setError(payload.message || "An agent error occurred.");
              setIsProcessing(false);
              break;

            default:
              break;
          }
        } catch (err) {
          console.error("Failed to parse incoming WebSocket message:", err);
        }
      };
    } catch (err) {
      console.error("WebSocket initialization error:", err);
    }
  }, [wsUrl]);

  useEffect(() => {
    connect();
    return () => {
      if (socketRef.current) socketRef.current.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    };
  }, [connect]);

  const sendQuery = useCallback((query: string) => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      setError("Cannot send query: backend WebSocket is not connected.");
      return;
    }
    setError(null);
    setIsProcessing(true);
    setThoughts([]);
    setToolExecutions([]);
    setFinalPayload(null);

    const message = {
      type: "user_query",
      session_id: `session_${Date.now()}`,
      payload: { query }
    };
    socketRef.current.send(JSON.stringify(message));
  }, []);

  const clearSession = useCallback(() => {
    setThoughts([]);
    setToolExecutions([]);
    setFinalPayload(null);
    setHotspotsGeoJSON(null);
    setHazeConesGeoJSON(null);
  }, []);

  return {
    isConnected,
    isProcessing,
    thoughts,
    toolExecutions,
    hotspotsGeoJSON,
    hazeConesGeoJSON,
    tileLayer,
    boundaryGeoJSON,
    mapCenter,
    finalPayload,
    error,
    sendQuery,
    clearSession
  };
}

