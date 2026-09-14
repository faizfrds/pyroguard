"use client";

import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  Legend
} from "recharts";

interface TimeSeriesProps {
  data: Array<{
    date: string;
    day_index: number;
    ndwi_mean: number;
    sar_vv_db: number;
    sar_vh_db: number;
    lst_celsius: number;
    precip_mm: number;
  }>;
}

export default function TimeSeriesCharts({ data }: TimeSeriesProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 text-center text-slate-500 text-sm">
        No regional telemetry loaded. Submit a disaster query to extract Earth Engine radar and optical time-series.
      </div>
    );
  }

  // Format short date label
  const formattedData = data.map((d) => ({
    ...d,
    shortDate: d.date.slice(5) // MM-DD
  }));

  return (
    <div className="bg-slate-900/80 backdrop-blur border border-slate-800 rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <span>📡 30-Day Multi-Sensor Telemetry & Moisture Desiccation Trends</span>
          </h3>
          <p className="text-xs text-slate-400">
            Coupled Sentinel-1 SAR C-band radar backscatter and Sentinel-2 optical canopy moisture.
          </p>
        </div>
        <div className="flex gap-4 text-xs">
          <span className="flex items-center gap-1 text-sky-400">
            <span className="w-2.5 h-2.5 rounded-full bg-sky-400" /> NDWI Canopy Moisture
          </span>
          <span className="flex items-center gap-1 text-emerald-400">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" /> SAR VV (Peat Permittivity)
          </span>
          <span className="flex items-center gap-1 text-amber-400">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400" /> LST (°C)
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Chart 1: NDWI & SAR Backscatter */}
        <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
          <div className="text-xs font-medium text-slate-300 mb-2">
            Foliar NDWI vs. Peatland Radar σ⁰ (dB)
          </div>
          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={formattedData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="shortDate" stroke="#64748b" tick={{ fontSize: 10 }} />
                <YAxis yAxisId="left" stroke="#38bdf8" domain={[-0.1, 0.7]} tick={{ fontSize: 10 }} />
                <YAxis yAxisId="right" orientation="right" stroke="#34d399" domain={[-14, -6]} tick={{ fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", fontSize: "11px" }}
                />
                <ReferenceLine yAxisId="right" y={-10.3} stroke="#ef4444" strokeDasharray="4 4" label={{ value: "BRGM -40cm Limit", fill: "#ef4444", fontSize: 9 }} />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="ndwi_mean"
                  name="NDWI"
                  stroke="#38bdf8"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="sar_vv_db"
                  name="SAR VV (dB)"
                  stroke="#34d399"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Land Surface Temp & Rainfall */}
        <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
          <div className="text-xs font-medium text-slate-300 mb-2">
            Land Surface Temp (°C) & Antecedent Rainfall (mm)
          </div>
          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={formattedData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="shortDate" stroke="#64748b" tick={{ fontSize: 10 }} />
                <YAxis yAxisId="temp" stroke="#fbbf24" domain={[24, 38]} tick={{ fontSize: 10 }} />
                <YAxis yAxisId="rain" orientation="right" stroke="#60a5fa" domain={[0, 30]} tick={{ fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", fontSize: "11px" }}
                />
                <Bar yAxisId="rain" dataKey="precip_mm" name="Rain (mm)" fill="#3b82f6" opacity={0.6} />
                <Line
                  yAxisId="temp"
                  type="monotone"
                  dataKey="lst_celsius"
                  name="LST (°C)"
                  stroke="#fbbf24"
                  strokeWidth={2}
                  dot={false}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

