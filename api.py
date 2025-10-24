from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uuid
import os
import uvicorn

# Import the agent components
from src.agent import create_agent
from src.memory import memory

# API models
class QueryRequest(BaseModel):
    query: str

class CommandRequest(BaseModel):
    command: str

class SessionResponse(BaseModel):
    session_id: str
    message: str

class QueryResponse(BaseModel):
    topic: str
    summary: str
    reasoning: Optional[str] = None
    sources: List[str] = []
    tools_used: List[str] = []

# Session management
active_sessions: Dict[str, Dict[str, Any]] = {}

app = FastAPI(title="AI Research Assistant API")

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get session
async def get_session(request: Request, response: Response, session_id: Optional[str] = None):
    # Check for session_id in cookie if not provided directly
    if not session_id and request.cookies:
        session_id = request.cookies.get("session_id")
    
    if session_id and session_id in active_sessions:
        return active_sessions[session_id]
    
    # Create new session
    new_session_id = str(uuid.uuid4())
    agent_executor, parser = create_agent()
    
    active_sessions[new_session_id] = {
        "session_id": new_session_id,
        "agent_executor": agent_executor,
        "parser": parser,
        "friendly_mode": False
    }
    
    # Set cookie for session tracking
    response.set_cookie(key="session_id", value=new_session_id, httponly=True)
    return active_sessions[new_session_id]

@app.post("/session", response_model=SessionResponse)
async def create_session(request: Request, response: Response):
    session = await get_session(request, response)
    return SessionResponse(
        session_id=session["session_id"],
        message="New session created successfully"
    )

@app.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest, 
    request_obj: Request,
    response: Response,
    session: Dict[str, Any] = Depends(get_session)
):
    try:
        agent_executor = session["agent_executor"]
        parser = session["parser"]
        
        # Process query through agent
        raw_response = agent_executor.invoke({"query": request.query})
        
        # Parse structured response
        structured_response = parser.parse(raw_response.get("output"))
        
        # Save conversation to memory
        memory.add_conversation(request.query, structured_response.model_dump())
        
        return structured_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.post("/command", response_model=Dict[str, Any])
async def execute_command(
    request: CommandRequest,
    request_obj: Request,
    response: Response,
    session: Dict[str, Any] = Depends(get_session)
):
    cmd = request.command.lower().strip()
    
    # Help command
    if cmd == "help":
        return {"result": get_help_text(), "type": "info"}

    # Memory summary command
    if cmd == "memory":
        summary = memory.summarize_memory()
        result = ["=== Memory Summary ==="]
        result.append(f"- Conversations: {summary['conversation_count']}")
        result.append(f"- Stored Facts: {summary['fact_count']}")
        if summary['fact_keys']:
            result.append(f"- Fact Keys: {', '.join(summary['fact_keys'])}")
        return {"result": "\n".join(result), "type": "info"}

    # Clear memory command
    if cmd == "clear memory":
        result = memory.clear_memory()
        return {"result": result, "type": "info"}

    # Toggle friendly mode
    if cmd == "friendly mode":
        # Get current state and toggle it
        current_mode = session.get("friendly_mode", False)
        session["friendly_mode"] = not current_mode
        
        # Get new state after toggling
        new_mode = session["friendly_mode"]
        status = "ON" if new_mode else "OFF"
        
        return {"result": f"🤖 Friendly mode: {status}", "type": "info"}
    
    # Not a recognized command
    return {"result": "Unknown command. Type 'help' to see available commands.", "type": "error"}

def get_help_text():
    """Get the help text as a string."""
    lines = ["=== Available Commands ==="]
    lines.append("- 'help': Show this help message")
    lines.append("- 'memory': Show memory summary")
    lines.append("- 'clear memory': Clear agent's memory (with backup)")
    lines.append("- 'friendly mode': Toggle character-by-character output")
    lines.append("=========================")
    return "\n".join(lines)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "active_sessions": len(active_sessions)}

if __name__ == "__main__":
    # For development only - use a proper ASGI server in production
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
 