# LangGraph + Ollama Chatbot

A local chatbot application using [LangGraph](https://langchain-ai.github.io/langgraph/) for state management and [Ollama](https://ollama.com/) (Llama 3.2) for the LLM backend. The user interface is built with [Streamlit](https://streamlit.io/).

## Features

- **Local LLM Inference**: Uses Ollama to run Llama 3.2 locally.
- **State Management**: LangGraph manages the chat state and message history.
- **Streamlit UI**: A clean and responsive chat interface.
- **Modular Design**: Separated frontend and backend logic (in `chatbot_frontend.py` and `chatbot_backend.py`).

## Prerequisites

- Python 3.8 or higher
- [Ollama](https://ollama.com/) installed and running
- Llama 3.2 model pulled:
  ```bash
  ollama pull llama3.2:3b
  ```

## Installation

1. Clone the repository (if applicable) or navigate to the project directory.
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Option 1: All-in-One Application
Run the single-file version which contains both logic and UI:
```bash
streamlit run chatbot.py
```

### Option 2: Modular Application
Run the frontend which imports the backend logic:
```bash
streamlit run chatbot_frontend.py
```

## Project Structure

- `chatbot.py`: Standalone application with both backend graph definition and Streamlit UI.
- `chatbot_backend.py`: Contains the LangGraph definition, LLM initialization, and compilation logic.
- `chatbot_frontend.py`: Streamlit UI that imports the compiled `chatbot` from `chatbot_backend.py`.
- `requirements.txt`: List of Python dependencies.
