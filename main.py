from dotenv import load_dotenv
import time
import sys

# Import agent components from restructured modules
from src.agent import create_agent
from src.memory import memory

load_dotenv()

def print_char_by_char(text, delay=0.01):
    """Print text character by character with a delay."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")

def get_help_text():
    """Get the help text as a string."""
    lines = ["\n=== Available Commands ==="]
    lines.append("- 'help': Show this help message")
    lines.append("- 'exit', 'quit', 'bye': End the conversation")
    lines.append("- 'memory': Show memory summary")
    lines.append("- 'clear memory': Clear agent's memory (with backup)")
    lines.append("- 'friendly mode': Toggle character-by-character output")
    lines.append("=========================")
    return "\n".join(lines)

def display_help():
    """Display available commands to the user."""
    print(get_help_text())

def process_command(cmd, friendly_mode):
    """Process a command and return (result, new_friendly_mode, is_exit)."""
    # Help command
    if cmd == "help":
        return get_help_text(), friendly_mode, False

    # Exit commands
    if cmd in ["exit", "quit", "bye"]:
        return "Goodbye! Thank you for chatting.", friendly_mode, True

    # Memory summary command
    if cmd == "memory":
        summary = memory.summarize_memory()
        result = ["\n=== Memory Summary ==="]
        result.append(f"- Conversations: {summary['conversation_count']}")
        result.append(f"- Stored Facts: {summary['fact_count']}")
        if summary['fact_keys']:
            result.append(f"- Fact Keys: {', '.join(summary['fact_keys'])}")
        return "\n".join(result), friendly_mode, False

    # Clear memory command
    if cmd == "clear memory":
        result = memory.clear_memory()
        return f"\n{result}", friendly_mode, False

    # Toggle friendly mode
    if cmd == "friendly mode":
        new_friendly_mode = not friendly_mode
        status = "ON" if new_friendly_mode else "OFF"
        return f"\n🤖 Friendly mode: {status}", new_friendly_mode, False

    # Not a command
    return None, friendly_mode, False

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

        # Check if it's a command
        result, friendly_mode, should_exit = process_command(query.lower().strip(), friendly_mode)

        # If it was a command
        if result is not None:
            print(result)
            if should_exit:
                break
            continue

        # Not a command, process as a query to the agent
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