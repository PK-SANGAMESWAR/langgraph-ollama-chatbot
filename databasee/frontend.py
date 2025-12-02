########################## IMPORTS ##############################
import streamlit as st
from backend import chatbot, retrieve_thread
from langchain_core.messages import HumanMessage, AIMessage
import uuid

######################### UTILITY FUNCTIONS #########################
def generate_thread_id():
    return f"thread-{uuid.uuid4()}"


def load_messages_from_db(thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Get the current state from the checkpointer
        state_snapshot = chatbot.get_state(config)
        
        # Extract messages from the state
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
# chat titles
if "thread_titles" not in st.session_state:
    st.session_state.thread_titles = {}

# current thread
if "thread_id" not in st.session_state:
    st.session_state.thread_id = generate_thread_id()

# initialize title
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

# all threads from DB
all_thread_ids = retrieve_thread(None)

for tid in all_thread_ids:
    label = st.session_state.thread_titles.get(tid, tid)
    if st.sidebar.button(label, key=tid):
        st.session_state.thread_id = tid
        st.rerun()

# rename chat
st.sidebar.subheader("Rename Chat")
current_title = st.session_state.thread_titles[st.session_state.thread_id]
new_name = st.sidebar.text_input("Chat name", value=current_title)

if new_name != current_title:
    st.session_state.thread_titles[st.session_state.thread_id] = new_name


############################ MAIN UI ############################

current_thread_id = st.session_state.thread_id

# load DB messages
messages = load_messages_from_db(current_thread_id)

# show messages newest-first
# Display messages in chronological order (oldest first)
for msg in messages:
    with st.chat_message("user" if isinstance(msg, HumanMessage) else "assistant"):
        st.write(msg.content)

# user input
# user input
user_input = st.chat_input("Type your message…")

if user_input:
    # Reload messages BEFORE displaying to ensure we have the latest
    messages = load_messages_from_db(current_thread_id)
    
    # show user message
    with st.chat_message("user"):
        st.write(user_input)

    # build full history for backend
    history = messages + [HumanMessage(content=user_input)]

    # stream AI response
    with st.chat_message("assistant"):
        stream_box = st.empty()
        streamed_text = ""

        config = {"configurable": {"thread_id": current_thread_id}}

        for chunk, meta in chatbot.stream(
            {"messages": history},
            config=config,
            stream_mode="messages"
        ):
            if hasattr(chunk, "content") and chunk.content:
                streamed_text += chunk.content
                stream_box.write(streamed_text)
    
    # Force reload to show updated messages
    st.rerun()