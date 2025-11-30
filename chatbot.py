import streamlit as st
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from langchain_ollama import ChatOllama
from typing import TypedDict, Annotated

# -------- LLM --------
llm = ChatOllama(model="llama3.2:3b")

# -------- State --------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# -------- Node --------
def chat_node(state: ChatState) -> ChatState:
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

# -------- Build Graph --------
checkpointer = MemorySaver()
graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)
chatbot = graph.compile(checkpointer=checkpointer)

# -------- Streamlit UI --------
st.set_page_config(page_title="ChatBot", layout="wide")
st.title("🤖 LangGraph + Ollama Chatbot")

# Initialize session
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "1"

# Chat bubble display
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.write(msg.content)
    else:
        with st.chat_message("assistant"):
            st.write(msg.content)

# User input
user_input = st.chat_input("Type your message...")

if user_input:
    # Show user message
    st.session_state.messages.append(HumanMessage(content=user_input))
    with st.chat_message("user"):
        st.write(user_input)

    # Run LangGraph
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    result = chatbot.invoke({"messages": st.session_state.messages}, config=config)

    ai_msg = result["messages"][-1]

    # Show assistant message
    st.session_state.messages.append(ai_msg)
    with st.chat_message("assistant"):
        st.write(ai_msg.content)
