from langchain.tools import tool

@tool
def analyze_problem(problem: str) -> str:
    """
    Break down a complex problem into smaller, more manageable steps.
    
    Args:
        problem: The problem statement to analyze
    
    Returns:
        A structured breakdown of the problem
    """
    steps = [
        "1. Understand the problem: what are we trying to solve?",
        f"Problem: {problem}",
        "2. Identify the key components of the problem:",
        "   - What information do we have?",
        "   - What are we trying to find out?",
        "   - What constraints or requirements exist?",
        "3. Determine what tools or approaches might help solve this",
        "4. Plan the steps to reach a solution",
    ]
    return "\n".join(steps)

@tool
def evaluate_options(options: str, criteria: str) -> str:
    """
    Evaluate different options based on given criteria.
    
    Args:
        options: Comma-separated list of options to evaluate
        criteria: Criteria to evaluate the options against
    
    Returns:
        An analysis of the options
    """
    option_list = [opt.strip() for opt in options.split(",")]
    result = [f"Evaluating {len(option_list)} options based on: {criteria}\n"]
    
    for i, option in enumerate(option_list):
        result.append(f"Option {i+1}: {option}")
        result.append(f"  Evaluation: This option should be considered in relation to the criteria.")
    
    result.append("\nRecommendation: Consider the evaluations above to make a decision.")
    return "\n".join(result)

@tool
def chain_of_thought(question: str) -> str:
    """
    Apply chain-of-thought reasoning to a question.
    
    Args:
        question: The question to reason about
    
    Returns:
        A step-by-step reasoning process
    """
    steps = [
        f"Question: {question}",
        "Let me think through this step-by-step:",
        "1. First, I need to understand what is being asked.",
        "2. Next, I'll consider what information I have or need to solve this.",
        "3. Then, I'll work through the problem logically.",
        "4. Finally, I'll review my reasoning to check for errors or omissions.",
        "",
        "This structured approach helps ensure thorough analysis of the question."
    ]
    return "\n".join(steps)

# Collect all reasoning tools
reasoning_tools = [analyze_problem, evaluate_options, chain_of_thought] 