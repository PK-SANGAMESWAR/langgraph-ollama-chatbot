# LangGraph + Ollama Chatbot

A powerful local chatbot application built with [LangGraph](https://langchain-ai.github.io/langgraph/), [Ollama](https://ollama.com/) (Llama 3.2), and [Streamlit](https://streamlit.io/).

This project offers multiple versions of the chatbot, ranging from a simple conversational agent to an advanced assistant equipped with tools (Search, Calculator, Weather, etc.) and persistent memory.

## Features

- **Local LLM Inference**: Runs completely locally using Ollama and Llama 3.2.
- **State Management**: Uses LangGraph for robust state handling and message history.
- **Persistent Memory**: Saves chat sessions using SQLite (in the advanced version).
- **Tool Integration**: Equipped with various tools:
  - Web Search (DuckDuckGo)
  - Calculator
  - Weather Information
  - Stock Prices
  - Wikipedia Search
  - Unit & Currency Conversion
  - URL Content Fetching
- **Streamlit UI**: A clean, responsive, and interactive chat interface.

## Prerequisites

1. **Python 3.8+**
2. **Ollama**: Installed and running.
3. **Llama 3.2 Model**:
   ```bash
   ollama pull llama3.2:3b
   ```
4. **API Keys** (For Advanced Version):
   - OpenWeatherMap API Key (for weather)
   - Alpha Vantage API Key (for stock prices)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd CHATBOT_USING_LANGGRAPH
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **(Optional) Configure Environment Variables**:
   Create a `.env` file in the `databasee` directory (or root) if you plan to use the tool-enhanced version:
   ```env
   WEATHER_API_KEY=your_api_key_here
   ALPHAVANTAGE_API_KEY=your_api_key_here
   ```

## Usage

### 1. Basic Chatbot
A simple conversational agent.

**Single-file version:**
```bash
streamlit run chatbot.py
```

**Modular version:**
```bash
streamlit run chatbot_frontend.py
```

### 2. Advanced Tool-Enhanced Chatbot
Includes persistent memory (SQLite) and access to external tools.

Navigate to the `databasee` directory and run:
```bash
cd databasee
streamlit run frontend.py
```
*Note: Ensure you have your `.env` file configured for external tools to work.*

## Project Structure

- `chatbot.py`: Simple standalone chatbot application.
- `chatbot_backend.py` / `chatbot_frontend.py`: Modularized basic chatbot.
- `databasee/`: Directory for the advanced chatbot.
  - `backendd.py`: Logic for tools, LangGraph nodes, and SQLite persistence.
  - `frontend.py`: Streamlit UI for the advanced chatbot.
  - `chatbot.db`: SQLite database for storing chat history.
- `requirements.txt`: Project dependencies.
