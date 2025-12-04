import os
import sqlite3
import aiohttp
import aiofiles
from bs4 import BeautifulSoup
from datetime import datetime
from typing import TypedDict, Annotated

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.sqlite import SqliteSaver

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_ollama import ChatOllama
from langchain_core.tools import tool

import asyncio

from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

# ---------------------------------------
# LLM
# ---------------------------------------
llm = ChatOllama(model="llama3.2:3b")


# ---------------------------------------
# MCP CLIENT (FIXED WINDOWS PATH)
# ---------------------------------------
client = MultiServerMCPClient(
    {
        "arith": {
            "transport": "stdio",
            "command": "python",
            "args": [
                r"C:\Users\LOQ\Downloads\CHATBOT_USING_LANGGRAPH\MCPSERVER\server.py"
            ],
        },
        "expense": {
            "transport": "streamable_http",
            "url": "https://considerable-lime-toad.fastmcp.app/mcp"
        },
    }
)

# ---------------------------------------
# ASYNC TOOLS (UNCHANGED)
# ---------------------------------------

@tool
async def duckduckgo_search(query: str) -> dict:
    """Search the web for information."""
    try:
        from langchain_community.tools import DuckDuckGoSearchRun
        result = DuckDuckGoSearchRun(region="us-en").run(query)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


@tool
async def weather(city_name: str) -> dict:
    """Get weather information."""
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return {"error": "Weather API key not configured"}

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            return {"result": await r.json()}


@tool
async def get_stock_price(symbol: str) -> dict:
    """Get stock price information."""
    api_key = os.getenv("ALPHAVANTAGE_API_KEY")
    if not api_key:
        return {"error": "Alpha Vantage API key not configured"}

    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            return {"result": await r.json()}


@tool
async def wikipedia_search(query: str) -> dict:
    """Search Wikipedia for information."""
    url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&format=json&utf8=1&srsearch={query}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            return {"result": await r.json()}


@tool
async def current_datetime(_: str = "") -> dict:
    """Get current date and time."""
    return {"result": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


@tool
async def unit_converter(value: float, from_unit: str, to_unit: str) -> dict:
    """Convert units."""
    table = {
        ("km", "mile"): value * 0.621371,
        ("mile", "km"): value / 0.621371,
        ("kg", "lb"): value * 2.20462,
        ("lb", "kg"): value / 2.20462,
        ("c", "f"): (value * 9/5) + 32,
        ("f", "c"): (value - 32) * 5/9,
    }
    result = table.get((from_unit.lower(), to_unit.lower()))
    if result is None:
        return {"error": "Unsupported conversion"}
    return {"result": result}


@tool
async def read_file(path: str) -> dict:
    """Read a file."""
    try:
        if path.endswith(".txt"):
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                return {"result": await f.read()}

        elif path.endswith(".pdf"):
            import PyPDF2
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text = "\n".join((page.extract_text() or "") for page in reader.pages)
                return {"result": text}

        return {"error": "Unsupported file type"}
    except Exception as e:
        return {"error": str(e)}


@tool
async def currency_convert(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert currency."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.exchangerate.host/latest") as r:
                data = await r.json()

        rates = data["rates"]
        if from_currency.upper() not in rates or to_currency.upper() not in rates:
            return {"error": "Unsupported currency"}

        result = amount / rates[from_currency.upper()] * rates[to_currency.upper()]
        return {"result": result}

    except Exception as e:
        return {"error": str(e)}


@tool
async def fetch_url(url: str) -> dict:
    """Fetch a URL."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                html = await r.text()

        soup = BeautifulSoup(html, "html.parser")
        return {"result": soup.get_text("\n")[:5000]}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------
# LOCAL TOOL LIST
# ---------------------------------------
local_tools = [
    duckduckgo_search,
    weather,
    get_stock_price,
    wikipedia_search,
    current_datetime,
    unit_converter,
    read_file,
    currency_convert,
    fetch_url,
]

llm_with_tools = llm.bind_tools(local_tools)

# ---------------------------------------
# STATE
# ---------------------------------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# ---------------------------------------
# BUILD GRAPH  (STRUCTURE FIXED)
# ---------------------------------------
async def build_graph():

    # GET MCP TOOLS
    mcp_tools = await client.get_tools()

    # MERGE tools
    all_tools = local_tools + mcp_tools

    async def chat_node(state: ChatState):
        messages = state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    tool_node = ToolNode(all_tools)

    graph = StateGraph(ChatState)
    graph.add_node("chat_node", chat_node)
    graph.add_node("tools", tool_node)

    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges("chat_node", tools_condition)
    graph.add_edge("tools", "chat_node")

    chatbot = graph.compile(async_mode=True)
    return chatbot


# ---------------------------------------
# RUN
# ---------------------------------------
async def main():
    chatbot = await build_graph()   # ✅ FIXED: await required

    result = await chatbot.ainvoke(
        {"messages": [HumanMessage(content="Convert 120 km to miles and explain like a pro cyclist.")]}
    )

    print(result["messages"][-1].content)


__all__ = ["build_graph"]

if __name__ == "__main__":
    asyncio.run(main())

