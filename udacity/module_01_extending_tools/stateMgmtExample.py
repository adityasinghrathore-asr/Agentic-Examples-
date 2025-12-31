from typing import TypedDict
from lib.state_machine import (
    StateMachine,
    Step,
    EntryPoint,
    Termination,
)

## Basic Example of State Management using a State Machine

class Schema(TypedDict):
    """Schema defining the structure of our state.
    
    Attributes:
        input: The input value to process
        output: The processed output value
    """
    input: int
    output: int


def step_input(state: Schema) -> Schema:
    """First step: Increment the input value.
    
    Args:
        state: Current state containing input value
        
    Returns:
        Updated state with incremented value in output
    """
    return {"output": state["input"] + 1}


def step_double(state: Schema) -> Schema:
    """Second step: Double the previous output.
    
    Args:
        state: Current state containing output from previous step
        
    Returns:
        Updated state with doubled output value
    """
    return {"output": state["output"] * 2}


# 2. Advanced State Management: Routing and Loops   

class CounterSchema(TypedDict):
    """Schema for a counter-based workflow.

    Attributes:
        count: Current counter value
        max_value: Maximum value before termination
    """
    count: int
    max_value: int


def increment_counter(state: CounterSchema) -> CounterSchema:
    """Increment the counter value.
    
    Args:
        state: Current state with counter value
        
    Returns:
        Updated state with incremented counter
    """
    return {"count": state["count"] + 1}



def demo_basic_workflow():
    """Demo 1: Basic Example of State Management using a State Machine"""
    print("=" * 60)
    print("Demo 1: Basic State Management with Linear Workflow")
    print("=" * 60)
    
    # Create our state machine instance
    workflow = StateMachine(Schema)
    
    # Create steps
    entry = EntryPoint()
    s1 = Step("input", step_input)
    s2 = Step("double", step_double)
    termination = Termination()
    
    # Add steps to workflow
    workflow.add_steps([entry, s1, s2, termination])
    
    # Connect steps linearly
    workflow.connect(entry, s1)
    workflow.connect(s1, s2)
    workflow.connect(s2, termination)
    
    print(f"Workflow: {workflow}")
    print(f"Transitions: {workflow.transitions}")
    
    # Run the workflow with initial state
    initial_state = {"input": 4}
    print(f"\nInitial State: {initial_state}")
    
    run_object = workflow.run(initial_state)
    
    print(f"\nRun Object: {run_object}")
    print(f"\nSnapshots ({len(run_object.snapshots)}):")
    for snapshot in run_object.snapshots:
        print(f"  {snapshot}")
    
    print(f"\nFinal State: {run_object.get_final_state()}")
    print()


def demo_routing_and_loops():
    """Demo 2: Advanced State Management with Routing and Loops"""
    print("=" * 60)
    print("Demo 2: Advanced State Management - Routing and Loops")
    print("=" * 60)
    
    workflow = StateMachine(CounterSchema)
    
    # Create steps
    entry = EntryPoint()
    increment = Step("increment", increment_counter)
    termination = Termination()
    
    # Router logic with closure to access termination and increment
    def check_counter_router(state: CounterSchema) -> Step:
        """Determine next step based on counter value."""
        if state["count"] >= state["max_value"]:
            return termination
        return increment
    
    # Add steps to workflow
    workflow.add_steps([entry, increment, termination])
    
    # Connect steps with a conditional loop
    workflow.connect(entry, increment)
    workflow.connect(increment, [increment, termination], check_counter_router)
    
    print(f"Workflow: {workflow}")
    print(f"Transitions: {workflow.transitions}")
    
    # Run with initial state
    initial_state = {"count": 0, "max_value": 3}
    print(f"\nInitial State: {initial_state}")
    
    run_object = workflow.run(initial_state)
    
    print(f"\nRun Object: {run_object}")
    print(f"\nSnapshots ({len(run_object.snapshots)}):")
    for snapshot in run_object.snapshots:
        print(f"  {snapshot}")
    
    print(f"\nFinal State: {run_object.get_final_state()}")
    print()


def main():
    """Main function to run all demos"""
    demo_basic_workflow()
    demo_routing_and_loops()


if __name__ == "__main__":
    main()