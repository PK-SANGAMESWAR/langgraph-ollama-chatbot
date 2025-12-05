# LangGraph + Ollama Chatbot

A powerful local chatbot application built with [LangGraph](https://langchain-ai.github.io/langgraph/), [Ollama](https://ollama.com/) (Llama 3.2), and [Streamlit](https://streamlit.io/).

This project offers multiple versions of the chatbot, ranging from a simple conversational agent to an advanced assistant equipped with tools (Search, Calculator, Weather, Stock Prices) and persistent memory, including PDF RAG (Retrieval-Augmented Generation) and MCP (Model Context Protocol) integration.

## Features

- **Local LLM Inference**: Runs completely locally using Ollama and Llama 3.2.
- **State Management**: Uses LangGraph for robust state handling and message history.
- **Persistent Memory**: Saves chat sessions using SQLite (in the advanced version).
- **RAG Support**: Upload PDFs to chat with your documents using `faiss-cpu` and `pypdf`.
- **Tool Integration**:
  - **Web Search**: DuckDuckGo
  - **Stock Prices**: Alpha Vantage
  - **MCP Tools**: Integrates with Model Context Protocol servers (e.g., local arithmetic server, remote expense server).
- **Streamlit UI**: A clean, responsive, and interactive chat interface with sidebar history and file uploads.

## Prerequisites

1.  **Python 3.8+**
2.  **Ollama**: Installed and running.
3.  **Llama 3.2 Model**:
    ```bash
    ollama pull llama3.2:3b
    ollama pull mxbai-embed-large:latest
    ```
    *Note: `mxbai-embed-large` is used for embedding PDF documents.*
4.  **API Keys** (For Advanced Version):
    -   Alpha Vantage API Key (for stock prices) - [Get Key](https://www.alphavantage.co/)
    -   *Optional*: Other keys if extending features.

## Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd CHATBOT_USING_LANGGRAPH
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  **(Optional) Configure Environment Variables**:
    Create a `.env` file in the root or `databasee` directory:
    ```env
    ALPHAVANTAGE_API_KEY=your_api_key_here
    ```

## Usage

### 1. Simple Chatbot
A basic conversational agent without tools or persistence.

**Standalone version:**
```bash
streamlit run chatbot.py
```

**Modular version:**
```bash
streamlit run chatbot_frontend.py
```

### 2. Advanced Tool-Enhanced Chatbot (Recommended)
Includes persistent memory (SQLite), RAG (PDF Chat), and access to external tools (Search, Stocks, MCP).

Navigate to the `databasee` directory and run:
```bash
cd databasee
streamlit run frontend.py
```

**Features in Advanced Mode:**
*   **Upload Files**: Use the sidebar to upload PDFs or text files. The bot can answer questions based on the uploaded content.
*   **Tools**: Ask for stock prices ("price of AAPL"), perform searches, or use connected MCP tools.
*   **History**: Chat sessions are saved. View past conversations in the sidebar.

## Project Structure

-   `chatbot.py`: Simple standalone chatbot application.
-   `chatbot_backend.py` / `chatbot_frontend.py`: Modularized basic chatbot.
-   `databasee/`: Directory for the advanced chatbot.
    -   `backendd.py`: Core logic for tools, LangGraph nodes, RAG ingestion, and SQLite persistence.
    -   `frontend.py`: Advanced Streamlit UI with file upload and chat history.
    -   `chatbot.db`: SQLite database for storing chat history.
-   `requirements.txt`: Project dependencies.
-   `MCPSERVER/`: Contains a sample local MCP server.

## Troubleshooting

-   **Ollama Connection**: Ensure Ollama is running (`ollama serve`).
-   **Model Missing**: If the bot fails to start, make sure you have pulled `llama3.2:3b`.
-   **Imports**: If you see `ModuleNotFoundError`, check that `requirements.txt` is fully installed.
