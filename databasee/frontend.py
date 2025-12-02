########################## IMPORTS ##############################
import streamlit as st
from backend import chatbot, retrieve_thread
from langchain_core.messages import HumanMessage, AIMessage
import uuid

from dotenv import load_dotenv
import os

load_dotenv()

# Optional: Only set these if you want LangSmith tracing
# Otherwise you can comment them out or remove them
if os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "false")
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "chatbot")


######################### UTILITY FUNCTIONS #########################
def generate_thread_id():
    return f"thread-{uuid.uuid4()}"


def load_messages_from_db(thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        state_snapshot = chatbot.get_state(config)
        
        if hasattr(state_snapshot, 'values') and 'messages' in state_snapshot.values:
            return state_snapshot.values['messages']
        elif isinstance(state_snapshot, dict) and 'messages' in state_snapshot:
            return state_snapshot['messages']
        else:
            return []
    except Exception as e:
        print(f"Error loading messages: {e}")
        return []


########################## UI SETUP ##########################
st.set_page_config(page_title="AI Chatbot", layout="centered")
st.title("🤖 AI Chatbot")


########################## SESSION SETUP #########################
if "thread_titles" not in st.session_state:
    st.session_state.thread_titles = {}

if "thread_id" not in st.session_state:
    st.session_state.thread_id = generate_thread_id()

if st.session_state.thread_id not in st.session_state.thread_titles:
    st.session_state.thread_titles[st.session_state.thread_id] = "New Chat"


########################### SIDEBAR ###########################
st.sidebar.title("Chatbot")

if st.sidebar.button("🆕 New Chat"):
    new_id = generate_thread_id()
    st.session_state.thread_id = new_id
    st.session_state.thread_titles[new_id] = "New Chat"
    st.rerun()

st.sidebar.header("My Conversations")

all_thread_ids = retrieve_thread(None)

for tid in all_thread_ids:
    label = st.session_state.thread_titles.get(tid, tid)
    if st.sidebar.button(label, key=tid):
        st.session_state.thread_id = tid
        st.rerun()

st.sidebar.subheader("Rename Chat")
current_title = st.session_state.thread_titles[st.session_state.thread_id]
new_name = st.sidebar.text_input("Chat name", value=current_title)

if new_name != current_title:
    st.session_state.thread_titles[st.session_state.thread_id] = new_name


############################ MAIN UI ############################

current_thread_id = st.session_state.thread_id

# Load messages from database
messages = load_messages_from_db(current_thread_id)

# Display all messages in chronological order
for msg in messages:
    with st.chat_message("user" if isinstance(msg, HumanMessage) else "assistant"):
        st.write(msg.content)

# User input
user_input = st.chat_input("Type your message…")

if user_input:
    # Configuration for LangGraph with thread tracking
    config = {
        "configurable": {"thread_id": current_thread_id},
        "metadata": {
            "thread_id": current_thread_id
        },
        "run_name": "chat_turn",
    }
    
    # Show user message immediately
    with st.chat_message("user"):
        st.write(user_input)
    
    # Prepare the full message history
    full_history = messages + [HumanMessage(content=user_input)]
    
    # Stream and collect AI response
    with st.chat_message("assistant"):
        stream_box = st.empty()
        collected_chunks = []
        
        # Stream the response
        for chunk, meta in chatbot.stream(
            {"messages": full_history},
            config=config,
            stream_mode="messages"
        ):
            if hasattr(chunk, "content") and chunk.content:
                collected_chunks.append(chunk.content)
                stream_box.write("".join(collected_chunks))
    
    # After streaming completes, messages are automatically saved to checkpoint
    # Force a rerun to reload messages from database
    st.rerun()