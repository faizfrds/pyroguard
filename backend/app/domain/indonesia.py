"""Indonesian Geographic, Hydrological, and Atmospheric Domain Logic.

Includes:
- Administrative hierarchy (Kabupaten / Provinsi) and KHG (Kesatuan Hidrologi Gambut)
- Calibrated Peatland Drying Index (PDI) calculation
- Active Hotspot Smoke/Haze Vector plume simulation
- Macro-climate teleconnection (ENSO / IOD) evaluation
"""

import math
from typing import Dict, Any, List, Optional, Tuple


# Pre-defined Indonesian priority fire-prone regencies with approximate boundaries & KHG units
REGIONS_REGISTRY: Dict[str, Dict[str, Any]] = {
    "kapuas": {
        "id": "ID-62-03",
        "name": "Kapuas Regency",
        "indonesian_name": "Kabupaten Kapuas",
        "province": "Central Kalimantan",
        "province_id": "ID-62",
        "center": [114.386, -2.015],  # [lon, lat]
        "bbox": [113.80, -3.20, 114.95, -1.00],  # [min_lon, min_lat, max_lon, max_lat]
        "area_ha": 1499900.0,
        "peatland_pct": 68.4,
        "khg_units": [
            "KHG Sungai Kahayan - Sungai Kapuas",
            "KHG Sungai Kapuas - Sungai Barito",
            "KHG Sungai Barito - Sungai Murung"
        ],
        "default_sar_wet_baseline_db": -7.8,
        "default_lst_baseline_c": 28.5
    },
    "pulang_pisau": {
        "id": "ID-62-11",
        "name": "Pulang Pisau Regency",
        "indonesian_name": "Kabupaten Pulang Pisau",
        "province": "Central Kalimantan",
        "province_id": "ID-62",
        "center": [114.250, -2.750],
        "bbox": [113.70, -3.45, 114.60, -2.10],
        "area_ha": 899700.0,
        "peatland_pct": 74.2,
        "khg_units": [
            "KHG Sebangau - Kahayan",
            "KHG Kahayan - Kapuas"
        ],
        "default_sar_wet_baseline_db": -7.5,
        "default_lst_baseline_c": 28.2
    },
    "bengkalis": {
        "id": "ID-14-03",
        "name": "Bengkalis Regency",
        "indonesian_name": "Kabupaten Bengkalis",
        "province": "Riau",
        "province_id": "ID-14",
        "center": [102.130, 1.480],
        "bbox": [101.20, 0.90, 102.65, 2.05],
        "area_ha": 777393.0,
        "peatland_pct": 71.8,
        "khg_units": [
            "KHG Pulau Bengkalis",
            "KHG Sungai Siak Kecil - Sungai Rokan"
        ],
        "default_sar_wet_baseline_db": -8.0,
        "default_lst_baseline_c": 29.0
    },
    "siak": {
        "id": "ID-14-08",
        "name": "Siak Regency",
        "indonesian_name": "Kabupaten Siak",
        "province": "Riau",
        "province_id": "ID-14",
        "center": [101.950, 0.800],
        "bbox": [101.25, 0.35, 102.40, 1.35],
        "area_ha": 855609.0,
        "peatland_pct": 57.5,
        "khg_units": [
            "KHG Sungai Siak - Sungai Kampar",
            "KHG Sungai Mandau"
        ],
        "default_sar_wet_baseline_db": -7.9,
        "default_lst_baseline_c": 29.1
    },
    "ogan_komering_ilir": {
        "id": "ID-16-02",
        "name": "Ogan Komering Ilir Regency",
        "indonesian_name": "Kabupaten Ogan Komering Ilir (OKI)",
        "province": "South Sumatra",
        "province_id": "ID-16",
        "center": [105.150, -3.400],
        "bbox": [104.40, -4.20, 106.05, -2.60],
        "area_ha": 1904260.0,
        "peatland_pct": 62.0,
        "ecosystem_type": "Tropical Peat Swamp Forest",
        "khg_units": [
            "KHG Sungai Sugihan - Sungai Saleh",
            "KHG Sungai Mesuji - Sungai Lumpur"
        ],
        "default_sar_wet_baseline_db": -8.2,
        "default_lst_baseline_c": 29.3
    },
    "mount_bromo": {
        "id": "ID-35-TNBTS",
        "name": "Mount Bromo National Park",
        "indonesian_name": "Taman Nasional Bromo Tengger Semeru (TNBTS)",
        "province": "East Java",
        "province_id": "ID-35",
        "center": [112.953, -7.942],
        "bbox": [112.80, -8.10, 113.10, -7.80],
        "area_ha": 50276.0,
        "peatland_pct": 0.0,
        "ecosystem_type": "Volcanic Highland Savanna & Montane Sub-Alpine Forest",
        "khg_units": [
            "Non-Peat Volcanic Mineral Savanna (Lautan Pasir & Bukit Teletubbies)"
        ],
        "default_sar_wet_baseline_db": -9.8,
        "default_lst_baseline_c": 21.5
    },
    "baluran": {
        "id": "ID-35-TNBL",
        "name": "Baluran National Park",
        "indonesian_name": "Taman Nasional Baluran",
        "province": "East Java",
        "province_id": "ID-35",
        "center": [114.380, -7.850],
        "bbox": [114.25, -7.98, 114.48, -7.72],
        "area_ha": 25000.0,
        "peatland_pct": 0.0,
        "ecosystem_type": "Lowland Dry Savanna & Acacia Woodland",
        "khg_units": [
            "Non-Peat Dry Savanna (Savana Bekol)"
        ],
        "default_sar_wet_baseline_db": -10.2,
        "default_lst_baseline_c": 31.0
    },
    "kubu_raya": {
        "id": "ID-61-12",
        "name": "Kubu Raya Regency",
        "indonesian_name": "Kabupaten Kubu Raya",
        "province": "West Kalimantan",
        "province_id": "ID-61",
        "center": [109.350, -0.250],
        "bbox": [108.80, -0.95, 109.85, 0.40],
        "area_ha": 698500.0,
        "peatland_pct": 65.8,
        "ecosystem_type": "Coastal Peatland & Mangrove Buffer",
        "khg_units": [
            "KHG Sungai Kapuas - Sungai Terentang",
            "KHG Sungai Terentang - Sungai Mendawak"
        ],
        "default_sar_wet_baseline_db": -7.7,
        "default_lst_baseline_c": 28.8
    }
}


