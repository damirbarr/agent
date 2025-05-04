from dotenv import load_dotenv
import time
import sys

# Import agent components from restructured modules
from src.agent import create_agent
from src.memory import memory

load_dotenv()

def display_help():
    """Display available commands to the user."""
    print("\n=== Available Commands ===")
    print("- 'help': Show this help message")
    print("- 'exit', 'quit', 'bye': End the conversation")
    print("- 'memory': Show memory summary")
    print("- 'clear memory': Clear agent's memory (with backup)")
    print("- 'friendly mode': Toggle character-by-character output")
    print("=========================")

def print_char_by_char(text, delay=0.01):
    """Print text character by character with a delay."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")

def main():
    print("=== AI Research Assistant ===")
    print("Type 'help' to see available commands")
    print("================================")
    
    # Create agent and parser
    agent_executor, parser = create_agent()
    friendly_mode = False
    
    while True:
        # Get user input
        query = input("\n> ")
        
        # Check for commands
        query_lower = query.lower()
        
        # Help command
        if query_lower == "help":
            display_help()
            continue
            
        # Exit commands
        if query_lower in ["exit", "quit", "bye"]:
            print("Goodbye! Thank you for chatting.")
            break
            
        # Memory summary command
        if query_lower == "memory":
            summary = memory.summarize_memory()
            print("\n=== Memory Summary ===")
            print(f"- Conversations: {summary['conversation_count']}")
            print(f"- Stored Facts: {summary['fact_count']}")
            if summary['fact_keys']:
                print(f"- Fact Keys: {', '.join(summary['fact_keys'])}")
            continue
            
        # Clear memory command
        if query_lower == "clear memory":
            result = memory.clear_memory()
            print(f"\n{result}")
            continue
            
        # Toggle friendly mode
        if query_lower == "friendly mode":
            friendly_mode = not friendly_mode
            status = "ON" if friendly_mode else "OFF"
            print(f"\n🤖 Friendly mode: {status}")
            continue
        
        try:
            # Get response from agent
            raw_response = agent_executor.invoke({"query": query})
            
            # Parse the structured response
            structured_response = parser.parse(raw_response.get("output"))
            
            # Prepare all output strings
            header = f"\n{'=' * 60}\n📋 TOPIC: {structured_response.topic}\n{'=' * 60}"
            
            answer_section = f"\n📌 ANSWER:\n{'-' * 60}\n{structured_response.summary}\n{'-' * 60}"
            
            reasoning_section = ""
            if structured_response.reasoning:
                reasoning_section = f"\n🔍 REASONING:\n{structured_response.reasoning}"
                
            sources = ", ".join(structured_response.sources) if structured_response.sources else "None"
            tools_used = ", ".join(structured_response.tools_used) if structured_response.tools_used else "None"
            metadata = f"\n📚 Sources: {sources}\n🛠️  Tools used: {tools_used}"
            
            # Print output based on mode
            if friendly_mode:
                print_char_by_char(header)
                print_char_by_char(answer_section)
                if reasoning_section:
                    print_char_by_char(reasoning_section)
                print_char_by_char(metadata)
            else:
                print(header)
                print(answer_section)
                if reasoning_section:
                    print(reasoning_section)
                print(metadata)
            
            # Save conversation to memory
            memory.add_conversation(query, structured_response.model_dump())
            
        except Exception as e:
            print(f"\n❌ Error processing response: {e}")
            print("Raw Response:", raw_response)


if __name__ == "__main__":
    main()