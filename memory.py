import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any

class Memory:
    """Simple file-based memory system for the AI agent."""
    
    def __init__(self, memory_file: str = "agent_memory.json"):
        self.memory_file = memory_file
        self._ensure_memory_file()
    
    def _ensure_memory_file(self) -> None:
        """Create memory file if it doesn't exist."""
        if not os.path.exists(self.memory_file):
            with open(self.memory_file, "w") as f:
                json.dump({"conversations": [], "facts": {}}, f)
    
    def _read_memory(self) -> Dict:
        """Read the current memory."""
        with open(self.memory_file, "r") as f:
            return json.load(f)
    
    def _write_memory(self, memory: Dict) -> None:
        """Write to memory file."""
        with open(self.memory_file, "w") as f:
            json.dump(memory, f, indent=2)
    
    def add_conversation(self, query: str, response: Any) -> None:
        """Add a conversation to memory."""
        memory = self._read_memory()
        memory["conversations"].append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response
        })
        self._write_memory(memory)
    
    def save_fact(self, key: str, value: Any) -> None:
        """Save a fact to memory."""
        memory = self._read_memory()
        memory["facts"][key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        self._write_memory(memory)
    
    def get_fact(self, key: str) -> Optional[Any]:
        """Retrieve a fact from memory."""
        memory = self._read_memory()
        fact = memory["facts"].get(key)
        return fact["value"] if fact else None
    
    def get_recent_conversations(self, limit: int = 5) -> List[Dict]:
        """Get recent conversations."""
        memory = self._read_memory()
        return memory["conversations"][-limit:]
    
    def summarize_memory(self) -> Dict:
        """Provide a summary of what's in memory."""
        memory = self._read_memory()
        return {
            "conversation_count": len(memory["conversations"]),
            "fact_count": len(memory["facts"]),
            "fact_keys": list(memory["facts"].keys())
        }
    
    def clear_memory(self) -> str:
        """Clear memory by backing up the current file and creating a new one."""
        if not os.path.exists(self.memory_file):
            return "No memory file exists yet."
        
        # Create a backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{os.path.splitext(self.memory_file)[0]}_{timestamp}.json"
        
        try:
            # Copy the current memory file to the backup
            shutil.copy2(self.memory_file, backup_file)
            
            # Create a new empty memory file
            with open(self.memory_file, "w") as f:
                json.dump({"conversations": [], "facts": {}}, f)
                
            return f"Memory cleared. Backup saved as {backup_file}"
        except Exception as e:
            return f"Error clearing memory: {str(e)}"


# Global memory instance
memory = Memory() 