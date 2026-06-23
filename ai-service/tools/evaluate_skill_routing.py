import json
import os
import sys
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT_DIR / "tests" / "fixtures" / "skill_routing_cases.json"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv(override=True)

from services.skill_service import SkillService


class DummyToolService:
    def __init__(self, allowed_tool_names):
        self.allowed_tool_names = tuple(allowed_tool_names)

    def get_allowed_tool_names(self, user_context=None, mode=None):
        return self.allowed_tool_names


def load_cases():
    with FIXTURE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


# Low-risk fallback tools — intentionally exposed on all queries
LOW_RISK_FALLBACK_TOOLS = frozenset((
    "search_properties",
    "get_top_properties",
    "tavily_search",
    "get_weather",
    "get_current_time",
    "geocode_location",
))


def evaluate_case(case, use_llm=False):
    service = SkillService(
        DummyToolService(case["allowed_tools"]),
        intent_router=_build_llm_router() if use_llm else None,
    )
    route = service.resolve(case["message"])

    actual_skills = list(route.active_skill_names)
    actual_tools = list(route.tool_names)
    expected_skills = list(case["expected_skills"])
    expected_tools = list(case["expected_tools"])
    should_call = bool(case.get("should_call_tools", True))

    # When no domain tools are expected, low-risk fallback tools are acceptable
    if not expected_tools and not should_call:
        tool_ok = all(t in LOW_RISK_FALLBACK_TOOLS for t in actual_tools)
        skill_ok = not actual_skills
    else:
        tool_ok = set(actual_tools) == set(expected_tools)
        skill_ok = set(actual_skills) == set(expected_skills)

    return {
        "id": case["id"],
        "category": case.get("category") or "unknown",
        "message": case["message"],
        "expected_skills": expected_skills,
        "actual_skills": actual_skills,
        "expected_tools": expected_tools,
        "actual_tools": actual_tools,
        "skill_exact_match": skill_ok,
        "tool_exact_match": tool_ok,
        "should_call_tools": should_call,
        "tool_exposed": bool(actual_tools),
    }


def _build_llm_router():
    from services.intent_router import IntentRouter, KeyPool

    # Try comma-separated pool first, then single key
    pool = os.getenv("XIAOMI_API_KEYS", "").strip()
    if pool:
        keys = [k.strip() for k in pool.split(",") if k.strip()]
        if keys:
            base_url = os.getenv("XIAOMI_BASE_URL", "https://api.xiaomimimo.com/v1")
            model = os.getenv("XIAOMI_MODEL", "mimo-v2-flash")
            return IntentRouter(
                key_pool=KeyPool(keys),
                base_url=base_url,
                model=model,
            )

    api_key = os.getenv("XIAOMI_API_KEY") or os.getenv("AI_ROUTER_API_KEY")
    base_url = os.getenv("XIAOMI_BASE_URL", "https://api.xiaomimimo.com/v1")
    model = os.getenv("XIAOMI_MODEL", "mimo-v2-flash")
    if not api_key:
        return None
    return IntentRouter(api_key=api_key, base_url=base_url, model=model)


def ratio(numerator, denominator):
    return 0.0 if denominator == 0 else numerator / denominator


def print_summary(results):
    total = len(results)
    skill_exact = sum(1 for item in results if item["skill_exact_match"])
    tool_exact = sum(1 for item in results if item["tool_exact_match"])

    domain_cases = [item for item in results if item["should_call_tools"]]
    domain_tool_exact = sum(1 for item in domain_cases if item["tool_exact_match"])
    domain_skill_exact = sum(1 for item in domain_cases if item["skill_exact_match"])

    should_not_call = [item for item in results if not item["should_call_tools"]]
    no_tool_ok = sum(1 for item in should_not_call if item["tool_exact_match"])

    category_stats = defaultdict(lambda: {"total": 0, "skill_exact": 0, "tool_exact": 0})
    for item in results:
        stats = category_stats[item["category"]]
        stats["total"] += 1
        stats["skill_exact"] += int(item["skill_exact_match"])
        stats["tool_exact"] += int(item["tool_exact_match"])

    print(f"fixture={FIXTURE_PATH}")
    print(f"total_cases={total}")
    print(f"")
    print(f"--- Overall (all cases) ---")
    print(f"skill_exact_match={skill_exact}/{total} ({ratio(skill_exact, total):.1%})")
    print(f"tool_exact_match={tool_exact}/{total} ({ratio(tool_exact, total):.1%})")
    print(f"")
    print(f"--- Domain-only (ignore fallback-intended cases) ---")
    print(f"domain_skill_exact={domain_skill_exact}/{len(domain_cases)} ({ratio(domain_skill_exact, len(domain_cases)):.1%})")
    print(f"domain_tool_exact={domain_tool_exact}/{len(domain_cases)} ({ratio(domain_tool_exact, len(domain_cases)):.1%})")
    print(f"")
    print(f"--- Fallback-intended cases (Content/Chat/General) ---")
    print(f"passed={no_tool_ok}/{len(should_not_call)} ({ratio(no_tool_ok, len(should_not_call)):.1%})")
    print("")
    print("category_breakdown:")
    for category in sorted(category_stats):
        stats = category_stats[category]
        print(
            f"  - {category}: "
            f"skill {stats['skill_exact']}/{stats['total']} ({ratio(stats['skill_exact'], stats['total']):.1%}), "
            f"tool {stats['tool_exact']}/{stats['total']} ({ratio(stats['tool_exact'], stats['total']):.1%})"
        )


def print_failures(results):
    failures = [item for item in results if not item["skill_exact_match"] or not item["tool_exact_match"]]
    if not failures:
        print("")
        print("failures: none")
        return

    print("")
    print("failures:")
    for item in failures:
        print(f"- id={item['id']} category={item['category']}")
        print(f"  message={item['message']}")
        if not item["skill_exact_match"]:
            print(f"  expected_skills={item['expected_skills']}")
            print(f"  actual_skills={item['actual_skills']}")
        if not item["tool_exact_match"]:
            print(f"  expected_tools={item['expected_tools']}")
            print(f"  actual_tools={item['actual_tools']}")


def main():
    use_llm = "--llm" in sys.argv
    mode = "LLM" if use_llm else "keyword"
    print(f"=== Routing mode: {mode} ===\n")

    cases = load_cases()
    results = [evaluate_case(case, use_llm=use_llm) for case in cases]
    print_summary(results)
    print_failures(results)


if __name__ == "__main__":
    main()
