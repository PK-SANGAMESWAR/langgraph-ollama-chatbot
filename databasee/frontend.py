import queue
import uuid
import base64
import streamlit as st
from backendd import chatbot, retrieve_all_threads, submit_async_task, ingest_pdf
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


def process_uploaded_file(file):
    """Process uploaded file and return appropriate content format."""
    file_type = file.type
    file_name = file.name
    
    # Read file bytes
    file_bytes = file.read()
    
    # Handle different file types
    if file_type.startswith("image/"):
        # For images, return base64 encoded data
        base64_data = base64.b64encode(file_bytes).decode("utf-8")
        return {
            "type": "image",
            "name": file_name,
            "data": base64_data,
            "media_type": file_type
        }
    elif file_type == "application/pdf":
        # For PDFs, return base64 encoded data
        base64_data = base64.b64encode(file_bytes).decode("utf-8")
        return {
            "type": "pdf",
            "name": file_name,
            "data": base64_data,
            "media_type": file_type
        }
    elif file_type.startswith("text/") or file_name.endswith((".txt", ".md", ".csv", ".json")):
        # For text files, decode as UTF-8
        try:
            text_content = file_bytes.decode("utf-8")
            return {
                "type": "text",
                "name": file_name,
                "content": text_content
            }
        except UnicodeDecodeError:
            # If decode fails, treat as binary
            base64_data = base64.b64encode(file_bytes).decode("utf-8")
            return {
                "type": "binary",
                "name": file_name,
                "data": base64_data,
                "media_type": file_type
            }
    else:
        # For other file types, return base64 encoded data
        base64_data = base64.b64encode(file_bytes).decode("utf-8")
        return {
            "type": "binary",
            "name": file_name,
            "data": base64_data,
            "media_type": file_type
        }


# ======================= Session Initialization ===================
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = retrieve_all_threads()

if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = []

add_thread(st.session_state["thread_id"])

# ============================ Sidebar ============================
st.sidebar.title("💬 LangGraph MCP Chatbot")

# -------- File Upload ----------
st.sidebar.header("📎 Upload Files")
uploaded_files = st.sidebar.file_uploader(
    "Upload files (PDF, images, text, etc.)",
    type=["pdf", "png", "jpg", "jpeg", "gif", "txt", "csv", "json", "md"],
    accept_multiple_files=True,
    key="file_uploader"
)

if uploaded_files:
    st.session_state["uploaded_files"] = uploaded_files
    st.sidebar.success(f"✅ {len(uploaded_files)} file(s) uploaded")
    for file in uploaded_files:
        st.sidebar.text(f"📄 {file.name}")

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
    # Process message content
    message_content = user_input
    pdf_ingested = False
    
    # If there are uploaded files, process them
    if st.session_state.get("uploaded_files"):
        file_info_list = []
        for uploaded_file in st.session_state["uploaded_files"]:
            # Reset file pointer before reading
            uploaded_file.seek(0)
            file_data = process_uploaded_file(uploaded_file)
            
            if file_data["type"] == "text":
                file_info_list.append(f"\n\n--- File: {file_data['name']} ---\n{file_data['content']}\n--- End of {file_data['name']} ---")
            elif file_data["type"] == "image":
                file_info_list.append(f"\n\n[Image uploaded: {file_data['name']}]")
            elif file_data["type"] == "pdf":
                # Ingest PDF into RAG system
                try:
                    uploaded_file.seek(0)  # Reset pointer again
                    pdf_bytes = uploaded_file.read()
                    metadata = ingest_pdf(
                        pdf_bytes,
                        thread_id=str(st.session_state["thread_id"]),
                        filename=file_data["name"]
                    )
                    file_info_list.append(f"\n\n[PDF '{file_data['name']}' ingested: {metadata['chunks']} chunks from {metadata['documents']} pages. You can now ask questions about it.]")
                    pdf_ingested = True
                except Exception as e:
                    file_info_list.append(f"\n\n[Error processing PDF '{file_data['name']}': {str(e)}]")
            else:
                file_info_list.append(f"\n\n[File uploaded: {file_data['name']}]")
        
        # Combine user input with file information
        if file_info_list:
            message_content = user_input + "".join(file_info_list)
    
    # Display user's message
    display_content = user_input
    if st.session_state.get("uploaded_files"):
        display_content += f"\n\n📎 {len(st.session_state['uploaded_files'])} file(s) attached"
    
    st.session_state["message_history"].append({"role": "user", "content": display_content})
    with st.chat_message("user"):
        st.markdown(display_content)
    
    # Clear uploaded files after sending
    st.session_state["uploaded_files"] = []

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
                        {"messages": [HumanMessage(content=message_content)]},
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