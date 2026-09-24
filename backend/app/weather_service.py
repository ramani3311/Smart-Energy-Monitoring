"""
weather_service.py

Fetches live weather for a node's latitude/longitude from OpenWeatherMap's
free "Current Weather Data" API, and caches the result on the node's own
MongoDB document (in its `weather` sub-object) so:

  - The node list/detail endpoints stay fast (no external call on every
    page load).
  - You control exactly when a fresh weather pull happens - via the
    dashboard's per-node "Refresh weather" button, which calls
    POST /api/nodes/{node_id}/weather/refresh.

Environment variables:
    OPENWEATHER_API_KEY   - required to fetch live weather. Get a free key
                             at https://openweathermap.org/api
"""

import os

import requests

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


class WeatherFetchError(Exception):
    pass


def fetch_live_weather(latitude: float, longitude: float) -> dict:
    """
    Calls OpenWeatherMap for the given coordinates and returns a dict shaped
    like our stored `weather` sub-document:
        { temperature, humidity, rain, wind_speed, weather_condition }
    Raises WeatherFetchError with a human-readable message on any failure -
    the caller (main.py) turns that into a clean 502 for the frontend.
    """
    if not OPENWEATHER_API_KEY:
        raise WeatherFetchError(
            "OPENWEATHER_API_KEY is not set. Get a free key at "
            "openweathermap.org/api and add it to your environment."
        )

    try:
        resp = requests.get(
            OPENWEATHER_URL,
            params={
                "lat": latitude,
                "lon": longitude,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
            },
            timeout=8,
        )
    except requests.exceptions.RequestException as e:
        raise WeatherFetchError(f"Could not reach OpenWeatherMap: {e}")

    if resp.status_code == 401:
        raise WeatherFetchError("OpenWeatherMap rejected the API key (401 Unauthorized).")
    if resp.status_code != 200:
        raise WeatherFetchError(f"OpenWeatherMap error: HTTP {resp.status_code} - {resp.text[:200]}")

    data = resp.json()
    main = data.get("main", {})
    wind = data.get("wind", {})
    rain = data.get("rain", {})
    weather_list = data.get("weather") or [{}]

    return {
        "temperature": main.get("temp"),
        "humidity": main.get("humidity"),
        "rain": rain.get("1h", 0.0) or rain.get("3h", 0.0) or 0.0,
        "wind_speed": wind.get("speed"),
        "weather_condition": weather_list[0].get("main", "Unknown"),
    }
