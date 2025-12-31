from typing import List, Any, Annotated, Optional
from datetime import date
from pydantic import BaseModel, Field
from lib.messages import UserMessage, SystemMessage
from lib.tooling import tool
from lib.llm import LLM
from lib.parsers import (
    StrOutputParser,
    JsonOutputParser, 
    PydanticOutputParser, 
    ToolOutputParser,
)
from dotenv import load_dotenv
import json

load_dotenv()

chat_model = LLM()

messages = [
    SystemMessage(content="Extract the event information."),
    UserMessage(content="Alice and Bob are going to a science fair on Friday.")
]

@tool
def calendar_event(name: str, date: str, participants: list[str]):
    """Identify name of the event, date when it will happen and all the participants"""
    return {
        "name": name,
        "date": date,
        "participants": participants
    }

class CalendarEvent(BaseModel):
    """A Pydantic model representing a calendar event."""
    name: Annotated[Optional[str], Field(description="Name/Title of the event. Defaults to ''")] = None
    date: Annotated[Optional[str], Field(description="Date of the event. Defaults to ''")] = None
    participants: Annotated[Optional[list[str]], Field(description="Who will participate. Defaults to []")] = None

class ActionItem(BaseModel):
    task: Annotated[str, Field(description="The task to be completed")]
    assignee: Annotated[str, Field(description="Person responsible for the task")]
    due_date: Annotated[str, Field(description="When the task should be completed")]

class MeetingSummary(BaseModel):
    title: Annotated[str, Field(description="Title of the meeting")]
    date: Annotated[str, Field(description="Date of the meeting")]
    participants: Annotated[list[str], Field(description="List of attendees")]
    key_points: Annotated[list[str], Field(description="Key discussion points from the meeting")]
    action_items: Annotated[list[ActionItem], Field(description="List of action items with details")]       

#Create a new class, `StructuredAgent`, that extends the functionality of the existing Agent class. This class will utilize the defined Pydantic models for structured outputs:

class StructuredAgent:
    def __init__(
            self, 
            role: str = "Meeting Assistant",
            instructions: str="Summarize meetings and track action items in a structured format",
            model: str="gpt-4o-mini", 
            temperature: float=0.0, 
            tools: List[Any]=None, 
            output_model: BaseModel=None):
        

        self.model = model
        self.role = role
        self.instructions = instructions
        self.tools = tools
        self.output_model = output_model
        load_dotenv()
        self.llm = LLM(model=model, temperature=temperature, tools=tools)

    def invoke(self, user_message: str) -> dict:
        if self.output_model:
            # Get the schema of the output model to include in the prompt
            schema = self.output_model.model_json_schema()
            system_content = f"You're an AI Agent and your role is {self.role}. Your instructions: {self.instructions}\n\nReturn your response as a JSON object matching this schema: {json.dumps(schema)}. Return ONLY the JSON object, no other text."
            messages = [SystemMessage(content=system_content)]
            messages.append(UserMessage(content=user_message))
            ai_message = self.llm.invoke(messages)
            print("Content:", ai_message.content)  # Debug print
            # Clean the response - remove markdown code blocks if present
            content = ai_message.content
            if content.startswith("```"):
                # Remove markdown code blocks
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]  # Remove ```json
                elif content.startswith("```"):
                    content = content[3:]  # Remove ```
                if content.endswith("```"):
                    content = content[:-3]  # Remove trailing ```
                content = content.strip()
            print("Cleaned Content:", content)  # Debug print
            parser = JsonOutputParser()
            # Parse using the cleaned content
            ai_message.content = content
            return parser.parse(ai_message)
        else:
            messages = [SystemMessage(content=f"You're an AI Agent and your role is {self.role}. Your instructions: {self.instructions}")]
            messages.append(UserMessage(content=user_message))
            ai_message = self.llm.invoke(messages)
            return {"response": ai_message.content}


def main():
    # print("=" * 60)
    # print("Demo 1: Basic String Output Parsing")
    # print("=" * 60)
    # ai_message = chat_model.invoke(messages)
    # parser = StrOutputParser()
    # parsed_output = parser.parse(ai_message)
    # print(parsed_output)
    # print(f"Parsed Output: {parsed_output}\n")

    # print("=" * 60)
    # print("Demo 2: Working with Tools for Structured Outputs")
    # print("=" * 60)
    # chat_model_with_tools = LLM(tools=[calendar_event])
    # ai_message = chat_model_with_tools.invoke(messages)
    # parser = ToolOutputParser()
    # structured_output = parser.parse(ai_message)[0]["args"]
    # print(f"structured_output: {structured_output}\n")

    # print("=" * 60)
    # print("Demo 3: Using Pydantic Models for Validation")
    # print("=" * 60)
    # json_messages = [
    #     SystemMessage(content="Extract the event information and return it as a JSON object with keys: name, date, participants. Return ONLY the JSON object, no other text."),
    #     UserMessage(content="Alice and Bob are going to a science fair on Friday.")
    # ]
    # ai_message = chat_model.invoke(json_messages)
    # parser = JsonOutputParser()
    # json_output = parser.parse(ai_message)
    # print(f"JSON Output: {json_output}\n")
    
    # parser = PydanticOutputParser(model_class=CalendarEvent)
    # event: CalendarEvent = parser.parse(ai_message)
    # print(f"Event Name: {event.name}")
    # print(f"Event Date: {event.date}\n") 
    # print(f"Event Participants: {event.participants}\n")

    # print("=" * 60)
    # print("Demo 4: Accessing Parsed Data from Pydantic Models")
    # print("=" * 60)
    # participants = event.participants
    # print(f"Event Participants: {participants}\n")

    print("=" * 60)
    print("Demo 5: Accessing Parsed Data from Pydantic Models")
    print("=" * 60)

    meeting_agent = StructuredAgent(
    role="Meeting Assistant",
    instructions="Summarize meetings and track action items in a structured format",
    output_model=MeetingSummary
    )

    meeting_transcript = """
        Project Planning Meeting - March 15, 2024
        Attendees: John, Sarah, Mike
        Discussion:

        * Reviewed Q1 project timeline
        * Discussed resource allocation
        * Identified potential risks
        Next steps:
        * John will update the project plan by next Friday
        * Sarah needs to coordinate with the design team by Wednesday
        * Mike will prepare the risk assessment document by end of month
    """

    summary = meeting_agent.invoke(meeting_transcript)
    print(json.dumps(summary, indent=2))

    validated_summary = MeetingSummary(**summary)
    print("Meeting Title:", validated_summary.title)
    print("\nParticipants:")
    for participant in validated_summary.participants:
        print(f"- {participant}")
    print("\nAction Items:")
    for item in validated_summary.action_items:
        print(f"- {item.task} (Assigned to: {item.assignee}, Due: {item.due_date})")


if __name__ == "__main__":
    main()  