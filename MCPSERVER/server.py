from __future__ import annotations

from fastmcp import FastMCP

mcp = FastMCP("arith")

def _as_number(x):
    if isinstance(x, int):
        return x
    elif isinstance(x, float):
        return int(x)
    elif isinstance(x, str):
        return int(x)
    else:
        raise ValueError("Invalid number")

@mcp.tool()
async def add(x: int, y: int) -> int:
    """Add two numbers."""
    return _as_number(x) + _as_number(y)

@mcp.tool()
async def sub(x: int, y: int) -> int:
    """Subtract two numbers."""
    return _as_number(x) - _as_number(y)

@mcp.tool()
async def mul(x: int, y: int) -> int:
    """Multiply two numbers."""
    return _as_number(x) * _as_number(y)

@mcp.tool()
async def div(x: int, y: int) -> int:
    """Divide two numbers."""
    return _as_number(x) / _as_number(y)