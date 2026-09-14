"use client";

import React, { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";

interface MapViewerProps {
  center: [number, number];
  zoom?: number;
  tileLayer?: any;
  boundaryGeoJSON?: any;
  hotspotsGeoJSON?: any;
  hazeConesGeoJSON?: any;
}

export default function MapViewer({
  center,
  zoom = 8.5,
  tileLayer,
  boundaryGeoJSON,
  hotspotsGeoJSON,
  hazeConesGeoJSON
}: MapViewerProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);

  // Initialize MapLibre GL
  useEffect(() => {
    if (!mapContainerRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
      center: center,
      zoom: zoom,
      attributionControl: false
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");
    mapRef.current = map;

    map.on("load", () => {
      // Source & Layer for Regency Boundary
      map.addSource("boundary-source", {
        type: "geojson",
        data: boundaryGeoJSON || { type: "FeatureCollection", features: [] }
      });

      map.addLayer({
        id: "boundary-fill",
        type: "fill",
        source: "boundary-source",
        paint: {
          "fill-color": "#ef4444",
          "fill-opacity": 0.08
        }
      });

      map.addLayer({
        id: "boundary-line",
        type: "line",
        source: "boundary-source",
        paint: {
          "line-color": "#f87171",
          "line-width": 2,
          "line-dasharray": [2, 2]
        }
      });

      // Source & Layer for Haze Dispersion Cones
      map.addSource("haze-source", {
        type: "geojson",
        data: hazeConesGeoJSON || { type: "FeatureCollection", features: [] }
      });

      map.addLayer({
        id: "haze-fill",
        type: "fill",
        source: "haze-source",
        paint: {
          "fill-color": "#f97316",
          "fill-opacity": 0.28
        }
      });

      map.addLayer({
        id: "haze-outline",
        type: "line",
        source: "haze-source",
        paint: {
          "line-color": "#ea580c",
          "line-width": 1.5
        }
      });
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update map center smoothly
  useEffect(() => {
    if (mapRef.current && center) {
      mapRef.current.flyTo({
        center: center,
        zoom: zoom,
        essential: true,
        duration: 1800
      });
    }
  }, [center, zoom]);

  // Update Regency Boundary Layer
  useEffect(() => {
    if (!mapRef.current) return;
    const source = mapRef.current.getSource("boundary-source") as maplibregl.GeoJSONSource;
    if (source && boundaryGeoJSON) {
      source.setData(boundaryGeoJSON);
    }
  }, [boundaryGeoJSON]);

  // Update Haze Cones Layer
  useEffect(() => {
    if (!mapRef.current) return;
    const source = mapRef.current.getSource("haze-source") as maplibregl.GeoJSONSource;
    if (source && hazeConesGeoJSON) {
      source.setData(hazeConesGeoJSON);
    }
  }, [hazeConesGeoJSON]);

  // Update Active Hotspot Markers
  useEffect(() => {
    if (!mapRef.current) return;

    // Clear existing markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    if (!hotspotsGeoJSON || !hotspotsGeoJSON.features) return;

    hotspotsGeoJSON.features.forEach((feature: any) => {
      const coords = feature.geometry.coordinates;
      const props = feature.properties || {};

      // Create custom pulsing DOM element for marker
      const el = document.createElement("div");
      el.className = "hotspot-marker cursor-pointer w-5 h-5 rounded-full flex items-center justify-center";
      el.style.backgroundColor = props.is_peatland ? "#ef4444" : "#f59e0b";
      el.style.border = "2px solid #ffffff";

      const popupContent = `
        <div style="color: #0f172a; font-size: 12px; font-family: sans-serif; line-height: 1.4;">
          <div style="font-weight: 700; font-size: 13px; color: ${props.is_peatland ? '#dc2626' : '#d97706'}; margin-bottom: 4px;">
            🔥 ${props.is_peatland ? 'Peatland Active Hotspot' : 'Mineral Soil Hotspot'}
          </div>
          <div><b>FRP:</b> ${props.frp_mw} MW</div>
          <div><b>Confidence:</b> ${props.confidence}</div>
          <div><b>Satellite:</b> ${props.satellite || 'VIIRS NOAA-20'}</div>
          <div style="margin-top: 4px; padding: 2px 4px; background: #fee2e2; border-radius: 3px; font-size: 11px;">
            ${props.khg_name || 'KHG Peat Hydrology Zone'}
          </div>
        </div>
      `;

      const popup = new maplibregl.Popup({ offset: 12 }).setHTML(popupContent);

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat(coords)
        .setPopup(popup)
        .addTo(mapRef.current!);

      markersRef.current.push(marker);
    });
  }, [hotspotsGeoJSON]);

  return (
    <div className="relative w-full h-full min-h-[450px] bg-slate-950 rounded-xl overflow-hidden border border-slate-800">
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* Layer Overlay Legend */}
      {tileLayer && tileLayer.legend && (
        <div className="absolute bottom-4 left-4 bg-slate-900/90 backdrop-blur-md p-3.5 rounded-lg border border-slate-700 shadow-xl max-w-xs text-xs z-10">
          <div className="font-semibold text-slate-200 mb-1 flex items-center justify-between">
            <span>{tileLayer.legend.title}</span>
            <span className="text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">GEE Active</span>
          </div>
          <p className="text-slate-400 text-[11px] mb-2 leading-relaxed">
            {tileLayer.legend.description}
          </p>
          <div className="flex items-center gap-1 mb-1">
            {tileLayer.legend.palette.map((color: string, idx: number) => (
              <div
                key={idx}
                className="h-2.5 flex-1 first:rounded-l last:rounded-r"
                style={{ backgroundColor: color }}
              />
            ))}
          </div>
          <div className="flex justify-between text-[10px] text-slate-400">
            <span>{tileLayer.legend.min} (Desiccated)</span>
            <span>{tileLayer.legend.max} (Moist)</span>
          </div>
        </div>
      )}

      {/* Hotspot & Haze Map Counter Badge */}
      <div className="absolute top-4 left-4 flex gap-2 z-10">
        {hotspotsGeoJSON && hotspotsGeoJSON.features && (
          <div className="bg-red-950/80 backdrop-blur-md border border-red-800 text-red-300 px-3 py-1.5 rounded-md text-xs font-medium flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
            <span>{hotspotsGeoJSON.features.length} Active VIIRS Hotspots</span>
          </div>
        )}
        {hazeConesGeoJSON && hazeConesGeoJSON.features && (
          <div className="bg-orange-950/80 backdrop-blur-md border border-orange-800 text-orange-300 px-3 py-1.5 rounded-md text-xs font-medium flex items-center gap-1.5">
            <span>💨 Smoke Plumes Projected</span>
          </div>
        )}
      </div>
    </div>
  );
}

