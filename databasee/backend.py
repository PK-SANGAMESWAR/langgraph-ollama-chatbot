from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated
import sqlite3

# LLM
llm = ChatOllama(model="llama3.2:3b")

# STATE
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# CHAT NODE
def chat_node(state: ChatState):
    """Process messages and generate AI response"""
    messages = state["messages"]
    
    # Get response from LLM
    response = llm.invoke(messages)
    
    # Return the new message to be added to state
    return {"messages": [response]}

# CHECKPOINTER - SQLite for persistence
conn = sqlite3.connect("chatbot.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)

# GRAPH
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

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