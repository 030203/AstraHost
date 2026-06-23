from skills.base import KeywordSkill


def build_customer_service_skills():
    return (
        KeywordSkill(
            name="property_support",
            description="Property and room type support",
            keywords=(
                "\u623f\u6e90",
                "\u6c11\u5bbf",
                "\u9152\u5e97",
                "\u516c\u5bd3",
                "\u623f\u578b",
                "\u8bbe\u65bd",
                "\u9644\u8fd1",
                "\u5730\u6bb5",
                "\u4f4d\u7f6e",
                "\u70ed\u95e8\u623f\u6e90",
                "\u7cbe\u9009\u623f\u6e90",
                "property",
                "room type",
            ),
            tool_names=(
                "list_properties",
                "search_properties",
                "get_property_detail",
                "get_top_properties",
                "list_room_types",
                "get_room_type_detail",
                "get_active_room_types",
            ),
            system_prompt=(
                "This request is about properties or room types. "
                "Use property and room tools first to confirm city, price, rating, facilities, room types and details."
            ),
        ),
        KeywordSkill(
            name="booking_support",
            description="Booking lookup and booking actions",
            keywords=(
                "\u8ba2\u5355",
                "\u9884\u8ba2",
                "\u8ba2\u5355\u53f7",
                "\u53d6\u6d88\u8ba2\u5355",
                "\u53d6\u6d88\u9884\u8ba2",
                "\u5165\u4f4f",
                "\u79bb\u5e97",
                "\u9000\u623f",
                "booking",
                "check-in",
                "check in",
                "check-out",
                "check out",
                "cancel booking",
            ),
            tool_names=(
                "list_bookings",
                "get_booking_detail",
                "get_booking_by_number",
                "create_booking",
                "cancel_booking",
                "check_in_booking",
                "check_out_booking",
            ),
            system_prompt=(
                "This request is about bookings. "
                "Use booking tools to confirm status, booking number and check-in or check-out timing. "
                "Only use action tools when the user explicitly asks to perform the action."
            ),
        ),
        KeywordSkill(
            name="payment_support",
            description="Payment status and payment record support",
            keywords=(
                "\u652f\u4ed8",
                "\u4ed8\u6b3e",
                "\u4ea4\u6613",
                "\u652f\u4ed8\u5355",
                "payment",
                "pay",
                "transaction",
            ),
            tool_names=(
                "list_payments",
                "get_payment_detail",
                "get_payment_by_number",
                "create_payment",
                "process_payment",
            ),
            system_prompt=(
                "This request is about payments. "
                "Use payment tools first to confirm payment status, payment number, amount and related booking. "
                "Only use action tools when the user explicitly asks to create or confirm a payment."
            ),
        ),
        KeywordSkill(
            name="review_support",
            description="Review lookup and review reply support",
            keywords=(
                "\u8bc4\u4ef7",
                "\u8bc4\u8bba",
                "\u8bc4\u5206",
                "\u56de\u590d\u8bc4\u4ef7",
                "\u56de\u590d\u8bc4\u8bba",
                "review",
                "reply review",
            ),
            tool_names=(
                "list_reviews",
                "get_review_detail",
                "get_review_by_booking",
                "reply_review",
            ),
            system_prompt=(
                "This request is about reviews. "
                "Use review tools first to confirm rating, review content and related booking. "
                "Only use the reply tool when the user explicitly requests a reply."
            ),
        ),
        KeywordSkill(
            name="notification_support",
            description="Notification lookup and read-state update support",
            keywords=(
                "\u901a\u77e5",
                "\u6d88\u606f",
                "\u63d0\u9192",
                "\u672a\u8bfb",
                "\u5df2\u8bfb",
                "notification",
                "message",
            ),
            tool_names=(
                "list_notifications",
                "get_unread_notification_count",
                "mark_notification_read",
                "mark_all_notifications_read",
            ),
            system_prompt=(
                "This request is about notifications. "
                "Use notification tools first to confirm notification content and unread counts. "
                "Only update read state when the user explicitly asks for it."
            ),
        ),
        KeywordSkill(
            name="coupon_support",
            description="Coupon support",
            keywords=(
                "\u4f18\u60e0\u5238",
                "\u4f18\u60e0",
                "\u6298\u6263",
                "coupon",
                "discount",
            ),
            tool_names=(
                "list_coupons",
                "get_coupon_detail",
            ),
            system_prompt=(
                "This request is about coupons. "
                "Use coupon tools first to confirm coupon status, scope and merchant information."
            ),
        ),
        KeywordSkill(
            name="merchant_support",
            description="Merchant support",
            keywords=(
                "\u5546\u5bb6",
                "\u623f\u4e1c",
                "merchant",
                "host",
            ),
            tool_names=(
                "list_merchants",
                "get_merchant_detail",
                "get_merchant_by_user",
            ),
            system_prompt=(
                "This request is about merchants. "
                "Use merchant tools first to confirm merchant status, city and linked information."
            ),
        ),
        KeywordSkill(
            name="user_support",
            description="User and account support",
            keywords=(
                "\u7528\u6237",
                "\u8d26\u53f7",
                "\u5e10\u53f7",
                "\u4e2a\u4eba\u8d44\u6599",
                "user",
                "account",
                "profile",
            ),
            tool_names=(
                "list_users",
                "get_user_detail",
            ),
            system_prompt=(
                "This request is about users or accounts. "
                "Use user tools first to confirm user profile details. "
                "For normal users, prefer the current user context."
            ),
        ),
    )
