import requests


class TavilySearchTool:
    name = "tavily_search"
    description = "Search the web for current information such as travel trends, destination guides, local recommendations, or general facts."
    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to send to Tavily.",
            }
        },
        "required": ["query"],
    }

    def __init__(self, config):
        self.config = config

    def execute(self, tool_input):
        api_key = self.config.tavily_api_key()
        if not api_key:
            return {"error": "Missing TAVILY_API_KEY."}

        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": tool_input.get("query", ""),
                "search_depth": "basic",
                "max_results": 5,
                "include_answer": True,
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("results", [])[:5]:
            results.append(
                {
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "content": item.get("content"),
                }
            )

        return {
            "query": tool_input.get("query", ""),
            "answer": data.get("answer"),
            "results": results,
        }
