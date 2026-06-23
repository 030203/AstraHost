"""
Two-layer LLM-based intent routing.

Layer 1: Task Router — Business / Query / Content / Chat
Layer 2: Domain Router — Property / Booking / Payment / Review / User

Uses Xiaomi MiMo API (OpenAI-compatible) with a key pool for high availability.
"""

import json
import logging
import re
import time
import threading

import requests

logger = logging.getLogger(__name__)


class KeyPool:
    """Thread-safe API key pool with round-robin and cooldown support.

    On 429 responses, the offending key is cooled down for cooldown_seconds
    and the pool automatically tries the next available key.
    """

    def __init__(self, keys, cooldown_seconds=60):
        if not keys:
            raise ValueError("KeyPool requires at least one API key")
        self._keys = list(keys)
        self._cooldown_seconds = cooldown_seconds
        self._cooldowns = {}  # key -> expiry unix timestamp
        self._lock = threading.Lock()
        self._index = 0

    @property
    def available_count(self):
        """Return number of keys not currently in cooldown."""
        now = time.time()
        with self._lock:
            return sum(
                1 for k in self._keys
                if k not in self._cooldowns or self._cooldowns[k] < now
            )

    def get_key(self):
        """Return the next available key (round-robin, skipping cooldown).

        If all keys are in cooldown, returns the next one anyway (call will
        likely fail, but allows cooldowns to be re-triggered with fresh timing).
        """
        with self._lock:
            now = time.time()
            for _ in range(len(self._keys)):
                key = self._keys[self._index]
                self._index = (self._index + 1) % len(self._keys)
                if key not in self._cooldowns or self._cooldowns[key] < now:
                    return key
            # All keys in cooldown — still hand one out
            key = self._keys[self._index]
            self._index = (self._index + 1) % len(self._keys)
            return key

    def mark_cooldown(self, key):
        """Put a key into cooldown so it won't be returned by get_key()."""
        expiry = time.time() + self._cooldown_seconds
        with self._lock:
            self._cooldowns[key] = expiry

TASK_CLASSIFICATION_PROMPT = """You are an intent classifier for a hotel booking customer service system.
Classify the user's message into exactly ONE of these categories.

Categories:
- Business: User wants to perform an action that changes system state.
  Examples: book a room, cancel an order, check in, check out, reply to a review,
  mark notification as read, process a payment, create a payment.
  Key pattern: the user is asking to DO something on the platform.

- Query: User wants to look up, search, or check information.
  Examples: check booking status, search for properties, view room types,
  check payment status, view reviews, check notification count, check coupons,
  search for travel guides/info, check weather forecast, look up locations.

- Content: User wants to write, polish, or generate standalone text content
  WITHOUT performing a platform action.
  Examples: draft a customer service reply template, polish text, compose
  a response message, write a refund apology.

- Chat: General greeting, chit-chat, or questions completely unrelated
  to the platform or travel.
  Examples: hello, hi, what can you do, tell me a joke.

Key rules:
- "帮我回复评价/差评/评论" = Business (it's performing the reply action on the platform)
- "帮我写一段回复/文案" = Content (writing standalone text, not executing the action)
- "天气" query = Query (checking weather is looking up information)
- "攻略" = Query (searching for information)
- "帮我查一下" or "查一下" = Query
- "帮我取消" or "帮我订" or "帮我办理" = Business
- "帮我润色" or "帮我写" = Content (if not tied to a specific platform action)
- If unsure, prefer Query over Chat.

Respond with ONLY valid JSON: {"task": "Business"}"""

