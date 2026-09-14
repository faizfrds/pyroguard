# PyroGuard AI 🔥🇮🇩
**Real-Time Tropical Peatland & Wildfire Risk Intelligence System for Indonesia**

PyroGuard AI is an autonomous, multi-sensor geospatial platform built for disaster managers, forestry authorities, and concession operators. It monitors real-time fuel moisture, tracks NASA thermal anomalies, and forecasts 14-to-30-day wildfire vulnerabilities across Indonesian tropical peatlands and forest zones (e.g., Central Kalimantan, Riau, South Sumatra).

---

## Key Features

1. **All-Weather Cloud-Penetrating Radar Sensing**:
   - Ingests **Sentinel-1 SAR C-band (VV/VH polarization)** via Google Earth Engine (GEE) to penetrate equatorial cloud and smoke.
   - Monitors dielectric permittivity drops ($\Delta\sigma^0_{\text{VV}} > 2.5\text{ dB}$) signaling water table drawdown in peat dome formations (*kubah gambut*).

2. **Peatland Drying Index (PDI)**:
   - Formulates a calibrated hydrological index cross-referenced against Indonesian Ministry of Environment and Forestry (KLHK) Peatland Hydrological Units (*Kesatuan Hidrologi Gambut* / KHG) and BRGM statutory water table danger thresholds (-40 cm).

3. **Autonomous ReAct Tool-Calling Agent**:
   - Streams live thoughts, tool executions, and advisories over WebSockets.
   - Foundation tools:
     - `extract_regional_fire_metrics`: 30-day GEE radar/optical time-series reduction
     - `fetch_active_hotspots`: NASA FIRMS (VIIRS 375m) + KHG spatial overlay
     - `forecast_wildfire_risk`: Sub-20ms ONNX neural network inference
     - `generate_gee_tile_layer`: Dynamic XYZ map tile templates for MapLibre

4. **Haze Dispersion & Macro Climate Teleconnection**:
   - Projects forward smoke vector dispersion cones from active hotspot Fire Radiative Power (FRP) and 10m wind fields.
   - Automatically factors in El Niño (ENSO Niño 3.4) and Indian Ocean Dipole (IOD DMI) compound drought dynamics.

5. **Fullstack Architecture**:
   - **Backend**: Python 3.10+, FastAPI, PyTorch / ONNX Runtime, Earth Engine API, WebSockets.
   - **Frontend**: Next.js 14+ (App Router), MapLibre GL JS, Recharts, Tailwind CSS.

---

## Quick Start

### 1. Environment Configuration
Verify or edit `.env` in the project root:
```env
GEE_PROJECT_ID=your-gcp-project-id
FIRMS_MAP_KEY=your_firms_map_key
PORT=8000
```
*(Note: If GEE or FIRMS credentials are unauthenticated or offline, PyroGuard AI automatically activates its calibrated simulation engine so you can test immediately without blockers).*

### 2. Run Backend
```bash
./run_backend.sh
```
Backend runs at `http://localhost:8000` (Swagger docs: `http://localhost:8000/docs`).

### 3. Run Frontend
```bash
./run_frontend.sh
```
Frontend runs at `http://localhost:3000`.

### 4. Run Discord Bot (Optional)

### Discord channel bot demo: https://discord.gg/A5wf3DbzV

Set your token in `.env`:
```env
DISCORD_BOT_TOKEN=your_bot_token_here
```
Then launch:
```bash
./run_discord_bot.sh
```
Supports slash commands:
- `/risk [region]` (with autocomplete for Kapuas, Mount Bromo, Pulang Pisau, Riau, etc.)
- `/hotspots [region] [days]`
- `/ask [query]`
- `/regions`

### 5. Run Test Suite
```bash
PYTHONPATH=backend backend/.venv/bin/pytest backend/tests/ -v
```

---

## Sample Agent Query

In the dashboard prompt input:
> *"What is the current fire risk in the Kapuas Regency, Central Kalimantan, and are there any active hotspots near peatland zones?"*

The agent will execute:
1. `extract_regional_fire_metrics(region="Kapuas Regency")` $\to$ Detects NDWI foliar drop and SAR VV drawdown below the -40cm BRGM threshold.
2. `fetch_active_hotspots(region="Kapuas Regency")` $\to$ Retrieves active VIIRS hotspots in KHG peat domes and computes smoke plume propagation.
3. `forecast_wildfire_risk(...)` $\to$ Ingests weather forecast and outputs **CRITICAL (0.87 / 1.00)**.
4. `generate_gee_tile_layer(...)` $\to$ Generates raster layer overlay on MapLibre.
5. Synthesizes a structured tactical intelligence briefing and action advisory.

