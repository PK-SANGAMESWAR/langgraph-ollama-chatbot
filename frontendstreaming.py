########################## IMPORTS ##############################
import streamlit as st
from chatbot_backend import chatbot
from langchain_core.messages import HumanMessage, AIMessage
import uuid

######################### UTILITY FUNCTIONS #########################
def generate_thread_id():
    return f"thread-{uuid.uuid4()}"

########################## UI SETUP ##########################
st.set_page_config(page_title="AI Chatbot", layout="centered")
st.title("🤖 AI Chatbot")

########################## SESSION SETUP #########################
# threads: dict[thread_id -> list[HumanMessage/AIMessage]]
if "threads" not in st.session_state:
    st.session_state.threads = {}

if "thread_id" not in st.session_state:
    st.session_state.thread_id = generate_thread_id()

# Ensure current thread exists
if st.session_state.thread_id not in st.session_state.threads:
    st.session_state.threads[st.session_state.thread_id] = []

########################### SIDEBAR UI ###########################
st.sidebar.title("Chatbot")

# New Chat
if st.sidebar.button("🆕 New Chat"):
    new_id = generate_thread_id()
    st.session_state.thread_id = new_id
    st.session_state.threads[new_id] = []
    st.rerun()

st.sidebar.header("My Conversations")

# List all threads
for tid in st.session_state.threads.keys():
    label = tid  # you can shorten this later
    if st.sidebar.button(label, key=tid):
        st.session_state.thread_id = tid
        st.rerun()

############################ MAIN UI ############################

current_thread_id = st.session_state.thread_id
messages = st.session_state.threads[current_thread_id]

# Show chat history
for msg in reversed(messages):
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.write(msg.content)

# User input
user_input = st.chat_input("Type your message…")

if user_input:
    # Save & show user message
    user_msg = HumanMessage(content=user_input)
    messages.append(user_msg)

    with st.chat_message("user"):
        st.write(user_input)

    # Assistant streaming
    with st.chat_message("assistant"):
        stream_box = st.empty()
        streamed_text = ""

        config = {"configurable": {"thread_id": current_thread_id}}

        for message_chunk, metadata in chatbot.stream(
            {"messages": messages},
            config=config,
            stream_mode="messages"
        ):
            if hasattr(message_chunk, "content") and message_chunk.content:
                streamed_text += message_chunk.content
                stream_box.write(streamed_text)

    # Save assistant message
    ai_msg = AIMessage(content=streamed_text)
    messages.append(ai_msg)

    # Store back into session (not strictly needed since list is mutable)
    st.session_state.threads[current_thread_id] = messages
