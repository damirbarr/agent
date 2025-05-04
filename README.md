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

## API Server

The project includes a REST API server that allows you to interact with the AI agent programmatically or through a web interface.

### Starting the API Server

```bash
make run-api
```

This will start the FastAPI server on http://localhost:8000. The API includes automatic interactive documentation accessible at http://localhost:8000/docs.

### API Endpoints

- `POST /session`: Create a new session with the agent
- `POST /query`: Send a query to the agent
- `POST /command`: Execute a command on the agent
- `GET /health`: Check the health of the API server

### Using the Command-Line Client

A simple command-line client is provided for testing the API:

```bash
make run-client
```

### Testing the API

Run the automated tests with pytest:

```bash
make test-api
```

This runs a suite of unit tests that verify the API's functionality, including session creation, query processing, and command execution.

## Project Structure

- `src/agent/`: Agent implementation
- `src/memory/`: Memory management
- `src/reasoning/`: Structured reasoning components
- `src/tools/`: Tool implementations (search, Wikipedia, shell, etc.)
- `main.py`: Entry point for the CLI application
- `api.py`: FastAPI server for the agent
- `client.py`: Command-line client for interacting with the API
- `test_api.py`: Test suite for the API server

## Dependencies

- LangChain
- Wikipedia API
- DuckDuckGo Search
- OpenAI/Anthropic integration
- Python-dotenv
- Pydantic
- FastAPI

## License

[MIT License]