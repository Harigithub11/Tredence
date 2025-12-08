"""Tests for ToolRegistry"""

import pytest
from app.core.state import WorkflowState
from app.core.registry import ToolRegistry, registry, get_tool, list_tools


def test_registry_creation():
    """Test creating a tool registry"""
    reg = ToolRegistry()
    assert len(reg) == 0
    assert reg.list_tool_names() == []


def test_registry_decorator():
    """Test registering tool with decorator"""
    reg = ToolRegistry()

    @reg.tool(name="test_func", description="Test function")
    async def my_tool(state: WorkflowState) -> WorkflowState:
        return state.set_data("executed", True)

    assert reg.has_tool("test_func")
    assert len(reg) == 1

    metadata = reg.get_metadata("test_func")
    assert metadata["name"] == "test_func"
    assert metadata["description"] == "Test function"
    assert metadata["is_async"] is True


def test_registry_decorator_default_name():
    """Test decorator uses function name by default"""
    reg = ToolRegistry()

    @reg.tool()
    async def my_function(state: WorkflowState) -> WorkflowState:
        return state

    assert reg.has_tool("my_function")


def test_registry_programmatic_registration():
    """Test registering tool programmatically"""
    reg = ToolRegistry()

    async def my_tool(state: WorkflowState) -> WorkflowState:
        return state

    reg.register("my_tool", my_tool, "Test tool")

    assert reg.has_tool("my_tool")
    tool = reg.get_tool("my_tool")
    assert tool == my_tool


def test_registry_get_tool():
    """Test retrieving a tool"""
    reg = ToolRegistry()

    @reg.tool(name="test_tool")
    async def my_tool(state: WorkflowState) -> WorkflowState:
        return state

    tool = reg.get_tool("test_tool")
    assert tool is not None


def test_registry_get_tool_not_found():
    """Test getting non-existent tool raises error"""
    reg = ToolRegistry()

    with pytest.raises(KeyError, match="not found"):
        reg.get_tool("non_existent")


def test_registry_has_tool():
    """Test checking if tool exists"""
    reg = ToolRegistry()

    @reg.tool(name="exists")
    async def my_tool(state: WorkflowState) -> WorkflowState:
        return state

    assert reg.has_tool("exists") is True
    assert reg.has_tool("not_exists") is False


def test_registry_list_tools():
    """Test listing all tools"""
    reg = ToolRegistry()

    @reg.tool(name="tool1")
    async def tool1(state: WorkflowState) -> WorkflowState:
        return state

    @reg.tool(name="tool2")
    async def tool2(state: WorkflowState) -> WorkflowState:
        return state

    tools = reg.list_tools()
    assert len(tools) == 2
    assert "tool1" in tools
    assert "tool2" in tools


def test_registry_list_tool_names():
    """Test getting list of tool names"""
    reg = ToolRegistry()

    @reg.tool(name="tool1")
    async def tool1(state: WorkflowState) -> WorkflowState:
        return state

    @reg.tool(name="tool2")
    async def tool2(state: WorkflowState) -> WorkflowState:
        return state

    names = reg.list_tool_names()
    assert set(names) == {"tool1", "tool2"}


def test_registry_search_tools():
    """Test searching for tools"""
    reg = ToolRegistry()

    @reg.tool(name="parse_json", description="Parses JSON data")
    async def parse_json(state: WorkflowState) -> WorkflowState:
        return state

    @reg.tool(name="parse_xml", description="Parses XML data")
    async def parse_xml(state: WorkflowState) -> WorkflowState:
        return state

    @reg.tool(name="format_output", description="Formats output")
    async def format_output(state: WorkflowState) -> WorkflowState:
        return state

    # Search by name
    results = reg.search_tools("parse")
    assert len(results) == 2

    # Search by description
    results = reg.search_tools("json")
    assert len(results) == 1
    assert results[0]["name"] == "parse_json"


def test_registry_remove_tool():
    """Test removing a tool"""
    reg = ToolRegistry()

    @reg.tool(name="temp_tool")
    async def temp_tool(state: WorkflowState) -> WorkflowState:
        return state

    assert reg.has_tool("temp_tool")

    removed = reg.remove_tool("temp_tool")
    assert removed is True
    assert not reg.has_tool("temp_tool")

    # Remove non-existent
    removed = reg.remove_tool("non_existent")
    assert removed is False


def test_registry_clear():
    """Test clearing all tools"""
    reg = ToolRegistry()

    @reg.tool(name="tool1")
    async def tool1(state: WorkflowState) -> WorkflowState:
        return state

    @reg.tool(name="tool2")
    async def tool2(state: WorkflowState) -> WorkflowState:
        return state

    assert len(reg) == 2

    reg.clear()
    assert len(reg) == 0


