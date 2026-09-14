"""Weather Forecasting Service.

Retrieves 14-day forecasts (2m temp, relative humidity, wind speed, wind direction U/V, precipitation)
using the Open-Meteo API (or cached/fallback meteorological distributions).
"""

import httpx
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

OPEN_METEO_API_URL = "https://api.open-meteo.com/v1/forecast"


async def fetch_weather_forecast(
    latitude: float,
    longitude: float,
    forecast_days: int = 14
) -> Dict[str, Any]:
    """
    Fetches daily & hourly weather parameters for the target coordinate.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
            "wind_direction_10m_dominant"
        ],
        "hourly": [
            "relative_humidity_2m",
            "wind_speed_10m",
            "wind_direction_10m"
        ],
        "forecast_days": forecast_days,
        "timezone": "Asia/Jakarta"
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(OPEN_METEO_API_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                daily = data.get("daily", {})
                
                # Compute aggregate metrics
                max_temps = daily.get("temperature_2m_max", [])
                precip = daily.get("precipitation_sum", [])
                wind_speeds = daily.get("wind_speed_10m_max", [])
                wind_dirs = daily.get("wind_direction_10m_dominant", [])
                
                # Count consecutive rainless days (< 1.0mm)
                consecutive_dry_days = 0
                for p in precip:
                    if p is not None and p < 1.0:
                        consecutive_dry_days += 1
                    else:
                        break
                        
                avg_wind_spd = sum(wind_speeds) / len(wind_speeds) if wind_speeds else 4.5
                dominant_wind_dir = wind_dirs[0] if wind_dirs else 120.0
                
                return {
                    "source": "OPEN_METEO_LIVE",
                    "latitude": latitude,
                    "longitude": longitude,
                    "forecast_days": forecast_days,
                    "max_temp_avg": round(sum(max_temps) / len(max_temps), 1) if max_temps else 33.2,
                    "total_forecast_rain_mm": round(sum(p for p in precip if p is not None), 1),
                    "consecutive_dry_days": consecutive_dry_days,
                    "avg_wind_speed_ms": round(avg_wind_spd / 3.6, 2),  # km/h to m/s
                    "dominant_wind_direction_deg": dominant_wind_dir,
                    "daily_forecast": [
                        {
                            "day": i + 1,
                            "max_temp_c": max_temps[i] if i < len(max_temps) else 33.0,
                            "precip_mm": precip[i] if i < len(precip) else 0.0,
                            "wind_speed_kmh": wind_speeds[i] if i < len(wind_speeds) else 15.0,
                            "wind_dir_deg": wind_dirs[i] if i < len(wind_dirs) else 120.0
                        }
                        for i in range(min(forecast_days, len(daily.get("time", []))))
                    ]
                }
    except Exception as exc:
        logger.warning(f"Open-Meteo fetch failed or offline: {exc}. Using climatological dry-season baseline.")

    # High-fidelity climatological fallback (typical Indonesian August/September dry season)
    return {
        "source": "CLIMATOLOGY_FALLBACK",
        "latitude": latitude,
        "longitude": longitude,
        "forecast_days": forecast_days,
        "max_temp_avg": 34.1,
        "total_forecast_rain_mm": 4.2,
        "consecutive_dry_days": 11,
        "avg_wind_speed_ms": 4.8,
        "dominant_wind_direction_deg": 135.0,  # Southeast trade wind blowing NW
        "daily_forecast": [
            {
                "day": d,
                "max_temp_c": round(33.0 + (d % 3) * 0.7, 1),
                "precip_mm": 0.0 if d < 11 else round((d - 10) * 1.5, 1),
                "wind_speed_kmh": 16.5,
                "wind_dir_deg": 135.0
            }
            for d in range(1, forecast_days + 1)
        ]
    }

