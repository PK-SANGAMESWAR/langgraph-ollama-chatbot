from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated
from langchain_core.messages import AIMessageChunk
import sqlite3

llm = ChatOllama(model="llama3.2:3b")

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def chat_node(state: ChatState):
    messages = state["messages"]
    final_chunks = []

    for chunk in llm.stream(messages):
        final_chunks.append(chunk)
        yield {"messages": [chunk]}

    full = "".join([c.content for c in final_chunks if hasattr(c, "content")])
    return {"messages": [AIMessage(content=full)]}


conn = sqlite3.connect("chatbot.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)


def retrieve_thread(_):
    ids = set()
    try:
        for chk in checkpointer.list(None):
            # Try different ways to access thread_id
            if hasattr(chk, 'config'):
                config = chk.config
                if isinstance(config, dict):
                    configurable = config.get('configurable', {})
                    thread_id = configurable.get('thread_id')
                    if thread_id:
                        ids.add(thread_id)
            elif hasattr(chk, 'checkpoint_ns'):
                # Some versions store it differently
                thread_id = getattr(chk, 'thread_id', None)
                if thread_id:
                    ids.add(thread_id)
    except Exception as e:
        print(f"Error retrieving threads: {e}")
    
    return list(ids)
