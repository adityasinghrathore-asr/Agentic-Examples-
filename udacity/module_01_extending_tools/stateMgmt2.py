from typing import TypedDict, List, Optional
import json
from dotenv import load_dotenv

from lib.state_machine import StateMachine, Step, EntryPoint, Termination
from lib.llm import LLM
from lib.messages import AIMessage, UserMessage, SystemMessage, ToolMessage
from lib.tooling import ToolCall, tool

load_dotenv()


class AgentState(TypedDict):
    """State schema for agent workflow with LLM and tools.
    
    Attributes:
        user_query: The current user query being processed
        instructions: System instructions for the agent
        messages: List of conversation messages
        current_tool_calls: Current pending tool calls
    """
    user_query: str
    instructions: str
    messages: List[dict]
    current_tool_calls: Optional[List[ToolCall]]


# ============================================================================
# Tool Definitions
# ============================================================================
@tool
def get_games(num_games: int = 1, top: bool = True) -> str:
    """Returns the top or bottom N games with highest or lowest scores.
    
    Args:
        num_games: Number of games to return (default is 1)
        top: If True, return top games, otherwise return bottom (default is True)
        
    Returns:
        List of game dictionaries sorted by score
    """
    data = [
        {"Game": "The Legend of Zelda: Breath of the Wild", "Platform": "Switch", "Score": 98},
        {"Game": "Super Mario Odyssey", "Platform": "Switch", "Score": 97},
        {"Game": "Metroid Prime", "Platform": "GameCube", "Score": 97},
        {"Game": "Super Smash Bros. Brawl", "Platform": "Wii", "Score": 93},
        {"Game": "Mario Kart 8 Deluxe", "Platform": "Switch", "Score": 92},
        {"Game": "Fire Emblem: Awakening", "Platform": "3DS", "Score": 92},
        {"Game": "Donkey Kong Country Returns", "Platform": "Wii", "Score": 87},
        {"Game": "Luigi's Mansion 3", "Platform": "Switch", "Score": 86},
        {"Game": "Pikmin 3", "Platform": "Wii U", "Score": 85},
        {"Game": "Animal Crossing: New Leaf", "Platform": "3DS", "Score": 88}
    ]
    # Sort the games list by Score
    # If top is True, descending order
    sorted_games = sorted(data, key=lambda x: x['Score'], reverse=top)
    
    # Return the N games
    return sorted_games[:num_games]


# Tool registry
tools = [get_games]
tools_map = {tool.name: tool for tool in tools}


# ============================================================================
# Step Functions
# ============================================================================

def prepare_messages_step(state: AgentState) -> AgentState:
    """Step logic: Prepare messages for LLM consumption.
    
    Args:
        state: Current agent state with user query and instructions
        
    Returns:
        Updated state with prepared message list
    """

    messages = [
        SystemMessage(content=state["instructions"]),
        UserMessage(content=state["user_query"])
    ]
    
    return {
        "messages": messages
    }

def llm_step(state: AgentState) -> AgentState:
    """Step logic: Process the current state through the LLM.
    
    Args:
        state: Current agent state with messages
        
    Returns:
        Updated state with LLM response and any tool calls
    """

    # Initialize LLM
    llm = LLM(
        model="gpt-4o-mini",
        temperature=0.3,
        tools=tools,
    )

    response = llm.invoke(state["messages"])
    tool_calls = response.tool_calls if response.tool_calls else None

    # Create AI message with content and tool calls
    ai_message = AIMessage(content=response.content, tool_calls=tool_calls)
    
    return {
        "messages": state["messages"] + [ai_message],
        "current_tool_calls": tool_calls
    }

def tool_step(state: AgentState) -> AgentState:
    """Step logic: Execute any pending tool calls.
    
    Args:
        state: Current agent state with pending tool calls
        
    Returns:
        Updated state with tool execution results
    """
    tool_calls = state["current_tool_calls"] or []
    tool_messages = []
    
    for call in tool_calls:
        function_name = call.function.name
        function_args = json.loads(call.function.arguments)
        tool_call_id = call.id
        
        # Efficient tool lookup using dictionary
        tool = tools_map.get(function_name)
        if tool:
            result = tool(**function_args)
            tool_messages.append(
                ToolMessage(
                    content=json.dumps(result),
                    tool_call_id=tool_call_id,
                    name=function_name,
                )
            )
    
    return {
        "messages": state["messages"] + tool_messages,
        "current_tool_calls": None
    }



# ============================================================================
# Demo Implementation
# ============================================================================

def demo_agentic_workflow():
    """Demo: Agentic Workflow with Tools and LLM Integration."""
    print("=" * 60)
    print("Demo: Agentic Workflow with Tools and LLM Integration")
    print("=" * 60)

    # Create state machine
    workflow = StateMachine(AgentState)

    # Create steps
    entry = EntryPoint()
    message_prep = Step("message_prep", prepare_messages_step)
    llm_processor = Step("llm_processor", llm_step)
    tool_executor = Step("tool_executor", tool_step)
    termination = Termination()
    
    # Add all steps to workflow
    workflow.add_steps([entry, message_prep, llm_processor, tool_executor, termination])
    
    # Define router function
    def check_tool_calls(state: AgentState) -> Step:
        """Determine next step based on whether there are pending tool calls."""
        if state.get("current_tool_calls"):
            return tool_executor
        return termination

    # Connect workflow steps
    workflow.connect(entry, message_prep)
    workflow.connect(message_prep, llm_processor)
    
    # Conditional routing: If tool calls present -> tool_executor, else -> termination
    workflow.connect(
        source=llm_processor,
        targets=[tool_executor, termination],
        condition=check_tool_calls
    )
    
    # Create loop: After tool execution, return to LLM for final response
    workflow.connect(
        source=tool_executor,
        targets=llm_processor
    )

    # Define initial state
    initial_state: AgentState = {
        "user_query": "What's the best game in the dataset?",
        "instructions": "You can bring insights about a game dataset based on user questions",
        "messages": [],
    }

    print(f"\nInitial State:")
    print(f"  Query: {initial_state['user_query']}")
    print(f"  Instructions: {initial_state['instructions']}")
    
    # Run the workflow
    run_object = workflow.run(initial_state)
    final_state = run_object.get_final_state()
    
    print(f"\nWorkflow completed with {len(run_object.snapshots)} snapshots")
    print(f"\nFinal Conversation:")
    for i, msg in enumerate(final_state["messages"], 1):
        msg_type = type(msg).__name__
        content = getattr(msg, 'content', str(msg))
        if len(str(content)) > 100:
            print(f"  [{i}] {msg_type}: {str(content)[:100]}...")
        else:
            print(f"  [{i}] {msg_type}: {content}")
    print()


def main():
    """Main function to run the demo."""
    demo_agentic_workflow()


if __name__ == "__main__":
    main()