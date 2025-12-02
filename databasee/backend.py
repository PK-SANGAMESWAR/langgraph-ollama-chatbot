from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated
import sqlite3
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
import requests
from dotenv import load_dotenv
import os

load_dotenv()

# LLM
llm = ChatOllama(model="llama3.2:3b")

# TOOLS
@tool
def duckduckgo_search(query: str) -> dict:
    """Search the internet using DuckDuckGo"""
    try:
        result = DuckDuckGoSearchRun(region="us-en").run(query)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

@tool
def calculator(expression: str) -> dict:
    """
    Evaluate a mathematical expression.
    Examples: "2+3", "10*5", "100/4", "15-7"
    Supports: +, -, *, /, ** (power), parentheses
    """
    try:
        # Clean the expression
        expression = expression.strip()
        
        # Safe evaluation - only allow mathematical operations
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expression):
            return {"error": "Invalid characters in expression"}
        
        # Evaluate the expression
        result = eval(expression, {"__builtins__": {}}, {})
        return {"result": result}
    except ZeroDivisionError:
        return {"error": "Cannot divide by zero"}
    except Exception as e:
        return {"error": f"Invalid expression: {str(e)}"}

@tool
def weather(city_name: str) -> dict:
    """Weather tool to get weather information for a specific city"""
    try:
        api_key = os.getenv('WEATHER_API_KEY')
        if not api_key:
            return {"error": "Weather API key not configured"}
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"
        response = requests.get(url)
        data = response.json()
        return {"result": data}
    except Exception as e:
        return {"error": str(e)}

@tool
def get_stock_price(symbol: str) -> dict:
    """Fetch the latest stock price for a given symbol (e.g. "AAPL", "TSLA") using Alpha Vantage API"""
    try:
        api_key = os.getenv('ALPHAVANTAGE_API_KEY')
        if not api_key:
            return {"error": "Alpha Vantage API key not configured"}
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
        response = requests.get(url)
        data = response.json()
        return {"result": data}
    except Exception as e:
        return {"error": str(e)}

@tool
def wikipedia_search(query: str) -> dict:
    """Search Wikipedia for a specific query"""
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&format=json&utf8=1&srsearch={query}"
        response = requests.get(url)
        data = response.json()
        return {"result": data}
    except Exception as e:
        return {"error": str(e)}

from datetime import datetime

@tool
def current_datetime(_: str = "") -> dict:
    """Get current date and time."""
    now = datetime.now()
    return {"result": now.strftime("%Y-%m-%d %H:%M:%S")}

@tool
def unit_converter(value: float, from_unit: str, to_unit: str) -> dict:
    """Convert units like km→miles, kg→lbs, C→F."""
    try:
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
    except Exception as e:
        return {"error": str(e)}

@tool
def read_file(path: str) -> dict:
    """Read text from .txt or .pdf file"""
    try:
        if path.endswith(".txt"):
            with open(path, "r", encoding="utf-8") as f:
                return {"result": f.read()}
        elif path.endswith(".pdf"):
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(path)
                text = "\n".join([page.extract_text() or "" for page in reader.pages])
                return {"result": text}
            except ImportError:
                return {"error": "PyPDF2 not installed. Run: pip install PyPDF2"}
        else:
            return {"error": "Unsupported file type"}
    except Exception as e:
        return {"error": str(e)}

@tool
def currency_convert(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert currency using ECB free exchange rates."""
    try:
        data = requests.get("https://api.exchangerate.host/latest").json()
        rates = data["rates"]

        f = from_currency.upper()
        t = to_currency.upper()

        if f not in rates or t not in rates:
            return {"error": "Unsupported currency"}

        result = amount / rates[f] * rates[t]
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

@tool
def fetch_url(url: str) -> dict:
    """Fetch and extract readable text from any public webpage."""
    try:
        from bs4 import BeautifulSoup
        html = requests.get(url, timeout=5).text
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n")
        return {"result": text[:5000]}  # limit
    except ImportError:
        return {"error": "BeautifulSoup4 not installed. Run: pip install beautifulsoup4"}
    except Exception as e:
        return {"error": str(e)}

# List of all tools
tools = [
    duckduckgo_search,
    calculator,
    weather,
    get_stock_price,
    wikipedia_search,
    current_datetime,
    unit_converter,
    read_file,
    currency_convert,
    fetch_url,
]

# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)

# Create ToolNode - THIS WAS MISSING!
tool_node = ToolNode(tools)

# STATE
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# CHAT NODE
def chat_node(state: ChatState):
    """Process messages and generate AI response"""
    messages = state["messages"]
    
    # Get response from LLM with tools
    response = llm_with_tools.invoke(messages)
    
    # Return the new message to be added to state
    return {"messages": [response]}

# CHECKPOINTER - SQLite for persistence
conn = sqlite3.connect("chatbot.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)

# GRAPH
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chat_node")
graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge("tools", "chat_node")

# Compile with checkpointer
chatbot = graph.compile(checkpointer=checkpointer)

# RETRIEVE THREADS
def retrieve_thread(_):
    """Get all thread IDs from the database"""
    ids = set()
    try:
        for chk in checkpointer.list(None):
            if hasattr(chk, 'config') and chk.config:
                config = chk.config
                if isinstance(config, dict):
                    configurable = config.get('configurable', {})
                    thread_id = configurable.get('thread_id')
                    if thread_id:
                        ids.add(thread_id)
    except Exception as e:
        print(f"Error retrieving threads: {e}")
    
    return list(ids)