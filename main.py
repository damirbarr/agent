from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from typing import List, Optional
import time
import sys

# Import existing tools
from tools import search_tool, wiki_tool, save_tool, shell_tool

# Import new modules
from memory import memory
from memory_tools import memory_tools
from reasoning_tools import reasoning_tools

load_dotenv()

class ResearchResponse(BaseModel):
    topic: str
    summary: str
    sources: list[str]
    tools_used: list[str]
    reasoning: Optional[str] = Field(default=None, description="The reasoning process used to arrive at the answer")


# llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
llm = ChatOpenAI(model="gpt-4o-mini")
parser = PydanticOutputParser(pydantic_object=ResearchResponse)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are an advanced AI agent that helps developers with research and problem-solving.
            
            When answering a question, follow these steps:
            1. THINK: Break down the problem and consider different approaches
            2. REASON: Explain your thought process step by step
            3. USE TOOLS: Gather necessary information using available tools
            4. REMEMBER: Store important facts in memory for future reference
            5. ANSWER: Provide a clear, comprehensive answer
            
            Use memory tools to recall previous conversations or facts when relevant.
            Use reasoning tools to structure your thinking on complex problems.
            
            Always provide your reasoning process to show how you arrived at your answer.
            
            Wrap the output in this format and provide no other text\n{format_instructions}
            """,
        ),
        ("placeholder", "{chat_history}"), # filled by the AgentExecutor
        ("human", "{query}"), # filled by the user
        ("placeholder", "{agent_scratchpad}"), # filled by the AgentExecutor
    ]
).partial(format_instructions=parser.get_format_instructions())

# Combine all tools
tools = [search_tool, wiki_tool, save_tool, shell_tool] + memory_tools + reasoning_tools

agent = create_tool_calling_agent(
    llm=llm,
    prompt=prompt,
    tools=tools
)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

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
    
    chat_history = []
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