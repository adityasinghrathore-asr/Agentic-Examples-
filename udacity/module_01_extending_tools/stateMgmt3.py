
from typing import TypedDict, List, Optional, Union
import json
from dotenv import load_dotenv

from lib.state_machine import StateMachine, Step, EntryPoint, Termination, Run
from lib.llm import LLM
from lib.messages import AIMessage, UserMessage, SystemMessage, ToolMessage
from lib.tooling import Tool, ToolCall, tool

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


class Agent:
    def __init__(self, 
                 model_name: str,
                 instructions: str, 
                 tools: List[Tool] = None,
                 temperature: float = 0.7):
        """
        Initialize an Agent instance
        
        Args:
            model_name: Name/identifier of the LLM model to use
            instructions: System instructions for the agent
            tools: Optional list of tools available to the agent
            temperature: Temperature parameter for LLM (default: 0.7)
        """
        self.instructions = instructions
        self.tools = tools if tools else []
        self.model_name = model_name
        self.temperature = temperature
                
        # Initialize state machine
        self.workflow = self._create_state_machine()

    def _prepare_messages_step(self, state: AgentState) -> AgentState:
        """Step logic: Prepare messages for LLM consumption"""

        messages = [
            SystemMessage(content=state["instructions"]),
            UserMessage(content=state["user_query"])
        ]
        
        return {
            "messages": messages
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
            "current_tool_calls": tool_calls
        }

    def _tool_step(self, state: AgentState) -> AgentState:
        """Step logic: Execute any pending tool calls"""
        tool_calls = state["current_tool_calls"] or []
        tool_messages = []
        
        for call in tool_calls:
            # Access tool call data correctly
            function_name = call.function.name
            function_args = json.loads(call.function.arguments)
            tool_call_id = call.id
            # Find the matching tool
            tool = next((t for t in self.tools if t.name == function_name), None)
            if tool:
                result = tool(**function_args)
                tool_messages.append(
                    ToolMessage(
                        content=json.dumps(result), 
                        tool_call_id=tool_call_id, 
                        name=function_name, 
                    )
                )
        
        # Clear tool calls and add results to messages
        return {
            "messages": state["messages"] + tool_messages,
            "current_tool_calls": None
        }

    def _create_state_machine(self) -> StateMachine[AgentState]:
        """Create the internal state machine for the agent"""
        machine = StateMachine[AgentState](AgentState)
        
        # Create steps
        entry = EntryPoint[AgentState]()
        message_prep = Step[AgentState]("message_prep", self._prepare_messages_step)
        llm_processor = Step[AgentState]("llm_processor", self._llm_step)
        tool_executor = Step[AgentState]("tool_executor", self._tool_step)
        termination = Termination[AgentState]()
        
        machine.add_steps([entry, message_prep, llm_processor, tool_executor, termination])
        
        # Add transitions
        machine.connect(entry, message_prep)
        machine.connect(message_prep, llm_processor)
        
        # Transition based on whether there are tool calls
        def check_tool_calls(state: AgentState) -> Union[Step[AgentState], str]:
            """Transition logic: Check if there are tool calls"""
            if state.get("current_tool_calls"):
                return tool_executor
            return termination
        
        machine.connect(llm_processor, [tool_executor, termination], check_tool_calls)
        machine.connect(tool_executor, llm_processor)  # Go back to llm after tool execution
        
        return machine

    def invoke(self, query: str) -> Run:
        """
        Run the agent on a query
        
        Args:
            query: The user's query to process
            
        Returns:
            The final run object after processing
        """

        initial_state: AgentState = {
            "user_query": query,
            "instructions": self.instructions,
            "messages": [],
        }

        run_object = self.workflow.run(initial_state)

        return run_object


@tool
def power(base:float, exponent:float):
    """Exponentatiation: base to the power of exponent"""
    
    return base ** exponent

@tool
def multiply(number_a:float, number_b:float):
    """Multiplication: number_a times number_b"""
    
    return number_a * number_b

tools = [power, multiply]

def math_state_loops():
    """Demo 2: Advanced State Management with Math State"""
    print("=" * 60)
    print("Demo 2: Advanced State Management - Math State")
    print("=" * 60)
    
    tools = [power, multiply]

    math_agent = Agent(
        model_name="gpt-4o-mini",
        tools=tools,
        instructions=(
            "You're an AI Agent very good with math operations "
            "You can answer multistep questions by sequentially calling functions. "
            "You follow a pattern of of Thought and Action. "
            "Create a plan of execution: "
            "- Use Thought to describe your thoughts about the question you have been asked. "
            "- Use Action to specify one of the tools available to you. if you don't have a tool available, you can respond directly."
            "When you think it's over, return the answer "
            "Never try to respond directly if the question needs a tool. "
            "But if you don't have a tool available, you can respond directly. "
            f"The actions you have are the Tools: {tools}. \n"
        )
    )
    
    run_object = math_agent.invoke(
        query="What's 3 to the power of 2? Take the result, then multiply it by 5.",
    )

    run_object.get_final_state()["messages"]
    print(f"\nRun Object: {run_object}")
    print(f"\nFinal State: {run_object.get_final_state()}")
    print()


def main():
    """Main function to run all demos"""
    math_state_loops()


if __name__ == "__main__":
    main()