from langchain.tools import tool
from src.memory.memory import memory

@tool
def remember_fact(key: str, value: str) -> str:
    """
    Save a fact to memory for later retrieval.

    Args:
        key: The identifier to save the fact under
        value: The fact to remember

    Returns:
        Confirmation message
    """
    memory.save_fact(key, value)
    return f"Saved fact '{value}' under key '{key}'"

@tool
def recall_fact(key: str) -> str:
    """
    Recall a fact from memory by its key.

    Args:
        key: The identifier of the fact to recall

    Returns:
        The stored fact or a message indicating it wasn't found
    """
    fact = memory.get_fact(key)
    if fact:
        return f"Recalled fact for '{key}': {fact}"
    else:
        return f"No fact found for key '{key}'"

@tool
def list_facts() -> str:
    """
    List all facts stored in memory.

    Returns:
        A summary of stored facts
    """
    summary = memory.summarize_memory()
    if summary["fact_count"] == 0:
        return "No facts stored in memory yet."

    return f"Stored facts ({summary['fact_count']} total): {', '.join(summary['fact_keys'])}"

@tool
def get_conversation_history(limit: int = 3) -> str:
    """
    Get recent conversation history.

    Args:
        limit: Number of recent conversations to retrieve (default: 3)

    Returns:
        Recent conversation history
    """
    conversations = memory.get_recent_conversations(limit)
    if not conversations:
        return "No conversation history available."

    result = f"Last {len(conversations)} conversations:\n"
    for i, conv in enumerate(conversations):
        result += f"{i+1}. Query: {conv['query']}\n"
        result += f"   Response: {str(conv['response'])[:100]}...\n"

    return result

# Collect all memory tools
memory_tools = [remember_fact, recall_fact, list_facts, get_conversation_history] 