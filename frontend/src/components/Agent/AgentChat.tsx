"use client";

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import { ToolExecution } from "@/hooks/useAgentSocket";

interface AgentChatProps {
  isConnected: boolean;
  isProcessing: boolean;
  thoughts: Array<{ step: number; text: string }>;
  toolExecutions: ToolExecution[];
  finalPayload: any | null;
  error: string | null;
  onSendQuery: (query: string) => void;
}

export default function AgentChat({
  isConnected,
  isProcessing,
  thoughts,
  toolExecutions,
  finalPayload,
  error,
  onSendQuery
}: AgentChatProps) {
  const [inputQuery, setInputQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim() || isProcessing) return;
    onSendQuery(inputQuery);
  };

  const sampleQueries = [
    "Assess current fire risk at Mount Bromo National Park, East Java",
    "What is the fire risk in Kapuas Regency, Central Kalimantan near peatlands?",
    "Assess peatland drying status and hotspots in Pulang Pisau Regency",
    "Current wildfire vulnerability and smoke dispersion in Bengkalis, Riau"
  ];

  return (
    <div className="flex flex-col h-full bg-slate-900/90 backdrop-blur border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
        <div className="flex items-center gap-2.5">
          <div className="w-2.5 h-2.5 rounded-full bg-orange-500 animate-pulse" />
          <h2 className="font-semibold text-slate-100 text-sm tracking-wide">
            PyroGuard Autonomous Agent
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              isConnected ? "bg-emerald-400" : "bg-red-400"
            }`}
          />
          <span className="text-xs text-slate-400 font-mono">
            {isConnected ? "WS: Connected" : "WS: Disconnected"}
          </span>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {error && (
          <div className="p-3 bg-red-950/80 border border-red-800 rounded-lg text-xs text-red-300">
            ⚠️ {error}
          </div>
        )}

        {/* Live Execution Status / Thought Steps */}
        {(thoughts.length > 0 || isProcessing) && (
          <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3.5 space-y-2">
            <div className="text-xs font-semibold text-slate-300 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <span className="text-orange-400">⚙️</span> Reasoning & Tool Invocation
              </span>
              {isProcessing && (
                <span className="text-[11px] text-orange-400 animate-pulse font-mono">
                  Running ReAct Loop...
                </span>
              )}
            </div>

            {/* Thought Stream */}
            <div className="space-y-1 text-xs text-slate-400 font-mono pl-2 border-l border-slate-800">
              {thoughts.map((t, idx) => (
                <div key={idx} className="leading-relaxed">
                  <span className="text-slate-600">[{t.step}]</span> {t.text}
                </div>
              ))}
            </div>

            {/* Tool Badges */}
            {toolExecutions.length > 0 && (
              <div className="pt-2 flex flex-wrap gap-1.5">
                {toolExecutions.map((t, idx) => (
                  <div
                    key={idx}
                    className={`text-[10px] px-2 py-1 rounded flex items-center gap-1 font-mono ${
                      t.status === "completed"
                        ? "bg-emerald-950/80 text-emerald-300 border border-emerald-800"
                        : "bg-orange-950/80 text-orange-300 border border-orange-800 animate-pulse"
                    }`}
                  >
                    <span>{t.status === "completed" ? "✓" : "⏳"}</span>
                    <span>{t.tool}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Final Synthesized Report & Intelligence Cards */}
        {finalPayload && (
          <div className="space-y-4">
            {/* Risk Index Banner */}
            <div
              className="p-4 rounded-xl border flex items-center justify-between"
              style={{
                backgroundColor: `${finalPayload.tier_color}15`,
                borderColor: finalPayload.tier_color
              }}
            >
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Wildfire Vulnerability Index
                </div>
                <div className="text-2xl font-bold flex items-baseline gap-2 mt-0.5">
                  <span style={{ color: finalPayload.tier_color }}>
                    {finalPayload.risk_tier}
                  </span>
                  <span className="text-sm font-normal text-slate-400">
                    ({finalPayload.risk_score} / 1.00)
                  </span>
                </div>
                <div className="text-xs text-slate-300 mt-1">
                  Peat Water Table: <b>{finalPayload.pdi_metrics?.estimated_water_table_cm} cm</b> (Status: {finalPayload.pdi_metrics?.status})
                </div>
              </div>

              {/* Mini WVI Gauge Visual */}
              <div className="w-16 h-16 rounded-full border-4 flex items-center justify-center font-bold text-lg"
                   style={{ borderColor: finalPayload.tier_color, color: finalPayload.tier_color }}>
                {Math.round(finalPayload.risk_score * 100)}%
              </div>
            </div>

            {/* Top Drivers Attribution Card */}
            {finalPayload.top_drivers && (
              <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3">
                <div className="text-xs font-semibold text-slate-300 mb-2">
                  Top Contributing Risk Drivers
                </div>
                <div className="space-y-2">
                  {finalPayload.top_drivers.map((drv: any, i: number) => (
                    <div key={i} className="text-xs">
                      <div className="flex justify-between text-slate-300 mb-0.5">
                        <span>{drv.feature}</span>
                        <span className="font-mono text-slate-400">{drv.contribution_pct}%</span>
                      </div>
                      <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                        <div
                          className="bg-orange-500 h-full rounded-full"
                          style={{ width: `${drv.contribution_pct}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Full Report Markdown */}
            <div className="bg-slate-950/50 border border-slate-800/80 rounded-xl p-4 text-xs text-slate-300 leading-relaxed space-y-3 prose prose-invert max-w-none">
              <ReactMarkdown>{finalPayload.report_markdown}</ReactMarkdown>
            </div>
          </div>
        )}

        {/* Empty State / Query Suggestions */}
        {!finalPayload && thoughts.length === 0 && (
          <div className="py-6 text-center space-y-3">
            <div className="text-3xl">🔥</div>
            <h3 className="text-sm font-semibold text-slate-200">
              PyroGuard AI Decision Support
            </h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Ask about real-time peatland moisture desiccation, VIIRS active hotspots, and 14-day wildfire forecasts across Indonesia.
            </p>
            <div className="pt-2 space-y-2 text-left">
              <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                Sample Operational Queries:
              </div>
              {sampleQueries.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => onSendQuery(q)}
                  className="w-full text-left p-2.5 bg-slate-950/60 hover:bg-slate-800/60 border border-slate-800 rounded-lg text-xs text-slate-300 hover:text-orange-300 transition"
                >
                  "{q}"
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Input Box */}
      <form onSubmit={handleSubmit} className="p-3 border-t border-slate-800 bg-slate-950">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={isProcessing}
            placeholder="Query region (e.g. Kapuas Regency, Pulang Pisau, Riau)..."
            className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-orange-500 transition disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isProcessing || !inputQuery.trim()}
            className="bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white text-xs px-4 py-2 rounded-lg font-medium transition flex items-center gap-1.5"
          >
            {isProcessing ? "Analyzing..." : "Send ⏎"}
          </button>
        </div>
      </form>
    </div>
  );
}