def resolve_region(query: str) -> Dict[str, Any]:
    """Resolves an input string (e.g. 'Mount Bromo', 'TNBTS', 'Kapuas', 'Riau') to a registered region."""
    normalized = query.lower().replace("kabupaten", "").replace("regency", "").replace("taman nasional", "").replace("national park", "").strip()
    clean_query = query.lower()

    # Specific aliases mapping
    aliases = {
        "bromo": "mount_bromo",
        "tnbts": "mount_bromo",
        "semeru": "mount_bromo",
        "tengger": "mount_bromo",
        "teletubbies": "mount_bromo",
        "baluran": "baluran",
        "situbondo": "baluran",
        "kubu raya": "kubu_raya",
        "pontianak": "kubu_raya",
        "kapuas": "kapuas",
        "kalteng": "kapuas",
        "pulang pisau": "pulang_pisau",
        "bengkalis": "bengkalis",
        "siak": "siak",
        "pekanbaru": "bengkalis",
        "oki": "ogan_komering_ilir",
        "ogan komering": "ogan_komering_ilir",
        "palembang": "ogan_komering_ilir"
    }

    for alias, reg_key in aliases.items():
        if alias in clean_query:
            return REGIONS_REGISTRY[reg_key]

    # Keyword and name match
    for key, data in REGIONS_REGISTRY.items():
        key_clean = key.replace("_", " ")
        if key_clean in clean_query or clean_query in key_clean:
            return data
        if data["name"].lower() in clean_query or clean_query in data["name"].lower():
            return data
        if data["indonesian_name"].lower() in clean_query or clean_query in data["indonesian_name"].lower():
            return data

    # Province level match fallback
    for key, data in REGIONS_REGISTRY.items():
        if data["province"].lower() in clean_query:
            return data

    # Default to Kapuas if unrecognized to allow robust demonstration
    return REGIONS_REGISTRY["kapuas"]


