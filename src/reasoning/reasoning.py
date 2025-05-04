from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

class ThoughtStep(BaseModel):
    """A single step in the reasoning process."""
    thought: str = Field(description="The agent's thought")
    
    def __str__(self) -> str:
        return f"Thought: {self.thought}"

class ActionStep(BaseModel):
    """An action the agent decides to take."""
    tool: str = Field(description="The tool to use")
    tool_input: Dict[str, Any] = Field(description="The input to the tool")
    reasoning: str = Field(description="Why this tool was chosen")
    
    def __str__(self) -> str:
        return f"Action: Use {self.tool} because {self.reasoning}"

class Reasoning(BaseModel):
    """A chain of thoughts and actions representing the agent's reasoning process."""
    steps: List[Union[ThoughtStep, ActionStep]] = Field(default_factory=list, 
                                               description="The steps in the reasoning process")
    final_answer: Optional[str] = Field(default=None, 
                                     description="The final answer after reasoning")
    
    def add_thought(self, thought: str) -> None:
        """Add a thought to the reasoning chain."""
        self.steps.append(ThoughtStep(thought=thought))
    
    def add_action(self, tool: str, tool_input: Dict[str, Any], reasoning: str) -> None:
        """Add an action to the reasoning chain."""
        self.steps.append(ActionStep(
            tool=tool,
            tool_input=tool_input,
            reasoning=reasoning
        ))
    
    def set_final_answer(self, answer: str) -> None:
        """Set the final answer."""
        self.final_answer = answer
    
    def get_chain_of_thought(self) -> str:
        """Get the full chain of thought as a string."""
        return "\n".join(str(step) for step in self.steps)
    
    def __str__(self) -> str:
        """String representation of the reasoning."""
        result = self.get_chain_of_thought()
        if self.final_answer:
            result += f"\nFinal Answer: {self.final_answer}"
        return result 