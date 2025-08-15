import asyncio
from typing import Dict, Any, List, Callable

from ..interfaces import ToolInterface
from . import tools


class ToolExecutor(ToolInterface):
    """Central tool execution coordinator."""

    def __init__(self):
        self.registered_tools: Dict[str, Callable] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register all tools exposed by the tools package."""
        for name in getattr(tools, "__all__", []):
            self.registered_tools[name] = getattr(tools, name)

    async def execute(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given parameters"""
        if tool_name not in self.registered_tools:
            return {"error": f"Tool {tool_name} not found"}

        tool = self.registered_tools[tool_name]
        try:
            if asyncio.iscoroutinefunction(tool):
                result = await tool(**parameters)
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, lambda: tool(**parameters)
                )
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_available_tools(self) -> List[str]:
        """Return list of available tool names"""
        return list(self.registered_tools.keys())

    def register_tool(self, name: str, tool_func: Callable) -> None:
        """Register a new tool"""
        self.registered_tools[name] = tool_func