def generate_simplified_geojson_boundary(bbox: List[float], name: str) -> Dict[str, Any]:
    """Constructs a standard GeoJSON Feature for the bounding polygon of a region."""
    min_lon, min_lat, max_lon, max_lat = bbox
    # Generate an organic 8-point polygon matching the bbox
    mid_lon = (min_lon + max_lon) / 2
    mid_lat = (min_lat + max_lat) / 2
    coords = [
        [min_lon, mid_lat],
        [min_lon + 0.1 * (max_lon - min_lon), max_lat],
        [mid_lon, max_lat],
        [max_lon, max_lat - 0.1 * (max_lat - min_lat)],
        [max_lon, mid_lat],
        [max_lon - 0.1 * (max_lon - min_lon), min_lat],
        [mid_lon, min_lat],
        [min_lon + 0.1 * (max_lon - min_lon), min_lat + 0.1 * (max_lat - min_lat)],
        [min_lon, mid_lat]
    ]
    return {
        "type": "Feature",
        "properties": {
            "name": name,
            "stroke": "#ef4444",
            "stroke-width": 2,
            "fill": "#ef4444",
            "fill-opacity": 0.1
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [coords]
        }
    }


def compute_peatland_drying_index(
    sar_vv: float,
    sar_wet_baseline: float,
    lst: float,
    lst_baseline: float,
    rain_14d_mm: float
) -> Dict[str, Any]:
    """
    Computes normalized Peatland Drying Index (PDI) (0.0 = Saturated, 1.0 = Extreme Desiccation).
    
    Formula:
      I_PDI = 0.50 * f_SAR + 0.25 * f_LST + 0.25 * f_Rain
      
    Where:
      - f_SAR = clamp((Baseline - VV) / 3.5, 0, 1)
      - f_LST = clamp((LST - Baseline) / 8.0, 0, 1)
      - f_Rain = exp(-rain_14d / 25.0)
    """
    # Radar soil moisture desiccation factor
    vv_drop = max(0.0, sar_wet_baseline - sar_vv)
    f_sar = min(1.0, vv_drop / 3.5)
    
    # Thermal anomaly factor
    temp_diff = lst - lst_baseline
    f_lst = min(1.0, max(0.0, temp_diff / 8.0))
    
    # Exponential decay of antecedent rain
    f_rain = math.exp(-max(0.0, rain_14d_mm) / 25.0)
    
    pdi = (0.50 * f_sar) + (0.25 * f_lst) + (0.25 * f_rain)
    pdi = round(min(1.0, max(0.0, pdi)), 3)
    
    # Estimate water table level below ground (cm) based on BRGM calibration
    # Saturated = 0cm to -15cm; Critical danger threshold is -40cm; Extreme = -90cm
    estimated_water_table_cm = round(-10.0 - (pdi * 80.0), 1)
    
    if pdi >= 0.75 or estimated_water_table_cm <= -40.0:
        status = "CRITICAL_DRAWDOWN"
        advisory = "Water table depleted below statutory 40cm limit. High risk of subterranean smoldering."
    elif pdi >= 0.45:
        status = "MODERATE_DRAWDOWN"
        advisory = "Active peat surface desiccation observed. Monitor canal blockages."
    else:
        status = "SATURATED_MOIST"
        advisory = "Adequate peat moisture content. Fire ignition probability low."
        
    return {
        "pdi_score": pdi,
        "status": status,
        "sar_vv_drop_db": round(vv_drop, 2),
        "lst_anomaly_celsius": round(temp_diff, 2),
        "antecedent_rain_14d_mm": round(rain_14d_mm, 1),
        "estimated_water_table_cm": estimated_water_table_cm,
        "advisory": advisory
    }


