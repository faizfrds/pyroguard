"use client";

import React, { useState } from "react";
import MapViewer from "@/components/Map/MapViewer";
import AgentChat from "@/components/Agent/AgentChat";
import TimeSeriesCharts from "@/components/Telemetry/TimeSeriesCharts";
import { useAgentSocket } from "@/hooks/useAgentSocket";

export default function Home() {
  const [showTelemetry, setShowTelemetry] = useState(true);

  const {
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
    sendQuery
  } = useAgentSocket();

  return (
    <div className="flex flex-col h-screen max-h-screen overflow-hidden bg-[#080c14]">
      {/* Top Navigation Bar */}
      <header className="h-14 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md px-5 flex items-center justify-between z-20">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-orange-600 to-amber-500 flex items-center justify-center font-bold text-slate-950 text-base shadow-lg shadow-orange-950">
            🔥
          </div>
          <div>
            <h1 className="font-bold text-sm text-slate-100 tracking-wide flex items-center gap-2">
              <span>PyroGuard AI</span>
              <span className="text-[10px] bg-orange-950 text-orange-400 border border-orange-800 px-1.5 py-0.5 rounded font-mono">
                Indonesia Peatland Intelligence
              </span>
            </h1>
          </div>
        </div>

        {/* System & Teleconnection Status Indicators */}
        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="hidden md:flex items-center gap-2 bg-slate-900 px-2.5 py-1 rounded-md border border-slate-800">
            <span className="text-slate-400">ENSO:</span>
            <span className="text-orange-400 font-semibold">El Niño (+1.2°C)</span>
            <span className="text-slate-600">|</span>
            <span className="text-slate-400">IOD:</span>
            <span className="text-amber-400 font-semibold">+0.5°C</span>
          </div>

          <div className="flex items-center gap-2 bg-slate-900 px-2.5 py-1 rounded-md border border-slate-800">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-slate-300">GEE Engine Active</span>
          </div>

          <button
            onClick={() => setShowTelemetry(!showTelemetry)}
            className={`px-2.5 py-1 rounded-md border text-xs transition ${
              showTelemetry
                ? "bg-orange-950/70 border-orange-800 text-orange-300"
                : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200"
            }`}
          >
            📊 {showTelemetry ? "Hide Telemetry" : "Show Telemetry"}
          </button>
        </div>
      </header>

      {/* Main Split-Pane Workspace */}
      <main className="flex-1 flex flex-col lg:flex-row overflow-hidden p-4 gap-4">
        {/* Left Column: Map Viewer + Bottom Telemetry Drawer */}
        <div className="flex-1 flex flex-col gap-4 overflow-hidden h-full">
          {/* Map Section */}
          <div className="flex-1 min-h-[350px] relative">
            <MapViewer
              center={mapCenter}
              tileLayer={tileLayer}
              boundaryGeoJSON={boundaryGeoJSON}
              hotspotsGeoJSON={hotspotsGeoJSON}
              hazeConesGeoJSON={hazeConesGeoJSON}
            />
          </div>

          {/* Collapsible Telemetry Charts */}
          {showTelemetry && (
            <div className="h-64 overflow-hidden transition-all">
              <TimeSeriesCharts
                data={finalPayload ? finalPayload.telemetry_chart_data : []}
              />
            </div>
          )}
        </div>

        {/* Right Column: Agent Chat Drawer */}
        <div className="w-full lg:w-[460px] h-full flex-shrink-0">
          <AgentChat
            isConnected={isConnected}
            isProcessing={isProcessing}
            thoughts={thoughts}
            toolExecutions={toolExecutions}
            finalPayload={finalPayload}
            error={error}
            onSendQuery={sendQuery}
          />
        </div>
      </main>
    </div>
  );
}

