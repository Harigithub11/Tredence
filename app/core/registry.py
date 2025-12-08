"""Tool Registry

Centralized registry for workflow tools and functions.
Provides decorator-based registration and tool discovery.
"""

from typing import Callable, Dict, Any, Optional, List
from functools import wraps
import asyncio
import inspect


class ToolRegistry:
    """
    Registry for workflow tools/functions.

    Tools are Python functions that can be used in workflow nodes.
    The registry maintains metadata about each tool for discovery and validation.
    """

    def __init__(self):
        """Initialize empty registry"""
        self.tools: Dict[str, Callable] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}

    def tool(
        self,
        name: Optional[str] = None,
        description: str = "",
        version: str = "1.0.0",
        **extra_metadata: Any
    ):
        """
        Decorator to register a tool.

        Args:
            name: Tool name (defaults to function name)
            description: Tool description (defaults to docstring)
            version: Tool version
            **extra_metadata: Additional metadata fields

        Returns:
            Decorator function

        Example:
            >>> @registry.tool(name="my_tool", description="Does something")
            >>> async def my_function(state):
            ...     return state
        """
        def decorator(func: Callable) -> Callable:
            # Determine tool name
            tool_name = name or func.__name__

            # Register the function
            self.tools[tool_name] = func

            # Extract metadata
            func_description = description or func.__doc__ or ""
            is_async = asyncio.iscoroutinefunction(func)

            # Get function signature
            sig = inspect.signature(func)
            parameters = {
                param_name: {
                    "annotation": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                    "default": param.default if param.default != inspect.Parameter.empty else None
                }
                for param_name, param in sig.parameters.items()
            }

            # Store metadata
            self.metadata[tool_name] = {
                "name": tool_name,
                "description": func_description.strip(),
                "version": version,
                "is_async": is_async,
                "function_name": func.__name__,
                "module": func.__module__,
                "parameters": parameters,
                **extra_metadata
            }

            # Return original function (or wrapped version)
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            return async_wrapper if is_async else wrapper

        return decorator

    def register(
        self,
        name: str,
        func: Callable,
        description: str = "",
        **metadata: Any
    ) -> None:
        """
        Register a tool programmatically (without decorator).

        Args:
            name: Tool name
            func: Function to register
            description: Tool description
            **metadata: Additional metadata

        Example:
            >>> async def my_func(state): return state
            >>> registry.register("my_tool", my_func)
        """
        self.tools[name] = func

        func_description = description or func.__doc__ or ""
        is_async = asyncio.iscoroutinefunction(func)

        self.metadata[name] = {
            "name": name,
            "description": func_description.strip(),
            "is_async": is_async,
            "function_name": func.__name__,
            "module": func.__module__,
            **metadata
        }

    def get_tool(self, name: str) -> Callable:
        """
        Retrieve a registered tool by name.

        Args:
            name: Tool name

        Returns:
            The tool function

        Raises:
            KeyError: If tool not found
        """
        if name not in self.tools:
            available = ", ".join(self.list_tool_names())
            raise KeyError(
                f"Tool '{name}' not found. Available tools: {available}"
            )

        return self.tools[name]

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered"""
        return name in self.tools

    def get_metadata(self, name: str) -> Dict[str, Any]:
        """
        Get metadata for a tool.

        Args:
            name: Tool name

        Returns:
            Metadata dictionary

        Raises:
            KeyError: If tool not found
        """
        if name not in self.metadata:
            raise KeyError(f"Tool '{name}' not found")

        return self.metadata[name].copy()

    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        List all registered tools with their metadata.

        Returns:
            Dictionary mapping tool names to metadata
        """
        return self.metadata.copy()

    def list_tool_names(self) -> List[str]:
        """
        Get list of all registered tool names.

        Returns:
            List of tool names
        """
        return list(self.tools.keys())

    def search_tools(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for tools by name or description.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching tool metadata
        """
        query_lower = query.lower()
        results = []

        for tool_name, meta in self.metadata.items():
            if (
                query_lower in tool_name.lower()
                or query_lower in meta.get("description", "").lower()
            ):
                results.append(meta)

        return results

    def remove_tool(self, name: str) -> bool:
        """
        Remove a tool from the registry.

        Args:
            name: Tool name

        Returns:
            True if tool was removed, False if not found
        """
        if name in self.tools:
            del self.tools[name]
            del self.metadata[name]
            return True
        return False

    def clear(self) -> None:
        """Remove all tools from the registry"""
        self.tools.clear()
        self.metadata.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with statistics
        """
        async_count = sum(
            1 for meta in self.metadata.values()
            if meta.get("is_async", False)
        )
        sync_count = len(self.tools) - async_count

        return {
            "total_tools": len(self.tools),
            "async_tools": async_count,
            "sync_tools": sync_count,
            "tool_names": self.list_tool_names()
        }

    def validate_tool(self, name: str) -> bool:
        """
        Validate that a tool is properly registered.

        Args:
            name: Tool name

        Returns:
            True if valid

        Raises:
            ValueError: If tool is invalid
        """
        if not self.has_tool(name):
            raise ValueError(f"Tool '{name}' not registered")

        tool = self.get_tool(name)

        # Check if function is callable
        if not callable(tool):
            raise ValueError(f"Tool '{name}' is not callable")

        # Check if function has correct signature
        sig = inspect.signature(tool)
        if len(sig.parameters) < 1:
            raise ValueError(
                f"Tool '{name}' must accept at least one parameter (state)"
            )

        return True

    def __len__(self) -> int:
        """Get number of registered tools"""
        return len(self.tools)

    def __contains__(self, name: str) -> bool:
        """Check if tool is registered (supports 'in' operator)"""
        return self.has_tool(name)

    def __getitem__(self, name: str) -> Callable:
        """Get tool by name (supports indexing)"""
        return self.get_tool(name)

    def __repr__(self) -> str:
        """String representation"""
        return f"ToolRegistry(tools={len(self.tools)})"


# Global registry instance
registry = ToolRegistry()


# Convenience functions

def get_tool(name: str) -> Callable:
    """Get a tool from the global registry"""
    return registry.get_tool(name)


def list_tools() -> Dict[str, Dict[str, Any]]:
    """List all tools from the global registry"""
    return registry.list_tools()


def register_tool(
    name: str,
    func: Callable,
    description: str = "",
    **metadata: Any
) -> None:
    """Register a tool in the global registry"""
    registry.register(name, func, description, **metadata)


# Example tool registration for testing

@registry.tool(name="test_tool", description="A test tool for unit tests")
async def test_tool(state):
    """Test tool that does nothing"""
    return state


@registry.tool(name="echo_tool", description="Echoes the input state")
async def echo_tool(state):
    """Echo tool for testing"""
    return state


@registry.tool(name="increment_counter", description="Increments a counter in state")
async def increment_counter(state):
    """Increment counter tool for testing"""
    current = state.get_data("counter", 0)
    return state.set_data("counter", current + 1)


# Utility decorators

def require_data_keys(*keys: str):
    """
    Decorator to validate that state has required data keys.

    Args:
        *keys: Required data keys

    Example:
        >>> @registry.tool()
        >>> @require_data_keys("user_id", "action")
        >>> async def my_tool(state):
        ...     return state
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(state, *args, **kwargs):
            # Check for required keys
            missing = [key for key in keys if key not in state.data]
            if missing:
                error_msg = f"Missing required data keys: {', '.join(missing)}"
                return state.add_error(error_msg)

            # Call original function
            if asyncio.iscoroutinefunction(func):
                return await func(state, *args, **kwargs)
            else:
                return func(state, *args, **kwargs)

        return wrapper
    return decorator


def log_execution(func: Callable) -> Callable:
    """
    Decorator to log tool execution.

    Example:
        >>> @registry.tool()
        >>> @log_execution
        >>> async def my_tool(state):
        ...     return state
    """
    @wraps(func)
    async def wrapper(state, *args, **kwargs):
        tool_name = func.__name__
        print(f"Executing tool: {tool_name}")

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(state, *args, **kwargs)
            else:
                result = func(state, *args, **kwargs)

            print(f"Tool {tool_name} completed successfully")
            return result

        except Exception as e:
            print(f"Tool {tool_name} failed: {e}")
            raise

    return wrapper