def simulate_haze_dispersion_cones(
    hotspots: List[Dict[str, Any]],
    wind_speed_ms: float = 4.5,
    wind_direction_deg: float = 120.0  # Wind FROM southeast blowing toward northwest (300 deg)
) -> Dict[str, Any]:
    """
    Generates forward smoke/haze dispersion cones (GeoJSON FeatureCollection)
    based on active hotspots, Fire Radiative Power (FRP), and wind vectors.
    """
    # Plume forward propagation angle (downwind = direction wind is blowing TO)
    downwind_deg = (wind_direction_deg + 180.0) % 360.0
    downwind_rad = math.radians(downwind_deg)
    
    features = []
    
    for i, spot in enumerate(hotspots):
        lat = spot.get("latitude", -2.0)
        lon = spot.get("longitude", 114.0)
        frp = spot.get("frp_mw", 15.0)
        is_peat = spot.get("is_peatland", True)
        
        # Peat fires generate more intense persistent smoke plumes
        multiplier = 1.6 if is_peat else 1.0
        # Projection distances for 6h, 12h, 24h in degrees (~111 km per deg lat)
        km_travel = (wind_speed_ms * 3.6 * 12.0) * (frp / 20.0) * 0.5 * multiplier
        dist_deg = min(1.8, max(0.2, km_travel / 111.0))
        
        # Spread angle (cone width) ~ 25 degrees
        half_spread_rad = math.radians(14.0)
        
        # Calculate cone end points
        angle_left = downwind_rad - half_spread_rad
        angle_right = downwind_rad + half_spread_rad
        
        # Tip (hotspot source)
        pt_origin = [lon, lat]
        pt_far_left = [lon + dist_deg * math.sin(angle_left), lat + dist_deg * math.cos(angle_left)]
        pt_far_center = [lon + (dist_deg * 1.15) * math.sin(downwind_rad), lat + (dist_deg * 1.15) * math.cos(downwind_rad)]
        pt_far_right = [lon + dist_deg * math.sin(angle_right), lat + dist_deg * math.cos(angle_right)]
        
        cone_coords = [[
            pt_origin,
            pt_far_left,
            pt_far_center,
            pt_far_right,
            pt_origin
        ]]
        
        features.append({
            "type": "Feature",
            "id": f"haze_cone_{i}",
            "properties": {
                "source_hotspot_id": spot.get("id", f"spot_{i}"),
                "frp_mw": frp,
                "is_peatland": is_peat,
                "projected_reach_km": round(dist_deg * 111.0, 1),
                "severity": "CRITICAL" if (frp > 20 and is_peat) else "MODERATE",
                "stroke": "#f97316",
                "stroke-width": 1.5,
                "fill": "#ea580c",
                "fill-opacity": 0.25
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": cone_coords
            }
        })
        
    return {
        "type": "FeatureCollection",
        "features": features
    }


def evaluate_macro_climate(oni: float = 1.2, dmi: float = 0.5) -> Dict[str, Any]:
    """
    Evaluates ENSO (Oceanic Niño Index) and IOD (Dipole Mode Index) conditions.
    """
    is_el_nino = oni >= 0.5
    is_strong_el_nino = oni >= 1.5
    is_positive_iod = dmi >= 0.4
    
    if is_el_nino and is_positive_iod:
        phase = "COMPOUND_DROUGHT_EXTREME"
        risk_amplifier = 1.25
        desc = "Co-occurring El Niño and Positive Indian Ocean Dipole severely suppress convective rainfall across Indonesia, prolonging dry season fire vulnerability."
    elif is_el_nino:
        phase = "EL_NINO_ACTIVE"
        risk_amplifier = 1.15
        desc = "Active El Niño conditions causing delayed monsoon onset and elevated regional flammability."
    elif is_positive_iod:
        phase = "POSITIVE_IOD_ACTIVE"
        risk_amplifier = 1.12
        desc = "Positive IOD phase reducing rainfall over Sumatra and western Kalimantan."
    else:
        phase = "NEUTRAL"
        risk_amplifier = 1.0
        desc = "Normal climatological rainfall baseline."
        
    return {
        "phase": phase,
        "oni_nino34": oni,
        "dmi_iod": dmi,
        "risk_multiplier": risk_amplifier,
        "summary": desc
    }

