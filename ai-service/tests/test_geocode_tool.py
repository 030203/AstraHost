import unittest
from unittest.mock import Mock, patch

from tools.geocode_tool import GeocodeTool


class DummyConfig:
    @staticmethod
    def http_user_agent():
        return "RoomOS-Test"

    @staticmethod
    def http_timeout():
        return 5


class GeocodeToolTest(unittest.TestCase):
    def test_returns_normalized_location(self):
        tool = GeocodeTool(DummyConfig())
        mocked_response = Mock()
        mocked_response.raise_for_status.return_value = None
        mocked_response.json.return_value = [
            {
                "display_name": "Shanghai Tower, Pudong, Shanghai, China",
                "lat": "31.2336",
                "lon": "121.5055",
                "address": {
                    "city": "Shanghai",
                    "suburb": "Pudong",
                    "country": "China",
                    "postcode": "200120",
                },
            }
        ]

        with patch("tools.geocode_tool.requests.get", return_value=mocked_response):
            result = tool.execute({"query": "Shanghai Tower"})

        self.assertEqual(result["query"], "Shanghai Tower")
        self.assertEqual(result["city"], "Shanghai")
        self.assertEqual(result["district"], "Pudong")
        self.assertEqual(result["country"], "China")
        self.assertAlmostEqual(result["latitude"], 31.2336)
        self.assertAlmostEqual(result["longitude"], 121.5055)
        self.assertIn("uri.amap.com/marker", result["map_url"])

    def test_empty_query_raises(self):
        tool = GeocodeTool(DummyConfig())

        with self.assertRaises(ValueError):
            tool.execute({"query": ""})


if __name__ == "__main__":
    unittest.main()
