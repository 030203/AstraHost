import unittest

from services.skill_service import SkillService


class DummyToolService:
    def __init__(self, allowed_tool_names):
        self.allowed_tool_names = tuple(allowed_tool_names)

    def get_allowed_tool_names(self, user_context=None, mode=None):
        return self.allowed_tool_names


class SkillServiceTest(unittest.TestCase):
    def test_unmatched_message_uses_only_low_risk_fallback_tools(self):
        service = SkillService(
            DummyToolService(
                (
                    "list_bookings",
                    "list_users",
                    "search_properties",
                    "get_top_properties",
                    "tavily_search",
                    "get_weather",
                )
            )
        )

        route = service.resolve("Help me plan a relaxed weekend trip.")

        self.assertEqual(route.active_skill_names, ())
        self.assertEqual(
            route.tool_names,
            (
                "search_properties",
                "get_top_properties",
                "tavily_search",
                "get_weather",
            ),
        )

    def test_unmatched_message_respects_available_fallback_tools(self):
        service = SkillService(DummyToolService(("get_top_properties", "get_weather")))

        route = service.resolve("Give me a simple travel checklist.")

        self.assertEqual(route.active_skill_names, ())
        self.assertEqual(route.tool_names, ("get_top_properties", "get_weather"))

    def test_matched_skill_uses_skill_tools_without_general_fallback(self):
        service = SkillService(
            DummyToolService(
                (
                    "list_properties",
                    "search_properties",
                    "get_property_detail",
                    "get_top_properties",
                    "list_room_types",
                    "get_room_type_detail",
                    "get_active_room_types",
                    "tavily_search",
                    "get_weather",
                )
            )
        )

        route = service.resolve("Find a property near Shenzhen.")

        self.assertEqual(route.active_skill_names, ("property_support",))
        self.assertEqual(
            route.tool_names,
            (
                "list_properties",
                "search_properties",
                "get_property_detail",
                "get_top_properties",
                "list_room_types",
                "get_room_type_detail",
                "get_active_room_types",
            ),
        )

    def test_matched_sensitive_skill_without_allowed_tools_does_not_fallback(self):
        service = SkillService(
            DummyToolService(("search_properties", "get_top_properties", "get_weather"))
        )

        route = service.resolve("Can you check my booking status?")

        self.assertEqual(route.active_skill_names, ("booking_support",))
        self.assertEqual(route.tool_names, ())

    def test_booking_and_payment_skills_include_new_action_tools_when_allowed(self):
        service = SkillService(
            DummyToolService(
                (
                    "list_bookings",
                    "get_booking_detail",
                    "get_booking_by_number",
                    "create_booking",
                    "cancel_booking",
                    "check_in_booking",
                    "check_out_booking",
                    "list_payments",
                    "get_payment_detail",
                    "get_payment_by_number",
                    "create_payment",
                    "process_payment",
                )
            )
        )

        booking_route = service.resolve("帮我订这个房型，下个周末入住")
        payment_route = service.resolve("我现在就去支付这笔订单")

        self.assertIn("create_booking", booking_route.tool_names)
        self.assertIn("create_payment", payment_route.tool_names)
        self.assertIn("process_payment", payment_route.tool_names)

    def test_time_hint_appends_time_tool(self):
        service = SkillService(
            DummyToolService(
                (
                    "search_properties",
                    "get_top_properties",
                    "tavily_search",
                    "get_weather",
                    "get_current_time",
                )
            )
        )

        route = service.resolve("东京现在几点？")

        self.assertIn("get_current_time", route.tool_names)

    def test_location_hint_appends_geocode_tool(self):
        service = SkillService(
            DummyToolService(
                (
                    "search_properties",
                    "get_top_properties",
                    "tavily_search",
                    "get_weather",
                    "geocode_location",
                )
            )
        )

        route = service.resolve("这家酒店的具体地址和坐标是什么？")

        self.assertIn("geocode_location", route.tool_names)


if __name__ == "__main__":
    unittest.main()
