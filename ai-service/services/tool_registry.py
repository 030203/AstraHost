class ToolRegistry:
    def __init__(self, tools):
        self.tools = {tool.name: tool for tool in tools}

    def definitions(self):
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self.tools.values()
        ]

    def execute(self, name, tool_input):
        tool = self.tools.get(name)
        if not tool:
            return {"error": f"Unknown tool: {name}"}
        return tool.execute(tool_input or {})