DOMAIN_CLASSIFICATION_PROMPT = """You are a domain classifier for a hotel booking customer service system.
Classify the user's message into exactly ONE of these business domains.
If the message does not clearly belong to any business domain, respond with "General".

Domains:
- Property: About properties/hotels, room types, facilities, locations, prices,
  accommodation search, recommendations.
  Keywords: 房源, 酒店, 民宿, 房型, 房价, 设施, 位置, 推荐.
- Booking: About orders/reservations, check-in, check-out, cancellations, booking status.
  Keywords: 订单, 预订, 入住, 离店, 取消, 退房.
- Payment: About payments, transactions, refunds, payment methods, payment status.
  Keywords: 支付, 付款, 交易, 退款, 支付单.
- Review: About reviews, ratings, comments, feedback.
  Keywords: 评价, 评论, 评分, 差评, 好评, 回复.
- User: About user accounts, profiles, notifications, coupons, merchants, settings.
  Keywords: 用户, 账号, 通知, 消息, 优惠券, 商家, 资料.
- General: Queries that are NOT tied to a specific business domain.
  Examples: checking weather, searching for travel guides/visa info, general
  travel tips, knowledge questions, chit-chat.

Rules:
- "评分 4.5" is filtering properties by rating → Property, not Review.
- "订单 1024 的支付成功了吗" is about payment status → Payment.
- "搜索日本签证攻略" → General (external search, no business domain).
- "杭州明天天气" → General (weather query, no business domain).
- A message can mention multiple domains; pick the PRIMARY one.
- If truly unsure or the query is non-business, choose General.

Respond with ONLY valid JSON: {"domain": "Booking"}"""

DOMAIN_RESOURCES = {
    "Property": {
        "skill_names": ("property_support",),
        "tool_names": (
            "list_properties",
            "search_properties",
            "get_property_detail",
            "get_top_properties",
            "list_room_types",
            "get_room_type_detail",
            "get_active_room_types",
        ),
        "system_prompt": (
            "This request is about properties or room types. "
            "Use property and room tools to confirm city, price, rating, "
            "facilities, room types and details."
        ),
    },
    "Booking": {
        "skill_names": ("booking_support",),
        "tool_names": (
            "list_bookings",
            "get_booking_detail",
            "get_booking_by_number",
            "create_booking",
            "cancel_booking",
            "check_in_booking",
            "check_out_booking",
        ),
        "system_prompt": (
            "This request is about bookings. "
            "Use booking tools to confirm status, booking number and "
            "check-in or check-out timing. "
            "Only use action tools when the user explicitly asks to perform the action."
        ),
    },
    "Payment": {
        "skill_names": ("payment_support",),
        "tool_names": (
            "list_payments",
            "get_payment_detail",
            "get_payment_by_number",
            "create_payment",
            "process_payment",
        ),
        "system_prompt": (
            "This request is about payments. "
            "Use payment tools first to confirm payment status, "
            "payment number, amount and related booking. "
            "Only use action tools when the user explicitly asks "
            "to create or confirm a payment."
        ),
    },
    "Review": {
        "skill_names": ("review_support",),
        "tool_names": (
            "list_reviews",
            "get_review_detail",
            "get_review_by_booking",
            "reply_review",
        ),
        "system_prompt": (
            "This request is about reviews. "
            "Use review tools first to confirm rating, review content "
            "and related booking. "
            "Only use the reply tool when the user explicitly requests a reply."
        ),
    },
    "User": {
        "skill_names": (
            "user_support",
            "notification_support",
            "coupon_support",
            "merchant_support",
        ),
        "tool_names": (
            "list_users",
            "get_user_detail",
            "list_notifications",
            "get_unread_notification_count",
            "mark_notification_read",
            "mark_all_notifications_read",
            "list_coupons",
            "get_coupon_detail",
            "list_merchants",
            "get_merchant_detail",
            "get_merchant_by_user",
        ),
        "system_prompt": (
            "This request is about user accounts, notifications, "
            "coupons or merchants. Use the appropriate tools to "
            "confirm user profile, notification status, coupon "
            "details or merchant information."
        ),
    },
}


