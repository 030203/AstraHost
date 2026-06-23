import logging
from dataclasses import dataclass

from skills import build_customer_service_skills

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SkillRoute:
    active_skill_names: tuple[str, ...]
    tool_names: tuple[str, ...]
    system_prompt: str


class SkillService:
    LOW_RISK_FALLBACK_TOOL_NAMES = (
        "search_properties",
        "get_top_properties",
        "tavily_search",
        "get_weather",
        "get_current_time",
        "geocode_location",
    )
    WEATHER_HINTS = (
        "天气",
        "气温",
        "温度",
        "下雨",
        "晴",
        "阴",
        "雪",
        "风力",
        "穿什么",
        "适不适合出行",
        "weather",
        "temperature",
    )
    EXTERNAL_INFO_HINTS = (
        "攻略",
        "热门",
        "趋势",
        "附近",
        "周边",
        "推荐",
        "搜索",
        "查一下",
        "搜一下",
        "帮我查",
        "tavily",
        "search",
    )
    TIME_HINTS = (
        "几点",
        "当前时间",
        "现在时间",
        "当地时间",
        "时区",
        "timezone",
        "time",
        "date",
        "日期",
    )
    LOCATION_HINTS = (
        "地址",
        "位置",
        "经纬度",
        "坐标",
        "在哪",
        "地理位置",
        "路线",
        "导航",
        "地图",
        "location",
        "address",
        "coordinate",
        "geo",
    )

    # === SECTION: lifecycle ===
    def __init__(self, tool_service, intent_router=None):
        self.tool_service = tool_service
        self.skills = build_customer_service_skills()
        self.intent_router = intent_router  # optional LLM-based router

    # === SECTION: routing ===
    def resolve(self, message, user_context=None):
        normalized = (message or "").strip()
        if not normalized:
            return SkillRoute(
                active_skill_names=(),
                tool_names=(),
                system_prompt="",
            )

        # Try LLM-based routing first
        if self.intent_router is not None:
            route = self._resolve_via_llm(normalized, user_context)
            if route is not None:
                return route

        # Fall back to keyword-based routing
        return self._resolve_via_keywords(normalized, user_context)

    def _resolve_via_llm(self, message, user_context):
        """Attempt LLM-based intent routing. Returns SkillRoute or None on failure."""
        try:
            task, domain, resources = self.intent_router.route(message)
        except Exception as exc:
            logger.warning("LLM routing failed, falling back to keywords: %s", exc)
            return None

        logger.info("LLM route: task=%s domain=%s message=%s", task, domain, message[:50])

        if task in ("Content", "Chat"):
            # No business domain tools for content/chat
            tool_names = []
            active_skill_names = ()
            system_prompt = ""
        elif task in ("Business",) and resources:
            active_skill_names = resources["skill_names"]
            tool_names = list(resources["tool_names"])
            system_prompt = resources["system_prompt"]
        elif task == "Query":
            if resources:
                # Has a specific business domain
                active_skill_names = resources["skill_names"]
                tool_names = list(resources["tool_names"])
                system_prompt = resources["system_prompt"]
            else:
                # General query (weather, search, etc.) — no domain tools
                active_skill_names = ()
                tool_names = []
                system_prompt = ""
        else:
            return None  # fallback

        # Filter by user permissions
        allowed_tool_names = set(
            self.tool_service.get_allowed_tool_names(user_context=user_context)
        )
        tool_names = [t for t in tool_names if t in allowed_tool_names]

        # Append hint tools (weather, time, geo, search)
        self._append_hint_tools(message, tool_names, allowed_tool_names)

        # Fallback: if no tools at all, expose low-risk tools
        if not active_skill_names and not tool_names:
            tool_names = [
                t for t in self.LOW_RISK_FALLBACK_TOOL_NAMES
                if t in allowed_tool_names
            ]

        return SkillRoute(
            active_skill_names=tuple(active_skill_names),
            tool_names=tuple(tool_names),
            system_prompt=system_prompt,
        )

    def _resolve_via_keywords(self, message, user_context):
        """Original keyword-based routing."""
        normalized = (message or "").strip()
        active_resolutions = [
            skill.resolve(normalized)
            for skill in self.skills
            if skill.matches(normalized)
        ]

        tool_names = []
        prompt_parts = []
        active_skill_names = []
        for resolution in active_resolutions:
            active_skill_names.append(resolution.name)
            prompt_parts.append(resolution.system_prompt)
            for tool_name in resolution.tool_names:
                if tool_name not in tool_names:
                    tool_names.append(tool_name)

        allowed_tool_names = set(
            self.tool_service.get_allowed_tool_names(user_context=user_context)
        )
        tool_names = [tool_name for tool_name in tool_names if tool_name in allowed_tool_names]

        self._append_hint_tools(normalized, tool_names, allowed_tool_names)

        if not active_resolutions and not tool_names:
            tool_names = [
                tool_name
                for tool_name in self.LOW_RISK_FALLBACK_TOOL_NAMES
                if tool_name in allowed_tool_names
            ]

        return SkillRoute(
            active_skill_names=tuple(active_skill_names),
            tool_names=tuple(tool_names),
            system_prompt="\n".join(part for part in prompt_parts if part),
        )

    def _append_hint_tools(self, message, tool_names, allowed_tool_names):
        lowered = (message or "").lower()

        if any(hint in lowered for hint in self.WEATHER_HINTS):
            self._append_tool_if_allowed("get_weather", tool_names, allowed_tool_names)

        if any(hint in lowered for hint in self.EXTERNAL_INFO_HINTS):
            self._append_tool_if_allowed("tavily_search", tool_names, allowed_tool_names)

        if any(hint in lowered for hint in self.TIME_HINTS):
            self._append_tool_if_allowed("get_current_time", tool_names, allowed_tool_names)

        if any(hint in lowered for hint in self.LOCATION_HINTS):
            self._append_tool_if_allowed("geocode_location", tool_names, allowed_tool_names)

    @staticmethod
    def _append_tool_if_allowed(tool_name, tool_names, allowed_tool_names):
        if tool_name in allowed_tool_names and tool_name not in tool_names:
            tool_names.append(tool_name)

    def describe(self):
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "keywords": list(getattr(skill, "keywords", ())),
                "tool_names": list(getattr(skill, "tool_names", ())),
            }
            for skill in self.skills
        ]
