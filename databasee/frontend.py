import queue
import uuid
import streamlit as st
from backendd import chatbot, retrieve_all_threads, submit_async_task
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

# =========================== Utilities ===========================
def generate_thread_id():
    return uuid.uuid4()


def reset_chat():
    thread_id = generate_thread_id()
    st.session_state["thread_id"] = thread_id
    add_thread(thread_id)
    st.session_state["message_history"] = []


def add_thread(thread_id):
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)


def load_conversation(thread_id):
    state = chatbot.get_state(config={"configurable": {"thread_id": thread_id}})
    return state.values.get("messages", [])


def summarize_history(messages):
    if not messages:
        return "(empty)"
    first = messages[0].content[:40].replace("\n", " ")
    count = len(messages)
    return f"{first}...   ({count} msgs)"


# ======================= Session Initialization ===================
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = retrieve_all_threads()

add_thread(st.session_state["thread_id"])

# ============================ Sidebar ============================
st.sidebar.title("💬 LangGraph MCP Chatbot")

# -------- PDF Upload ----------
# TODO: Implement PDF ingestion in backend
# uploaded_pdf = st.sidebar.file_uploader("📄 Upload PDF for Q&A", type=["pdf"])

st.sidebar.divider()

# -------- New Chat Button ----------
if st.sidebar.button("➕ New Chat", use_container_width=True):
    reset_chat()

st.sidebar.header("🧵 Conversations")

# -------- Chat History Preview ----------
for thread_id in st.session_state["chat_threads"][::-1]:
    messages = load_conversation(thread_id)
    preview = summarize_history(messages)

    if st.sidebar.button(preview, key=str(thread_id), use_container_width=True):
        st.session_state["thread_id"] = thread_id

        session_messages = []
        for msg in messages:
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            session_messages.append({"role": role, "content": msg.content})

        st.session_state["message_history"] = session_messages

# ============================ Main UI ============================
st.title("🤖 LangGraph + MCP Chatbot")

# Render history
for message in st.session_state["message_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Type here…")

if user_input:
    # Add user's message
    st.session_state["message_history"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    CONFIG = {
        "configurable": {"thread_id": st.session_state["thread_id"]},
        "metadata": {"thread_id": st.session_state["thread_id"]},
        "run_name": "chat_turn",
    }

    # Assistant streaming block
    with st.chat_message("assistant"):
        status_holder = {"box": None}

        def ai_stream_generator():
            event_queue: queue.Queue = queue.Queue()

            async def run_stream():
                try:
                    async for message_chunk, metadata in chatbot.astream(
                        {"messages": [HumanMessage(content=user_input)]},
                        config=CONFIG,
                        stream_mode="messages",
                    ):
                        event_queue.put((message_chunk, metadata))
                except Exception as exc:
                    event_queue.put(("error", exc))
                finally:
                    event_queue.put(None)

            submit_async_task(run_stream())

            while True:
                item = event_queue.get()
                if item is None:
                    break

                message_chunk, metadata = item

                if message_chunk == "error":
                    raise metadata

                # Tool Message Handler
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Running `{tool_name}`…", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Running `{tool_name}`…",
                            state="running",
                            expanded=True,
                        )

                # Assistant Stream
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content

        ai_message = st.write_stream(ai_stream_generator())

        # Close tool box
        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool completed",
                state="complete",
                expanded=False,
            )

    # Save the collected response
    if not ai_message or ai_message.strip() == "":
        ai_message = "(no output)"

    st.session_state["message_history"].append(
        {"role": "assistant", "content": ai_message}
    )