class IntentRouter:
    """Two-layer LLM-based intent router using Xiaomi MiMo API.

    Supports an API key pool with round-robin and automatic 429 cooldown.

    Args:
        api_key: Single API key (string) — wraps into a KeyPool.
        key_pool: Pre-built KeyPool instance (takes precedence over api_key).
        base_url: API endpoint base URL.
        model: Model name.
    """

    def __init__(self, api_key=None, key_pool=None, base_url=None, model=None):
        self.base_url = (base_url or "https://api.xiaomimimo.com/v1").rstrip("/")
        self.model = model or "mimo-v2-flash"
        if key_pool is not None:
            self.key_pool = key_pool
        elif api_key:
            self.key_pool = KeyPool([api_key])
        else:
            raise ValueError("Either api_key or key_pool is required")

    def route(self, message):
        """Classify a user message.

        Returns:
            (task, domain, resources) on success.
            task: "Business" | "Query" | "Content" | "Chat"
            domain: str or None (None for Content/Chat)
            resources: dict or None

        Raises:
            ValueError: if LLM call fails or response is unparseable.
        """
        task = self._classify_task(message)
        domain = None
        resources = None

        if task in ("Business", "Query"):
            domain = self._classify_domain(message)
            resources = DOMAIN_RESOURCES.get(domain)

        return task, domain, resources

    def _classify_task(self, message):
        """Returns "Business", "Query", "Content", or "Chat"."""
        text = self._llm_call(TASK_CLASSIFICATION_PROMPT, message)
        return self._extract_json_value(text, "task", "Query")

    def _classify_domain(self, message):
        """Returns a domain name string, or None for General."""
        text = self._llm_call(DOMAIN_CLASSIFICATION_PROMPT, message)
        domain = self._extract_json_value(text, "domain", None)
        if not domain:
            return None
        # "General" means no specific business domain
        if domain.lower() == "general":
            return None
        if domain not in DOMAIN_RESOURCES:
            # Normalize case — accept "property" → "Property"
            for key in DOMAIN_RESOURCES:
                if key.lower() == domain.lower():
                    return key
            logger.warning("Unknown domain from LLM: %s, falling back to None", domain)
            return None
        return domain

    def _llm_call(self, system_prompt, user_message):
        """Make a chat completion call through the key pool.

        Automatically retries with the next available key on 429.
        Returns the response text.
        Raises ValueError if all keys are exhausted or response is unparseable.
        """
        max_attempts = max(len(self.key_pool._keys), 3) * 2
        last_error = None

        for attempt in range(max_attempts):
            key = self.key_pool.get_key()
            masked_key = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "***"

            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "api-key": key,
                        "Authorization": f"Bearer {key}",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message},
                        ],
                        "temperature": 0.1,
                        "max_tokens": 50,
                    },
                    timeout=10,
                )

                if response.status_code == 429:
                    logger.warning(
                        "Xiaomi key %s hit 429 — cooling down for %ds, attempt %d/%d",
                        masked_key, self.key_pool._cooldown_seconds,
                        attempt + 1, max_attempts,
                    )
                    self.key_pool.mark_cooldown(key)
                    if self.key_pool.available_count == 0:
                        logger.warning("All Xiaomi keys in cooldown, waiting before retry")
                        time.sleep(3)
                    continue

                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return content or ""

            except requests.RequestException as exc:
                status = getattr(exc.response, "status_code", None)
                if status == 429:
                    logger.warning(
                        "Xiaomi key %s hit 429 (exception path) — cooling down",
                        masked_key,
                    )
                    self.key_pool.mark_cooldown(key)
                    if self.key_pool.available_count == 0:
                        time.sleep(3)
                    continue
                last_error = exc
                logger.error(
                    "Xiaomi API request failed key=%s status=%s: %s",
                    masked_key, status, exc,
                )
                # Non-429 error — still try next key
                continue

            except (KeyError, IndexError, json.JSONDecodeError) as exc:
                last_error = exc
                logger.error(
                    "Xiaomi API response parse failed key=%s: %s",
                    masked_key, exc,
                )
                continue

        raise ValueError(
            f"LLM classification failed after {max_attempts} attempts: "
            f"{last_error or 'all keys exhausted / in cooldown'}"
        )

    @staticmethod
    def _extract_json_value(text, key, default):
        """Extract a JSON value from text with robust parsing."""
        if not text:
            return default

        # Try to find {...} block
        brace_match = re.search(r"\{[^{}]*\}", text)
        if brace_match:
            try:
                data = json.loads(brace_match.group())
                return data.get(key, default)
            except (json.JSONDecodeError, TypeError):
                pass

        # Try the entire text as JSON
        stripped = text.strip()
        if stripped.startswith("{"):
            try:
                data = json.loads(stripped)
                return data.get(key, default)
            except (json.JSONDecodeError, TypeError):
                pass

        # Try matching key: value patterns
        pattern = re.compile(rf'"{key}"\s*:\s*"([^"]+)"', re.IGNORECASE)
        match = pattern.search(stripped)
        if match:
            return match.group(1)

        return default
