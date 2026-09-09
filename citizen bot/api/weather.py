"""Public Weather API Integration.

Isolated service for fetching dynamic real-time and forecast weather data
using the Open-Meteo REST API (free, reliable, no API key required).
Adheres strictly to the rule:
    Never fabricate weather data if the API is unavailable.
"""

from __future__ import annotations
import logging
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger(__name__)

# Default municipal coordinates for Bengaluru, Karnataka, India
DEFAULT_LATITUDE = 12.9716
DEFAULT_LONGITUDE = 77.5946
DEFAULT_CITY = "Bengaluru (Municipal Region)"

WMO_WEATHER_CODES: Dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherService:
    """Service client for public weather data retrieval."""

    def __init__(
        self,
        base_url: str = "https://api.open-meteo.com/v1/forecast",
        timeout: float = 3.5,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout

    def get_weather(
        self,
        timeframe: str = "today",
        latitude: float = DEFAULT_LATITUDE,
        longitude: float = DEFAULT_LONGITUDE,
    ) -> Dict[str, Any]:
        """Fetch current weather or forecast.

        Args:
            timeframe: 'today' or 'tomorrow'
            latitude: Geographic latitude
            longitude: Geographic longitude

        Returns:
            Structured dictionary with weather data or error status.
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": "true",
            "daily": ["weathercode", "temperature_2m_max", "temperature_2m_min", "precipitation_probability_max", "precipitation_sum"],
            "timezone": "auto",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(self.base_url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_weather_response(data, timeframe)
                else:
                    logger.warning("Weather API returned HTTP %s: %s", response.status_code, response.text)
                    return {
                        "status": "error",
                        "error_message": f"Weather service responded with status {response.status_code}.",
                        "data": None,
                    }
        except httpx.TimeoutException:
            logger.warning("Weather API timed out after %s seconds", self.timeout)
            return {
                "status": "error",
                "error_message": "Weather service request timed out.",
                "data": None,
            }
        except Exception as e:
            logger.warning("Weather API call failed: %s", e)
            return {
                "status": "error",
                "error_message": "Unable to connect to the weather service at this time.",
                "data": None,
            }

    def _parse_weather_response(self, raw: Dict[str, Any], timeframe: str) -> Dict[str, Any]:
        """Normalize raw weather API payload into standard civic report format."""
        current = raw.get("current_weather", {})
        daily = raw.get("daily", {})

        current_temp = current.get("temperature")
        current_code = current.get("weathercode", 0)
        current_condition = WMO_WEATHER_CODES.get(current_code, "Fair")
        wind_speed = current.get("windspeed")

        # Today is index 0, Tomorrow is index 1
        day_idx = 1 if timeframe == "tomorrow" and len(daily.get("time", [])) > 1 else 0

        temp_max = None
        temp_min = None
        rain_prob = None
        precip_sum = None
        condition = current_condition

        if daily.get("temperature_2m_max"):
            temp_max = daily["temperature_2m_max"][day_idx]
        if daily.get("temperature_2m_min"):
            temp_min = daily["temperature_2m_min"][day_idx]
        if daily.get("precipitation_probability_max"):
            rain_prob = daily["precipitation_probability_max"][day_idx]
        if daily.get("precipitation_sum"):
            precip_sum = daily["precipitation_sum"][day_idx]
        if daily.get("weathercode"):
            code = daily["weathercode"][day_idx]
            condition = WMO_WEATHER_CODES.get(code, current_condition)

        rain_expected = bool(rain_prob is not None and rain_prob > 35)

        text_lines = [
            f"**Weather for {DEFAULT_CITY} ({timeframe.capitalize()}):**",
            f"• Condition: {condition}",
        ]
        if current_temp is not None and timeframe == "today":
            text_lines.append(f"• Current Temperature: {current_temp}°C")
        if temp_max is not None and temp_min is not None:
            text_lines.append(f"• High / Low: {temp_max}°C / {temp_min}°C")
        if rain_prob is not None:
            text_lines.append(f"• Rain Probability: {rain_prob}%")
        if wind_speed is not None:
            text_lines.append(f"• Wind Speed: {wind_speed} km/h")

        if rain_expected:
            text_lines.append("\n*Precipitation alert:* Rain is likely today. Bringing an umbrella is recommended.")

        return {
            "status": "success",
            "timeframe": timeframe,
            "city": DEFAULT_CITY,
            "condition": condition,
            "current_temp": current_temp,
            "temp_max": temp_max,
            "temp_min": temp_min,
            "rain_probability": rain_prob,
            "rain_expected": rain_expected,
            "summary_text": "\n".join(text_lines),
            "source": "Open-Meteo Public Weather API",
        }
