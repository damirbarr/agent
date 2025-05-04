from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from pydantic import BaseModel, Field
from typing import List, Optional

# Import tools from modules
from src.tools.base import search_tool, wiki_tool, save_tool, shell_tool
from src.memory.tools import memory_tools
from src.reasoning.tools import reasoning_tools
from src.agent.commands import CommandProcessor, create_default_processor

class ResearchResponse(BaseModel):
    topic: str
    summary: str
    sources: list[str]
    tools_used: list[str]
    reasoning: Optional[str] = Field(default=None, description="The reasoning process used to arrive at the answer")

def create_agent(model="gpt-4o-mini"):
    """Create and configure an agent with all necessary tools."""

    # Select the LLM
    if "claude" in model:
        llm = ChatAnthropic(model=model)
    else:
        llm = ChatOpenAI(model=model)

    # Create the output parser
    parser = PydanticOutputParser(pydantic_object=ResearchResponse)

    # Define the prompt template
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

    # Create the agent
    agent = create_tool_calling_agent(
        llm=llm,
        prompt=prompt,
        tools=tools
    )

    # Create the agent executor
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    return agent_executor, parser
