import streamlit as st
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from langchain_ollama import ChatOllama
from typing import TypedDict, Annotated

# LLM
llm = ChatOllama(model="llama3.2:3b")

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Streaming node
from langchain_core.messages import AIMessageChunk

def chat_node(state: ChatState):
    messages = state["messages"]

    final_chunks = []

    # STREAM chunks
    for chunk in llm.stream(messages):
        final_chunks.append(chunk)
        yield {"messages": [chunk]}  # streaming

    # FINAL OUTPUT: convert all chunks into 1 AIMessage
    full_output = "".join([c.content for c in final_chunks if hasattr(c, "content")])

    return {"messages": [AIMessage(content=full_output)]}



# Build graph
checkpointer = MemorySaver()
graph = StateGraph(ChatState)

graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)
