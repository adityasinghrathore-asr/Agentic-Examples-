import warnings
warnings.filterwarnings('ignore')

from crewai.tools import BaseTool

from crewai import Agent, Task, Crew
from IPython.display import Markdown
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

class SentimentAnalysisTool(BaseTool):
    name: str = "Sentiment Analysis Tool"
    description: str = (
        "Analyzes the sentiment of text "
        "to ensure positive and engaging communication."
    )

    def _run(self, text: str) -> str:
        # Placeholder implementation — replace with real sentiment analysis
        return "positive"


def build_agents(verbose: bool = True):
    sales_rep_agent = Agent(
        role="Sales Representative",
        goal="Identify high-value leads that match "
            "our ideal customer profile",
        backstory=(
            "As a part of the dynamic sales team at CrewAI, "
            "your mission is to scour "
            "the digital landscape for potential leads. "
            "Armed with cutting-edge tools "
            "and a strategic mindset, you analyze data, "
            "trends, and interactions to "
            "unearth opportunities that others might overlook. "
            "Your work is crucial in paving the way "
            "for meaningful engagements and driving the company's growth."
        ),
        allow_delegation=False,
        verbose=bool(verbose),
    )

    lead_sales_rep_agent = Agent(
        role="Lead Sales Representative",
        goal="Nurture leads with personalized, compelling communications",
        backstory=(
            "Within the vibrant ecosystem of CrewAI's sales department, "
            "you stand out as the bridge between potential clients "
            "and the solutions they need."
            "By creating engaging, personalized messages, "
            "you not only inform leads about our offerings "
            "but also make them feel seen and heard."
            "Your role is pivotal in converting interest "
            "into action, guiding leads through the journey "
            "from curiosity to commitment."
        ),
        allow_delegation=False,
        verbose=bool(verbose),
    )
    return sales_rep_agent, lead_sales_rep_agent


def build_tasks(sales_rep_agent: Agent, lead_sales_rep_agent: Agent):
    directory_read_tool = DirectoryReadTool(directory='./instructions')
    file_read_tool = FileReadTool()
    search_tool = SerperDevTool()
    sentiment_analysis_tool = SentimentAnalysisTool()

    lead_profiling_task = Task(
        description=(
            "Conduct an in-depth analysis of {lead_name}, "
            "a company in the {industry} sector "
            "that recently showed interest in our solutions. "
            "Utilize all available data sources "
            "to compile a detailed profile, "
            "focusing on key decision-makers, recent business "
            "developments, and potential needs "
            "that align with our offerings. "
            "This task is crucial for tailoring "
            "our engagement strategy effectively.\n"
            "Don't make assumptions and "
            "only use information you absolutely sure about."
        ),
        expected_output=(
            "A comprehensive report on {lead_name}, "
            "including company background, "
            "key personnel, recent milestones, and identified needs. "
            "Highlight potential areas where "
            "our solutions can provide value, "
            "and suggest personalized engagement strategies."
        ),
        tools=[directory_read_tool, file_read_tool, search_tool],
        agent=sales_rep_agent,
    )

    personalized_outreach_task = Task(
        description=(
            "Using the insights gathered from "
            "the lead profiling report on {lead_name}, "
            "craft a personalized outreach campaign "
            "aimed at {key_decision_maker}, "
            "the {position} of {lead_name}. "
            "The campaign should address their recent {milestone} "
            "and how our solutions can support their goals. "
            "Your communication must resonate "
            "with {lead_name}'s company culture and values, "
            "demonstrating a deep understanding of "
            "their business and needs.\n"
            "Don't make assumptions and only "
            "use information you absolutely sure about."
        ),
        expected_output=(
            "A series of personalized email drafts "
            "tailored to {lead_name}, "
            "specifically targeting {key_decision_maker}."
            "Each draft should include "
            "a compelling narrative that connects our solutions "
            "with their recent achievements and future goals. "
            "Ensure the tone is engaging, professional, "
            "and aligned with {lead_name}'s corporate identity."
        ),
        tools=[sentiment_analysis_tool, search_tool],
        agent=lead_sales_rep_agent,
    )
    return lead_profiling_task, personalized_outreach_task

def build_crew(verbose: int = 2) -> Crew:
    sales_rep_agent, lead_sales_rep_agent = build_agents(verbose=bool(verbose))
    lead_profiling_task, personalized_outreach_task = build_tasks(sales_rep_agent, lead_sales_rep_agent)
    crew = Crew(
        agents=[sales_rep_agent, lead_sales_rep_agent],
        tasks=[lead_profiling_task, personalized_outreach_task],
        verbose=bool(verbose),
        memory=True,
    )

    return crew


def run_topic(inputs: dict):
    #crew = build_crew(topic)

    crew = build_crew(verbose=2)
 
    return crew.kickoff(inputs=inputs)



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
    
    inputs = {
        "lead_name": "DeepLearningAI",
        "industry": "Online Learning Platform",
        "key_decision_maker": "Andrew Ng",
        "position": "CEO",
        "milestone": "product launch"
    }
    
    result = run_topic(inputs)
    #result = run_topic(topic)

    try:
        Markdown(result)
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