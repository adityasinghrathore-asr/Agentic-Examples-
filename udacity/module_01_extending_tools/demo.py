from typing import List, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import json
from lib.messages import UserMessage, SystemMessage, ToolMessage, AIMessage
from lib.tooling import tool
from lib.llm import LLM

load_dotenv()

temperature = 0 

class Agent:
    def __init__(self, role: str, tools: List = None):
        self.role = role
        self.tools = tools or []
        self.llm = LLM(model="gpt-4o-mini", temperature=temperature, tools=self.tools)
        self.tool_map = {tool.name: tool for tool in self.tools}

    def invoke(self, query: str) -> str:
        messages = [
            SystemMessage(content=f"You are a helpful assistant with the role of {self.role}."),
            UserMessage(content=query),
        ]
        
        # Handle tool calls in a loop
        max_iterations = 5
        for _ in range(max_iterations):
            response: AIMessage = self.llm.invoke(messages)
            
            # If no tool calls, return the final response
            if not response.tool_calls:
                return response.content or "No response generated."
            
            # Add assistant message to conversation
            messages.append(response)
            
            # Execute each tool call
            for tool_call in response.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                # Execute the tool
                if tool_name in self.tool_map:
                    try:
                        result = self.tool_map[tool_name](**tool_args)
                        tool_response = ToolMessage(
                            content=str(result),
                            tool_call_id=tool_call.id,
                            name=tool_name
                        )
                        messages.append(tool_response)
                    except Exception as e:
                        tool_response = ToolMessage(
                            content=f"Error executing tool: {str(e)}",
                            tool_call_id=tool_call.id,
                            name=tool_name
                        )
                        messages.append(tool_response)
        
        return "Max iterations reached without final answer."

@tool
def calculate(expression: str) -> float:
    """Evaluates a mathematical expression and returns the result."""
    try:
        # Safe evaluation - only allow basic math operations
        return float(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def get_games(num_games: int = 1, top: bool = True) -> str:
    """Returns information about top or bottom games from a dataset.
    
    Args:
        num_games: Number of games to return (default: 1)
        top: If True, returns top games; if False, returns bottom games (default: True)
    """
    # Sample game data
    games = [
        {"name": "The Legend of Zelda: Breath of the Wild", "rating": 97, "genre": "Action-Adventure"},
        {"name": "Super Mario Odyssey", "rating": 97, "genre": "Platform"},
        {"name": "Red Dead Redemption 2", "rating": 96, "genre": "Action-Adventure"},
        {"name": "God of War", "rating": 94, "genre": "Action-Adventure"},
        {"name": "The Witcher 3: Wild Hunt", "rating": 93, "genre": "RPG"},
        {"name": "Cyberpunk 2077", "rating": 70, "genre": "RPG"},
        {"name": "Fallout 76", "rating": 52, "genre": "RPG"},
    ]
    
    # Sort by rating
    sorted_games = sorted(games, key=lambda x: x["rating"], reverse=top)
    selected_games = sorted_games[:num_games]
    
    result = []
    for game in selected_games:
        result.append(f"{game['name']} (Rating: {game['rating']}, Genre: {game['genre']})")
    
    return "\n".join(result)

def main():
    print("=" * 60)
    print("Demo 1: Basic Agent (No Tools)")
    print("=" * 60)
    agent = Agent(role="Coding Assistant")
    response = agent.invoke("What is Python? Be concise")
    print(f"Response: {response}\n")

    print("=" * 60)
    print("Demo 2: Math Agent with Calculator Tool")
    print("=" * 60)
    math_agent = Agent(role="Math Assistant", tools=[calculate])
    response = math_agent.invoke("What is 23 * 45?")
    print(f"Response: {response}\n")

    print("=" * 60)
    print("Demo 3: Game Stats Agent")
    print("=" * 60)
    data_analyst_agent = Agent(role="Game Stats Assistant", tools=[get_games])
    response = data_analyst_agent.invoke("What's the best game in the dataset?")
    print(f"Response: {response}\n")

    print("=" * 60)
    print("Demo 4: Agent without appropriate tool")
    print("=" * 60)
    response = data_analyst_agent.invoke("If I multiply 3 by 5, what do I get? Then add 7")
    print(f"Response: {response}\n")

if __name__ == "__main__":
    main()  