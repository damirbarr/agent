# Ottopia AI Agent

A flexible AI research assistant built from scratch using Python and LangChain.

## Overview

This project implements an AI agent with memory capabilities, structured reasoning, and various tools for research tasks. The agent can:

- Answer queries with structured responses
- Maintain conversation memory
- Search the web using DuckDuckGo
- Query Wikipedia for information
- Read PDF documents
- Execute shell commands
- Save research outputs to text files

## Setup

1. Clone the repository
2. Install dependencies using Make:
   ```
   make install
   ```
   This will create a virtual environment and install all required packages.
3. Create a `.env` file based on `sample.env` with your API keys

## Usage

Run the assistant using Make:
```
make run
```

### Available Commands

- `help`: Show help message
- `exit`, `quit`, `bye`: End the conversation
- `memory`: Show memory summary
- `clear memory`: Clear agent's memory (with backup)
- `friendly mode`: Toggle character-by-character output

## Project Structure

- `src/agent/`: Agent implementation
- `src/memory/`: Memory management
- `src/reasoning/`: Structured reasoning components
- `src/tools/`: Tool implementations (search, Wikipedia, shell, etc.)
- `main.py`: Entry point for the application

## Dependencies

- LangChain
- Wikipedia API
- DuckDuckGo Search
- OpenAI/Anthropic integration
- Python-dotenv
- Pydantic

## License

[MIT License]