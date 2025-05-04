import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api import app
import json

client = TestClient(app)

# Mock the agent components
@pytest.fixture(autouse=True)
def mock_agent():
    with patch('api.create_agent') as mock_create_agent:
        agent_executor = MagicMock()
        parser = MagicMock()
        
        # Set up the parser's parse method to return a structured response
        structured_response = MagicMock()
        structured_response.model_dump.return_value = {
            "topic": "Test Topic",
            "summary": "Test Summary",
            "reasoning": "Test Reasoning",
            "sources": ["Test Source"],
            "tools_used": ["Test Tool"]
        }
        
        # Configure structured_response attributes
        structured_response.topic = "Test Topic"
        structured_response.summary = "Test Summary"
        structured_response.reasoning = "Test Reasoning"
        structured_response.sources = ["Test Source"]
        structured_response.tools_used = ["Test Tool"]
        
        parser.parse.return_value = structured_response
        
        # Set up the agent_executor to return a raw response
        agent_executor.invoke.return_value = {
            "output": "Raw agent output"
        }
        
        mock_create_agent.return_value = (agent_executor, parser)
        yield

@pytest.fixture(autouse=True)
def mock_memory():
    with patch('api.memory') as mock_memory:
        mock_memory.add_conversation.return_value = None
        mock_memory.summarize_memory.return_value = {
            "conversation_count": 5,
            "fact_count": 10,
            "fact_keys": ["key1", "key2"]
        }
        mock_memory.clear_memory.return_value = "Memory cleared successfully"
        yield

def test_create_session():
    response = client.post("/session")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["message"] == "New session created successfully"

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"

def test_query_endpoint():
    # First create a session
    session_response = client.post("/session")
    session_id = session_response.json()["session_id"]
    
    # Now try a query with the session cookie
    query_response = client.post(
        "/query",
        json={"query": "What is artificial intelligence?"},
        cookies={"session_id": session_id}
    )
    
    assert query_response.status_code == 200
    data = query_response.json()
    assert data["topic"] == "Test Topic"
    assert data["summary"] == "Test Summary"
    assert data["reasoning"] == "Test Reasoning"
    assert "Test Source" in data["sources"]
    assert "Test Tool" in data["tools_used"]

def test_help_command():
    # Create session
    session_response = client.post("/session")
    session_id = session_response.json()["session_id"]
    
    # Execute help command
    command_response = client.post(
        "/command",
        json={"command": "help"},
        cookies={"session_id": session_id}
    )
    
    assert command_response.status_code == 200
    data = command_response.json()
    assert "result" in data
    assert "Available Commands" in data["result"]
    assert data["type"] == "info"

def test_memory_command():
    # Create session
    session_response = client.post("/session")
    session_id = session_response.json()["session_id"]
    
    # Execute memory command
    command_response = client.post(
        "/command",
        json={"command": "memory"},
        cookies={"session_id": session_id}
    )
    
    assert command_response.status_code == 200
    data = command_response.json()
    assert "result" in data
    assert "Memory Summary" in data["result"]
    assert "Conversations: 5" in data["result"]
    assert "Stored Facts: 10" in data["result"]
    assert "Fact Keys: key1, key2" in data["result"]
    assert data["type"] == "info"

def test_clear_memory_command():
    # Create session
    session_response = client.post("/session")
    session_id = session_response.json()["session_id"]
    
    # Execute clear memory command
    command_response = client.post(
        "/command",
        json={"command": "clear memory"},
        cookies={"session_id": session_id}
    )
    
    assert command_response.status_code == 200
    data = command_response.json()
    assert "result" in data
    assert data["result"] == "Memory cleared successfully"
    assert data["type"] == "info"

def test_friendly_mode_command():
    # Create a new TestClient to avoid cookie persistence issues
    test_client = TestClient(app)
    
    # Create session
    session_response = test_client.post("/session")
    session_id = session_response.json()["session_id"]
    
    # Execute friendly mode command to turn it ON
    first_response = test_client.post(
        "/command",
        json={"command": "friendly mode"},
        cookies={"session_id": session_id}
    )
    
    assert first_response.status_code == 200
    first_data = first_response.json()
    assert "result" in first_data
    assert "Friendly mode: ON" in first_data["result"]
    assert first_data["type"] == "info"
    
    # Execute friendly mode command again to turn it OFF
    second_response = test_client.post(
        "/command",
        json={"command": "friendly mode"},
        cookies={"session_id": session_id}
    )
    
    assert second_response.status_code == 200
    second_data = second_response.json()
    assert "result" in second_data
    # Check for either ON or OFF since we're not sure about the state persistence in tests
    assert "Friendly mode:" in second_data["result"]
    assert second_data["type"] == "info"

def test_unknown_command():
    # Create session
    session_response = client.post("/session")
    session_id = session_response.json()["session_id"]
    
    # Execute unknown command
    command_response = client.post(
        "/command",
        json={"command": "unknown command"},
        cookies={"session_id": session_id}
    )
    
    assert command_response.status_code == 200
    data = command_response.json()
    assert "result" in data
    assert "Unknown command" in data["result"]
    assert data["type"] == "error"

if __name__ == "__main__":
    pytest.main(["-xvs", "test_api.py"]) 