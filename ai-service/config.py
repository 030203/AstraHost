import os

from dotenv import load_dotenv


load_dotenv(override=True)
if os.getenv("ANTHROPIC_BASE_URL"):
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)


class AppConfig:
    @staticmethod
    def app_host():
        return os.getenv("APP_HOST") or os.getenv("AI_SERVICE_HOST", "0.0.0.0")

    @staticmethod
    def app_port():
        return int(os.getenv("APP_PORT") or os.getenv("AI_SERVICE_PORT", "5001"))

    @staticmethod
    def app_debug():
        return (os.getenv("APP_DEBUG") or os.getenv("AI_SERVICE_DEBUG", "false")).lower() == "true"

    @staticmethod
    def live_reload_enabled():
        return os.getenv("APP_DEV_LIVE_RELOAD", "true").lower() == "true"

    @staticmethod
    def anthropic_base_url():
        return os.getenv("ANTHROPIC_BASE_URL")

    @staticmethod
    def anthropic_api_key():
        return os.getenv("ANTHROPIC_API_KEY")

    @staticmethod
    def anthropic_model():
        return os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")

    @staticmethod
    def anthropic_max_tokens():
        return int(os.getenv("ANTHROPIC_MAX_TOKENS", "1024"))

    @staticmethod
    def anthropic_timeout():
        return int(os.getenv("ANTHROPIC_TIMEOUT", "60"))

    @staticmethod
    def tavily_api_key():
        return os.getenv("TAVILY_API_KEY")

    @staticmethod
    def openweather_api_key():
        return os.getenv("OPENWEATHER_API_KEY")

    @staticmethod
    def booking_service_base_url():
        return os.getenv("BOOKING_SERVICE_BASE_URL", "http://127.0.0.1:8080/api")

    @staticmethod
    def frontend_base_url():
        return os.getenv("FRONTEND_BASE_URL", "http://localhost:5400")

    @staticmethod
    def http_timeout():
        return int(os.getenv("HTTP_TIMEOUT", "20"))

    @staticmethod
    def http_user_agent():
        return os.getenv("HTTP_USER_AGENT", "RoomOS-AI-Service/1.0")

    @staticmethod
    def request_id_header():
        return os.getenv("REQUEST_ID_HEADER", "X-Request-ID")

    @staticmethod
    def log_level():
        return os.getenv("LOG_LEVEL", "INFO").upper()

    @staticmethod
    def tool_call_max_steps():
        return int(os.getenv("TOOL_CALL_MAX_STEPS", "6"))

    @staticmethod
    def action_confirmation_ttl_seconds():
        return int(os.getenv("ACTION_CONFIRMATION_TTL_SECONDS", "300"))

    @staticmethod
    def allow_mock_user_context():
        return os.getenv("ALLOW_MOCK_USER_CONTEXT", "true").lower() == "true"

    @staticmethod
    def conversation_ttl_seconds():
        return int(os.getenv("CONVERSATION_TTL_SECONDS", "86400"))

    @staticmethod
    def conversation_max_messages():
        return int(os.getenv("CONVERSATION_MAX_MESSAGES", "20"))

    @staticmethod
    def conversation_store_path():
        return os.getenv("CONVERSATION_STORE_PATH", "")

    @staticmethod
    def xiaomi_api_key():
        """Return the primary Xiaomi API key (backward-compatible)."""
        return os.getenv("XIAOMI_API_KEY") or os.getenv("AI_ROUTER_API_KEY")

    @staticmethod
    def xiaomi_api_keys():
        """Return a list of all Xiaomi API keys from XIAOMI_API_KEYS.

        Supports comma-separated list in a single env var.
        Falls back to [xiaomi_api_key()] if XIAOMI_API_KEYS is not set.
        """
        pool = os.getenv("XIAOMI_API_KEYS", "").strip()
        if pool:
            keys = [k.strip() for k in pool.split(",") if k.strip()]
            if keys:
                return keys
        primary = os.getenv("XIAOMI_API_KEY") or os.getenv("AI_ROUTER_API_KEY")
        return [primary] if primary else []

    @staticmethod
    def xiaomi_base_url():
        return os.getenv("XIAOMI_BASE_URL", "https://api.xiaomimimo.com/v1")

    @staticmethod
    def xiaomi_model():
        return os.getenv("XIAOMI_MODEL", "mimo-v2-flash")
