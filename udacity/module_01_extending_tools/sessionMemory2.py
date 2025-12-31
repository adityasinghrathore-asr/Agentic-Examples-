from typing import TypedDict, List, Optional
import json
from dotenv import load_dotenv

from lib.state_machine import StateMachine, Step, EntryPoint, Termination, Run
from lib.llm import LLM
from lib.messages import AIMessage, UserMessage, SystemMessage, ToolMessage, BaseMessage
from lib.tooling import ToolCall, tool
from lib.memory import ShortTermMemory

load_dotenv()

class AgentState(TypedDict):
    user_query: str  # The current user query being processed
    instructions: str  # System instructions for the agent
    messages: List[dict]  # List of conversation messages
    current_tool_calls: Optional[List[ToolCall]]  # Current pending tool calls
    session_id: str  # Session identifier for memory management


class MemoryAgent:
    def __init__(self,
                 model_name: str,
                 instructions: str,
                 tools: List = None,
                 temperature: float = 0.7):
        """
        Initialize a MemoryAgent instance
        
        Args:
            model_name: Name/identifier of the LLM model to use
            instructions: System instructions for the agent
            tools: Optional list of tools available to the agent
            temperature: Temperature parameter for LLM (default: 0.7)
        """
        self.instructions = instructions
        self.tools = tools if tools else []
        self.tools_map = {tool.name: tool for tool in self.tools}
        self.model_name = model_name
        self.temperature = temperature
        
        # Initialize memory and state machine
        self.memory = ShortTermMemory()
        self.workflow = self._create_state_machine()

    def _prepare_messages_step(self, state: AgentState) -> AgentState:
        """Step logic: Prepare messages for LLM consumption"""
        messages = state.get("messages", [])
        
        # If no messages exist, start with system message
        if not messages:
            messages = [SystemMessage(content=state["instructions"])]
            
        # Add the new user message
        messages.append(UserMessage(content=state["user_query"]))
        
        return {
            "messages": messages,
            "session_id": state["session_id"]
        }

    def _llm_step(self, state: AgentState) -> AgentState:
        """Step logic: Process the current state through the LLM"""
        # Initialize LLM
        llm = LLM(
            model=self.model_name,
            temperature=self.temperature,
            tools=self.tools
        )

        response = llm.invoke(state["messages"])
        tool_calls = response.tool_calls if response.tool_calls else None

        # Create AI message with content and tool calls
        ai_message = AIMessage(content=response.content, tool_calls=tool_calls)
        
        return {
            "messages": state["messages"] + [ai_message],
            "current_tool_calls": tool_calls,
            "session_id": state["session_id"]
        }

    def _tool_step(self, state: AgentState) -> AgentState:
        """Step logic: Execute any pending tool calls"""
        tool_calls = state["current_tool_calls"] or []
        tool_messages = []
        
        for call in tool_calls:
            function_name = call.function.name
            function_args = json.loads(call.function.arguments)
            tool_call_id = call.id
            
            # Efficient tool lookup using dictionary
            tool = self.tools_map.get(function_name)
            if tool:
                result = tool(**function_args)
                tool_message = ToolMessage(
                    content=json.dumps(result),
                    tool_call_id=tool_call_id,
                    name=function_name,
                )
                tool_messages.append(tool_message)
        
        return {
            "messages": state["messages"] + tool_messages,
            "current_tool_calls": None,
            "session_id": state["session_id"]
        }

    def _create_state_machine(self) -> StateMachine:
        """Create the internal state machine for the agent"""
        machine = StateMachine(AgentState)
        
        # Create steps
        entry = EntryPoint()
        message_prep = Step("message_prep", self._prepare_messages_step)
        llm_processor = Step("llm_processor", self._llm_step)
        tool_executor = Step("tool_executor", self._tool_step)
        termination = Termination()
        
        machine.add_steps([entry, message_prep, llm_processor, tool_executor, termination])
        
        # Define router function
        def check_tool_calls(state: AgentState) -> Step:
            """Determine next step based on whether there are pending tool calls"""
            if state.get("current_tool_calls"):
                return tool_executor
            return termination
        
        # Connect workflow steps
        machine.connect(entry, message_prep)
        machine.connect(message_prep, llm_processor)
        machine.connect(llm_processor, [tool_executor, termination], check_tool_calls)
        machine.connect(tool_executor, llm_processor)
        
        return machine

    def invoke(self, query: str, session_id: Optional[str] = None) -> Run:
        """
        Run the agent on a query
        
        Args:
            query: The user's query to process
            session_id: Optional session identifier (uses "default" if None)
            
        Returns:
            The final run object after processing
        """
        session_id = session_id or "default"

        # Create session if it doesn't exist
        self.memory.create_session(session_id)

        # Get previous messages from last run if available
        previous_messages = []
        last_run: Run = self.memory.get_last_object(session_id)
        if last_run:
            last_state = last_run.get_final_state()
            if last_state:
                previous_messages = last_state["messages"]

        initial_state: AgentState = {
            "user_query": query,
            "instructions": self.instructions,
            "messages": previous_messages,
            "current_tool_calls": None,
            "session_id": session_id,
        }

        run_object = self.workflow.run(initial_state)
        
        # Store the complete run object in memory
        self.memory.add(run_object, session_id)
        
        return run_object

    def get_session_runs(self, session_id: Optional[str] = None) -> List[Run]:
        """Get all Run objects for a session
        
        Args:
            session_id: Optional session ID (uses "default" if None)
            
        Returns:
            List of Run objects in the session
        """
        return self.memory.get_all_objects(session_id)

    def reset_session(self, session_id: Optional[str] = None):
        """Reset memory for a specific session
        
        Args:
            session_id: Optional session to reset (uses "default" if None)
        """
        self.memory.reset(session_id)

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

