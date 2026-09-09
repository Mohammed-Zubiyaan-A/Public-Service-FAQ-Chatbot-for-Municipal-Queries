"""Unit tests for Public Weather API Integration."""

import pytest
from api.weather import WeatherService


@pytest.fixture
def weather_service():
    return WeatherService(timeout=4.0)


def test_weather_live_or_timeout(weather_service):
    """Test that weather service returns either valid data or clean error without exception."""
    res = weather_service.get_weather(timeframe="today")
    assert "status" in res
    if res["status"] == "success":
        assert "condition" in res
        assert "current_temp" in res or "temp_max" in res
        assert "source" in res
        assert "Open-Meteo" in res["source"]
    else:
        assert res["status"] == "error"
        assert "error_message" in res


def test_weather_tomorrow_forecast(weather_service):
    """Test forecast query for tomorrow."""
    res = weather_service.get_weather(timeframe="tomorrow")
    assert "status" in res
    if res["status"] == "success":
        assert res["timeframe"] == "tomorrow"
        assert "summary_text" in res


def test_weather_failure_handling():
    """Test that an invalid base URL is handled safely without crashing."""
    bad_service = WeatherService(base_url="https://invalid-nonexistent-domain-xyz.org/weather", timeout=1.0)
    res = bad_service.get_weather("today")
    assert res["status"] == "error"
    assert "error_message" in res
    assert res["data"] is None
