import logging
import re


logger = logging.getLogger(__name__)


class AuthIdentityService:
    DEV_TOKEN_PATTERN = re.compile(r"^Bearer\s+dev-token-(\d+)$", re.IGNORECASE)

    def __init__(self, backend_api_service):
        self.backend_api_service = backend_api_service

    def resolve_user_context(self, auth_header, fallback_user_context=None):
        token_user_id = self._parse_dev_token_user_id(auth_header)
        if token_user_id is not None:
            return self._build_user_context_from_backend(token_user_id)
        return self._normalize_fallback_user_context(fallback_user_context)

    def _build_user_context_from_backend(self, user_id):
        user_result = self.backend_api_service.get_user_detail(user_id)
        user = user_result.get("item") or {}
        role = str(user.get("role") or "").strip().upper()
        context = {
            "id": user.get("id"),
            "username": user.get("username"),
            "role": role,
        }

        if role == "MERCHANT":
            merchant_id = self._lookup_merchant_id(user_id)
            if merchant_id is not None:
                context["merchantId"] = merchant_id

        return context

    def _lookup_merchant_id(self, user_id):
        try:
            merchant_result = self.backend_api_service.get_merchant_by_user_id(user_id)
        except Exception:
            logger.warning("merchant_lookup_failed user_id=%s", user_id, exc_info=True)
            return None
        merchant = merchant_result.get("item") or {}
        merchant_id = merchant.get("id")
        return merchant_id if merchant_id not in {"", None} else None

    def _normalize_fallback_user_context(self, user_context):
        if not user_context:
            return {}
        normalized = {
            "id": user_context.get("id"),
            "username": user_context.get("username"),
            "role": str(user_context.get("role") or "").strip().upper(),
        }
        if user_context.get("merchantId") not in {None, ""}:
            normalized["merchantId"] = user_context.get("merchantId")
        return normalized

    def _parse_dev_token_user_id(self, auth_header):
        if not auth_header:
            return None
        matched = self.DEV_TOKEN_PATTERN.match(str(auth_header).strip())
        if not matched:
            return None
        return int(matched.group(1))
