import streamlit as st
from chatbot_backend import chatbot
from langchain_core.messages import HumanMessage, AIMessage

# Page setup
st.set_page_config(page_title="AI Chatbot", layout="centered")

# Title
st.title("🤖 AI Chatbot")

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "1"

# Chat history area
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.write(msg.content)
    else:
        with st.chat_message("assistant"):
            st.write(msg.content)

# Input bar
user_input = st.chat_input("Type your message…")

if user_input:
    # Display user message
    st.session_state.messages.append(HumanMessage(content=user_input))

    with st.chat_message("user"):
        st.write(user_input)

    # Backend response
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    response = chatbot.invoke({"messages": st.session_state.messages}, config=config)

    ai_msg = response["messages"][-1]

    st.session_state.messages.append(ai_msg)

    # Display bot response
    with st.chat_message("assistant"):
        st.write(ai_msg.content)