def demo_memory_agent():
    """Demo: Memory-enabled agent with session-based conversation history"""
    print("=" * 60)
    print("Demo: Memory-Enabled Agent with Session Management")
    print("=" * 60)
    
    # Initialize agent with tools
    tools = [get_games]
    agent = MemoryAgent(
        model_name="gpt-4o-mini",
        instructions="You can bring insights about a game dataset based on user questions",
        tools=tools
    )
    
    def print_summary(run: Run, label: str):
        """Print a summary of a run's final state"""
        final_state = run.get_final_state()
        messages = final_state["messages"]
        last_msg = messages[-1]
        print(f"\n{label}")
        print(messages)
        print(f"Message count: {len(messages)}")
        print(f"Last response: {last_msg.content[:150]}..." if len(str(last_msg.content)) > 150 else f"Last response: {last_msg.content}")
       


    # Session 1: First interaction
    print("\n--- Session 'games': Query 1 ---")
    query1 = "What's the best game in the dataset?"
    print(f"User: {query1}")
    run1 = agent.invoke(query1, "games")
    print_summary(run1, "Result:")

    # Session 1: Second interaction (maintains context)
    print("\n--- Session 'games': Query 2 (with context) ---")
    query2 = "And what was its score?"
    print(f"User: {query2}")
    run2 = agent.invoke(query2, "games")
    print_summary(run2, "Result:")

    # Session 2: New conversation (no context from Session 1)
    print("\n--- Session 'other_session': Query 1 (isolated) ---")
    query3 = "What's the worst game?"
    print(f"User: {query3}")
    run3 = agent.invoke(query3, "other_session")
    print_summary(run3, "Result:")

    
    # Show session statistics
    print("\n" + "=" * 60)
    print("Session Statistics")
    print("=" * 60)
    all_sessions = agent.memory.get_all_sessions()
    print(f"Active sessions: {all_sessions}")
    print(f"  'games' session: {len(agent.get_session_runs('games'))} runs")
    print(f"  'other_session' session: {len(agent.get_session_runs('other_session'))} runs")
    print()


def main():
    """Main function to run the demo.
    
    Demonstrates how memory-enabled agents maintain conversation history
    across queries within sessions while keeping different sessions isolated.
    """
    demo_memory_agent()

if __name__ == "__main__":
    main()