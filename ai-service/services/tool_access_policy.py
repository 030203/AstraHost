class ToolAccessPolicy:
    def __init__(self, backend_api_service):
        self.backend_api_service = backend_api_service

    def resolve_role(self, user_context):
        if not user_context:
            return ""
        return str(user_context.get("role") or "").strip().upper()

    def is_role_allowed(self, spec, user_context):
        if spec.allowed_roles is None:
            return True
        role = self.resolve_role(user_context)
        return bool(role) and role in spec.allowed_roles

    def current_user_id(self, user_context):
        user_id = self.to_int((user_context or {}).get("id"))
        if user_id is None:
            raise ValueError("当前会话缺少 userId，无法执行该操作。")
        return user_id

    def current_merchant_id(self, user_context):
        merchant_id = self.to_int((user_context or {}).get("merchantId"))
        if merchant_id is None:
            raise ValueError("当前会话缺少 merchantId，无法执行该操作。")
        return merchant_id

    def assert_access(self, allowed, message):
        if not allowed:
            raise ValueError(message)

    def to_int(self, value):
        try:
            if value is None or value == "":
                return None
            return int(value)
        except (TypeError, ValueError):
            return None

    def get_path(self, payload, *path):
        current = payload
        for key in path:
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return current

    def unwrap_item(self, result):
        if isinstance(result, dict) and "item" in result:
            return result.get("item") or {}
        return result if isinstance(result, dict) else {}

    def unwrap_items(self, result):
        if isinstance(result, dict):
            items = result.get("items")
            if isinstance(items, list):
                return items
        return []

    def set_items(self, result, items):
        updated = dict(result)
        updated["items"] = items
        updated["count"] = len(items)
        if "total" in updated:
            updated["total"] = len(items)
        return updated

    def filter_items(self, result, predicate):
        if not isinstance(result, dict):
            return result
        items = self.unwrap_items(result)
        if not items:
            return result
        return self.set_items(result, [item for item in items if predicate(item)])

    def booking_user_id(self, item):
        return self.to_int(self.get_path(item, "user", "id"))

    def booking_merchant_id(self, item):
        return self.to_int(self.get_path(item, "property", "merchantId"))

    def payment_user_id(self, item):
        return self.to_int(self.get_path(item, "booking", "user", "id"))

    def payment_merchant_id(self, item):
        return self.to_int(self.get_path(item, "booking", "property", "merchantId"))

    def review_user_id(self, item):
        return self.to_int(self.get_path(item, "user", "id"))

    def review_merchant_id(self, item):
        return self.to_int(self.get_path(item, "property", "merchantId"))

    def notification_user_id(self, item):
        return self.to_int(self.get_path(item, "user", "id"))

    def merchant_owner_user_id(self, item):
        return self.to_int(self.get_path(item, "user", "id"))

    def coupon_merchant_id(self, item):
        return self.to_int(self.get_path(item, "merchant", "id"))

    def can_access_booking(self, item, user_context):
        role = self.resolve_role(user_context)
        if role == "ADMIN":
            return True
        if role == "USER":
            return self.booking_user_id(item) == self.current_user_id(user_context)
        if role == "MERCHANT":
            return self.booking_merchant_id(item) == self.current_merchant_id(user_context)
        return False

    def can_access_payment(self, item, user_context):
        role = self.resolve_role(user_context)
        if role == "ADMIN":
            return True
        if role == "USER":
            return self.payment_user_id(item) == self.current_user_id(user_context)
        if role == "MERCHANT":
            return self.payment_merchant_id(item) == self.current_merchant_id(user_context)
        return False

    def can_access_review_action(self, item, user_context):
        role = self.resolve_role(user_context)
        if role == "ADMIN":
            return True
        if role == "MERCHANT":
            return self.review_merchant_id(item) == self.current_merchant_id(user_context)
        return False

    def can_access_review_by_booking(self, item, user_context):
        role = self.resolve_role(user_context)
        if role == "ADMIN":
            return True
        if role == "USER":
            return self.review_user_id(item) == self.current_user_id(user_context)
        if role == "MERCHANT":
            return self.review_merchant_id(item) == self.current_merchant_id(user_context)
        return False

    def can_access_notification(self, item, user_context):
        role = self.resolve_role(user_context)
        if role == "ADMIN":
            return True
        if role in {"USER", "MERCHANT"}:
            return self.notification_user_id(item) == self.current_user_id(user_context)
        return False

    def ensure_property_owned_by_current_merchant(self, property_id, user_context):
        merchant_id = self.current_merchant_id(user_context)
        result = self.backend_api_service.get_property_detail(property_id)
        property_item = self.get_path(self.unwrap_item(result), "property") or {}
        owner_merchant_id = self.to_int(property_item.get("merchantId"))
        self.assert_access(
            owner_merchant_id == merchant_id,
            "当前商家无权访问该房源。",
        )

    def ensure_notification_owned(self, notification_id, user_context):
        if self.resolve_role(user_context) == "ADMIN":
            return
        notifications = self.backend_api_service.list_notifications(
            user_id=self.current_user_id(user_context),
            unread_only=False,
        )
        notification_ids = {self.to_int(item.get("id")) for item in self.unwrap_items(notifications)}
        self.assert_access(
            self.to_int(notification_id) in notification_ids,
            "当前用户无权操作该通知。",
        )

    def list_current_merchant_property_ids(self, user_context):
        merchant_id = self.current_merchant_id(user_context)
        result = self.backend_api_service.list_properties(merchant_id=merchant_id)
        return [
            self.to_int(item.get("id"))
            for item in self.unwrap_items(result)
            if self.to_int(item.get("id")) is not None
        ]