def test_registry_get_stats():
    """Test getting registry statistics"""
    reg = ToolRegistry()

    @reg.tool(name="async_tool")
    async def async_tool(state: WorkflowState) -> WorkflowState:
        return state

    @reg.tool(name="sync_tool")
    def sync_tool(state: WorkflowState) -> WorkflowState:
        return state

    stats = reg.get_stats()

    assert stats["total_tools"] == 2
    assert stats["async_tools"] == 1
    assert stats["sync_tools"] == 1
    assert set(stats["tool_names"]) == {"async_tool", "sync_tool"}


def test_registry_validate_tool():
    """Test tool validation"""
    reg = ToolRegistry()

    @reg.tool(name="valid_tool")
    async def valid_tool(state: WorkflowState) -> WorkflowState:
        return state

    # Should pass validation
    assert reg.validate_tool("valid_tool") is True

    # Non-existent tool
    with pytest.raises(ValueError, match="not registered"):
        reg.validate_tool("non_existent")


def test_registry_validate_tool_no_params():
    """Test validation fails for tool without parameters"""
    reg = ToolRegistry()

    @reg.tool(name="no_params")
    async def no_params() -> WorkflowState:
        return WorkflowState(workflow_id="test", run_id="test")

    with pytest.raises(ValueError, match="must accept at least one parameter"):
        reg.validate_tool("no_params")


def test_registry_metadata_extraction():
    """Test metadata extraction from function"""
    reg = ToolRegistry()

    @reg.tool(name="documented_tool", version="2.0.0", author="Test Author")
    async def documented_tool(state: WorkflowState, extra_param: str = "default") -> WorkflowState:
        """This is a documented tool"""
        return state

    metadata = reg.get_metadata("documented_tool")

    assert metadata["name"] == "documented_tool"
    assert metadata["description"] == "This is a documented tool"
    assert metadata["version"] == "2.0.0"
    assert metadata["author"] == "Test Author"
    assert metadata["is_async"] is True
    assert "parameters" in metadata


def test_registry_contains_operator():
    """Test 'in' operator support"""
    reg = ToolRegistry()

    @reg.tool(name="test_tool")
    async def test_tool(state: WorkflowState) -> WorkflowState:
        return state

    assert "test_tool" in reg
    assert "non_existent" not in reg


def test_registry_getitem_operator():
    """Test indexing support"""
    reg = ToolRegistry()

    @reg.tool(name="test_tool")
    async def test_tool(state: WorkflowState) -> WorkflowState:
        return state

    tool = reg["test_tool"]
    assert tool is not None


def test_global_registry():
    """Test global registry instance"""
    # The global registry should have pre-registered test tools
    assert registry is not None
    assert len(registry) > 0  # Has test tools
    assert registry.has_tool("test_tool")
    assert registry.has_tool("echo_tool")
    assert registry.has_tool("increment_counter")


def test_global_convenience_functions():
    """Test global convenience functions"""
    # get_tool
    tool = get_tool("test_tool")
    assert tool is not None

    # list_tools
    tools = list_tools()
    assert isinstance(tools, dict)
    assert len(tools) > 0


@pytest.mark.asyncio
async def test_registry_tool_execution():
    """Test executing a registered tool"""
    reg = ToolRegistry()

    @reg.tool(name="increment")
    async def increment(state: WorkflowState) -> WorkflowState:
        count = state.get_data("count", 0)
        return state.set_data("count", count + 1)

    tool = reg.get_tool("increment")
    state1 = WorkflowState(
        workflow_id="test",
        run_id="run1",
        data={"count": 5}
    )

    state2 = await tool(state1)
    assert state2.get_data("count") == 6


@pytest.mark.asyncio
async def test_registry_sync_tool_execution():
    """Test executing a sync tool"""
    reg = ToolRegistry()

    @reg.tool(name="double")
    def double(state: WorkflowState) -> WorkflowState:
        value = state.get_data("value", 1)
        return state.set_data("value", value * 2)

    tool = reg.get_tool("double")
    state1 = WorkflowState(
        workflow_id="test",
        run_id="run1",
        data={"value": 10}
    )

    # Sync tool should still be callable
    state2 = tool(state1)
    assert state2.get_data("value") == 20


@pytest.mark.asyncio
async def test_increment_counter_global_tool():
    """Test the pre-registered increment_counter tool"""
    tool = get_tool("increment_counter")

    state1 = WorkflowState(
        workflow_id="test",
        run_id="run1",
        data={"counter": 0}
    )

    state2 = await tool(state1)
    assert state2.get_data("counter") == 1

    state3 = await tool(state2)
    assert state3.get_data("counter") == 2
