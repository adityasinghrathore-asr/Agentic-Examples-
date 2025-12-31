import warnings
warnings.filterwarnings('ignore')

from crewai.tools import BaseTool
from pydantic import BaseModel

from crewai import Agent, Task, Crew
from IPython.display import Markdown
import json
from pprint import pprint
from crewai_tools import (
    SerperDevTool,
    ScrapeWebsiteTool,
    WebsiteSearchTool,
    DirectoryReadTool,
    FileReadTool,
)

import os
import argparse
from utils import get_openai_api_key, get_serper_api_key
# Default model; can be overridden via environment
os.environ.setdefault("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
# Initialize the tools
search_tool = SerperDevTool()
scrape_tool = ScrapeWebsiteTool()

class VenueDetails(BaseModel):
    name: str
    address: str
    capacity: int
    booking_status: str


def build_agents(verbose: bool = True):
    # Agent 1: Venue Coordinator
    venue_coordinator = Agent(
        role="Venue Coordinator",
        goal="Identify and book an appropriate venue "
        "based on event requirements",
        tools=[search_tool, scrape_tool],
        verbose=verbose,
        backstory=(
            "With a keen sense of space and "
            "understanding of event logistics, "
            "you excel at finding and securing "
            "the perfect venue that fits the event's theme, "
            "size, and budget constraints."
        )
    )

    # Agent 2: Logistics Manager
    logistics_manager = Agent(
        role='Logistics Manager',
        goal=(
            "Manage all logistics for the event "
            "including catering and equipment"
        ),
        tools=[search_tool, scrape_tool],
        verbose=verbose,
        backstory=(
            "Organized and detail-oriented, "
            "you ensure that every logistical aspect of the event "
            "from catering to equipment setup "
            "is flawlessly executed to create a seamless experience."
        )
    )

    # Agent 3: Marketing and Communications Agent
    marketing_communications_agent = Agent(
        role="Marketing and Communications Agent",
        goal="Effectively market the event and "
            "communicate with participants",
        tools=[search_tool, scrape_tool],
        verbose=verbose,
        backstory=(
            "Creative and communicative, "
            "you craft compelling messages and "
            "engage with potential attendees "
            "to maximize event exposure and participation."
        )
    )
    return venue_coordinator, logistics_manager, marketing_communications_agent

def build_tasks(venue_coordinator: Agent, logistics_manager: Agent, marketing_communications_agent: Agent, inputs: dict):
    venue_task = Task(
        description=(
            f"Find a venue in {inputs['event_city']} "
            f"that meets criteria for {inputs['event_topic']}."
        ),
        expected_output=(
            "All the details of a specifically chosen "
            "venue you found to accommodate the event."
        ),
        human_input=True,
        output_json=VenueDetails,
        output_file="venue_details.json",
        # Outputs the venue details as a JSON file
        agent=venue_coordinator
    )

    logistics_task = Task(
        description=(
            f"Coordinate catering and "
            f"equipment for an event "
            f"with {inputs['expected_participants']} participants "
            f"on {inputs['tentative_date']}."
        ),
        expected_output=(
            "Confirmation of all logistics arrangements "
            "including catering and equipment setup."
        ),
        human_input=True,
        agent=logistics_manager
    )

    marketing_task = Task(
        description=(
            f"Promote the {inputs['event_topic']} "
            f"aiming to engage at least "
            f"{inputs['expected_participants']} potential attendees."
        ),
        expected_output=(
            "Report on marketing activities "
            "and attendee engagement formatted as markdown."
        ),
        async_execution=True,
        output_file="marketing_report.md",
        # Outputs the report as a text file
        agent=marketing_communications_agent
    )

    return venue_task, logistics_task, marketing_task

def build_crew(inputs: dict, verbose: int = 2) -> Crew:
    venue_coordinator, logistics_manager, marketing_communications_agent = build_agents(verbose=bool(verbose))
    venue_task, logistics_task, marketing_task = build_tasks(venue_coordinator, logistics_manager, marketing_communications_agent, inputs=inputs)
    event_management_crew = Crew(
        agents=[venue_coordinator, logistics_manager, marketing_communications_agent],
        tasks=[venue_task, logistics_task, marketing_task],
        verbose=bool(verbose),
        memory=True
    )

    return event_management_crew


def run_topic(inputs: dict):
    #crew = build_crew(topic)

    event_management_crew = build_crew(inputs=inputs, verbose=2)
 
    return event_management_crew.kickoff(inputs=inputs)



def main():
    #parser = argparse.ArgumentParser(description="Run the content crew for a topic")
    #parser.add_argument("--topic", default="The Impact of Artificial Intelligence on Modern Healthcare", help="Topic to create content for")
    #args = parser.parse_args()
    #topic = args.topic
    #print("Topic111:", topic)

    # Ensure API key available: prefer environment, then utils.get_openai_api_key()
    if not os.environ.get("OPENAI_API_KEY"):
        try:
            key = get_openai_api_key()
            if key:
                os.environ["OPENAI_API_KEY"] = key
            else:
                raise ValueError(
                    "OPENAI_API_KEY not found. Please set it in:\n"
                    "1. Environment variable: export OPENAI_API_KEY=your-key\n"
                    "2. Create a .env file in the project root with: OPENAI_API_KEY=your-key\n"
                    "3. Create ~/.openai_api_key file with your key"
                )
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(
                f"Failed to retrieve OPENAI_API_KEY: {e}\n"
                "Please set it in:\n"
                "1. Environment variable: export OPENAI_API_KEY=your-key\n"
                "2. Create a .env file in the project root with: OPENAI_API_KEY=your-key\n"
                "3. Create ~/.openai_api_key file with your key"
            )
        
    if not os.environ.get("SERPER_API_KEY"):
        try:
            key = get_serper_api_key()
            if key:
                os.environ["SERPER_API_KEY"] = key
            else:
                raise ValueError(
                    "SERPER_API_KEY not found. Please set it in:\n"
                    "1. Environment variable: export SERPER_API_KEY=your-key\n"
                    "2. Create a .env file in the project root with: SERPER_API_KEY=your-key\n"
                    "3. Create ~/.serper_api_key file with your key"
                )
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(
                f"Failed to retrieve SERPER_API_KEY: {e}\n"
                "Please set it in:\n"
                "1. Environment variable: export SERPER_API_KEY=your-key\n"
                "2. Create a .env file in the project root with: SERPER_API_KEY=your-key\n"
                "3. Create ~/.serper_api_key file with your key"
            )
    #args.topic = "Artificial Intelligence in Healthcare: Transforming Patient Care and Medical Research"


    event_details = {
    'event_topic': "Tech Innovation Conference",
    'event_description': "A gathering of tech innovators "
                         "and industry leaders "
                         "to explore future technologies.",
    'event_city': "San Francisco",
    'tentative_date': "2024-09-15",
    'expected_participants': 500,
    'budget': 20000,
    'venue_type': "Conference Hall"
}
    
    result = run_topic(inputs=event_details)
    #result = run_topic(topic)
    try:
        with open('venue_details.json') as f:
            data = json.load(f)
        pprint(data)
    except FileNotFoundError:
        print("venue_details.json not found yet")

    try:
        with open("marketing_report.md") as f:
            Markdown(f.read())
        Markdown(result)
    except FileNotFoundError:
        print("marketing_report.md not found yet")
        print(result)
    except Exception:
        print(result)

    return result


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback

        traceback.print_exc()
        raise