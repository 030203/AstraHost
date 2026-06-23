import requests


class WeatherTool:
    name = "get_weather"
    description = "Get current weather for a city or destination using OpenWeather."
    input_schema = {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City or destination name, such as Hangzhou or Dali.",
            }
        },
        "required": ["location"],
    }

    def __init__(self, config):
        self.config = config

    def execute(self, tool_input):
        api_key = self.config.openweather_api_key()
        if not api_key:
            return {"error": "Missing OPENWEATHER_API_KEY."}

        location = tool_input.get("location", "")
        geo_response = requests.get(
            "https://api.openweathermap.org/geo/1.0/direct",
            params={"q": location, "limit": 1, "appid": api_key},
            timeout=20,
        )
        geo_response.raise_for_status()
        geo_data = geo_response.json()
        if not geo_data:
            return {"error": f"Location not found: {location}"}

        place = geo_data[0]
        weather_response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "lat": place["lat"],
                "lon": place["lon"],
                "appid": api_key,
                "units": "metric",
                "lang": "zh_cn",
            },
            timeout=20,
        )
        weather_response.raise_for_status()
        weather_data = weather_response.json()

        main = weather_data.get("main", {})
        wind = weather_data.get("wind", {})
        weather = weather_data.get("weather", [{}])[0]

        return {
            "location": f"{place.get('name')}, {place.get('country')}",
            "description": weather.get("description"),
            "temperature_c": main.get("temp"),
            "feels_like_c": main.get("feels_like"),
            "humidity": main.get("humidity"),
            "wind_speed": wind.get("speed"),
        }
