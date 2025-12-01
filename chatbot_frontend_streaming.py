import streamlit as st
from chatbot_backend import chatbot
from langchain_core.messages import HumanMessage, AIMessage

st.set_page_config(page_title="AI Chatbot", layout="centered")
st.title("🤖 AI Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "1"

# Display previous chat
for msg in st.session_state.messages:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.write(msg.content)

# Input box
user_input = st.chat_input("Type your message…")

if user_input:
    # show user msg
    st.session_state.messages.append(HumanMessage(content=user_input))
    with st.chat_message("user"):
        st.write(user_input)

    # assistant streaming
    with st.chat_message("assistant"):
        stream_box = st.empty()
        streamed_text = ""

        config = {"configurable": {"thread_id": st.session_state.thread_id}}

        for event in chatbot.stream(
            {"messages": st.session_state.messages},
            config=config,
            stream_mode="messages"
        ):
            for node, messages in event.items():
                for chunk in messages:
                    if hasattr(chunk, "content") and chunk.content:
                        streamed_text += chunk.content
                        stream_box.write(streamed_text)

        st.session_state.messages.append(AIMessage(content=streamed_text))
