from urllib.parse import quote

import requests


class GeocodeTool:
    name = "geocode_location"
    description = "Resolve a place name or address into normalized location details, coordinates, and a map link."
    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Place name, landmark, hotel name, district, or address to resolve.",
            }
        },
        "required": ["query"],
    }

    def __init__(self, config):
        self.config = config

    def execute(self, tool_input):
        query = str(tool_input.get("query") or "").strip()
        if not query:
            raise ValueError("query 不能为空")

        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": query,
                "format": "jsonv2",
                "limit": 1,
                "addressdetails": 1,
            },
            headers={"User-Agent": self.config.http_user_agent()},
            timeout=self.config.http_timeout(),
        )
        response.raise_for_status()
        payload = response.json()
        if not payload:
            return {"error": f"未找到位置：{query}"}

        item = payload[0]
        address = item.get("address") if isinstance(item.get("address"), dict) else {}
        latitude = self._to_float(item.get("lat"))
        longitude = self._to_float(item.get("lon"))

        return {
            "query": query,
            "display_name": item.get("display_name") or "",
            "latitude": latitude,
            "longitude": longitude,
            "city": self._first_non_empty(
                address.get("city"),
                address.get("town"),
                address.get("village"),
                address.get("state"),
            ),
            "district": self._first_non_empty(
                address.get("suburb"),
                address.get("city_district"),
                address.get("county"),
            ),
            "country": address.get("country") or "",
            "postcode": address.get("postcode") or "",
            "map_url": self._build_map_url(latitude, longitude, item.get("display_name") or query),
        }

    @staticmethod
    def _to_float(value):
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _first_non_empty(*values):
        for value in values:
            text = str(value or "").strip()
            if text:
                return text
        return ""

    @staticmethod
    def _build_map_url(latitude, longitude, label):
        if latitude is None or longitude is None:
            return ""
        return (
            "https://uri.amap.com/marker?position="
            f"{longitude},{latitude}&name={quote(str(label))}"
        )
