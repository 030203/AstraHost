"""
Generate 100 diverse skill routing test fixtures.
Run: python tools/generate_skill_routing_fixtures.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "tests" / "fixtures" / "skill_routing_cases.json"

# ── Tool sets ──────────────────────────────────────────────────
PROPERTY_TOOLS = [
    "list_properties", "search_properties", "get_property_detail",
    "get_top_properties", "list_room_types", "get_room_type_detail",
    "get_active_room_types",
]
BOOKING_TOOLS = [
    "list_bookings", "get_booking_detail", "get_booking_by_number",
    "create_booking", "cancel_booking", "check_in_booking", "check_out_booking",
]
PAYMENT_TOOLS = [
    "list_payments", "get_payment_detail", "get_payment_by_number",
    "create_payment", "process_payment",
]
REVIEW_TOOLS = [
    "list_reviews", "get_review_detail", "get_review_by_booking", "reply_review",
]
USER_TOOLS = ["list_users", "get_user_detail"]
NOTIFICATION_TOOLS = [
    "list_notifications", "get_unread_notification_count",
    "mark_notification_read", "mark_all_notifications_read",
]
COUPON_TOOLS = ["list_coupons", "get_coupon_detail"]
MERCHANT_TOOLS = ["list_merchants", "get_merchant_detail", "get_merchant_by_user"]
EXTERNAL_TOOLS = ["tavily_search", "get_weather", "get_current_time", "geocode_location"]

ALL_TOOLS = (
    PROPERTY_TOOLS + BOOKING_TOOLS + PAYMENT_TOOLS + REVIEW_TOOLS
    + USER_TOOLS + NOTIFICATION_TOOLS + COUPON_TOOLS + MERCHANT_TOOLS
    + EXTERNAL_TOOLS
)

# ── Domain resources ──────────────────────────────────────────
PROPERTY_SKILLS = ["property_support"]
BOOKING_SKILLS = ["booking_support"]
PAYMENT_SKILLS = ["payment_support"]
REVIEW_SKILLS = ["review_support"]
USER_SKILLS = ["user_support", "notification_support", "coupon_support", "merchant_support"]

ALL_USER_TOOLS = USER_TOOLS + NOTIFICATION_TOOLS + COUPON_TOOLS + MERCHANT_TOOLS

# ── Helpers ───────────────────────────────────────────────────
case_id = [0]


def new_id(prefix):
    case_id[0] += 1
    return f"{prefix}_{case_id[0]:03d}"


def make(
    prefix,
    message,
    expected_skills,
    expected_tools,
    category,
    allowed_tools=None,
    should_call_tools=True,
):
    return {
        "id": new_id(prefix),
        "message": message,
        "allowed_tools": allowed_tools or ALL_TOOLS,
        "expected_skills": expected_skills,
        "expected_tools": expected_tools,
        "category": category,
        "should_call_tools": should_call_tools,
    }


# ══════════════════════════════════════════════════════════════
#  1. PROPERTY (18 cases)
# ══════════════════════════════════════════════════════════════
PROPERTY_CASES = [
    # Basic searches
    make("prop", "帮我找一下深圳南山的民宿", PROPERTY_SKILLS, PROPERTY_TOOLS, "property"),
    make("prop", "上海浦东新区有什么好的酒店推荐", PROPERTY_SKILLS, PROPERTY_TOOLS, "property"),
    make("prop", "北京三里屯附近有没有性价比高的公寓", PROPERTY_SKILLS, PROPERTY_TOOLS, "property"),
    # Price + rating filters
    make("prop", "找深圳南山 800 以内评分 4.5 以上的民宿", PROPERTY_SKILLS, PROPERTY_TOOLS, "property"),
    make("prop", "预算 500-1000 的酒店有哪些", PROPERTY_SKILLS, PROPERTY_TOOLS, "property"),
    make("prop", "评分 4.8 以上的高端酒店", PROPERTY_SKILLS, PROPERTY_TOOLS, "property"),
    # Facility / feature search
    make("prop", "找一下带游泳池和健身房的海景酒店", PROPERTY_SKILLS, PROPERTY_TOOLS, "property"),
    make("prop", "有亲子房的民宿推荐吗", PROPERTY_SKILLS, PROPERTY_TOOLS, "property"),
    # Room types
    make("prop", "这个酒店有哪些房型，双床房还能订吗", PROPERTY_SKILLS, PROPERTY_TOOLS, "property"),
    make("prop", "看看豪华大床房的价格和设施", PROPERTY_SKILLS, PROPERTY_TOOLS, "property"),
    # Details / top
    make("prop", "帮我查一下房源 1024 的详细信息", PROPERTY_SKILLS, PROPERTY_TOOLS, "property"),
    make("prop", "本周热门酒店排行榜", PROPERTY_SKILLS, PROPERTY_TOOLS, "property"),
    # Location
    make("prop", "距离地铁站步行 5 分钟的酒店", PROPERTY_SKILLS, PROPERTY_TOOLS, "property"),
    make("prop", "靠近故宫的民宿有哪些", PROPERTY_SKILLS, PROPERTY_TOOLS, "property"),
    # Mixed filters
    make("prop", "成都春熙路附近 300 以内评分 4 分以上的酒店", PROPERTY_SKILLS, PROPERTY_TOOLS, "property"),
    make("prop", "广州塔周边适合情侣入住的精品民宿", PROPERTY_SKILLS, PROPERTY_TOOLS, "property"),
]

# ══════════════════════════════════════════════════════════════
#  2. BOOKING (18 cases)
# ══════════════════════════════════════════════════════════════
BOOKING_CASES = [
    # Status / lookup
    make("book", "帮我查一下订单号 BK202605080001 现在是什么状态", BOOKING_SKILLS, BOOKING_TOOLS, "booking"),
    make("book", "订单 12345 到哪一步了", BOOKING_SKILLS, BOOKING_TOOLS, "booking"),
    make("book", "查一下我最近的订单列表", BOOKING_SKILLS, BOOKING_TOOLS, "booking"),
    make("book", "帮我看看商家 678 的今日入住订单", BOOKING_SKILLS, BOOKING_TOOLS, "booking"),
    # Cancel (capability vs action)
    make("book", "这个订单还能不能取消", BOOKING_SKILLS, BOOKING_TOOLS, "booking"),
    make("book", "帮我取消订单 BK202605080001，原因是我行程有变", BOOKING_SKILLS, BOOKING_TOOLS, "booking"),
    make("book", "取消的话要收手续费吗", BOOKING_SKILLS, BOOKING_TOOLS, "booking"),
    make("book", "帮我取消今晚的订单", BOOKING_SKILLS, BOOKING_TOOLS, "booking"),
    # Check-in / check-out
    make("book", "我要办理入住，订单号 BK123456", BOOKING_SKILLS, BOOKING_TOOLS, "booking"),
    make("book", "明天退房，帮我办理离店", BOOKING_SKILLS, BOOKING_TOOLS, "booking"),
    make("book", "提前入住可以吗", BOOKING_SKILLS, BOOKING_TOOLS, "booking"),
    make("book", "我想续住一晚，可以吗", BOOKING_SKILLS, BOOKING_TOOLS, "booking"),
    # Create booking
    make("book", "帮我订一间 6 月 20 号到 22 号的双床房，两个人住", BOOKING_SKILLS, BOOKING_TOOLS, "booking"),
    make("book", "预订下周五到周日的大床房，联系人是张三，电话 13800138000", BOOKING_SKILLS, BOOKING_TOOLS, "booking"),
    make("book", "我想在深圳湾观海酒店订一间海景房，3 月 15 号入住", BOOKING_SKILLS, BOOKING_TOOLS, "booking"),
    # Ambiguous / edge
    make("book", "加一张床多少钱", BOOKING_SKILLS, BOOKING_TOOLS, "booking"),
    make("book", "订单里的入住人数能改吗", BOOKING_SKILLS, BOOKING_TOOLS, "booking"),
]
PAYMENT_CASES = [
    # Status
    make("pay", "订单 1024 的支付成功了吗", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
    make("pay", "查一下支付单号 PAY202605080001 的状态", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
    make("pay", "我的支付记录在哪里看", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
    make("pay", "这笔订单的押金退了吗", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
    # Create / process
    make("pay", "帮我付一下订单 BK123456 的尾款，用支付宝", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
    make("pay", "我要支付订单 1024，金额 899 元，微信支付", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
    make("pay", "客人已经转账了，确认到账，交易流水号 TXN20260508", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
    # Refund / deposit
    make("pay", "取消订单后什么时候退款", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
    make("pay", "押金怎么退，退到哪里", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
    make("pay", "我多付了，能退差价吗", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
    make("pay", "支持哪些支付方式", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
]
USER_CASES = [
    # User profile
    make("user", "帮我看看这个用户的账号资料", USER_SKILLS, ALL_USER_TOOLS, "user"),
    make("user", "查一下我自己的个人信息", USER_SKILLS, ALL_USER_TOOLS, "user"),
    make("user", "用户 1001 注册多久了", USER_SKILLS, ALL_USER_TOOLS, "user"),
    make("user", "怎么修改个人资料", USER_SKILLS, ALL_USER_TOOLS, "user"),
    # Notifications
    make("user", "我还有几条未读通知", USER_SKILLS, ALL_USER_TOOLS, "notification"),
    make("user", "把我所有未读通知都标为已读", USER_SKILLS, ALL_USER_TOOLS, "notification"),
    make("user", "把通知 567 标记为已读", USER_SKILLS, ALL_USER_TOOLS, "notification"),
    # Coupons
    make("user", "我现在有什么优惠券可以用", USER_SKILLS, ALL_USER_TOOLS, "coupon"),
    make("user", "优惠券 888 的详情和使用条件", USER_SKILLS, ALL_USER_TOOLS, "coupon"),
    make("user", "有没有新用户优惠券", USER_SKILLS, ALL_USER_TOOLS, "coupon"),
    # Merchants
    make("user", "查一下这个商家的资料和状态", USER_SKILLS, ALL_USER_TOOLS, "merchant"),
    make("user", "看看我关联的是哪个商家", USER_SKILLS, ALL_USER_TOOLS, "merchant"),
    make("user", "商家 42 的联系方式是什么", USER_SKILLS, ALL_USER_TOOLS, "merchant"),
]
GENERAL_CASES = [
    # Weather
    make("gen", "杭州明天天气怎么样，适不适合出行", [], [], "weather"),
    make("gen", "深圳这周末会下雨吗", [], [], "weather"),
    make("gen", "去三亚旅游这几天的气温如何", [], [], "weather"),
    # External search
    make("gen", "帮我搜索一下最近的日本签证攻略", [], [], "external"),
    make("gen", "查一下北京到上海的高铁时刻表", [], [], "external"),
    make("gen", "附近有什么好玩的景点推荐", [], [], "external"),
    # Fallback / general
    make("gen", "给我一个周末旅行准备清单", [], [], "fallback"),
    make("gen", "商务出差一般带什么东西", [], [], "fallback"),
    # Chit-chat
    make("gen", "你好，请问你能帮我做什么", [], [], "chat"),
    make("gen", "谢谢你，服务很好", [], [], "chat"),
    make("gen", "今天天气真不错", [], [], "chat"),
]
AMBIGUOUS_CASES = [
    # "处理补偿" — ambiguous, LLM says Business:Review
    make("amb", "客人说不满意，帮我处理一下补偿", REVIEW_SKILLS, REVIEW_TOOLS, "ambiguous"),
    # Time / location
    make("amb", "现在几点了，当地时间是多少", [], [], "time_fallback"),
    make("amb", "查一下这个地址的经纬度", [], [], "location_fallback"),
    # "评分 4.5" should be Property, not Review
    make("amb", "找评分 4.5 以上的酒店", PROPERTY_SKILLS, PROPERTY_TOOLS, "property_edge"),
    # "多少钱" could be price query
    make("amb", "大床房多少钱一晚", PROPERTY_SKILLS, PROPERTY_TOOLS, "property_edge"),
    # Multi-intent
    make("amb", "帮我查一下订单状态，顺便取消另一个订单", BOOKING_SKILLS, BOOKING_TOOLS, "booking_multi"),
    # "回复" in different context → Content
    make("amb", "帮我回复一下客人的投诉", [], [], "copywriting", should_call_tools=False),
    # "能帮我看看" → coupon
    make("amb", "能帮我看看我有哪些优惠", USER_SKILLS, ALL_USER_TOOLS, "coupon"),
    # Service info → chat
    make("amb", "你们客服电话多少", [], [], "chat"),
    # Booking with property context
    make("amb", "看了深圳湾酒店，帮我订一间海景房", BOOKING_SKILLS, BOOKING_TOOLS, "booking"),
]

# ══════════════════════════════════════════════════════════════
#  3. PAYMENT (12 cases)
# ══════════════════════════════════════════════════════════════
PAYMENT_CASES = [
    # Status
    make("pay", "订单 1024 的支付成功了吗", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
    make("pay", "查一下支付单号 PAY202605080001 的状态", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
    make("pay", "我的支付记录在哪里看", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
    make("pay", "这笔订单的押金退了吗", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
    # Create / process
    make("pay", "帮我付一下订单 BK123456 的尾款，用支付宝", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
    make("pay", "我要支付订单 1024，金额 899 元，微信支付", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
    make("pay", "客人已经转账了，确认到账，交易流水号 TXN20260508", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
    make("pay", "帮我确认一下支付单 567 到账了没有", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
    # Refund / deposit
    make("pay", "取消订单后什么时候退款", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
    make("pay", "押金怎么退，退到哪里", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
    make("pay", "我多付了，能退差价吗", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
    make("pay", "支持哪些支付方式", PAYMENT_SKILLS, PAYMENT_TOOLS, "payment"),
]

# ══════════════════════════════════════════════════════════════
#  4. REVIEW (12 cases)
# ══════════════════════════════════════════════════════════════
REVIEW_CASES = [
    # View / list
    make("rev", "看看这个酒店的评价怎么样", REVIEW_SKILLS, REVIEW_TOOLS, "review"),
    make("rev", "查一下房源 1001 的最新评论", REVIEW_SKILLS, REVIEW_TOOLS, "review"),
    make("rev", "这个订单的评价了没", REVIEW_SKILLS, REVIEW_TOOLS, "review"),
    make("rev", "查看我的历史评价记录", REVIEW_SKILLS, REVIEW_TOOLS, "review"),
    # Reply
    make("rev", "帮我回复这条差评，语气诚恳一点", REVIEW_SKILLS, REVIEW_TOOLS, "review"),
    make("rev", "回复评价编号 888 的评论", REVIEW_SKILLS, REVIEW_TOOLS, "review"),
    make("rev", "客人给了 3 分，帮我回复一下", REVIEW_SKILLS, REVIEW_TOOLS, "review"),
    make("rev", "这条差评说有噪音问题，帮我回复道歉并说明已整改", REVIEW_SKILLS, REVIEW_TOOLS, "review"),
    # Edge: Content vs Review
    # "帮我写一条回复" → Content (writing standalone text)
    # "帮我回复这条差评" → Business:Review (executing platform action)
    make("rev", "有一条差评说卫生不好，帮我回复解释一下", REVIEW_SKILLS, REVIEW_TOOLS, "review"),
    make("rev", "帮我回复一下客人关于退款的评价", REVIEW_SKILLS, REVIEW_TOOLS, "review"),
    # Mixed
    make("rev", "这个酒店评分 4.2，看看大家的评价", REVIEW_SKILLS, REVIEW_TOOLS, "review"),
    make("rev", "好评率多少，差评主要说什么", REVIEW_SKILLS, REVIEW_TOOLS, "review"),
    make("rev", "这个酒店评分 4.2，看看大家的评价", REVIEW_SKILLS, REVIEW_TOOLS, "review"),
]

# ══════════════════════════════════════════════════════════════
#  5. USER DOMAIN (15 cases: user 4 + notification 4 + coupon 4 + merchant 3)
# ══════════════════════════════════════════════════════════════
USER_CASES = [
    # User profile
    make("user", "帮我看看这个用户的账号资料", USER_SKILLS, ALL_USER_TOOLS, "user"),
    make("user", "查一下我自己的个人信息", USER_SKILLS, ALL_USER_TOOLS, "user"),
    make("user", "用户 1001 注册多久了", USER_SKILLS, ALL_USER_TOOLS, "user"),
    make("user", "怎么修改个人资料", USER_SKILLS, ALL_USER_TOOLS, "user"),
    # Notifications
    make("user", "我还有几条未读通知", USER_SKILLS, ALL_USER_TOOLS, "notification"),
    make("user", "帮我查看最新的系统通知", USER_SKILLS, ALL_USER_TOOLS, "notification"),
    make("user", "把通知 567 标记为已读", USER_SKILLS, ALL_USER_TOOLS, "notification"),
    make("user", "把所有未读通知都标为已读", USER_SKILLS, ALL_USER_TOOLS, "notification"),
    # Coupons
    make("user", "我现在有什么优惠券可以用", USER_SKILLS, ALL_USER_TOOLS, "coupon"),
    make("user", "看看最近的优惠活动", USER_SKILLS, ALL_USER_TOOLS, "coupon"),
    make("user", "优惠券 888 的详情和使用条件", USER_SKILLS, ALL_USER_TOOLS, "coupon"),
    make("user", "有没有新用户优惠券", USER_SKILLS, ALL_USER_TOOLS, "coupon"),
    # Merchants
    make("user", "查一下这个商家的资料和状态", USER_SKILLS, ALL_USER_TOOLS, "merchant"),
    make("user", "看看我关联的是哪个商家", USER_SKILLS, ALL_USER_TOOLS, "merchant"),
    make("user", "商家 42 的联系方式是什么", USER_SKILLS, ALL_USER_TOOLS, "merchant"),
]

# ══════════════════════════════════════════════════════════════
#  6. CONTENT (10 cases)
# ══════════════════════════════════════════════════════════════
CONTENT_CASES = [
    make("cnt", "帮我写一段客服回复，安抚因延迟入住而不满的客人，并提供补偿建议", [], [], "copywriting", should_call_tools=False),
    make("cnt", "帮我润色一段退款安抚话术，语气温和一点", [], [], "copywriting", should_call_tools=False),
    make("cnt", "写一个入住温馨提醒的模板", [], [], "copywriting", should_call_tools=False),
    make("cnt", "帮我编一条促销短信，推广周末特价房", [], [], "copywriting", should_call_tools=False),
    make("cnt", "客人不满意，帮我写个道歉文案", [], [], "copywriting", should_call_tools=False),
    make("cnt", "帮我拟一份取消政策的说明文本", [], [], "copywriting", should_call_tools=False),
    make("cnt", "写一条好评感谢回复模板", [], [], "copywriting", should_call_tools=False),
    make("cnt", "帮我把这段话改得更有礼貌一些", [], [], "copywriting", should_call_tools=False),
    make("cnt", "帮我起草一份酒店推荐语", [], [], "copywriting", should_call_tools=False),
    # Content vs Business edge: "帮我回复客人" = writing text, not platform action
    make("cnt", "帮我回复客人说抱歉，送一份水果拼盘作为补偿", [], [], "copywriting", should_call_tools=False),
]

# ══════════════════════════════════════════════════════════════
#  7. GENERAL / EXTERNAL / CHAT / FALLBACK (15 cases)
# ══════════════════════════════════════════════════════════════
GENERAL_CASES = [
    # Weather
    make("gen", "杭州明天天气怎么样，适不适合出行", [], [], "weather"),
    make("gen", "深圳这周末会下雨吗", [], [], "weather"),
    make("gen", "去三亚旅游这几天的气温如何", [], [], "weather"),
    # External search
    make("gen", "帮我搜索一下最近的日本签证攻略", [], [], "external"),
    make("gen", "查一下北京到上海的高铁时刻表", [], [], "external"),
    make("gen", "附近有什么好玩的景点推荐", [], [], "external"),
    # Fallback / general
    make("gen", "给我一个周末旅行准备清单", [], [], "fallback"),
    make("gen", "商务出差一般带什么东西", [], [], "fallback"),
    make("gen", "酒店行业有什么最新的趋势", [], [], "fallback"),
    # Chit-chat
    make("gen", "你好，请问你能帮我做什么", [], [], "chat"),
    make("gen", "谢谢你，服务很好", [], [], "chat"),
    make("gen", "今天天气真不错", [], [], "chat"),
]

# ══════════════════════════════════════════════════════════════
#  8. AMBIGUOUS / EDGE CASES (remaining)
# ══════════════════════════════════════════════════════════════
# These are intentionally tricky messages
AMBIGUOUS_CASES = [
    # "处理补偿" — ambiguous, LLM says Business:Review
    make("amb", "客人说不满意，帮我处理一下补偿", REVIEW_SKILLS, REVIEW_TOOLS, "ambiguous"),
    # Time-related
    make("amb", "现在几点了，当地时间是多少", [], [], "time_fallback"),
    # Location
    make("amb", "查一下这个地址的经纬度", [], [], "location_fallback"),
    # "评分 4.5" should be Property, not Review
    make("amb", "找评分 4.5 以上的酒店", PROPERTY_SKILLS, PROPERTY_TOOLS, "property_edge"),
    # "多少钱" could be price query → Property
    make("amb", "大床房多少钱一晚", PROPERTY_SKILLS, PROPERTY_TOOLS, "property_edge"),
    # Multi-intent (primary: booking status)
    make("amb", "帮我查一下订单状态，顺便取消另一个订单", BOOKING_SKILLS, BOOKING_TOOLS, "booking_multi"),
    # "回复" in different context
    make("amb", "帮我回复一下客人的投诉", [], [], "copywriting", should_call_tools=False),
    # "能帮我看看" ambiguous
    make("amb", "能帮我看看我有哪些优惠", USER_SKILLS, ALL_USER_TOOLS, "coupon"),
    # Service info
    make("amb", "你们客服电话多少", [], [], "chat"),
    # Booking with property context
    make("amb", "看了深圳湾酒店，帮我订一间海景房", BOOKING_SKILLS, BOOKING_TOOLS, "booking"),
]

# ── Combine ──────────────────────────────────────────────────
ALL_CASES = (
    PROPERTY_CASES + BOOKING_CASES + PAYMENT_CASES + REVIEW_CASES
    + USER_CASES + CONTENT_CASES + GENERAL_CASES + AMBIGUOUS_CASES
)

# Sanity checks
ids = [c["id"] for c in ALL_CASES]
assert len(ids) == len(set(ids)), "Duplicate IDs!"
print(f"DEBUG: {len(ALL_CASES)} total cases")
print(f"  property={len(PROPERTY_CASES)} booking={len(BOOKING_CASES)} payment={len(PAYMENT_CASES)} review={len(REVIEW_CASES)}")
print(f"  user={len(USER_CASES)} content={len(CONTENT_CASES)} general={len(GENERAL_CASES)} ambiguous={len(AMBIGUOUS_CASES)}")
assert len(ALL_CASES) == 100, f"Expected 100 cases, got {len(ALL_CASES)}"

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(
    json.dumps(ALL_CASES, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(f"✅ Generated {len(ALL_CASES)} test cases → {OUTPUT}")

# Category summary
from collections import Counter
cats = Counter(c["category"] for c in ALL_CASES)
print("\nCategory breakdown:")
for cat, count in sorted(cats.items()):
    print(f"  {cat}: {count}")
